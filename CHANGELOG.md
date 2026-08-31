# Changelog

All notable documentation and tooling changes for RFID-Cooler.

## Unreleased

### Added

- Bilingual README (`README.md` EN default, `README.fa.md` FA) with Rynix-style header/footer
- Mermaid architecture, state machine, protocol, and dry-switch diagrams
- GitHub Actions CI (`.github/workflows/ci.yml`) + `scripts/validate.py`
- Issue/PR templates, CONTRIBUTING, SECURITY, INSTALL (EN + FA)
- Docs hub (`docs/README.md`) and English canonical docs with `.fa.md` companions
- Brand assets: `assets/logo.svg`, `assets/logo-3d.png`, `docs/LOGO_PROMPT.md`
- MIT `LICENSE`

### Changed

- `.gitignore` cleanup (MicroPython tooling, scoped root text dumps, `.cursor/plans/`)
- `outbox.py`: backup file colocated with queue (`outbox.jsonl.bak`) — fixes atomic rewrite on Windows/other drives
- `local_http.py`: correct HTTP status reason phrases (401/409/503 not labeled "OK")

### Added (bench & integration)

- [`docs/BENCH_WALKTHROUGH.md`](docs/BENCH_WALKTHROUGH.md) / `.fa.md` — step-by-step hardware guide (A)
- [`docs/INTEGRATION.md`](docs/INTEGRATION.md) / `.fa.md` — backend integration docs (B)
- `scripts/integration/mock_ws_backend.py` — mock cloud with `--interactive` for ESP32 bench
- `scripts/integration/probe_device_session.py` — probe live/mock WSS
- `scripts/integration/run_integration.py` — WebSocket E2E without ESP32
- `requirements-dev.txt` — `websockets` for integration tooling

- `scripts/run_tests.py` + `test/host/test_suite.py` — 22+ honest host tests (CloudBridge ACK contract, outbox, WS path, SMS parser, pin/README contract)
- Expanded `scripts/validate.py` — 32 config keys, doc links, pin contract, repo file gate

### Removed

- Lowercase `readme.md` superseded by `README.md`
