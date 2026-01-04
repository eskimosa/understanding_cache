import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from cache import LruTtlCache
from db import SessionLocal, Product, init_db_and_seed

CACHE_CAPACITY = int(os.getenv("CACHE_CAPACITY", "200"))
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "20"))

app = FastAPI()
cache = LruTtlCache(capacity=CACHE_CAPACITY, default_ttl_s=CACHE_TTL_SECONDS)

def cache_key(product_id: int) -> str:
    return f"product:{product_id}"

class ProductOut(BaseModel):
    id: int
    name: str
    price_cents: int

class ProductUpdate(BaseModel):
    name: str
    price_cents: int

@app.on_event("startup")
def startup():
    init_db_and_seed()

@app.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int):
    key = cache_key(product_id)

    # check cache first
    cached = cache.get(key)
    if cached is not None:
        return cached
    
    # if not in cache, get from database
    with SessionLocal() as db:
        product = db.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Not found")

        data = {"id": product.id, "name": product.name, "price_cents": product.price_cents}
        cache.set(key, data) # uses default TTL
        return data

@app.put("/products/{product_id}", response_model=ProductOut)
def upsert_product(product_id: int, payload: ProductUpdate):
    with SessionLocal() as db:
        product = db.get(Product, product_id)
        if not product:
            product = Product(id=product_id, name=payload.name, price_cents=payload.price_cents)
            db.add(product)
        else:
            product.name = payload.name
            product.price_cents = payload.price_cents

    db.commit()

    # invalidate cache after write
    cache.delete(cache_key(product_id))

    return {"id": product_id, "name": payload.name, "price_cents": payload.price_cents}

@app.get("/cache/stats")
def cache_stats():
    return cache.stats()
