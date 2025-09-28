# /tests/test_orders.py

from fastapi.testclient import TestClient

# Тест главной бизнес-логики: добавление товара в заказ
def test_add_item_to_order_flow(test_client: TestClient):
    # --- ARRANGE (Подготовка данных) ---
    # 1. Создаем клиента
    client_res = test_client.post("/clients/", json={"name": "Test Client", "address": "123 Test St"})
    assert client_res.status_code == 201
    client_id = client_res.json()["id"]

    # 2. Создаем категорию
    cat_res = test_client.post("/categories/", json={"name": "Test Category"})
    assert cat_res.status_code == 201
    category_id = cat_res.json()["id"]

    # 3. Создаем товар с начальным остатком 10 штук
    product_res = test_client.post("/products/", json={
        "name": "Test Product",
        "price": 100.0,
        "category_id": category_id,
        "initial_stock": 10
    })
    assert product_res.status_code == 201
    product_id = product_res.json()["id"]
    assert product_res.json()["stock"] == 10

    # 4. Создаем пустой заказ
    order_res = test_client.post("/orders/", json={"client_id": client_id})
    assert order_res.status_code == 201
    order_id = order_res.json()["id"]
    assert order_res.json()["items"] == []

    # --- ACT (Действие) ---
    # 5. Добавляем 3 штуки товара в заказ
    add_item_res = test_client.post(f"/orders/{order_id}/items", json={
        "product_id": product_id,
        "quantity": 3
    })

    # --- ASSERT (Проверки) ---
    # 6. Проверяем, что запрос прошел успешно
    assert add_item_res.status_code == 200
    order_data = add_item_res.json()

    # 7. Проверяем состав заказа
    assert len(order_data["items"]) == 1
    assert order_data["items"][0]["product_id"] == product_id
    assert order_data["items"][0]["quantity"] == 3
    assert order_data["total_amount"] == 300.0

    # 8. САМАЯ ВАЖНАЯ ПРОВЕРКА: убеждаемся, что остаток на складе уменьшился
    product_check_res = test_client.get(f"/products/{product_id}")
    assert product_check_res.status_code == 200
    assert product_check_res.json()["stock"] == 7 # Было 10, купили 3, осталось 7

    # --- ACT 2 (Проверяем логику увеличения количества) ---
    # 9. Добавляем еще 2 штуки того же товара
    add_again_res = test_client.post(f"/orders/{order_id}/items", json={
        "product_id": product_id,
        "quantity": 2
    })
    
    # --- ASSERT 2 ---
    assert add_again_res.status_code == 200
    order_data_2 = add_again_res.json()
    assert len(order_data_2["items"]) == 1 # Позиция не добавилась, а обновилась
    assert order_data_2["items"][0]["quantity"] == 5 # 3 + 2 = 5
    assert order_data_2["total_amount"] == 500.0

    # 10. Проверяем, что остаток снова уменьшился
    product_check_res_2 = test_client.get(f"/products/{product_id}")
    assert product_check_res_2.status_code == 200
    assert product_check_res_2.json()["stock"] == 5 # Было 7, купили 2, осталось 5

    # --- ACT 3 (Проверяем проверку остатков) ---
    # 11. Пытаемся купить больше, чем есть на складе (осталось 5, пытаемся купить 6)
    add_fail_res = test_client.post(f"/orders/{order_id}/items", json={
        "product_id": product_id,
        "quantity": 6
    })

    # --- ASSERT 3 ---
    assert add_fail_res.status_code == 400 # Ожидаем ошибку
    assert "Insufficient stock" in add_fail_res.json()["detail"]