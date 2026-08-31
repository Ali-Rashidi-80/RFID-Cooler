# Flash outbox for uplink when WSS is down (at-least-once best-effort)
import json
import os

OUTBOX_FILE = "outbox.jsonl"
OUTBOX_BAK = "outbox.bak"  # default suffix; instance uses path + ".bak"
MAX_RECORDS = 512


class Outbox:
    def __init__(self, enabled=True, path=OUTBOX_FILE):
        self.enabled = enabled
        self.path = path
        self.bak = path + ".bak"

    def append(self, record):
        if not self.enabled:
            return
        try:
            line = json.dumps(record) + "\n"
            with open(self.path, "a") as f:
                f.write(line)
            self._trim()
        except Exception as e:
            print("[OUTBOX] append error:", e)

    def _trim(self):
        try:
            with open(self.path, "r") as f:
                lines = f.readlines()
            if len(lines) <= MAX_RECORDS:
                return
            keep = lines[-MAX_RECORDS:]
            with open(self.bak, "w") as f:
                f.writelines(keep)
            try:
                os.remove(self.path)
            except OSError:
                pass
            os.rename(self.bak, self.path)
        except Exception:
            pass

    def peek(self):
        """Read all records without clearing (safe for retry)."""
        if not self.enabled:
            return []
        records = []
        try:
            with open(self.path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        records.append(json.loads(line))
                    except Exception:
                        pass
        except OSError:
            return []
        except Exception as e:
            print("[OUTBOX] peek error:", e)
        return records

    def replace_all(self, records):
        """Atomically rewrite queue (empty list clears)."""
        if not self.enabled:
            return
        try:
            if not records:
                try:
                    os.remove(self.path)
                except OSError:
                    pass
                return
            with open(self.bak, "w") as f:
                for rec in records:
                    f.write(json.dumps(rec) + "\n")
            try:
                os.remove(self.path)
            except OSError:
                pass
            os.rename(self.bak, self.path)
        except Exception as e:
            print("[OUTBOX] replace_all error:", e)

    def drain(self):
        """Compatibility: peek then clear. Prefer peek+replace_all in cloud."""
        records = self.peek()
        self.replace_all([])
        return records

    def pending_count(self):
        try:
            with open(self.path, "r") as f:
                return sum(1 for line in f if line.strip())
        except Exception:
            return 0
