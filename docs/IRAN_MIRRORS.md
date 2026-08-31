# Iran mirrors (national priority) — Cooler / SentryGate

During international internet disruption or national network filtering, **always prefer Chabokan mirror first**.

## Chabokan (`mirror2.chabokan.net`)

| Service | URL |
|---------|-----|
| NPM | `https://mirror2.chabokan.net/npm/` |
| PyPI | `https://mirror2.chabokan.net/pypi/simple/` |
| Docker | `docker pull mirror2.chabokan.net/<image>` or `registry-mirrors` |
| APT (Debian/Ubuntu) | Per [iran.chabokan.net](https://iran.chabokan.net/) guide |

### NPM (cooler-web / frontend)

```bash
npm config set registry https://mirror2.chabokan.net/npm/
# or project .npmrc in cooler-web
npm install --legacy-peer-deps
```

### PyPI (backend)

```bash
pip install --index-url https://mirror2.chabokan.net/pypi/simple/ --trusted-host mirror2.chabokan.net -r requirements.txt
```

Sample file: `door_control/backend/pip.conf`

### Docker

```json
{
  "registry-mirrors": ["https://mirror2.chabokan.net"]
}
```

`door_control` compose files may already use `mirror2.chabokan.net/...` prefix.

### MicroPython / mip

Chabokan has no dedicated mip index. For Iran:

1. Download packages on PC from internal mirror/cache
2. Copy to device with `mpremote fs cp`  
   Or host a static `package.json` on internal server / Chabokan.

## Registry priority (engineering recommendation)

1. Chabokan mirror2  
2. Other in-country mirrors (Arvan / Liara / …) if needed  
3. Public registries only when 1 and 2 are unavailable  

**Languages:** [English](IRAN_MIRRORS.md) · [Persian](IRAN_MIRRORS.fa.md)
