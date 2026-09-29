import json
from src.redact_archive import ArchiveDocument, redact_for_archive


def test_archive_request_uses_pdf_boundary(monkeypatch):
    captured = {}

    class Response:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self): return json.dumps({"ok": True, "data": {"pdf": "7265646163746564"}}).encode()

    def fake_urlopen(request, timeout):
        captured["method"] = request.get_method()
        captured["body"] = json.loads(request.data.decode())
        return Response()

    monkeypatch.setenv("INFRAI_API_KEY", "test-key")
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    result = redact_for_archive(ArchiveDocument("p7", "live-event", b"raw"))
    assert result == b"redacted"
    assert captured["method"] == "POST"
    assert captured["body"] == {"pdf": "cmF3"}
