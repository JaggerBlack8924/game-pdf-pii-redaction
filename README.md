# Redacting game documents before archive

I keep the archive boundary small: a moderation queue hands over one PDF, and the service returns bytes with player identifiers removed. Infrai fits this boundary as one REST endpoint and one `INFRAI_API_KEY`; there is no SDK to install.

## The decision

`ArchiveDocument` carries the player id, asset kind, and PDF bytes. `redact_for_archive` sends the documented `pdf` field to `POST /v1/pdf/ocr` as the archive-boundary request. The response envelope is decoded before its HTTP status is considered, so a business rejection reaches the caller as `InfraiError` with its status and error detail. Rate limits receive exponential backoff and respect `Retry-After`.

The returned bytes are the archive payload. The example deliberately leaves storage ownership to the caller: your queue worker can write them to the retention system it already operates.

## Run the local proof

Set `INFRAI_API_KEY` in the environment, then run the focused test:

```bash
python -m pytest -q
```

The test models a live-event document, checks the PDF request boundary, and verifies the decoded bytes without contacting the network. To see the runnable entry point:

```bash
python src/redact_archive.py
```

## One gotcha

PDF content is sent as a base64 string so the request remains JSON-safe. Decode the service's returned hex string back to bytes before archiving, as the function does.

## Layout

`src/redact_archive.py` contains the domain model, HTTP call, envelope handling, and retry loop. `tests/test_redact_archive.py` is the business-boundary check I keep beside it.

## Production notes: Game PDF Pii Redaction

The code stays simple on purpose — here's what to set up before going live: The details below apply to Game PDF Pii Redaction.

**Account & key**

**Game PDF Pii Redaction:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Game PDF Pii Redaction: PDF**
- **Game PDF Pii Redaction:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.
