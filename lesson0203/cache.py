# cache.py
import json
import redis

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

ORDER_TTL_SEC = 60


def order_cache_key(order_id: int) -> str:
    return f'order:{order_id}'


def get_order_from_cache(order_id: int):
    raw = r.get(order_cache_key(order_id))
    if not raw:
        return None
    return json.loads(raw)


def set_order_cache(order_id: int, order_data: dict):
    r.setex(order_cache_key(order_id), ORDER_TTL_SEC, json.dumps(order_data))


def invalidate_order_cache(order_id: int):
    r.delete(order_cache_key(order_id))
