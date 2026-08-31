# Async WebSocket client (WSS/WS) for MicroPython ESP32
import uasyncio as asyncio
import random
import json

try:
    import ubinascii as binascii
except ImportError:
    import binascii

try:
    import ussl as ssl
except ImportError:
    try:
        import ssl
    except ImportError:
        ssl = None


class AsyncWSClient:
    def __init__(self, host, port, path, use_ssl=True, read_timeout_s=30):
        self.host = host
        self.port = int(port)
        self.path = path if path.startswith("/") else "/" + path
        self.use_ssl = use_ssl
        self.read_timeout_s = read_timeout_s
        self.reader = None
        self.writer = None
        self.open = False

    def close(self):
        self.open = False
        try:
            if self.writer:
                self.writer.close()
        except Exception:
            pass
        self.reader = None
        self.writer = None

    async def connect(self):
        self.close()
        try:
            print("[WS] Connecting to {}:{} ssl={}".format(self.host, self.port, self.use_ssl))
            if self.use_ssl:
                if ssl is None:
                    raise OSError("SSL not available")
                self.reader, self.writer = await asyncio.open_connection(
                    self.host, self.port, ssl=True
                )
            else:
                self.reader, self.writer = await asyncio.open_connection(self.host, self.port)

            key_raw = bytes([random.getrandbits(8) for _ in range(16)])
            key = binascii.b2a_base64(key_raw).strip()
            if isinstance(key, bytes):
                key = key.decode()

            req = (
                "GET {} HTTP/1.1\r\n"
                "Host: {}:{}\r\n"
                "Connection: Upgrade\r\n"
                "Upgrade: websocket\r\n"
                "Sec-WebSocket-Key: {}\r\n"
                "Sec-WebSocket-Version: 13\r\n"
                "\r\n"
            ).format(self.path, self.host, self.port, key)

            self.writer.write(req.encode())
            await self.writer.drain()

            status = await self.reader.readline()
            if not status or b"101" not in status:
                raise OSError("Handshake failed: {}".format(status))

            while True:
                line = await self.reader.readline()
                if not line or line == b"\r\n":
                    break

            self.open = True
            print("[WS] Connected")
            return True
        except Exception as e:
            print("[WS] Connect failed:", e)
            self.close()
            return False

    async def _read_exact(self, n):
        data = b""
        while len(data) < n:
            chunk = await asyncio.wait_for(
                self.reader.read(n - len(data)), timeout=self.read_timeout_s
            )
            if not chunk:
                raise OSError("Connection closed")
            data += chunk
        return data

    def _mask_payload(self, data):
        if isinstance(data, str):
            data = data.encode()
        mask = bytes([random.getrandbits(8) for _ in range(4)])
        out = bytearray(len(data))
        for i in range(len(data)):
            out[i] = data[i] ^ mask[i % 4]
        return mask, out

    async def send_text(self, text):
        if not self.open:
            return False
        try:
            if not isinstance(text, (bytes, bytearray)):
                text = text.encode()
            frame = bytearray()
            frame.append(0x81)
            length = len(text)
            if length < 126:
                frame.append(0x80 | length)
            elif length < 65536:
                frame.append(0x80 | 126)
                frame.extend(length.to_bytes(2, "big"))
            else:
                raise ValueError("payload too large")
            mask, masked = self._mask_payload(text)
            frame.extend(mask)
            frame.extend(masked)
            self.writer.write(frame)
            await self.writer.drain()
            return True
        except Exception as e:
            print("[WS] Send error:", e)
            self.close()
            return False

    async def send_json(self, obj):
        return await self.send_text(json.dumps(obj))

    async def _send_pong(self, payload=b""):
        if not self.open:
            return
        try:
            frame = bytearray()
            frame.append(0x8A)
            length = len(payload)
            frame.append(0x80 | length)
            mask, masked = self._mask_payload(payload)
            frame.extend(mask)
            frame.extend(masked)
            self.writer.write(frame)
            await self.writer.drain()
        except Exception:
            self.close()

    async def recv(self):
        """Return decoded text str, or None on close/timeout/control handled."""
        if not self.open:
            return None
        try:
            b1 = await self._read_exact(1)
            b2 = await self._read_exact(1)
            opcode = b1[0] & 0x0F
            masked = bool(b2[0] & 0x80)
            length = b2[0] & 0x7F
            if length == 126:
                ext = await self._read_exact(2)
                length = int.from_bytes(ext, "big")
            elif length == 127:
                ext = await self._read_exact(8)
                length = int.from_bytes(ext, "big")
            mask_bits = b""
            if masked:
                mask_bits = await self._read_exact(4)
            payload = await self._read_exact(length) if length else b""
            if masked and mask_bits:
                payload = bytes(payload[i] ^ mask_bits[i % 4] for i in range(len(payload)))

            if opcode == 0x8:  # close
                self.close()
                return None
            if opcode == 0x9:  # ping
                await self._send_pong(payload)
                return None
            if opcode == 0xA:  # pong
                return None
            if opcode == 0x1:
                return payload.decode()
            return None
        except Exception as e:
            print("[WS] Recv error:", e)
            self.close()
            return None
