#!/usr/bin/env python3

import sys
import functools
import time
import configparser
import os
import pyaudio
import pymumble.pymumble_py3 as pymumble
from PyQt5 import uic, QtWidgets, QtCore, QtGui
from PyQt5.QtCore import pyqtSignal, pyqtSlot


class SignalSlotHandler(QtCore.QObject):
    '''Handles the QtSignals and Slots
    for communication between the Mumble thread and the Qt thread'''
    message_recieved = pyqtSignal('QString', 'QString', 'int')

    def __init__(self, host_mumble_gui=None):
        if host_mumble_gui is not None:
            self.mumble_gui = host_mumble_gui
        super(SignalSlotHandler, self).__init__()

    @pyqtSlot('QString', 'QString', 'int')
    def recieve_message(self, message_text, username, tab_index):
        '''On message signal,
        edits the text view with the username and the text body'''
#        coursor = self.mumble_gui.channel_chat_view.textCursor()
        current_chat = self.mumble_gui.tabbed_chat.widget(tab_index).findChild(
            QtWidgets.QTextEdit)
        cursor = current_chat.textCursor()
        cursor.setPosition(
            len(current_chat.toPlainText()))
        current_chat.setTextCursor(cursor)
        current_chat.insertPlainText(message_text)
#        self.mumble_gui.chat_view.setPlainText(
#            self.mumble_gui.chat_view.toPlainText() + message_text)


class MumbleGUI:
    '''MumbleGUI: contains the QT gui stuff and
    loads the .ui file from designer'''

    def __init__(self):
        self.app = QtWidgets.QApplication(sys.argv)
        self.window = uic.loadUi('pymumblegui.ui')
        self.window.setStyleSheet(
            open('MetroMumble/MetroDark.qss', 'r').read())
        self.window.show()
        self.centralwidget = self.window.centralwidget

        self.tabbed_chat = self.centralwidget.findChild(
            QtWidgets.QTabWidget, 'tabbed_chat')
        # self.tabbed_chat.setTabsClosable(True)

        self.channel_chat_view = self.centralwidget.findChild(
            QtWidgets.QTextEdit, "channel_chat")
        self.chat_entry = self.centralwidget.findChild(QtWidgets.QLineEdit)

        self.channel_view = self.centralwidget.findChild(QtWidgets.QTreeWidget)
        self.channel_view.setColumnCount(4)
        self.channel_view.setColumnHidden(1, True)
        self.channel_view.setColumnHidden(2, True)
        self.channel_view.setColumnHidden(3, True)
        self.channel_view.header().close()
        self.channel_view.setSortingEnabled(True)
        self.channel_view.sortByColumn(2, QtCore.Qt.AscendingOrder)

        self.centralwidget.findChild(
            QtWidgets.QScrollArea, 'scrollArea_2').setStyleSheet(
            "background-color:#1f1f1f;")

        self.root = 0
        self.root_tree = 0
        self.root_sub_channels = 0
        self.users = 0
        # self.top_level = QtWidgets.QTreeWidgetItem(['A', 'B', 'C'])

        self.reciever = SignalSlotHandler(self)

        self.__setup_connect_dialog()
        # self.show_connect_dialog()

    def populate_channel_list(self, mumble_client):
        '''Populates the QTreeViewWidget with all the channels on the server'''
        # print(mumble_client.mumble.channels)
        if mumble_client.mumble.channels == {}:
            # print('Quitting')
            os._exit(1)
        self.root = mumble_client.mumble.channels[0]
        self.root_tree = QtWidgets.QTreeWidgetItem(
            [self.root['name'], str(self.root['channel_id']), 'channel'])
        self.channel_view.addTopLevelItem(self.root_tree)
        self.root_sub_channels = [
            v for k, v in mumble_client.mumble.channels.items() if k != 0]
        # for key, value in mumble_client.mumble.channels.items():
        #    if key == 0:
        #        continue
        #    self.root_sub_channels.append(value)
        self.root_sub_channels.sort(key=lambda tup: tup['position'])
        for channel in self.root_sub_channels:
            # print(channel['channel_id'])
            channel_to_add = QtWidgets.QTreeWidgetItem([channel['name'], str(
                channel['channel_id']), 'channel', str(channel['position'])])
            self.root_tree.addChild(channel_to_add)
        self.root_tree.setExpanded(True)

    def user_created(self, mumble_client, user):
        '''Updates the channel list when a user connects'''
        self.__add_user_to_tree(user, mumble_client)

    def user_deleted(self, mumble_client, user, message):
        '''Updates the channel list when a user disconnects'''
        self.__delete_user_from_tree(user, mumble_client)

    def user_modified(self, mumble_client, user, fields):
        '''Updates the channel list when a user is
        modified (changes channels, names, or mute/deaf status)'''
        if 'channel_id' in fields:
            self.__delete_user_from_tree(user, mumble_client)
            self.__add_user_to_tree(user, mumble_client)
        elif 'self_deaf' in fields:
            if 'self_mute' in fields:
                if fields['self_deaf']:
                    self.__change_user_tree_icon(user, mumble_client, 'deaf')
                    # print('deafened')
                else:
                    if not fields['self_mute']:
                        self.__change_user_tree_icon(
                            user, mumble_client, 'normal')
                        # print('talking')
                    else:
                        self.__change_user_tree_icon(
                            user, mumble_client, 'muted')
                        # print('muted')
            else:
                if fields['self_deaf']:
                    self.__change_user_tree_icon(user, mumble_client, 'deaf')
                    # print('deafened')
                else:
                    self.__change_user_tree_icon(user, mumble_client, 'muted')
                    # print('muted')
        elif 'self_mute' in fields:
            if fields['self_mute']:
                self.__change_user_tree_icon(user, mumble_client, 'muted')
                # print('muted')
            else:
                self.__change_user_tree_icon(user, mumble_client, 'normal')
                # print('normal')

    def user_start_stop_talking(self, user, icon):
        if icon == 'talking':
            self.__change_user_tree_icon(user, None, icon)
        elif icon == 'normal':
            self.__change_user_tree_icon(user, None, icon)

    def __change_user_tree_icon(self, user, mumble_client, icon):
        user_to_change = self.channel_view.findItems(
            str(user['session']), QtCore.Qt.MatchExactly |
            QtCore.Qt.MatchRecursive, 1)[0]
        if icon == 'muted':
            user_to_change.setIcon(0, QtGui.QIcon(
                "MetroMumble/muted_self.svg"))
        elif icon == 'normal':
            user_to_change.setIcon(0, QtGui.QIcon(
                "MetroMumble/talking_off.svg"))
        elif icon == 'deaf':
            user_to_change.setIcon(0, QtGui.QIcon(
                "MetroMumble/deafened_self.svg"))
        elif icon == 'talking':
            user_to_change.setIcon(0, QtGui.QIcon(
                "MetroMumble/talking_on.svg"))

    def populate_user_list(self, mumble_client):
        '''Populated the QTreeViewWidget with all the users on the server'''
        for value in mumble_client.mumble.users.values():
            self.__add_user_to_tree(value, mumble_client)

    def __add_user_to_tree(self, user, mumble_client):
        channel_id = user['channel_id']
        # print(user)
        user_to_add = QtWidgets.QTreeWidgetItem(
            [user['name'], str(user['session']), 'user'])
        # channel_name = mumble_client.mumble.channels[channel_id]['name']
        channel_widget = self.channel_view.findItems(
            str(channel_id), QtCore.Qt.MatchExactly |
            QtCore.Qt.MatchRecursive, 1)[0]
        channel_widget.addChild(user_to_add)
        channel_widget.setExpanded(True)
        # print(user)
        # print(user['session'])
        # print(channel_name)
        # print(channel_id)
        # print(channel_widget.data(0, 0))
        if 'self_deaf' in user:
            if user['self_deaf']:
                user_to_add.setIcon(0, QtGui.QIcon(
                    "MetroMumble/deafened_self.svg"))
                # self.__change_user_tree_icon(user, mumble_client, 'deaf')
        elif 'self_mute' in user:
            if user['self_mute']:
                user_to_add.setIcon(0, QtGui.QIcon(
                    "MetroMumble/muted_self.svg"))
                # self.__change_user_tree_icon(user, mumble_client, 'muted')
        else:
            user_to_add.setIcon(0, QtGui.QIcon("MetroMumble/talking_off.svg"))
            # self.__change_user_tree_icon(user, mumble_client, 'normal')

    def __delete_user_from_tree(self, user, mumble_client):
        channel_id = user['channel_id']
        # channel_name = mumble_client.mumble.channels[channel_id]['name']
        # user_name = user['name']
        channel_widget = self.channel_view.findItems(
            str(channel_id), QtCore.Qt.MatchExactly |
            QtCore.Qt.MatchRecursive, 1)[0]
        user_widget = self.channel_view.findItems(
            str(user['session']), QtCore.Qt.MatchExactly |
            QtCore.Qt.MatchRecursive, 1)[0]
        channel_widget.removeChild(user_widget)

    def __setup_connect_dialog(self):
        self.connect_dialog = uic.loadUi('connect_dialog.ui')
        self.connect_dialog.setStyleSheet(
            open('MetroMumble/MetroDark.qss', 'r').read())
        self.connect_dialog.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        self.favorites = self.connect_dialog.treeWidget
        header = QtWidgets.QTreeWidgetItem(['Address', 'Port', 'Username'])
        self.favorites.setHeaderItem(header)
        self.favorites.setColumnCount(3)
        self.favorites_tree = QtWidgets.QTreeWidgetItem(['Favorites'])

        self.favorites_file = configparser.ConfigParser()
        self.favorites_file.read('favorites.ini')

        for fav in self.favorites_file.sections():
            if 'address' in self.favorites_file[fav]:
                address = self.favorites_file[fav]['address']
                port = self.favorites_file[fav]['port']
                user = self.favorites_file[fav]['user']
                fav_to_add = QtWidgets.QTreeWidgetItem([address, port, user])
                self.favorites_tree.addChild(fav_to_add)

        self.favorites_tree.setIcon(0, QtGui.QIcon(
            "MetroMumble/emblems/emblem-favorite.svg"))
        # favorite1 = QtWidgets.QTreeWidgetItem(
        # ['saltisland.tk', '64738', 'pymumblegui'])
        # self.favorites_tree.addChild(favorite1)

        self.favorites.addTopLevelItem(self.favorites_tree)
        self.favorites.expandAll()
        self.favorites.setColumnWidth(0, 250)

        self.connect_dialog.findChild(
            QtWidgets.QPushButton, 'add_new_button').clicked.connect(
            self.__add_favorite_gui)
        self.connect_dialog.findChild(
            QtWidgets.QPushButton, 'quit_button').clicked.connect(
            lambda: sys.exit(0))

    def show_connect_dialog(self, mumble_client):
        '''Shows the dialog that lists favorite servers
        and allows connections to be initiated'''

        self.connect_dialog.connect_button.clicked.connect(
            functools.partial(
                self.__make_mumble_client_connect, mumble_client))
        self.connect_dialog.exec()

    def __make_mumble_client_connect(self, mumble_client):
        favorite_info = self.favorites.selectedItems()

        if favorite_info != [] and favorite_info[0].data(0, 0) != 'Favorites':
            selected_item = favorite_info[0]
            host = selected_item.data(0, 0)
            port = selected_item.data(1, 0)
            user = selected_item.data(2, 0)
#            print('Host: %s, Port: %s, User: %s'%(host, port, user))
            try:
                mumble_client.connect(host, port, user)
            except ConnectionError:
                error = QtWidgets.QMessageBox(self.connect_dialog)
                error.setText('Connection Error\n')
                error.show()
            else:
                self.connect_dialog.done(0)

    def __add_favorite_gui(self):

        self.add_fav = uic.loadUi('fav_editor.ui')
        self.add_fav.setStyleSheet(
            open('MetroMumble/MetroDark.qss', 'r').read())
        self.add_fav.buttonBox.buttons()[0].clicked.connect(
            self.__add_favorite)
        self.add_fav.exec()

    def __add_favorite(self):

        address = self.add_fav.address_edit.text()
        port = self.add_fav.port_edit.text()
        username = self.add_fav.username_edit.text()
        self.favorites_file[address] = {
            'address': address, 'port': port, 'user': username}
        with open('favorites.ini', 'w') as configfile:
            self.favorites_file.write(configfile)
        to_add = QtWidgets.QTreeWidgetItem([address, port, username])
        self.favorites_tree.addChild(to_add)

    def make_signal_slot_connection(self, mumble_client):
        '''Connects the pyqtSignal and pyqtSlot from
        the mumble callbacks to the GUI class'''
        mumble_client.sender.message_recieved.connect(
            self.reciever.recieve_message)


class MumbleClient:
    '''MumbleClient: includes all the variables
    to initalize a mumble server connection'''

    def __init__(self):

        self.host = 'saltisland.tk'
        self.port = 64738
        self.user = 'pymumblegui'
        self.password = ''
        self.reconnect = False
        self.mumble = 0
        self.mumble_gui = 0
        self.pyaudio = pyaudio.PyAudio()
        self.pcm_buffer = bytearray()
        self.stream = self.pyaudio.open(
            format=pyaudio.paInt16,
            channels=1, rate=48000,
            # input=True,
            output=True,
            # stream_callback=self.on_audio_ready,
            output_device_index=6, input_device_index=6
        )
        # for i in range(0, self.pyaudio.get_device_count()):
        #     print(self.pyaudio.get_device_info_by_index(i))
        # print(self.pyaudio.get_default_output_device_info())
        # os._exit(1)

    def connect(self, host, port, user):
        self.host = host
        self.port = int(port)
        self.user = user
        self.mumble = pymumble.Mumble(host=self.host, port=self.port,
                                      user=self.user, password=self.password)
        self.mumble.start()
        # self.mumble.is_ready()
        j = 0
        while self.mumble.users.myself is None and j < 10:
            time.sleep(.5)
            j += 1

        self.sender = SignalSlotHandler()
        self.mumble.callbacks.set_callback(
            pymumble.constants.PYMUMBLE_CLBK_TEXTMESSAGERECEIVED,
            self.on_message_recieved)
        self.mumble.callbacks.set_callback(
            pymumble.constants.PYMUMBLE_CLBK_SOUNDRECEIVED,
            self.on_sound_received)
        self.mumble.set_receive_sound(True)

        if self.mumble.users.myself is None:
            raise ConnectionError

    def on_sound_received(self, user, sound_chunk):
        # self.pcm_buffer = self.pcm_buffer + sound_chunk.pcm
        # self.mumble_gui.user_start_stop_talking(user, 'talking')
        # self.stream.write(sound_chunk.pcm)
        self.pcm_buffer = self.pcm_buffer + sound_chunk.pcm
        # print(len(self.pcm_buffer))
        if len(self.pcm_buffer) > 4096 * 4:
            self.stream.write(bytes(self.pcm_buffer))
            self.pcm_buffer = bytearray()
        # self.mumble_gui.user_start_stop_talking(user, 'normal')

    # def on_audio_ready(self, in_data, frame_count, time_info, status_flags):

        # print('test')
        # return (bytes(self.pcm_buffer), pyaudio.paContinue)

    def send_message(self, client_gui):
        '''send_message: sends a message using
        the pymumble client and updates the text output'''
        if client_gui.tabbed_chat.currentIndex() == 1:
            target = self.mumble.channels[self.mumble.users.myself['channel_id']]
        elif client_gui.tabbed_chat.currentIndex() == 0:
            message_post = 'Sending messages to notification stream is not supported\n'
            self.sender.message_recieved.emit(
                message_post, None, client_gui.tabbed_chat.currentIndex())
            client_gui.chat_entry.setText('')
            return
        else:
            client_gui.chat_entry.setText('')
            return
        # print(client_gui.tabbed_chat.currentIndex())
        target.send_text_message(client_gui.chat_entry.text())
        message_post = '{}: {}\n'.format(
            self.user, client_gui.chat_entry.text())
        client_gui.chat_entry.setText('')
        self.sender.message_recieved.emit(
            message_post, self.user, client_gui.tabbed_chat.currentIndex())
        # new_text = client_gui.chat_view.toPlainText() + message_post
        # client_gui.chat_view.setText(new_text)

    def on_message_recieved(self, message):
        'recieve_message: recieves a message'
        message_post = '{}: {}\n'.format(
            self.mumble.users[message.actor]['name'], message.message)
        self.sender.message_recieved.emit(message_post, None, None)

    def set_mumble_gui(self, mumble_gui):
        self.mumble_gui = mumble_gui
        self.mumble.callbacks.set_callback(
            pymumble.constants.PYMUMBLE_CLBK_USERUPDATED,
            functools.partial(self.mumble_gui.user_modified, self))
        self.mumble.callbacks.set_callback(
            pymumble.constants.PYMUMBLE_CLBK_USERCREATED,
            functools.partial(self.mumble_gui.user_created, self))
        self.mumble.callbacks.set_callback(
            pymumble.constants.PYMUMBLE_CLBK_USERREMOVED,
            functools.partial(self.mumble_gui.user_deleted, self))


def main():
    '''main: main function of program'''
    client = MumbleClient()
    client_gui = MumbleGUI()
    while client.mumble == 0 or client.mumble.users.myself is None:
        client_gui.show_connect_dialog(client)
    # client.connect()z
    client.set_mumble_gui(client_gui)
    client_gui.make_signal_slot_connection(client)
    client_gui.populate_channel_list(client)
    client_gui.populate_user_list(client)
    client_gui.chat_entry.returnPressed.connect(
        functools.partial(client.send_message, client_gui))
    sys.exit(client_gui.app.exec_())


if __name__ == '__main__':
    main()
