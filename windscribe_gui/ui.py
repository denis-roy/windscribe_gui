import os
import subprocess
import pexpect
from PySide2 import QtCore, QtWidgets, QtGui, Qt
from mainwindow import Ui_MainWindow
from .login_window import Login


US_C = "US Central"
US = "US East"
US_W = "US West"
CA = "Canada East"
CA_W = "Canada West"
FR = "France"
DE = "Germany"
NL = "Netherlands"
NO = "Norway"
RO = "Romania"
CH = "Switzerland"
GB = "United Kingdom"
HK = "Hong Kong"
SERVER_LIST = ["choose server", US_C, US, US_W, CA, CA_W, FR, DE,
                NL, NO, RO, CH, GB, HK]
servers = {
    US_C: "US-C",
    US: "US",
    US_W: "US-W",
    CA: "CA",
    CA_W: "CA-W",
    FR: "FR",
    DE: "DE",
    NL: "NL",
    NO: "NO",
    RO: "RO",
    CH: "CH",
    GB: "GB",
    HK: "HK"
    }

class MainWindow(Ui_MainWindow, QtWidgets.QMainWindow):
    def __init__(self) -> None:

        super().__init__()
        self.setupUi(self)
        # self.setWindowIcon(QtGui.QIcon("ui/resources/icons/virtual-private-network.png"))
        self.informLabel.setText("Welcome to Windscribe GUI") # displays info
        self.mainButton.setVisible(False) # changes name and connects to different slots
        self.logoutButton.setVisible(False)
        self.comboBox.setVisible(False)
        self.comboBox.addItems(SERVER_LIST)
               

        self.status = None # info which displays in statusbar
        self.log_window = Login() # dialog window 
        self.error = QtWidgets.QErrorMessage(self)

        self.actionAccountStatus.triggered.connect(self.get_account_info)
        self.log_window.accepted.connect(self.log_in)
        self.logoutButton.clicked.connect(self.log_out)
        self.mainButton.clicked.disconnect()
       
    def get_account_info(self) -> None:

        self.mainButton.setVisible(True)
        account = pexpect.spawn("windscribe account")
        status = account.read()
        if status == b'Please login to use Windscribe\x1b[0m\r\n':
            self.informLabel.setText("Please login to use Windscribe")
            self.logoutButton.setVisible(False)
            self.mainButton.setText("Log In")
            self.mainButton.clicked.connect(self.show_login_dialog)
            self.statusbar.showMessage("")
        else:
            self.logoutButton.setVisible(True)
            status = status.split(b"\r\n")
            for i in range(len(status)):
                status[i] = status[i].decode("utf-8").replace("\x1b[0m", "").replace("\x1b[30m", "").replace("\x1b[47m", "")
            self.informLabel.setText("\n".join(status))
            self.status = self.get_status()
            if self.status == "DISCONNECTED":
                self.mainButton.setText("Connect")
                self.comboBox.setVisible(True)
                self.mainButton.clicked.connect(self.connect_to_server)
            else:
                self.mainButton.setText("Disconnect")
                self.mainButton.clicked.connect(self.disconnect_server)
            self.statusbar.showMessage(self.status)

    def show_login_dialog(self) -> None:

        self.log_window.setParent(self)
        self.log_window.setWindowModality(QtCore.Qt.ApplicationModal)
        self.log_window.setWindowFlags(QtCore.Qt.Window)
        self.log_window.exec_()    

    def log_in(self) -> None:

        self.error.setWindowTitle("Login Error")
        command = pexpect.spawn("windscribe login")
        command.expect([pexpect.TIMEOUT ,"Windscribe Username: "])
        if len(self.log_window.loginLine.text()) >= 3:
            command.sendline(self.log_window.loginLine.text())
        else:
            self.error.showMessage("Username must be at least 3 characters")
            return
        command.expect([pexpect.TIMEOUT, "Windscribe Password: "])
        if len(self.log_window.passwordLine.text()) >= 4:
            command.sendline(self.log_window.passwordLine.text())
        else:
            self.error.showMessage("Password must be at least 4 characters")
            return

        self.log_window.loginLine.clear()
        self.log_window.passwordLine.clear()
        answer = command.read()
        if b"Logged In" in answer:
            self.mainButton.clicked.disconnect(self.show_login_dialog)
            self.get_account_info()
            self.logoutButton.setVisible(True)
        else:
            self.error.showMessage("API Error: Could not log in with provided credentials")
            return

    def get_status(self) -> str:

        message = pexpect.spawn("windscribe status")
        message_to_show = message.read().split(b"\r\n")
        for i in range(len(message_to_show)):
            message_to_show[i] = message_to_show[i].decode("utf-8").replace("\x1b[31m", "").replace("\x1b[0m", "").replace("\x1b[32m", "")
        if "Service communication error" in message_to_show:
            self.error.setWindowTitle("Service communication error")
            self.error.showMessage("Service communication error")
            return
        else:
            return message_to_show[2]

    def connect_to_server(self) -> None:

        if self.comboBox.currentText() == "choose server":
            command = pexpect.spawn("windscribe connect")
        else:
            command = pexpect.spawn(
                f"windscribe connect {servers[self.comboBox.currentText()]}"
            )
        command.expect([pexpect.EOF, "Connected to*"])
        # 
        self.mainButton.clicked.disconnect()
        self.get_account_info()

    def disconnect_server(self) -> None:

        command = pexpect.spawn("windscribe disconnect")
        command.expect([pexpect.EOF, "Firewall Disabled*"])
        self.comboBox.setVisible(False)
        self.mainButton.clicked.disconnect()
        self.get_account_info()

    def log_out(self) -> None:

        self.disconnect_server()
        command = pexpect.spawn("windscribe logout")
        answer = command.read()
        if "Service communication error" in answer.split():
            self.error.showMessage("Service communication error")
            return
        self.comboBox.setVisible(False)
        self.mainButton.clicked.disconnect()
        self.get_account_info()
