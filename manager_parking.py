# SmartParking/manager_parking.py
# Manager: listens to sensor & payment topics, updates SQLite, publishes OPEN/CLOSE to gate,
# and emits INFO/ALARM alerts. Compatible with agent.py (paho-mqtt 2.x).
import re
import sqlite3
import time
from datetime import datetime, timedelta

from agent import Mqtt_client
from init import (
    comm_topic,            # expected to be 'smartparking/' (with trailing slash)
    db_path,
    valid_payment_window_min,
    broker_ip, broker_port, username, password,
)

CREATE_SPOTS = """CREATE TABLE IF NOT EXISTS spots(
  spot_id INTEGER PRIMARY KEY,
  status TEXT NOT NULL DEFAULT 'FREE',
  last_payment_ts TEXT
);"""

CREATE_EVENTS = """CREATE TABLE IF NOT EXISTS events(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  severity TEXT NOT NULL,
  message TEXT NOT NULL
);"""


class ParkingManager(Mqtt_client):
    def __init__(self):
        super().__init__()

        # --- DB bootstrap ---
        self._db = sqlite3.connect(db_path, check_same_thread=False)
        self._db.execute(CREATE_SPOTS)
        self._db.execute(CREATE_EVENTS)
        self._db.commit()
        for i in (1, 2, 3):
            self._db.execute("INSERT OR IGNORE INTO spots (spot_id) VALUES (?);", (i,))
        self._db.commit()

        # Topics we care about
        self.topic_payment = rf"^{re.escape(comm_topic)}payment-(\d+)/pub$"
        self.topic_sensor  = rf"^{re.escape(comm_topic)}spot-(\d+)/pub$"
        # Gate control (we שומרים על gate-1 כמו במימוש ה-GUI שלך)
        self.topic_gate_cmd = f"{comm_topic}gate-1/sub"
        # Alerts / GUI
        self.topic_alerts   = f"{comm_topic}alerts"

        # Precompiled regexes (מונע באגים של backslash ברו-סטרינג)
        self._re_payment = re.compile(self.topic_payment)
        self._re_sensor  = re.compile(self.topic_sensor)

    # ---------- helpers ----------
    def _now(self) -> datetime:
        return datetime.utcnow()

    def _log_event(self, severity: str, msg: str) -> None:
        self._db.execute(
            "INSERT INTO events(ts, severity, message) VALUES (?,?,?)",
            (self._now().isoformat(), severity, msg),
        )
        self._db.commit()
        # publish alert to GUI
        self.publish_to(self.topic_alerts, f"{severity}: {msg}")
        print(f"[{severity}] {msg}")

    def _set_status(self, spot_id: int, status: str) -> None:
        self._db.execute(
            "UPDATE spots SET status=?, last_payment_ts=last_payment_ts WHERE spot_id=?",
            (status, spot_id),
        )
        self._db.commit()

    def _record_payment(self, spot_id: int) -> None:
        ts = self._now().isoformat()
        self._db.execute(
            "UPDATE spots SET last_payment_ts=? WHERE spot_id=?",
            (ts, spot_id),
        )
        self._db.commit()

    # ---------- MQTT callbacks ----------
    def on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode("utf-8", "ignore")
        up = payload.upper()

        # Debug visibility – ראה מה נכנס בפועל
        print(f"[DBG] recv topic={topic} payload={payload}")

        # Payment
        m = self._re_payment.match(topic)
        if m:
            spot_id = int(m.group(1))
            # מזהים תשלום בכל אחד מהפורמטים שהאמולטור עשוי לשלוח
            paid = ("PAID: 1" in up) or ("PAID=1" in up) or ("PAID TRUE" in up)
            if paid:
                self._record_payment(spot_id)
                self._log_event("INFO", f"Payment received for spot {spot_id}")
            return

        # Sensor (FREE/OCCUPIED)
        m = self._re_sensor.match(topic)
        if m:
            spot_id = int(m.group(1))
            status_match = re.search(r"STATUS:\s*(OCCUPIED|FREE)", up)
            if not status_match:
                return

            status = status_match.group(1)
            self._set_status(spot_id, status)

            if status == "OCCUPIED":
                # בדיקת חלון זמן התשלום
                row = self._db.execute(
                    "SELECT last_payment_ts FROM spots WHERE spot_id=?", (spot_id,)
                ).fetchone()
                ok = False
                if row and row[0]:
                    try:
                        last_pay = datetime.fromisoformat(row[0])
                        ok = (self._now() - last_pay) <= timedelta(
                            minutes=valid_payment_window_min
                        )
                    except Exception:
                        ok = False

                if ok:
                    self._log_event("INFO", f"Spot {spot_id}: entry allowed (payment OK)")
                    print(f"[DBG] publish OPEN -> {self.topic_gate_cmd}")
                    self.publish_to(self.topic_gate_cmd, "OPEN")
                else:
                    self._log_event("ALARM", f"Spot {spot_id}: entry WITHOUT payment")
                    print(f"[DBG] publish CLOSE -> {self.topic_gate_cmd}")
                    self.publish_to(self.topic_gate_cmd, "CLOSE")
            else:
                # FREE
                self._log_event("INFO", f"Spot {spot_id}: now FREE")
                print(f"[DBG] publish CLOSE -> {self.topic_gate_cmd}")
                self.publish_to(self.topic_gate_cmd, "CLOSE")
            return

        # Optional: log gate pub (status echoes from gate GUI)
        if topic == f"{comm_topic}gate-1/pub":
            self._log_event("INFO", payload)
            return

    # ---------- lifecycle ----------
    def run(self):
        # Connect & listen
        self.set_broker(broker_ip)
        self.set_port(int(broker_port))
        self.set_clientName("SmartParking-Manager")
        self.set_username(username)
        self.set_password(password)
        self.connect_to()
        self.start_listening()

        # Subscribe to everything under namespace
        self.subscribe_to(f"{comm_topic}#")
        self._log_event("INFO", "SmartParking Manager is up and listening")


if __name__ == "__main__":
    mgr = ParkingManager()
    mgr.run()
    # keep alive (agent uses loop_forever in a thread)
    while True:
        time.sleep(1)
