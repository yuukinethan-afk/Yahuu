"""Provider Indosaku – kirim OTP via API terenkripsi AES-ECB."""
from __future__ import annotations

import base64
import json
import os
import warnings
from typing import Any

warnings.filterwarnings(
    "ignore",
    message="Unable to find acceptable character detection dependency",
)

from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad, unpad
from requests.sessions import Session

BASE = "https://app.indosaku.id"
SEND_PATH = "/jdn49uXCY9hp/mvNa/f8t_UdUf"

AES_KEY = b"b0b53117-94ab-424f-91c4-10a78f42"
APP_VERSION = "112"

OTP_CHANNEL = "1"

_HEADERS: dict[str, str] = {
    "bZ6LZqlrL6vMGIwhALp": "IND",
    "rGjS96": APP_VERSION,
    "lAsnNVkU0U9C": "android",
    "g9Z76E9boK": "Google",
    "x6FDnYreNpNWph": "",
    "Content-Type": "application/json; charset=UTF-8",
    "User-Agent": "okhttp/4.12.0",
}


def _random_android_id() -> str:
    return os.urandom(8).hex()


class _IndosakuAuth:

    def __init__(self, session: Session | None = None):
        self.s = session or Session()
        self.s.headers.update(_HEADERS)
        self.s.headers.update({"b9uMD": _random_android_id()})

    @staticmethod
    def _encrypt(payload: dict[str, Any]) -> str:
        raw = json.dumps(payload, separators=(",", ":")).encode()
        cipher = AES.new(AES_KEY, AES.MODE_ECB)
        return base64.b64encode(cipher.encrypt(pad(raw, 16))).decode()

    @staticmethod
    def _decrypt(text: str) -> dict[str, Any]:
        blob = text.strip()
        if blob.startswith("{"):
            body = json.loads(blob)
            if not isinstance(body, dict):
                raise RuntimeError(f"respons tidak valid: {body}")
            return body
        cleaned = blob.replace('"', "")
        cipher = AES.new(AES_KEY, AES.MODE_ECB)
        raw = cipher.decrypt(base64.b64decode(cleaned))
        body = json.loads(unpad(raw, 16).decode())
        if not isinstance(body, dict):
            raise RuntimeError(f"respons tidak valid: {body}")
        return body

    def send_otp(self, mobile: str, channel: str = OTP_CHANNEL) -> dict[str, Any]:
        payload = {
            "cVWzn1Oq": int(channel),
            "e8dv2iH": "INSA4",
            "yidTRs": mobile[1:],
            "mKm0HT8WuK": channel,
            "fnKDg": "Google",
        }
        res = self.s.post(
            BASE + SEND_PATH,
            data=self._encrypt(payload),
            timeout=30,
        )
        return self._decrypt(res.text)


def send_otp(mobile: str) -> bool:
    """Kirim OTP ke *mobile* via Indosaku. Kembalikan True jika berhasil."""
    auth = _IndosakuAuth()
    res = auth.send_otp(mobile)
    data = res.get("data") or {}
    return res.get("code") == 200 and data.get("tsFzo") == 1
