# Minimal async HTTP control server (AP + STA LAN)
# PIN header/query required for mode changes.
import uasyncio as asyncio
import json
import network


HTML = """<!DOCTYPE html><html><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Cooler Local</title>
<style>body{font-family:sans-serif;margin:1.2rem;background:#0f172a;color:#e2e8f0}
button,input{font-size:1rem;padding:.6rem 1rem;margin:.3rem;border-radius:8px;border:0}
button{background:#38bdf8;color:#0f172a;font-weight:700}
.card{background:#1e293b;padding:1rem;border-radius:12px;margin-bottom:1rem}
input{width:90%;background:#334155;color:#fff}</style></head><body>
<h1>Cooler Local</h1>
<div class=card><p>State: <b id=st>—</b> &nbsp; IP: <span id=ip>—</span></p>
<button onclick="cmd(0)">Off</button>
<button onclick="cmd(1)">Slow</button>
<button onclick="cmd(2)">Fast</button>
<button onclick="cmd('cycle')">Cycle</button>
</div>
<div class=card><h3>PIN</h3>
<input id=pin type=password placeholder=local_pin value="">
</div>
<div class=card><h3>WiFi setup</h3>
<input id=ssid placeholder=SSID><br>
<input id=pass type=password placeholder=Password><br>
<button onclick="wifi()">Save WiFi</button>
</div>
<script>
async function status(){const r=await fetch('/api/status');const j=await r.json();
document.getElementById('st').textContent=['Off','Slow','Fast'][j.mode]||j.mode;
document.getElementById('ip').textContent=j.ip||'';}
async function cmd(m){const pin=document.getElementById('pin').value;
const body=m==='cycle'?{cmd:'CYCLE'}:{cmd:'SET_MODE',mode:m};
await fetch('/api/command?pin='+encodeURIComponent(pin),{method:'POST',
headers:{'Content-Type':'application/json','X-Local-Pin':pin},
body:JSON.stringify(body)});status();}
async function wifi(){const pin=document.getElementById('pin').value;
await fetch('/api/wifi?pin='+encodeURIComponent(pin),{method:'POST',
headers:{'Content-Type':'application/json','X-Local-Pin':pin},
body:JSON.stringify({ssid:document.getElementById('ssid').value,
password:document.getElementById('pass').value})});alert('Saved');}
status();setInterval(status,3000);
</script></body></html>
"""


class LocalHttpServer:
    def __init__(
        self,
        apply_mode,
        cycle,
        get_state,
        get_learn,
        local_pin,
        save_wifi=None,
        channel="http_local",
        rf_learn=None,
        on_wifi_saved=None,
    ):
        self.apply_mode = apply_mode
        self.cycle = cycle
        self.get_state = get_state
        self.get_learn = get_learn
        self.local_pin = str(local_pin or "1234")
        self.save_wifi = save_wifi
        self.channel = channel
        self.rf_learn = rf_learn
        self.on_wifi_saved = on_wifi_saved
        self._server = None

    def _check_pin(self, headers, qs):
        pin = qs.get("pin") or headers.get("x-local-pin") or headers.get("X-Local-Pin") or ""
        return str(pin) == self.local_pin

    def _audit_channel(self):
        """http_ap when only SoftAP is up; http_local when STA has an IP."""
        try:
            sta = network.WLAN(network.STA_IF)
            if sta.active() and sta.isconnected():
                return "http_local"
        except Exception:
            pass
        try:
            ap = network.WLAN(network.AP_IF)
            if ap.active():
                return "http_ap"
        except Exception:
            pass
        return self.channel or "http_local"

    def _parse_qs(self, path):
        qs = {}
        if "?" not in path:
            return path, qs
        base, q = path.split("?", 1)
        for part in q.split("&"):
            if "=" in part:
                k, v = part.split("=", 1)
                qs[k] = v
            else:
                qs[part] = ""
        return base, qs

    def _sta_ip(self):
        try:
            wlan = network.WLAN(network.STA_IF)
            if wlan.active() and wlan.isconnected():
                return wlan.ifconfig()[0]
        except Exception:
            pass
        try:
            ap = network.WLAN(network.AP_IF)
            if ap.active():
                return ap.ifconfig()[0]
        except Exception:
            pass
        return "0.0.0.0"

    async def _read_request(self, reader):
        req_line = await reader.readline()
        if not req_line:
            return None
        parts = req_line.decode().split()
        if len(parts) < 2:
            return None
        method, path = parts[0], parts[1]
        headers = {}
        while True:
            line = await reader.readline()
            if not line or line == b"\r\n":
                break
            try:
                s = line.decode().strip()
                if ":" in s:
                    k, v = s.split(":", 1)
                    headers[k.strip().lower()] = v.strip()
            except Exception:
                pass
        body = b""
        cl = int(headers.get("content-length", "0") or "0")
        if cl > 0:
            body = await reader.readexactly(cl)
        return method, path, headers, body

    async def _handle(self, reader, writer):
        try:
            req = await self._read_request(reader)
            if not req:
                return
            method, path, headers, body = req
            path, qs = self._parse_qs(path)

            if path in ("/", "/index.html", "/generate_204", "/hotspot-detect.html", "/ncsi.txt"):
                await self._send(writer, 200, "text/html", HTML)
                return

            if path == "/api/status" and method == "GET":
                ch = self._audit_channel()
                payload = json.dumps(
                    {
                        "mode": self.get_state(),
                        "learn_mode": bool(self.get_learn()),
                        "ip": self._sta_ip(),
                        "channel": ch,
                    }
                )
                await self._send(writer, 200, "application/json", payload)
                return

            if path == "/api/command" and method == "POST":
                if not self._check_pin(headers, qs):
                    await self._send(writer, 401, "application/json", '{"ok":false,"reason":"bad_pin"}')
                    return
                try:
                    msg = json.loads(body.decode() or "{}")
                except Exception:
                    await self._send(writer, 400, "application/json", '{"ok":false}')
                    return
                cmd = msg.get("cmd")
                ch = self._audit_channel()
                ok = False
                if cmd == "SET_MODE":
                    ok = await self.apply_mode(msg.get("mode"), source=ch)
                elif cmd == "CYCLE":
                    ok = await self.cycle(source=ch)
                await self._send(
                    writer,
                    200 if ok else 409,
                    "application/json",
                    json.dumps({"ok": ok, "mode": self.get_state(), "channel": ch}),
                )
                return

            if path == "/api/wifi" and method == "POST":
                if not self._check_pin(headers, qs):
                    await self._send(writer, 401, "application/json", '{"ok":false,"reason":"bad_pin"}')
                    return
                try:
                    msg = json.loads(body.decode() or "{}")
                except Exception:
                    msg = {}
                ssid = msg.get("ssid", "")
                password = msg.get("password", "")
                if self.save_wifi:
                    self.save_wifi(ssid, password)
                if self.on_wifi_saved:
                    try:
                        self.on_wifi_saved(ssid, password)
                    except Exception as e:
                        print("[HTTP] on_wifi_saved error:", e)
                await self._send(writer, 200, "application/json", '{"ok":true,"reconnect":true}')
                return

            if path == "/api/rf433/learn" and method == "POST":
                if not self._check_pin(headers, qs):
                    await self._send(writer, 401, "application/json", '{"ok":false,"reason":"bad_pin"}')
                    return
                if not self.rf_learn:
                    await self._send(
                        writer, 503, "application/json", '{"ok":false,"reason":"rf433_disabled"}'
                    )
                    return
                try:
                    msg = json.loads(body.decode() or "{}")
                except Exception:
                    msg = {}
                slot = str(msg.get("slot", "")).lower()
                if slot not in ("off", "slow", "fast", "cycle"):
                    await self._send(
                        writer, 400, "application/json", '{"ok":false,"reason":"bad_slot"}'
                    )
                    return
                self.rf_learn(slot)
                await self._send(
                    writer,
                    200,
                    "application/json",
                    json.dumps({"ok": True, "learning": slot}),
                )
                return

            # Captive DNS clients probe many hosts — always serve portal
            await self._send(writer, 200, "text/html", HTML)
        except Exception as e:
            print("[HTTP] handle error:", e)
        finally:
            try:
                await writer.aclose()
            except Exception:
                pass

    _HTTP_REASON = {
        200: "OK",
        400: "Bad Request",
        401: "Unauthorized",
        409: "Conflict",
        503: "Service Unavailable",
    }

    async def _send(self, writer, code, ctype, body):
        if isinstance(body, str):
            body = body.encode()
        reason = self._HTTP_REASON.get(code, "Error")
        hdr = (
            "HTTP/1.0 %d %s\r\nContent-Type: %s\r\nContent-Length: %d\r\n"
            "Connection: close\r\n\r\n"
        ) % (code, reason, ctype, len(body))
        writer.write(hdr.encode())
        writer.write(body)
        await writer.drain()

    async def start(self, host="0.0.0.0", port=80):
        self._server = await asyncio.start_server(self._handle, host, port)
        print("[HTTP] Listening on", host, port)
        return self._server
