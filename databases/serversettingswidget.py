import hashlib
import string
import random
from kivy.properties import *
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from .subsonic import ServerSettings

from kivy.lang.builder import Builder
Builder.load_string("""
<ServerSettingsWidget>:
    canvas.before:
        Color:
            rgba: app.theme.button_down[:3]+[0.75]
        BorderImage:
            display_border: [app.display_border, app.display_border, app.display_border, app.display_border]
            size: root.width, root.height
            pos: root.pos
            source: 'data/buttonflat.png'
    padding: app.button_scale / 4
    cols: 1
    size_hint_y: None
    height: self.minimum_height
    Holder:
        WideButton:
            text: "Connect To This Preset"
            on_release: root.connect()
        NormalButton:
            text: "X"
            warn: True
            on_release: root.delete()
    Holder:
        LeftNormalLabel:
            size_hint_x: 0.5
            text: "Name:"
        NormalInput:
            text: root.name
            hint_text: 'Preset name'
            write_tab: False
            multiline: False
            on_text: root.name = self.text
    Holder:
        LeftNormalLabel:
            size_hint_x: 0.5
            text: "IP Address:"
        NormalInput:
            text: root.ip
            hint_text: '127.0.0.1'
            write_tab: False
            multiline: False
            on_text: root.ip = self.text
    Holder:
        LeftNormalLabel:
            size_hint_x: 0.5
            text: "Port:"
        IntegerInput:
            allow_negative: False
            text: root.port
            hint_text: '4040'
            write_tab: False
            multiline: False
            on_text: root.port = self.text
    Holder:
        LeftNormalLabel:
            size_hint_x: 0.5
            text: "Username:"
        NormalInput:
            text: root.username
            hint_text: 'user'
            write_tab: False
            multiline: False
            on_text: root.username = self.text
    Holder:
        LeftNormalLabel:
            size_hint_x: 0.5
            text: "Password:"
        NormalInput:
            text: root.password_entry
            hint_text: 'Enter Password' if not root.password else 'Password Secured'
            password: True
            write_tab: False
            multiline: False
            on_text: root.password_entry = self.text
    Holder:
        LeftNormalLabel:
            size_hint_x: 0.5
            text: "Sub-URL:"
        NormalInput:
            text: root.suburl
            hint_text: 'rest'
            write_tab: False
            multiline: False
            on_text: root.suburl = self.text
    Holder:
        LeftNormalLabel:
            size_hint_x: 0.5
            text: "Use SSH:"
        WideToggle:
            text: "On" if self.state == 'down' else "Off"
            state: 'down' if root.use_ssh else 'normal'
            on_state: root.use_ssh = True if self.state == 'down' else False
""")


class ServerSettingsWidget(GridLayout):
    name = StringProperty('')
    ip = StringProperty('127.0.0.1')
    port = StringProperty('4040')
    username = StringProperty('user')
    salt = StringProperty('')
    password = StringProperty('')
    password_entry = StringProperty('')
    suburl = StringProperty('rest')
    use_ssh = BooleanProperty(False)
    index = NumericProperty(0)
    owner = ObjectProperty(allownone=True)
    vars = ['name', 'ip', 'port', 'username', 'salt', 'password', 'suburl', 'use_ssh']

    def load_settings(self, settings):
        #load a ServerSettings object into this widget
        for var in self.vars:
            setattr(self, var, getattr(settings, var))

    def save_settings(self):
        settings = ServerSettings()
        for var in self.vars:
            setattr(settings, var, getattr(self, var))
        return settings

    def on_password_entry(self, *_):
        if self.password_entry:
            self.salt = self.generate_password_salt()
            self.password = self.generate_hashed_password(self.salt)
        else:
            self.salt = ''
            self.password = ''

    def connect(self):
        self.owner.connect(self.index)

    def delete(self):
        self.owner.delete(self.index)

    def generate_password_salt(self):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

    def generate_hashed_password(self, pass_salt):
        pass_hash = hashlib.md5((self.password_entry+pass_salt).encode('utf-8'))
        return pass_hash.hexdigest()
