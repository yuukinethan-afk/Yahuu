from __future__ import annotations

import base64
import json
import uuid
from typing import Any

from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad, unpad
import requests

_BASE_URL = "https://buzzly.nexlendquontic.com/uploadtool/"
_AES_KEY = b"98cCLqPsTpEZXFu1"
_AES_IV = b"A2FtdvL7ewBOHc3t"
_CONTENT_TYPE = "application/json;charset=utf-8"
_PACKAGE = "com.dana.kredit.navigator"
_VERSION_NAME = "1.1.6"
_VERSION_CODE = 6
_CLIENT_KEY = "46pF5ta0gyLIV6sz"
_DEFAULT_APP_ID = "00000000-0000-0000-0000-000000000000"
_TIMEOUT = 30.0


def _json_compact(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def _encrypt(plaintext: str) -> str:
    cipher = AES.new(_AES_KEY, AES.MODE_CBC, _AES_IV)
    raw = cipher.encrypt(pad(plaintext.encode("utf-8"), AES.block_size))
    return base64.b64encode(raw).decode("ascii")


def _decrypt(ciphertext_b64: str) -> str:
    cipher = AES.new(_AES_KEY, AES.MODE_CBC, _AES_IV)
    raw = base64.b64decode(ciphertext_b64)
    return unpad(cipher.decrypt(raw), AES.block_size).decode("utf-8")


def _device_info(
    *,
    android_id: str | None = None,
    user_id: str = "",
    app_id: str = "",
    access_token: str = "",
) -> dict[str, Any]:
    return {
        "aawp": 1,
        "unpd": _CLIENT_KEY,
        "oiuaua": _VERSION_NAME,
        "mtz": _VERSION_CODE,
        "fojie": _PACKAGE,
        "jebrmbxz": "app",
        "gkzcowuo": user_id,
        "hpiizoni": {
            "lkioasz": app_id,
            "bnbrdp": "SM-G991B",
            "spi": "samsung",
            "bbuvlb": "12",
            "qnw": 31,
            "hjqy": "",
            "dcr": "",
            "qpfpaotm": android_id or uuid.uuid4().hex,
        },
        "wvhkpls": access_token,
        "vxfrx": 1,
        "sgqq": 1,
        "wsg": "android",
    }


def _build_body(params: dict[str, Any], **device_kwargs: Any) -> str:
    payload = {"vfwt": params, "psyhkiwd": _device_info(**device_kwargs)}
    return _encrypt(_json_compact(payload))


def _post(path: str, body: str) -> requests.Response:
    url = _BASE_URL + path.lstrip("/")
    return requests.post(
        url,
        data=body.encode("utf-8"),
        headers={"Content-Type": _CONTENT_TYPE},
        timeout=_TIMEOUT,
    )


def _decode_response(resp: requests.Response) -> Any:
    text = resp.text
    try:
        parsed = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        parsed = None

    if isinstance(parsed, (dict, list)):
        return parsed

    candidate: str | None = None
    if isinstance(parsed, str) and len(parsed) > 16:
        candidate = parsed
    elif text and len(text) > 16:
        candidate = text.strip().strip('"')

    if not candidate:
        return None
    try:
        plain = _decrypt(candidate)
    except (ValueError, KeyError):
        return None
    try:
        return json.loads(plain)
    except (json.JSONDecodeError, ValueError):
        return plain


def _bootstrap_session() -> dict[str, str]:
    android_id = uuid.uuid4().hex[:16]
    app_id = _DEFAULT_APP_ID
    params = {
        "odywqsjc": "",
        "rpbpyxgh": android_id,
        "qcurs": 0,
        "levchzj": 0,
        "ljpggxmh": 1,
        "dtqp": app_id,
    }
    body = _build_body(params, android_id=android_id, user_id="", app_id=app_id, access_token="")
    resp = _post("device/user/create", body)
    result = _decode_response(resp)

    if not isinstance(result, dict):
        return {}
    gan = result.get("gan")
    user_id = gan.get("ujieqzbw") if isinstance(gan, dict) else None
    if not user_id:
        return {}

    return {"android_id": android_id, "user_id": user_id, "app_id": app_id, "access_token": ""}


def send_otp(mobile: str) -> bool:
    try:
        session = _bootstrap_session()
        if not session:
            return False

        device_kwargs: dict[str, Any] = {
            "android_id": session["android_id"],
            "user_id": session["user_id"],
            "app_id": session["app_id"],
            "access_token": session["access_token"],
        }

        validity_body = _build_body({"aqpkhypy": mobile, "izjfn": 1}, **device_kwargs)
        validity_resp = _post("user/validity/check", validity_body)
        validity = _decode_response(validity_resp)

        if not isinstance(validity, dict):
            return False

        gan = validity.get("gan")
        frle = gan.get("frle") if isinstance(gan, dict) else None
        if frle is None:
            return False

        if frle == 0:
            otp_path = "user-service/text-message"
            otp_params: dict[str, Any] = {"ogeuvrfa": mobile, "xyldzdmx": "TEXT", "tvafse": 0}
        else:
            otp_path = "auth/inbound-sms"
            otp_params = {"hjhi": mobile, "str": "TEXT", "uzho": 0}

        otp_body = _build_body(otp_params, **device_kwargs)
        otp_resp = _post(otp_path, otp_body)
        result = _decode_response(otp_resp)

        return isinstance(result, dict) and result.get("lil") == 0

    except (requests.RequestException, KeyError, TypeError):
        return False
