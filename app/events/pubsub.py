import json
import os
import threading
import redis
from typing import Callable, List

REDIS_URL = os.environ["REDIS_URL"]
CHANNEL = "cache.invalidate"

def publish_invalidate(keys: List[str]) -> None:
    r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    r.publish(CHANNEL, json.dumps({"keys": keys}))

def start_invalidation_listener(on_invalidate: Callable[[List[str]], None]) -> None:
    def _run():
        r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        pubsub = r.pubsub()
        pubsub.subscribe(CHANNEL)

        for msg in pubsub.listen():
            if msg["type"] != "message":
                continue
            payload = json.loads(msg["data"])
            keys = payload.get("keys", [])
            if keys:
                on_invalidate(keys)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
