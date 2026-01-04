import time
from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class _Node:
    key: str
    value: Any
    expires_at: float
    prev: Optional["_Node"] = None
    next: Optional["_Node"] = None

class LruTtlCache:
    def __init__(self, capacity: int = 256, default_ttl_s: int = 30):
        self.capacity = capacity
        self.default_ttl_s = default_ttl_s
        self.map: dict[str, _Node] = {}
        self.head: Optional[_Node] = None
        self.tail: Optional[_Node] = None

        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def _now(self) -> float:
        return time.time()

    def _expired(self, node: _Node) -> bool:
        # Check if expired, with small epsilon to handle floating point precision
        now = self._now()
        return node.expires_at <= now

    def _remove(self, node: _Node) -> None:
        if node.prev:
            node.prev.next = node.next
        if node.next:
            node.next.prev = node.prev
        if self.head is node:
            self.head = node.next
        if self.tail is node:
            self.tail = node.prev
        node.prev = node.next = None

    def _add_front(self, node: _Node) -> None:
        node.prev = None
        node.next = self.head
        if self.head:
            self.head.prev = node
        self.head = node
        if self.tail is None:
            self.tail = node

    def _move_front(self, node: _Node) -> None:
        if self.head is node:
            return
        self._remove(node)
        self._add_front(node)

    def _evict_if_needed(self) -> None:
        while len(self.map) > self.capacity and self.tail:
            old = self.tail
            self._remove(old)
            self.map.pop(old.key, None)
            self.evictions += 1

    def get(self, key: str) -> Optional[Any]:
        node = self.map.get(key)
        if not node:
            self.misses += 1
            return None
        if self._expired(node):
            # Item expired - remove it and count as miss
            self._remove(node)
            self.map.pop(key, None)
            self.misses += 1
            return None
        # Item exists and is not expired - move to front and return
        self._move_front(node)
        self.hits += 1
        return node.value

    def set(self, key: str, value: Any, ttl_s: Optional[int] = None) -> None:
        ttl_s = self.default_ttl_s if ttl_s is None else ttl_s
        expires_at = self._now() + ttl_s

        node = self.map.get(key)
        if node:
            node.value = value
            node.expires_at = expires_at
            self._move_front(node)
            return

        node = _Node(key=key, value=value, expires_at=expires_at)
        self.map[key] = node
        self._add_front(node)
        self._evict_if_needed()

    def delete(self, key: str) -> None:
        node = self.map.pop(key, None)
        if node:
            self._remove(node)

    def stats(self) -> dict [str, int]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "size": len(self.map),
            "capacity": self.capacity,
            "default_ttl_s": self.default_ttl_s,
        }
