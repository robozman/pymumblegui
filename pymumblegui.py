#!/usr/bin/env python3

import threading
import pymumble.pymumble_py3 as pymumble
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import GLib



# Class that loads the glade file and hold all the gtk widgets
class MumbleGUI:
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("gui.glade")
        self.window = self.builder.get_object("main_window")
        self.window.show_all()
        self.chat_view = self.builder.get_object("chat_view")
        self.chat_entry = self.builder.get_object("chat_entry")
        self.chat_entry.set_text("Hello, World!")
    

# Class that initlizes the mumble connection and hold the related variables
# Also hold the functions for sending and recieving messages
class MumbleClient:
    def __init__(self):
            
        self.host = "saltisland.tk"
        self.port = 64738
        self.user = "pymumblegui"
        self.password = ""
        self.reconnect = False
        self.gui = True
            
            
            
        self.mumble = pymumble.Mumble(host=self.host, user=self.user, port=self.port, password=self.password)
        self.mumble.start()
        self.mumble.is_ready()
    
    
    def send_message(self, widget):
        target = self.mumble.channels[self.mumble.users.myself["channel_id"]]
        buffer = widget.get_buffer()
        currentChat = clientGUI.chat_view.get_buffer()
        currentChat.set_text(currentChat.get_text(currentChat.get_start_iter(), currentChat.get_end_iter(), False) + self.user + ": " + buffer.get_text() + "\n" )
        message = buffer.get_text()
        buffer.set_text("", 0)
        target.send_text_message(message)
    def recieve_message(self, message):
        #print(self.mumble.users[message.actor]["name"] + ": " + message.message + "\n")
        currentChat = clientGUI.chat_view.get_buffer()
        currentChat.set_text(currentChat.get_text(currentChat.get_start_iter(), currentChat.get_end_iter(), False) + 
                                self.mumble.users[message.actor]["name"] + ": " + message.message + "\n" )
        #print(self.mumble.users.myself["name"] + ": " + self.mumble.channels[self.mumble.users.myself["channel_id"]]["name"])


if __name__ == '__main__':
    client = MumbleClient()
    client.mumble.callbacks.set_callback(pymumble.constants.PYMUMBLE_CLBK_TEXTMESSAGERECEIVED, client.recieve_message)
    if client.gui == True:
        clientGUI = MumbleGUI()
        clientGUI.chat_entry.connect("activate", client.send_message)
        GLib.MainLoop().run()
    else:
        client.mumble.loop()
    
    
    
    

