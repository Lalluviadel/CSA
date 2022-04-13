import subprocess
import sys

from PyQt6 import QtGui
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QLineEdit, QInputDialog


class ConsoleMessengerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.processes = []
        self.clientsButton = QPushButton('Число клиентов', self)
        self.portButton = QPushButton('Номер порта', self)
        self.hostButton = QPushButton('Номер хоста', self)
        self.startButton = QPushButton('Старт мессенджера', self)
        self.closeButton = QPushButton('Закрыть консоли', self)
        self.clients = QLineEdit('3', self)
        self.port = QLineEdit('7777', self)
        self.host = QLineEdit('127.0.0.1', self)
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Запуск мессенджера')
        self.setWindowIcon(QtGui.QIcon('chat-bubble.png'))
        self.setWindowIcon(QtGui.QIcon('chat-bubble.png'))
        self.setGeometry(400, 400, 300, 260)

        self.clientsButton.move(20, 20)
        self.clientsButton.clicked.connect(lambda: self.data_request('Введите число клиентов', self.clients))

        self.portButton.move(20, 60)
        self.portButton.clicked.connect(lambda: self.data_request('Введите порт', self.port))

        self.hostButton.move(20, 100)
        self.hostButton.clicked.connect(lambda: self.data_request('Введите хост', self.host))

        self.startButton.setShortcut('Ctrl+S')
        self.startButton.clicked.connect(self.start)
        self.startButton.setToolTip('Запуск консолей сервера и клиентов мессенджера')
        self.startButton.move(20, 200)

        self.closeButton.setShortcut('Ctrl+Q')
        self.closeButton.clicked.connect(self.stop)
        self.closeButton.setToolTip('Закрыть все консоли')
        self.closeButton.move(170, 200)

        self.clients.setReadOnly(True)
        self.clients.setMaxLength(1)
        self.clients.move(130, 22)

        self.port.setReadOnly(True)
        self.port.setMaxLength(5)
        self.port.move(130, 62)

        self.host.setReadOnly(True)
        self.host.move(130, 102)

    def data_request(self, msg, obj):
        text, ok = QInputDialog.getText(self, msg, msg)
        if ok:
            obj.setText(str(text))

    def start(self):
        self.processes.append(subprocess.Popen(f'python server_script.py -p {self.port.text()} -a {self.host.text()}',
                                               creationflags=subprocess.CREATE_NEW_CONSOLE))
        for i in range(int(self.clients.text())):
            self.processes.append(
                subprocess.Popen(f'python client_script.py. {self.host.text()} {self.port.text()} -n test{i + 1}',
                                 creationflags=subprocess.CREATE_NEW_CONSOLE))

    def stop(self):
        while self.processes:
            victim = self.processes.pop()
            victim.kill()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ConsoleMessengerWindow()
    ex.show()
    sys.exit(app.exec())
