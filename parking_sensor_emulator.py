# SmartParking/parking_sensor_emulator.py
import sys, random
from PyQt5 import QtCore
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QDockWidget, QWidget,
    QFormLayout, QLineEdit, QPushButton
)
from PyQt5.QtGui import QIntValidator
from PyQt5.QtCore import Qt
from agent import Mqtt_client
from init import comm_topic, broker_ip, broker_port, username, password

class MC(Mqtt_client):
    pass  # publish-only

class ConnectionDock(QDockWidget):
    def __init__(self, mc, spot_id, update_rate_s=5):
        super().__init__()
        self.mc = mc
        self.spot_id = spot_id
        self.topic_pub = f"{comm_topic}spot-{spot_id}/pub"
        self.update_rate_s = int(update_rate_s)
        self.status = "FREE"

        # UI
        self.eHostInput = QLineEdit(broker_ip)
        self.ePort      = QLineEdit(str(broker_port)); self.ePort.setValidator(QIntValidator()); self.ePort.setMaxLength(5)
        self.eClientID  = QLineEdit(f"ParkingSensor-{spot_id}")
        self.eUserName  = QLineEdit(username)
        self.ePassword  = QLineEdit(password); self.ePassword.setEchoMode(QLineEdit.Password)

        self.btnConnect = QPushButton("Enable/Connect")
        self.btnConnect.clicked.connect(self.on_connect_click)
        self.btnConnect.setStyleSheet("background-color: gray")

        self.btnToggle  = QPushButton("Toggle Now")
        self.btnToggle.clicked.connect(self.toggle_and_publish)

        self.eStatus = QLineEdit(self.status); self.eStatus.setReadOnly(True)

        form = QFormLayout()
        form.addRow("Broker", self.eHostInput)
        form.addRow("Port", self.ePort)
        form.addRow("ClientID", self.eClientID)
        form.addRow("Turn On/Off", self.btnConnect)
        form.addRow("Spot Status", self.eStatus)
        form.addRow("Manual", self.btnToggle)

        content = QWidget()
        content.setLayout(form)
        self.setWidget(content)                   # ← רק setWidget; בלי setTitleBarWidget
        self.setWindowTitle(f"ParkingSensor-{spot_id}")

    def on_connect_click(self):
        self.mc.set_broker(self.eHostInput.text())
        self.mc.set_port(int(self.ePort.text()))
        self.mc.set_clientName(self.eClientID.text())
        self.mc.set_username(self.eUserName.text())
        self.mc.set_password(self.ePassword.text())
        self.mc.connect_to(); self.mc.start_listening()
        self.btnConnect.setStyleSheet("background-color: green")

    def toggle_and_publish(self):
        # אם לא מחוברים – ננסה להתחבר
        if not getattr(self.mc, "connected", False):
            self.on_connect_click()
            if not getattr(self.mc, "connected", False):
                return
        # החלפת מצב ושליחה
        self.status = "FREE" if self.status == "OCCUPIED" else "OCCUPIED"
        self.eStatus.setText(self.status)
        payload = f"From: ParkingSensor-{self.spot_id} Status: {self.status}"
        self.mc.publish_to(self.topic_pub, payload)

class MainWindow(QMainWindow):
    def __init__(self, spot_id=1, update_rate_s=5):
        super().__init__()
        self.conn = ConnectionDock(MC(), spot_id, update_rate_s)
        self.addDockWidget(Qt.TopDockWidgetArea, self.conn)

        # טיימר לסימולציה אוטומטית (אם רוצים). 0 = רק ידני.
        if update_rate_s > 0:
            self.timer = QtCore.QTimer(self)
            self.timer.timeout.connect(self.conn.toggle_and_publish)
            self.timer.start(update_rate_s * 1000)

        self.setGeometry(30, 600, 320, 180)
        self.setWindowTitle(f"ParkingSensor-{spot_id}")

if __name__ == "__main__":
    app = QApplication.instance() or QApplication(sys.argv)
    spot = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    rate = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    mw = MainWindow(spot, rate); mw.show()
    sys.exit(app.exec_())
