from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from pathlib import Path


class Vault:
    """Small encrypted local secret store.

    This intentionally avoids third-party dependencies so the template remains
    installable in a bare Hermes/Python environment. It is scoped to local V1 use.
    """

    def __init__(self, path: Path, passphrase: str):
        if not passphrase:
            raise ValueError("Vault passphrase is required")
        self.path = path
        self.passphrase = passphrase.encode("utf-8")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def set_secret(self, scope: str, name: str, value: str) -> None:
        self.data.setdefault("secrets", {}).setdefault(scope, {})[name] = self._encrypt(value)
        self._save()

    def get_secret(self, scope: str, name: str) -> str:
        record = self.data.get("secrets", {}).get(scope, {}).get(name)
        if not record:
            return ""
        return self._decrypt(record)

    def _load(self) -> dict:
        if not self.path.exists():
            return {"version": 1, "secrets": {}}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self) -> None:
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _derive(self, salt: bytes) -> bytes:
        return hashlib.pbkdf2_hmac("sha256", self.passphrase, salt, 200_000, dklen=32)

    def _keystream(self, key: bytes, nonce: bytes, length: int) -> bytes:
        blocks: list[bytes] = []
        counter = 0
        while sum(len(block) for block in blocks) < length:
            blocks.append(hmac.new(key, nonce + counter.to_bytes(4, "big"), hashlib.sha256).digest())
            counter += 1
        return b"".join(blocks)[:length]

    def _encrypt(self, value: str) -> dict[str, str]:
        salt = os.urandom(16)
        nonce = os.urandom(16)
        key = self._derive(salt)
        plaintext = value.encode("utf-8")
        stream = self._keystream(key, nonce, len(plaintext))
        ciphertext = bytes(a ^ b for a, b in zip(plaintext, stream))
        tag = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()
        return {
            "salt": base64.b64encode(salt).decode("ascii"),
            "nonce": base64.b64encode(nonce).decode("ascii"),
            "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
            "tag": base64.b64encode(tag).decode("ascii"),
        }

    def _decrypt(self, record: dict[str, str]) -> str:
        salt = base64.b64decode(record["salt"])
        nonce = base64.b64decode(record["nonce"])
        ciphertext = base64.b64decode(record["ciphertext"])
        expected_tag = base64.b64decode(record["tag"])
        key = self._derive(salt)
        actual_tag = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(actual_tag, expected_tag):
            raise ValueError("Vault secret integrity check failed")
        stream = self._keystream(key, nonce, len(ciphertext))
        plaintext = bytes(a ^ b for a, b in zip(ciphertext, stream))
        return plaintext.decode("utf-8")
