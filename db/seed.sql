-- =======================================
-- SEED для demo-данных (psql, COPY FROM STDIN)
-- =======================================

BEGIN;

-- Рекомендуется для повторных прогонов на dev:
-- TRUNCATE order_items, orders, inventory, products, categories, clients RESTART IDENTITY CASCADE;

-- ---------- Clients ----------
COPY clients (id, name, address) FROM STDIN;
1	Alice Johnson	123 Main St, Springfield
2	Bob Smith	456 Oak Ave, Rivertown
3	Charlie Brown	789 Pine Rd, Hill Valley
\.

-- ---------- Categories ----------
-- ВАЖНО: родители раньше детей (FK на parent_id)
COPY categories (id, name, path, parent_id) FROM STDIN;
1	Electronics	Electronics	\N
2	Home	        Home	        \N
3	Phones	        Electronics.Phones	1
4	Laptops	        Electronics.Laptops	1
5	Smartphones	Electronics.Phones.Smartphones	3
6	Feature Phones	Electronics.Phones.FeaturePhones	3
7	Kitchen	        Home.Kitchen	2
8	Furniture	Home.Furniture	2
\.

-- ---------- Products ----------
COPY products (id, name, price, category_id) FROM STDIN;
1	iPhone 14	999.99	5
2	Samsung Galaxy S23	899.99	5
3	Nokia 3310	59.99	6
4	MacBook Pro 14"	1999.99	4
5	Dell XPS 13	1499.00	4
6	Blender Philips	120.00	7
7	Dining Table	499.00	8
\.

-- ---------- Inventory ----------
COPY inventory (product_id, stock) FROM STDIN;
1	10
2	15
3	50
4	5
5	8
6	20
7	3
\.

-- ---------- Orders (ручные 3 шт.) ----------
COPY orders (id, client_id, created_at, status) FROM STDIN;
1	1	2025-09-10 12:00:00+03	COMPLETED
2	2	2025-09-15 14:30:00+03	PROCESSING
3	3	2025-09-18 18:45:00+03	NEW
\.

-- ---------- Order Items для этих 3 заказов ----------
-- amount НЕ вставляем: это STORED generated column
COPY order_items (order_id, product_id, qty, price_at_moment) FROM STDIN;
1	1	1	999.99
1	6	2	120.00
2	3	2	59.99
2	7	1	499.00
3	2	1	899.99
\.

-- ---------- Синхронизация последовательностей BIGSERIAL ----------
SELECT setval(pg_get_serial_sequence('clients','id'),   COALESCE((SELECT max(id) FROM clients),0), true);
SELECT setval(pg_get_serial_sequence('categories','id'),COALESCE((SELECT max(id) FROM categories),0), true);
SELECT setval(pg_get_serial_sequence('products','id'),  COALESCE((SELECT max(id) FROM products),0), true);
SELECT setval(pg_get_serial_sequence('orders','id'),    COALESCE((SELECT max(id) FROM orders),0), true);

-- =======================================
-- Автогенерация демо-данных
-- =======================================

-- 100 случайных заказов за последние 30 дней
INSERT INTO orders (client_id, created_at, status)
SELECT
    (SELECT id FROM clients ORDER BY random() LIMIT 1),
    now() - (random() * interval '30 days'),
    (ARRAY['NEW','PROCESSING','COMPLETED','CANCELLED'])[ceil(random()*4)]
FROM generate_series(1, 100);

-- Для сгенерированных заказов: 1–3 случайных товара на заказ
INSERT INTO order_items (order_id, product_id, qty, price_at_moment)
SELECT
    o.id,
    p.id,
    (trunc(random()*3)+1)::int,
    p.price
FROM orders o
JOIN LATERAL (
    SELECT id, price
    FROM products
    ORDER BY random()
    LIMIT (1 + (random()*2)::int)  -- 1..3 товаров
) p ON true
WHERE o.id > 3; -- не трогаем первые ручные

COMMIT;
