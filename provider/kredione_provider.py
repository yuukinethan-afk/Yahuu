"""Provider KrediOne – kirim OTP via API bertanda-tangan MD5."""
from __future__ import annotations

import hashlib
import time
import warnings
from typing import Any
from urllib.parse import urlencode

warnings.filterwarnings(
    "ignore",
    message="Unable to find acceptable character detection dependency",
)

from requests.sessions import Session

BASE = "https://m.kredione.id"
API_BASE = f"{BASE}/gateway"
LANDING_URL = (
    f"{BASE}/#/registerV2"
    "?campaign_name=GG_h5_Search_kredione_Industry_fire_creditall_auto_20260331"
)

USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
)

_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": BASE,
    "Referer": f"{BASE}/",
    "User-Agent": USER_AGENT,
}

MERCHANT_NO = "6666XF20230306001"
MSG_ID = "666"
APP_ID = "10000000006666001"
GW_PUBLIC_KEY = (
    "YyQyCaWdilrUL3oFZ6oeS8ZvWxHuGkmFsTZvq3eKYLyMY3autqJK2ik7EzuMpaCRBJ5ojwB3Ffs9vSqhT67Kx"
    "G3KbAiQgf12qNZDGYfVaAEtscbJXCcGvSDIWsbuZkmyH5NzlcsZsOR90HvGPZCD9OFcIYbksqfoDcLISB8kFaONi7"
    "TwYpofSuJLYGaJvDROyeG74kvJCriGBICGZE3MDVWej7pXaUtSnofre6GFJhUD673thInTvDLFiw7yS1GF"
)
AES_KEY = "5KF4efouyBWmx643Hps1uw=="
CHANNEL = "com.id.kredi360"
APP_MERCHANT = "ZF_360_CREDIT"

SEND_METHOD = "whatsapp"
CHECK_ENDPOINT = "/idn-app-server/api/v2/users/check/"
SEND_ENDPOINT = "/idn-app-server/api/v2/verification/send_code/"


def _signed_headers(path: str, method: str) -> dict[str, str]:
    timestamp = int(time.time() * 1000)
    fields: dict[str, Any] = {
        "api_gw_public_key": GW_PUBLIC_KEY,
        "app_id": APP_ID,
        "merchant_no": MERCHANT_NO,
        "method_name": path,
        "msg_id": MSG_ID,
        "request_method": method,
        "sign_timestamp": timestamp,
    }
    raw = ""
    for key in sorted(fields):
        if key == "sign_timestamp":
            raw += "timestamp" + str(fields[key])
        else:
            raw += key + str(fields[key])
    text = f"secret{AES_KEY}{raw}{AES_KEY}secret".upper()
    signature = hashlib.md5(text.encode()).hexdigest()
    return {
        "channel": CHANNEL,
        "appMerchant": APP_MERCHANT,
        "appId": "12",
        "Content-Type": "application/json;charset=UTF-8",
        "merchant_no": MERCHANT_NO,
        "msg_id": MSG_ID,
        "app_id": APP_ID,
        "method_name": path,
        "request_method": method,
        "sign_timestamp": str(timestamp),
        "api_gw_public_key": GW_PUBLIC_KEY,
        "request_sign": signature,
    }


class _KredioneAuth:

    def __init__(self, session: Session | None = None):
        self.s = session or self._new_session()

    @staticmethod
    def _new_session() -> Session:
        s = Session()
        s.headers.update(_HEADERS)
        s.get(LANDING_URL, timeout=30)
        return s

    def _request(self, method: str, path: str) -> dict:
        url = API_BASE + path
        res = self.s.request(
            method.upper(),
            url,
            headers=_signed_headers(path, method),
            timeout=30,
        )
        res.raise_for_status()
        body = res.json()
        if not isinstance(body, dict):
            raise RuntimeError(f"respons tidak valid: {body}")
        return body

    def send_otp(self, mobile: str, method: str = SEND_METHOD) -> dict:
        query = urlencode(
            {"method": method, "reason": "register", "phone_number": mobile}
        )
        return self._request("post", f"{SEND_ENDPOINT}?{query}")


def send_otp(mobile: str) -> bool:
    """Kirim OTP ke *mobile* via KrediOne. Kembalikan True jika berhasil."""
    auth = _KredioneAuth()
    res = auth.send_otp(mobile)
    return res.get("suc") is True or res.get("status") == 0
