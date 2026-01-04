import json
import os
import redis
from typing import Optional

REDIS_URL = os.environ["REDIS_URL"]

r = redis.Redis.from_url(REDIS_URL, decode_responses=True) # decode_responses=True makes Redis return strings (not bytes)

def get_json(key: str) -> Optional[dict]:
    raw = r.get(key)
    return json.loads(raw) if raw else None

def set_json(key: str, value: dict, ttl_s: int) -> None:
    r.set(key, json.dumps(value), ex=ttl_s)

def delete(key: str) -> None:
    r.delete(key)



