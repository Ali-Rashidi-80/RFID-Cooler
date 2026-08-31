# Contributing

**Languages:** [English](CONTRIBUTING.md) (default) · [Persian](CONTRIBUTING.fa.md)

1. Keep changes **atomic** and run `python scripts/validate.py` and `python scripts/run_tests.py` before opening a PR.
2. **English is the canonical docs language.** Persian companions (`.fa.md`) must stay fact-aligned.
3. Never commit secrets: `config.json`, `cards.json`, tokens, phone numbers, WiFi passwords.
4. GPIO / wiring claims in docs must match `main.py` pin constants.
5. Do not weaken dry-switch safety for convenience (mechanical relay moves only with SSR off).
6. `test/test_ssrRelay.py` is a **legacy lab script**, not a product regression gate.

## Pull request checklist

- [ ] `python scripts/validate.py` passes
- [ ] No secrets in diff
- [ ] README / INSTALL updated if user-facing behavior changed
- [ ] Persian `.fa.md` updated when English user docs change

## Commit style

- Imperative subject (~72 chars): `Add LAN HTTP status endpoint docs`
- Body explains **why**, not only what changed.

## Useful commands

```bash
python scripts/validate.py
python scripts/run_tests.py

# Flash single file (example)
mpremote connect COM3 fs cp main.py :main.py
mpremote connect COM3 reset
```

## Hardware changes

If you change relay timing or pinout:

1. Update `main.py` constants
2. Update README hardware tables (EN + FA)
3. Add a line to the hardware checklist if it is a new invariant

## Documentation

- Product map: [`docs/PRODUCT_ROADMAP_RESILIENCE.md`](docs/PRODUCT_ROADMAP_RESILIENCE.md)
- Iran mirrors: [`docs/IRAN_MIRRORS.md`](docs/IRAN_MIRRORS.md)
- OTA status (honest): [`docs/OTA.md`](docs/OTA.md)
