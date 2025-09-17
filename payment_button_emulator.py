# SmartParking/payment_button_emulator.py
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QDockWidget, QWidget, QFormLayout, QLineEdit, QPushButton
from PyQt5.QtGui import QIntValidator
from PyQt5.QtCore import Qt
from agent import Mqtt_client
from init import comm_topic, broker_ip, broker_port, username, password

class MC(Mqtt_client):
    pass  # publish-only

class PaymentDock(QDockWidget):
    def __init__(self, mc, spot_id):
        super().__init__()
        self.mc = mc
        self.spot_id = spot_id
        self.topic_pub = f"{comm_topic}payment-{spot_id}/pub"

        self.mc.set_on_connected_to_form(self.on_connected)

        self.eHostInput = QLineEdit(broker_ip)
        self.ePort      = QLineEdit(str(broker_port)); self.ePort.setValidator(QIntValidator()); self.ePort.setMaxLength(5)
        self.eClientID  = QLineEdit(f"PaymentButton-{spot_id}")
        self.eUserName  = QLineEdit(username)
        self.ePassword  = QLineEdit(password); self.ePassword.setEchoMode(QLineEdit.Password)

        self.btnConnect = QPushButton("Enable/Connect"); self.btnConnect.clicked.connect(self.on_connect_click)
        self.btnConnect.setStyleSheet("background-color: gray")

        self.btnPay = QPushButton("Pay Now"); self.btnPay.clicked.connect(self.pay)

        form = QFormLayout()
        form.addRow("Broker", self.eHostInput); form.addRow("Port", self.ePort)
        form.addRow("ClientID", self.eClientID); form.addRow("Turn On/Off", self.btnConnect)
        form.addRow("Action", self.btnPay)

        w = QWidget(); w.setLayout(form)
        self.setTitleBarWidget(w); self.setWidget(w); self.setWindowTitle(f"PaymentButton-{spot_id}")

    def on_connected(self): self.btnConnect.setStyleSheet("background-color: green")

    def on_connect_click(self):
        self.mc.set_broker(self.eHostInput.text()); self.mc.set_port(int(self.ePort.text()))
        self.mc.set_clientName(self.eClientID.text()); self.mc.set_username(self.eUserName.text()); self.mc.set_password(self.ePassword.text())
        self.mc.connect_to(); self.mc.start_listening()

    def pay(self):
        if not self.mc.connected: self.on_connect_click()
        payload = f"From: PaymentButton-{self.spot_id} Paid: 1"
        self.mc.publish_to(self.topic_pub, payload)

class MainWindow(QMainWindow):
    def __init__(self, spot_id=1):
        super().__init__()
        self.dock = PaymentDock(Mqtt_client(), spot_id)
        self.addDockWidget(Qt.TopDockWidgetArea, self.dock)
        self.setGeometry(350, 600, 300, 150); self.setWindowTitle(f"PaymentButton-{spot_id}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    spot = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    mw = MainWindow(spot); mw.show()
    app.exec_()
