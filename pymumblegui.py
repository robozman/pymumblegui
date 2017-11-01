#!/usr/bin/env python3

import sys
import functools
import pymumble.pymumble_py3 as pymumble
import PyQt5
from PyQt5 import uic, QtWidgets
from PyQt5.QtWidgets import QApplication
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal, pyqtSlot

class ChatView(QtWidgets.QTextEdit):
    

    def __init__(self):
        super(ChatView, self).__init__()


class SignalSlotHandler(QtCore.QObject):

    message_recieved = pyqtSignal('QString')

    def __init__(self, MumbleGUI = None):
        if MumbleGUI != None:
            self.mumble_gui = MumbleGUI
        super(SignalSlotHandler, self).__init__()
    @pyqtSlot('QString')
    def recieve_message(self, message_text):
        self.mumble_gui.chat_view.setPlainText(self.mumble_gui.chat_view.toPlainText() + message_text) 


class MumbleGUI:
    'MumbleGUI: contains the QT gui stuff and loads the .ui file from designer'
    def __init__(self):
        self.app = QtWidgets.QApplication(sys.argv)
        self.window = uic.loadUi('pymumblegui.ui')
        self.window.show()
        self.centralwidget = self.window.centralwidget
        self.chat_view = ChatView()
        self.chat_view.setReadOnly(True)
        self.chat_view.setCursorWidth(0)
        self.chat_view_scroll_area = self.centralwidget.findChild(QtWidgets.QScrollArea, 'scrollArea')
        self.chat_view_scroll_area.setWidget(self.chat_view)
        self.chat_entry = self.centralwidget.findChild(QtWidgets.QLineEdit)
        self.reciever = SignalSlotHandler(self)

    def make_connection(self, mumble_client):
        mumble_client.sender.message_recieved.connect(self.reciever.recieve_message)
class MumbleClient:
    'MumbleClient: includes all the variables to initalize a mumble server connection'
    
    
    def __init__(self):

        self.host = 'saltisland.tk'
        self.port = 64738
        self.user = 'pymumblegui'
        self.password = ''
        self.reconnect = False
        
            
            
        self.mumble = pymumble.Mumble(host=self.host, user=self.user, port=self.port, password=self.password)
        self.mumble.start()
        self.mumble.is_ready()
        self.sender = SignalSlotHandler()
        self.mumble.callbacks.set_callback(pymumble.constants.PYMUMBLE_CLBK_TEXTMESSAGERECEIVED, self.on_message_recieved)

    def send_message(self, client_gui):
        'send_message: sends a message using the pymumble client and updates the text output'
        target = self.mumble.channels[self.mumble.users.myself['channel_id']]
        target.send_text_message(client_gui.chat_entry.text())
        message_post = '%s: %s\n'%(self.user, client_gui.chat_entry.text())
        client_gui.chat_entry.setText('')
        new_text = client_gui.chat_view.toPlainText() + message_post
        client_gui.chat_view.setText(new_text)

    def on_message_recieved(self, message):
        'recieve_message: recieves a message'
        message_post = '%s: %s\n'%(self.mumble.users[message.actor]['name'], message.message)
        self.sender.message_recieved.emit(message_post)



def main():
    'main: main function of program'
    client = MumbleClient()
    client_gui = MumbleGUI()
    client_gui.make_connection(client)
    client_gui.chat_entry.returnPressed.connect(functools.partial(client.send_message, client_gui))
    sys.exit(client_gui.app.exec_())



if __name__ == '__main__':
    main()
