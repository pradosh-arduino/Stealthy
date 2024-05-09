#
#   Written by @pradosh-arduino on github
#

import sys
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QInputDialog, QMessageBox, QHBoxLayout, QFileDialog, QMenu, QDialog
from PyQt6.QtGui import QIcon, QCursor, QMovie
from PyQt6.QtCore import Qt, QThread
from random import randint
import subprocess
import socket
import threading
import time
import base64
import mimetypes
from playsound import playsound
import re
import os
import requests

buffer_size = 4096

class FunctionMenu(QMenu):
    def __init__(self, functions, parent=None):
        super().__init__(parent)
        self.functions = functions
        for function_name, function in functions.items():
            action = self.addAction(function_name)
            action.triggered.connect(function)

class Stealthy(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Stealthy Chat")
        self.setWindowIcon(QIcon("./client-data/icon.png"))
        self.setGeometry(100, 100, 600, 400)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        if not os.path.exists("./client-data"):
            QMessageBox.critical(self, 'Error', 'The client-data folder is missing which is required for the Stealthy Chat! (to fix it git clone the https://github.com/pradosh-arduino/Stealthy and copy the client-data folder from that)')
            exit(-1)

        self.global_css = """
                           background-color: #121c1a; 
                           color: white;
                           """

        self.menu_css = """QMenu {
                            background-color: #121c1a;
                            border-radius: 5px;
                            border: 1px solid gray;
                            color: #c9c9c9;
                            padding-left: 4px;
                            padding-top: 4px;
                        }
                        QMenu::item:selected { 
                            background-color: #00618e; 
                            border-radius: 5px;
                            color: white;
                        }"""

        self.setStyleSheet(self.global_css)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        # Connect button
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_to_server)
        self.connect_button.setIcon(QIcon("./client-data/connect-48.png"))
        self.layout.addWidget(self.connect_button)

        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        with open('./client-data/unconnected.html', 'r') as file:
            html = file.read()
            self.chat_history.append(html)
        self.chat_history.textChanged.connect(self.text_changed)
        self.layout.addWidget(self.chat_history)

        hbox = QHBoxLayout()
        self.upload_button = QPushButton("")
        self.upload_button.clicked.connect(self.open_upload_menu)
        self.upload_button.setIcon(QIcon("./client-data/upload-48.png"))

        self.upload_menu = QMenu()

        files_action = self.upload_menu.addAction("Upload Files...")
        files_action.setIcon(QIcon('./client-data/QMenu/file-upload-96.png'))
        files_action.triggered.connect(self.upload_file)

        images_action = self.upload_menu.addAction("Upload Images...")
        images_action.setIcon(QIcon('./client-data/QMenu/img-upload-96.png'))
        images_action.triggered.connect(self.upload_image)

        command_action = self.upload_menu.addAction("Upload Command output...")
        command_action.setIcon(QIcon('./client-data/QMenu/command-line-96.png'))
        command_action.triggered.connect(self.upload_output)

        self.upload_menu.setStyleSheet(self.menu_css)

        self.input_box = QLineEdit()
        self.input_box.returnPressed.connect(self.send_message)

        self.send_button = QPushButton("")
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setIcon(QIcon("./client-data/send-50.png"))

        hbox.addWidget(self.upload_button)
        hbox.addWidget(self.input_box)
        hbox.addWidget(self.send_button)
        self.layout.addLayout(hbox)

        self.client_socket = None
        self.username = ""
        self.connected = False
    
    def open_upload_menu(self):
        self.upload_menu.exec(QCursor.pos())

    def upload_output(self):
        command, ok = QInputDialog.getText(self, 'Enter value', 'Enter the command to be executed and to share the output:')
        if ok:
            if command:
                final_message = f"<br><i>Attachment of a command output - {command}</i><hr>"
                try:
                    result = subprocess.run(command.split(), capture_output=True, text=True)  # Capture output as string
                    output = result.stdout.splitlines()
                    for line in output:
                        final_message += line + "<br>"
                except subprocess.CalledProcessError as error:
                    final_message += error
                final_message += "<hr>"
                self.client_socket.send(final_message.encode('utf-8'))

    def upload_file(self):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        file_dialog.setViewMode(QFileDialog.ViewMode.List)
        file_dialog.setNameFilter("All files (*.*)")
        file_dialog.setWindowTitle("Select file(s) only - Upload Stealthy Chat")
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            for file_path in selected_files:
                try:
                    with open(file_path, 'r') as file:
                        data = file.readlines()

                        final_message = f'<br><i>Attachment - {os.path.basename(file_path)}</i><hr style="color:gray;background-color:gray;">'
                        for info in data:
                            final_message += f'{info}<br>'
                        final_message += '<hr style="color:gray;background-color:gray;">'
                        self.client_socket.send(final_message.encode('utf-8'))

                except Exception as e:
                    QMessageBox.critical(self, 'Error', 'Failed uploading file(s), backend message: ' + str(e))
                    break

    def upload_image(self):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        file_dialog.setViewMode(QFileDialog.ViewMode.List)
        file_dialog.setNameFilter("All files (*.*)")
        file_dialog.setWindowTitle("Select image(s) only - Upload Stealthy Chat")

        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            for file_path in selected_files:
                try:
                    with open(file_path, 'rb') as file:
                        encoded_string = base64.b64encode(file.read()).decode("utf-8")
                        mime_type, _ = mimetypes.guess_type(file_path)

                        if mime_type:
                            image_type = mime_type.split('/')[1]
                            self.client_socket.send(f'<br><img src=\"data:image/{image_type};base64,{encoded_string}\" alt=\"Image\">'.encode('utf-8'))
                        else:
                            QMessageBox.critical(self, 'Error', 'Failed uploading file(s), Unknown image type.')
                            break
                except Exception as e:
                    QMessageBox.critical(self, 'Error', 'Failed uploading file(s), backend message: ' + str(e))
                    break
        
    def closeEvent(self, event):
        try:
            self.client_socket.send('/quit'.encode('utf-8'))
            self.client_socket.close()
        except:
            foo = 0
        sys.exit()

    def text_changed(self):
        scroll_bar = self.chat_history.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())
        
    def input_ip_port(self):
        ip, ok1 = QInputDialog.getText(self, 'Enter IP and Port', 'Enter IP and Port in format of IP:Port (e.g. localhost:5454)')
        if ok1:
            ip_port = ip.split(":")
            if len(ip_port) == 2:
                if type(ip_port[1]) == str:
                    try:
                        temp_x = int(ip_port[1])
                    except:
                        QMessageBox.critical(self, 'Error', 'Only numbers are allowed in ports!')
                        return (None, None);
                if ip_port[0] == 'localhost':
                    ip_port[0] = '127.0.0.1'
                return (ip_port[0], int(ip_port[1]))
        return (None, None)

    def input_username(self):
        username, ok = QInputDialog.getText(self, 'Enter Username', 'Username (leave blank if you want an autogenerated name):')
        if ok:
            return username
        return None

    def receive_messages(self):
        while True:
            try:
                message = self.client_socket.recv(buffer_size).decode('utf-8')
                if message.__contains__(':'):
                    split_msg = message.split(':', 1)

                    if len(split_msg) > 1:
                        new_msg = split_msg[0] + '</font>:' + split_msg[1]
                    else:
                        new_msg = split_msg[0] + '</font>'

                    self.chat_history.append('<font color=\'cyan\'>' + new_msg)
                    if not self.window().isActiveWindow():
                        playsound('./client-data/notification.mp3')
                else:
                    self.chat_history.append(message)

            except ConnectionResetError:
                QMessageBox.critical(self, 'Error', 'Connection to the server closed.')
                break
            except Exception as e:
                break
    
    def markdown_to_html(self, markdown):
        html = markdown
    
        # Convert bold
        html = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', html)
    
        # Convert italic
        html = re.sub(r'\*(.*?)\*', r'<i>\1</i>', html)
    
        # Convert underline
        html = re.sub(r'__(.*?)__', r'<u>\1</u>', html)

        html = re.sub(r'^#+\s*(.*?)$', lambda match: f'<h{match.group(0).count("#")}>{match.group(1)}</h{match.group(0).count("#")}>', html, flags=re.MULTILINE)
        return html

    def send_message(self):
        if not self.connected:
            QMessageBox.critical(self, 'Error', 'You must be connected to a server to send messages.')
            return
        
        message = self.input_box.text()
        if message == '/quit':
            self.client_socket.send(message.encode('utf-8'))
            self.client_socket.close()
            sys.exit()
        elif message == '/ping':
            self.client_socket.sendall(message.encode())
            start_time = time.time()
            response = self.client_socket.recv(buffer_size).decode()
            end_time = time.time()
            round_trip_time = (end_time - start_time) * 1000
            self.chat_history.append(f"Server response: {response}, Round-trip time: {round(round_trip_time, 4)}ms")
            self.input_box.clear()
        elif message == '/clear':
            self.chat_history.clear()
            self.input_box.clear()
        elif not message:
            return
        elif message.replace(" ", "") == "":
            return
        else:
            self.client_socket.send(self.markdown_to_html(message).encode('utf-8'))
            self.input_box.clear()
    
    def is_valid_port(self, port):
        try:
            return 0 < port <= 65535
        except ValueError:
            return False

    def connect_to_server(self):
        QMessageBox.warning(self, 'Warning', 'The server you are connecting to can see your IP Address. Unless you trust them use a VPN/Tor')
        ip, port = self.input_ip_port()
        if not ip and not port:
            QMessageBox.critical(self, 'Error', 'Empty IP/Port has been entered!')
        elif ip and self.is_valid_port(port):
            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect((ip, port))

                self.username = self.input_username()
                if self.username:
                    self.chat_history.clear()
                    bytes_sent = self.client_socket.send(self.username.encode('utf-8'))
                    
                else:

                    url = "https://random-word-api.herokuapp.com/word?number=2"
                    try:
                        response = requests.get(url)
                        if response.status_code == 200:
                            data = response.json()
                            capitalized_words = [word.capitalize() for word in data]
                            combined_string = "".join(capitalized_words)
                            self.client_socket.send(combined_string.encode('utf-8'))
                        else:
                            self.client_socket.send(('user-'+str(randint(100, 999))).encode('utf-8'))
                    except:
                        self.client_socket.send(('user-'+str(randint(100, 999))).encode('utf-8'))

                    self.chat_history.clear()
                
                receive_thread = threading.Thread(target=self.receive_messages)
                receive_thread.start()
                self.connect_button.hide()
                self.connected = True
                self.setWindowTitle("Stealthy Chat : Connected")

            except Exception as e:
                error_msg = str(e)
                QMessageBox.critical(self, 'Error', 'Backend error : ' + error_msg)
        else:
            QMessageBox.critical(self, 'Error', 'Invalid IP/Port has been entered!')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    client = Stealthy() # pun intended
    client.show()
    sys.exit(app.exec())
