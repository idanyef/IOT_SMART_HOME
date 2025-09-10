# SmartParking/agent.py — paho-mqtt 2.x compatible (with fallbacks)
import threading
from paho.mqtt import client as mqtt


class Mqtt_client:
    def __init__(self):
        self._broker = "127.0.0.1"
        self._port = 1883
        self._client_id = "SmartParkingClient"
        self._username = ""
        self._password = ""
        self.connected = False
        self.subscribed = False
        self._on_connected_form_cb = None

        # צור לקוח MQTT בצורה שתחזיק גם בגרסאות שונות של paho 2.x
        self._client = self._new_client(self._client_id)
        self._apply_handlers()

    # ---------- internal helpers ----------
    def _new_client(self, client_id: str) -> mqtt.Client:
        """
        paho 2.x שינה את חתימות הקולבקים.
        ננסה קודם עם enum v311 (המצב ה"ישן"), ואם לא קיים—ננסה בלי הפרמטר.
        """
        # נסה API ישן מפורש (on_connect(client, userdata, flags, rc))
        try:
            return mqtt.Client(
                client_id=client_id,
                protocol=mqtt.MQTTv311,
                callback_api_version=mqtt.CallbackAPIVersion.v311,
            )
        except Exception:
            # fallback: בלי הפרמטר (מתאים להתקנות שונות)
            return mqtt.Client(
                client_id=client_id,
                protocol=mqtt.MQTTv311,
            )

    def _apply_handlers(self):
        if self._username or self._password:
            self._client.username_pw_set(self._username, self._password)
        self._client.on_connect = self._on_connect
        self._client.on_message = self.on_message

    # ---------- public API ----------
    def set_broker(self, ip):
        self._broker = ip

    def set_port(self, port):
        self._port = port

    def set_clientName(self, name):
        # במקום reinitialise (בעייתי ב-2.x) נייצר קליינט חדש תואם ונתקין handlers
        self._client_id = name
        self._client = self._new_client(self._client_id)
        self._apply_handlers()

    def set_username(self, user):
        self._username = user

    def set_password(self, pwd):
        self._password = pwd

    def set_on_connected_to_form(self, cb):
        self._on_connected_form_cb = cb

    def connect_to(self):
        if self._username or self._password:
            self._client.username_pw_set(self._username, self._password)
        self._client.connect(self._broker, int(self._port), keepalive=60)

    def start_listening(self):
        t = threading.Thread(target=self._client.loop_forever, daemon=True)
        t.start()

    def publish_to(self, topic, payload):
        if not isinstance(payload, (bytes, bytearray)):
            payload = str(payload).encode("utf-8")
        self._client.publish(topic, payload, qos=0, retain=False)

    def subscribe_to(self, topic):
        self._client.subscribe(topic, qos=0)
        self.subscribed = True

    # ---------- callbacks ----------
    def _on_connect(self, client, userdata, flags, rc):
        self.connected = (rc == 0)
        if self._on_connected_form_cb and self.connected:
            self._on_connected_form_cb()

    # מיועד לדריסה ע"י יורשים (אמולטורים/מנהל/GUI)
    def on_message(self, client, userdata, msg):
        pass
