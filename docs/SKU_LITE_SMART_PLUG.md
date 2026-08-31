# SKU Lite — market plug / relay for whole supply only

## Safety rule

**Never** wire a home smart plug or single-channel relay as Off / Slow / Fast motor control for the cooler.

Inductive load + inrush current can weld contacts or cause fire. Speed control only from RFID-Cooler core (SSR + mechanical dry-switch).

## Allowed use

```
[mains] → [market plug/relay] → [rated contactor] → [whole board/cooler supply]
                              ↘ RFID-Cooler still manages Off/Slow/Fast
```

- Plug = **whole supply ON/OFF only** when device must be fully de-energized.
- For 3-speed physical remote, learn 433 on the controller with `rf433_enabled` (not on the plug).

## Iran market guidance

| Need | Correct path |
|------|----------------|
| Simple physical remote | RF433 learn on ESP32 |
| Remote over internet | Cloud WSS / Melipayamak alerts |
| Emergency supply cut | SKU Lite plug/contactor |

**Languages:** [English](SKU_LITE_SMART_PLUG.md) · [Persian](SKU_LITE_SMART_PLUG.fa.md)
