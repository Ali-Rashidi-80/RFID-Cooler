# Security policy

**Languages:** [English](SECURITY.md) (default) · [Persian](SECURITY.fa.md)

## Supported versions

| Version | Supported |
|---------|-----------|
| main branch | best effort |

## Reporting a vulnerability

Report security issues **privately** — do not open a public issue with exploit details or live device tokens.

Include:

- Affected component (`main.py`, `local_http.py`, `ws_client.py`, etc.)
- Reproduction steps (redact tokens)
- Impact (motor control, credential leak, LAN bypass, etc.)

We aim to acknowledge within 7 days.

## Scope notes

- **Mains wiring** is out of software scope but safety-critical — follow qualified electrician practices.
- **`local_pin` / BLE PIN / SMS PIN** protect local channels; use non-default PINs in production.
- **`hardware_token`** is per-device; treat like a password; rotate via dashboard if leaked.
- **MicroPython TLS** may have limited certificate verification — prefer WSS on trusted networks + strong tokens.
- **Learn Mode** intentionally blocks remote motor commands — do not bypass for “convenience.”
- **Door commands** (`OPEN`) are ignored by design — report if a regression moves the cooler.

## Secure development

- CI runs `python scripts/validate.py` on every push/PR.
- Secrets are gitignored (`config.json`, `cards.json`, `outbox.jsonl`, etc.).
- Example config uses placeholders only.

## Out of scope

- Physical theft of ESP32 (attacker with UART/USB access)
- RF433 replay after successful learn (mitigate with PIN + physical access control)
