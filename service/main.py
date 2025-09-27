from fastapi import FastAPI

from routes.client_router import client_router
from routes.product_router import product_router


app = FastAPI(title="Task Service", version="1.0.0")

app.include_router(product_router,   prefix="/products",   tags=["products"])
#app.include_router(category_router, prefix="/categories", tags=["categories"])
app.include_router(client_router,   prefix="/clients",    tags=["clients"])
#app.include_router(order_router,    prefix="/orders",     tags=["orders"])
#app.include_router(inventory_router,prefix="/inventory",  tags=["inventory"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8088, reload=True)