# SmartParking/gate_relay_emulator.py
import os, sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QDockWidget, QWidget,
    QFormLayout, QLineEdit, QPushButton
)
from PyQt5.QtGui import QIntValidator
from PyQt5.QtCore import Qt, QObject, pyqtSignal
from agent import Mqtt_client
from init import comm_topic, broker_ip, broker_port, username, password

# דרוש במק ליציבות ציור Qt
os.environ.setdefault("QT_MAC_WANTS_LAYER", "1")

class GateSignals(QObject):
    gateStatus = pyqtSignal(str)

class MC(Mqtt_client):
    def __init__(self, signals: GateSignals):
        super().__init__()
        self.signals = signals

    def on_message(self, client, userdata, msg):
        m = msg.payload.decode("utf-8", "ignore").upper()
        if "OPEN" in m:
            self.signals.gateStatus.emit("OPEN")
        elif "CLOSE" in m:
            self.signals.gateStatus.emit("CLOSED")

class GateDock(QDockWidget):
    def __init__(self, gate_id="1"):
        super().__init__()
        self.gate_id = gate_id
        self.topic_sub = f"{comm_topic}gate-{gate_id}/sub"
        self.topic_pub = f"{comm_topic}gate-{gate_id}/pub"

        # UI
        self.eHostInput = QLineEdit(broker_ip)
        self.ePort      = QLineEdit(str(broker_port)); self.ePort.setValidator(QIntValidator()); self.ePort.setMaxLength(5)
        self.eClientID  = QLineEdit(f"GateRelay-{gate_id}")
        self.eUserName  = QLineEdit(username)
        self.ePassword  = QLineEdit(password); self.ePassword.setEchoMode(QLineEdit.Password)

        self.btnConnect = QPushButton("Enable/Connect")
        self.btnConnect.setStyleSheet("background-color: gray")
        self.btnConnect.clicked.connect(self.on_connect_click)

        self.eStatus = QLineEdit("CLOSED"); self.eStatus.setReadOnly(True)

        form = QFormLayout()
        form.addRow("Broker", self.eHostInput)
        form.addRow("Port", self.ePort)
        form.addRow("ClientID", self.eClientID)
        form.addRow("Turn On/Off", self.btnConnect)
        form.addRow("Gate Status", self.eStatus)
        w = QWidget(); w.setLayout(form)
        self.setWidget(w); self.setWindowTitle(f"GateRelay-{gate_id}")

        # MQTT + signals
        self.signals = GateSignals()
        self.signals.gateStatus.connect(self._set_gate_status)
        self.mc = MC(self.signals)

        # >>> זה הקסם: כשהלקוח מתחבר – נצבע ירוק ונבטיח subscribe
        self.mc.set_on_connected_to_form(self.on_connected)

    def on_connected(self):
        self.btnConnect.setStyleSheet("background-color: green")
        if not self.mc.subscribed:
            self.mc.subscribe_to(self.topic_sub)

    def _set_gate_status(self, s: str):
        self.eStatus.setText(s)
        self.mc.publish_to(self.topic_pub, f"Gate-{self.gate_id} Status: {s}")

    def on_connect_click(self):
        self.mc.set_broker(self.eHostInput.text())
        self.mc.set_port(int(self.ePort.text()))
        self.mc.set_clientName(self.eClientID.text())
        self.mc.set_username(self.eUserName.text())
        self.mc.set_password(self.ePassword.text())
        self.mc.connect_to()
        self.mc.start_listening()
        if not self.mc.subscribed:
            self.mc.subscribe_to(self.topic_sub)

class MainWindow(QMainWindow):
    def __init__(self, gate_id="1"):
        super().__init__()
        self.dock = GateDock(gate_id)
        self.addDockWidget(Qt.TopDockWidgetArea, self.dock)
        self.setGeometry(670, 600, 300, 150)
        self.setWindowTitle(f"GateRelay-{gate_id}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gid = sys.argv[1] if len(sys.argv) > 1 else "1"
    mw = MainWindow(gid); mw.show()
    app.exec_()
