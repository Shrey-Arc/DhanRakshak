from __future__ import annotations

import hashlib
import json
import os
import secrets
from typing import Any

import httpx

from app.config import get_settings


def canonical_hash(payload: dict[str, Any]) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def simulate_tx() -> str:
    return f"SIMULATED_TX_{secrets.token_hex(16)}"


def send_to_blockchain(payload_hash: str) -> str:
    settings = get_settings()
    if not settings.blockchain_rpc:
        return simulate_tx()

    private_key = os.getenv("BLOCKCHAIN_PRIVATE_KEY")
    if not private_key:
        return simulate_tx()

    payload = {
        "jsonrpc": "2.0",
        "method": "eth_sendRawTransaction",
        "params": [payload_hash],
        "id": 1,
    }
    response = httpx.post(settings.blockchain_rpc, json=payload, timeout=10)
    response.raise_for_status()
    result = response.json().get("result")
    if not result:
        return simulate_tx()
    return result
