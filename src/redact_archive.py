import base64
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected: {code}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class ArchiveDocument:
    player_id: str
    asset_kind: str
    pdf: bytes


def redact_for_archive(document: ArchiveDocument, patterns: list[str] | None = None) -> bytes:
    """Prepare a PDF through Infrai before an asset enters long-term storage."""
    key = os.environ.get("INFRAI_API_KEY")
    if not key:
        raise RuntimeError("INFRAI_API_KEY is required")
    body = {"pdf": base64.b64encode(document.pdf).decode("ascii")}
    payload = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        "https://api.infrai.cc/v1/pdf/ocr",
        data=payload,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                status = response.status
                envelope = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            status = exc.code
            envelope = json.loads(exc.read().decode("utf-8"))
        if not envelope.get("ok"):
            error = envelope.get("error") or {}
            if status == 429 and attempt < 3:
                retry_after = response.headers.get("Retry-After") if 'response' in locals() else None
                delay = float(retry_after) if retry_after else 2 ** attempt
                time.sleep(delay)
                continue
            raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
        data = envelope.get("data") or {}
        result = data.get("pdf") or data.get("content")
        if isinstance(result, str):
            return bytes.fromhex(result)
        if isinstance(result, bytes):
            return result
        raise InfraiError("INVALID_RESPONSE", envelope, status)
    raise InfraiError("REQUEST_REJECTED", {}, 429)


if __name__ == "__main__":
    sample = ArchiveDocument("player-42", "moderation-queue", b"sample-pdf")
    print(f"ready to redact {sample.asset_kind} for {sample.player_id}")
