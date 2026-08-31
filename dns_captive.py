# Tiny DNS server that answers every query with AP IP (captive portal)
import uasyncio as asyncio
import socket
import struct


class CaptiveDns:
    def __init__(self, ip="192.168.4.1"):
        self.ip = ip
        self._sock = None

    def _answer(self, data):
        if len(data) < 12:
            return None
        # Copy transaction ID + flags (response, recursion)
        txn = data[:2]
        flags = b"\x81\x80"
        qdcount = data[4:6]
        # Questions section starts at 12; find end of QNAME
        i = 12
        while i < len(data) and data[i] != 0:
            i += 1 + data[i]
        i += 5  # null + type + class
        question = data[12:i]
        # Build A record answer
        name = b"\xc0\x0c"
        atype = b"\x00\x01"
        aclass = b"\x00\x01"
        ttl = b"\x00\x00\x00\x3c"
        rdlen = b"\x00\x04"
        try:
            parts = [int(x) for x in self.ip.split(".")]
            rdata = bytes(parts)
        except Exception:
            rdata = b"\xc0\xa8\x04\x01"
        return (
            txn
            + flags
            + qdcount
            + b"\x00\x01\x00\x00\x00\x00"
            + question
            + name
            + atype
            + aclass
            + ttl
            + rdlen
            + rdata
        )

    async def run(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setblocking(False)
            sock.bind(("0.0.0.0", 53))
            self._sock = sock
            print("[DNS] Captive on :53 ->", self.ip)
        except Exception as e:
            print("[DNS] Bind failed:", e)
            return
        while True:
            try:
                try:
                    data, addr = sock.recvfrom(256)
                except OSError:
                    await asyncio.sleep(0.05)
                    continue
                ans = self._answer(data)
                if ans:
                    sock.sendto(ans, addr)
            except Exception as e:
                print("[DNS] Error:", e)
                await asyncio.sleep(0.2)
