# SmartParking/gui_parking.py
import sys, re
from PyQt5 import QtCore, QtWidgets
from agent import Mqtt_client
from init import comm_topic, broker_ip, broker_port, username, password

class GuiSignals(QtCore.QObject):
    spotChanged = QtCore.pyqtSignal(int, str)
    alertAdded  = QtCore.pyqtSignal(str)

class GuiClient(Mqtt_client):
    def __init__(self, signals: GuiSignals):
        super().__init__()
        self.signals = signals

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode("utf-8", "ignore")
        m = re.match(rf"^{re.escape(comm_topic)}spot-(\d+)/pub$", topic)
        if m:
            spot_id = int(m.group(1))
            up = payload.upper()
            status = "OCCUPIED" if "OCCUPIED" in up else ("FREE" if "FREE" in up else None)
            if status:
                # לשדר סיגנל במקום לגעת ישירות ב־UI
                self.signals.spotChanged.emit(spot_id, status)
        if topic == f"{comm_topic}alerts":
            self.signals.alertAdded.emit(payload)

class SmartParkingUI(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.signals = GuiSignals()

        self.labels = {i: QtWidgets.QLabel(f"Spot {i}: ?") for i in (1,2,3)}
        for i in self.labels.values():
            i.setAlignment(QtCore.Qt.AlignCenter)
            i.setStyleSheet("font-size:18px; padding:6px; border:1px solid #999; border-radius:8px;")

        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.labels[1]); row.addWidget(self.labels[2]); row.addWidget(self.labels[3])

        self.alerts = QtWidgets.QListWidget()

        layout = QtWidgets.QVBoxLayout()
        title = QtWidgets.QLabel("SmartParking — Dashboard")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size:22px; font-weight:bold;")
        layout.addWidget(title)
        layout.addLayout(row)
        layout.addWidget(QtWidgets.QLabel("Alerts:"))
        layout.addWidget(self.alerts)
        self.setLayout(layout)
        self.setWindowTitle("SmartParking GUI")
        self.resize(800, 520)

        # לחבר סיגנלים ל־slots שרצים על ה־Main Thread
        self.signals.spotChanged.connect(self._set_spot)
        self.signals.alertAdded.connect(self._add_alert)

        # MQTT client
        self.mc = GuiClient(self.signals)
        self.mc.set_broker(broker_ip); self.mc.set_port(int(broker_port))
        self.mc.set_clientName("SmartParking-GUI")
        self.mc.set_username(username); self.mc.set_password(password)
        self.mc.connect_to(); self.mc.start_listening()
        for i in (1,2,3):
            self.mc.subscribe_to(f"{comm_topic}spot-{i}/pub")
        self.mc.subscribe_to(f"{comm_topic}alerts")

    # ----- slots (Main Thread) -----
    @QtCore.pyqtSlot(int, str)
    def _set_spot(self, i, status):
        self.labels[i].setText(f"Spot {i}: {status}")
        if status == "OCCUPIED":
            self.labels[i].setStyleSheet(
                "font-size:18px; padding:6px; border:1px solid #999; "
                "border-radius:8px; background:#ffdddd;"
            )
        else:
            self.labels[i].setStyleSheet(
                "font-size:18px; padding:6px; border:1px solid #999; "
                "border-radius:8px; background:#ddffdd;"
            )

    @QtCore.pyqtSlot(str)
    def _add_alert(self, text):
        self.alerts.addItem(text)

if __name__=="__main__":
    # לעיתים ב־macOS זה מונע תקלות ציור ב־Qt5
    import os
    os.environ.setdefault("QT_MAC_WANTS_LAYER", "1")

    app = QtWidgets.QApplication(sys.argv)
    ui = SmartParkingUI()
    ui.show()
    app.exec_()
