# OTA (R3 — deferred; stub only)

**Honest status:** There is **no** signed/auto OTA in firmware. `ota_stub.py` returns `ota_not_implemented` if called. Do not expect fleet OTA until a dedicated R3 release.

## Safe update workflow (today)

1. Drain outbox / confirm device online and ACK healthy.
2. On a PC with Chabokan-first tooling, prepare verified `.py` files.
3. Flash with offline copy:

```bash
mpremote connect COM3 fs cp main.py :main.py
mpremote connect COM3 reset
```

4. Keep previous known-good copy for rollback.

## Future (not shipped)

- HTTPS pull of signed bundle + rollback partition
- Block OTA while Learn Mode or dry-switch task active

**Languages:** [English](OTA.md) · [Persian](OTA.fa.md)
