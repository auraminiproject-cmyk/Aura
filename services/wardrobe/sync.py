"""Wardrobe sync helpers — server-wins conflict resolution for offline mode."""

from typing import Any


def merge_wardrobe(server_items: list[dict], local_items: list[dict]) -> list[dict]:
    by_id = {str(i.get("id")): i for i in local_items if i.get("id")}
    for item in server_items:
        by_id[str(item.get("id"))] = item
    return list(by_id.values())
