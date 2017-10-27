#!/usr/bin/env python3

import threading
import pymumble.pymumble_py3 as pymumble
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import GLib




class MumbleGUI:
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("gui.glade")
        self.window = self.builder.get_object("main_window")
        self.window.show_all()
        self.chat_view = self.builder.get_object("chat_view")
        self.chat_entry = self.builder.get_object("chat_entry")
        self.chat_entry.set_text("Hello, World!")
    


class MumbleClient:
    def __init__(self):
            
        self.host = "saltisland.tk"
        self.port = 64738
        self.user = "pymumblegui"
        self.password = ""
        self.reconnect = False
            
            
            
        self.mumble = pymumble.Mumble(host=self.host, user=self.user, port=self.port, password=self.password)
        self.mumble.start()
        self.mumble.is_ready()
    def send_message(self, widget):
        target = self.mumble.channels.find_by_name("ChatChatChat")
        target.send_text_message(widget.get_text())
        #figure out what function allows getting the current channel


if __name__ == '__main__':
    client = MumbleClient()
    clientGUI = MumbleGUI()
    clientGUI.chat_entry.connect("activate", client.send_message)
    GLib.MainLoop().run()
    
    
    

