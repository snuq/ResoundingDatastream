#todo:
#   need to figure out how to receive wired headset media key on android
#   bluetooth pause needs to be able to resume when app is not active
#   if unable to set rating on playlist, will end up triggering long-press
#   add sort by rating
#   issues when loading with no internet connection - queue doesnt fallback to local, cached lists dont load right now

from kivy.config import Config
Config.set('graphics', 'maxfps', '30')

import time
import threading
import json
import random
import os
import datetime

from kivy.app import App
from plyer import tts
from kivy.base import EventLoop
from kivy.resources import resource_find
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import Screen
from kivy.uix.modalview import ModalView
from kivy.properties import *
from kivy.event import EventDispatcher
from kivy.clock import Clock
from kivy.utils import platform
from kivy.lang.builder import Builder
from kivy.core.window import Window

from snu.app import NormalApp, SimpleTheme
from snu.button import *
from snu.label import NormalLabel, ShortLabel, LeftNormalLabel
from snu.layouts import *
from snu.recycleview import *
from snu.settings import AboutPopup

from player import Player
from screens import *
from widgets import *
from playlists import WidgetDatabase, WidgetListQueue
from settings import MusicPlayerSettings
from databases.subsonic import ServerSettings, parse_song_created, get_utc_offset, song_keys

if platform in ['win', 'linux', 'macosx', 'unknown']:
    desktop = True
    Config.set('input', 'mouse', 'mouse,disable_multitouch')
else:
    desktop = False
if platform == 'android':
    from android.runnable import run_on_ui_thread
    from jnius import autoclass, PythonJavaClass, java_method
    from android.permissions import request_permission, check_permission, Permission
    can_internet = check_permission(Permission.INTERNET)
    if not can_internet:
        request_permission(Permission.INTERNET)

    can_foreground = check_permission(Permission.FOREGROUND_SERVICE)
    if not can_foreground:
        request_permission(Permission.FOREGROUND_SERVICE)

    can_audio_settings = check_permission(Permission.MODIFY_AUDIO_SETTINGS)
    if not can_audio_settings:
        request_permission(Permission.MODIFY_AUDIO_SETTINGS)

    class Runnable(PythonJavaClass):
        """Wrapper around Java Runnable class. This class can be used to schedule a
        call of a Python function into the PythonActivity thread.
        """

        __javainterfaces__ = ["java/lang/Runnable"]
        __runnables__ = []

        def __init__(self, func, read_thread, *args, **kwargs):
            super().__init__()
            self.read_thread = read_thread
            self.func = func
            self.args = args
            self.kwargs = kwargs

        @java_method("()V")
        def run(self):
            self.func(*self.args, **self.kwargs)
            self.read_thread.quit()
else:
    from kivy.clock import mainthread as run_on_ui_thread


KV = """
<-InfoPopup>:
    canvas.before:
        Color:
            rgba: app.theme.background[:3]+[0.9]
        Rectangle:
            pos: self.pos
            size: self.width, self.height - app.button_scale
    size_hint: 1, self.opacity
    overlay_color: 0, 0, 0, 0
    BoxLayout:
        orientation: 'vertical'
        NormalButton:
            size_hint: 1, None
            height: app.button_scale
            opacity: 0
            on_press: root.dismiss()
        WideButton:
            text: 'Show Queue'
            on_release: app.open_queue_popup()
            on_release: root.dismiss()
        WideButton:
            text: 'Show Database'
            on_release: app.open_database_popup()
            on_release: root.dismiss()
        WidgetPlayerVolume:
            swipe_mode: 'none'
            size_hint_y: None
            height: app.button_scale
            player: app.player
        WidgetPlayerModeToggle:
            swipe_mode: 'none'
            size_hint_y: None
            height: app.button_scale
            player: app.player
        Holder:
            ShortLabel:
                text: 'Queue Backup:'
            WideButton:
                text: 'Save'
                on_release: app.save_temp_queue()
                on_release: root.dismiss()
            WideButton:
                text: 'Load'
                on_release: app.load_temp_queue()
                on_release: root.dismiss()
        Widget:
            size_hint_y: None
            height: app.button_scale
        LeftNormalLabel:
            text: 'Action Log:'
        NormalRecycleView:
            orientation: 'vertical'
            data: app.infotext_history
            viewclass: 'ElementLabel'
            SelectableRecycleBoxLayout:
                id: rvbox
                default_size: None, app.button_scale * .5
                default_size_hint: 1, None
        WideButton:
            text: "App Settings"
            on_release: app.open_settings()
            on_release: root.dismiss()
        WideButton:
            disabled: not app.desktop
            opacity: 0 if self.disabled else 1
            height: 0 if self.disabled else app.button_scale
            warn: True
            text: "Quit"
            on_release: app.stop()

<InfoLabel2>:
    image_width: self.height * 7.6923 if (self.height/self.width) < 0.13 else self.width
    image_height: self.height if (self.height/self.width) < 0.13 else self.width * 0.13
    canvas.before:
        Color:
            rgba: root.bgcolor
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: [1, 1, 1, self.bg_alpha]
        Rectangle:
            size: self.image_width, self.image_height
            pos: self.x, self.y + ((self.height - self.image_height) / 2)
            source: 'data/titletransparent.png'
    mipmap: True
    text: app.infotext
    color: app.theme.info_text

<CachePopup>:
    background_color: 0, 0, 0, 0
    overlay_color: app.theme.menu_background[:3]+[0.66]
    auto_dismiss: False
    BoxLayout:
        canvas.before:
            Color:
                rgb: app.theme.menu_background[:3]
            Rectangle:
                size: self.size
                pos: self.pos
        orientation: 'vertical'
        Widget:
        NormalLabel:
            text: "Downloading Files..."
        SliderThemed:
            cursor_color: 0, 0, 0, 0
            value: root.progress
            min: 0
            max: 1
            size_hint_y: None
            height: app.button_scale
        NormalLabel:
            multiline: True
            height: app.button_scale * 2
            text: root.completed_info
        WideButton:
            text: 'Stopping...' if root.want_cancel else 'Stop Downloading'
            on_release: root.cancel()
        Widget:

<LoadingPopup>:
    delay: 0.5
    background_color: 0, 0, 0, 0
    overlay_color: app.theme.menu_background[:3]+[0.66]
    auto_dismiss: False
    BoxLayout:
        orientation: 'vertical'
        Widget:
        NormalLabel:
            text: 'Loading, Please Wait...'
        Image:
            canvas.before:
                PushMatrix
                Rotate:
                    angle: root.angle
                    axis: 0, 0, 1
                    origin: self.center
            canvas.after:
                PopMatrix
            color: app.theme.text
            size_hint: 1, None
            height: app.button_scale
            source: 'data/pause.png'
        NormalLabel:
            text: app.player.database.loading_status
        WideButton:
            text: "Cancel Loading"
            disabled: not app.player.database.allow_cancel
            opacity: 0 if self.disabled else 1
            on_release: app.player.database.cancel_load = True
        Widget:

<NotConnectedPopup>:
    auto_dismiss: False
    BoxLayout:
        canvas.before:
            Color:
                rgb: app.theme.menu_background[:3]
            Rectangle:
                size: self.size
                pos: self.pos
        orientation: 'vertical'
        Widget:
        GridLayout:
            size_hint_y: None
            height: app.button_scale * 3
            cols: 1
            NormalLabel:
                padding: app.button_scale/2
                text_size: self.width, None
                size_hint_y: None
                height: self.texture_size[1]
                text: app.connection_message
            WideButton:
                text: "Reconnect..."
                on_release: app.load_player()
            WideButton:
                text: "Open Server Settings"
                on_release: app.open_server_settings()
            WideButton:
                text: "Save/Load Queue Remotely" if app.autoload_queue else "Save/Load Queue Locally"
                on_release: app.autoload_queue = not app.autoload_queue
            NormalLabel:
                padding: app.button_scale/2
                text_size: self.width, None
                size_hint_y: None
                height: self.texture_size[1]
                text: root.reconnect_countdown_text
        Widget:

MainArea:
    canvas.before:
        Color:
            rgb: app.theme.main_background
        Rectangle:
            size: self.size
            pos: self.pos
    ElementWidget:
        player: app.player
        screen_manager: app.screen_manager
        cols: 1
        size_hint_y: None
        height: app.button_scale * (2 if app.connection_status else 3)
        Header:
            Button:
                text: 'T'
                size_hint_x: None
                width: 0 if self.disabled else self.height
                opacity: 0 if self.disabled else 1
                disabled: not app.test
                on_release: app.run_test()
            ButtonBoxLayout:
                on_release: app.show_info(self)
                Widget:
                    size_hint: None, 1
                    width: self.height/4
                InfoLabel2:
                    text_size: self.size
                    valign: 'center'
                Image:
                    fit_mode: 'contain'
                    color: app.theme.text
                    size_hint: None, 1
                    width: self.height
                    source: 'data/settings.png'
        Header:
            disabled: bool(app.connection_status)
            opacity: 0 if self.disabled else 1
            height: 0 if self.disabled else app.button_scale
            BoxLayout:
                orientation: 'vertical'
                LeftNormalLabel:
                    size_hint_y: 1
                    text: 'No Connection:'
                TickerLabel:
                    size_hint_y: 1
                    text: app.connection_message
            NormalButton:
                size_hint_y: 1
                text: "Server Settings"
                on_release: app.open_server_settings()
        Header:
            disabled: not app.switch_screens
            opacity: 0 if self.disabled else 1
            height: 0 if self.disabled else app.button_scale
            size_hint_x: 0.001 if self.disabled else 1
            ImageButton:
                size_hint: 1, 1
                text: "Prev Screen"
                padding: app.button_scale / 4, 0
                halign: 'right'
                image_halign: 'left'
                image_padding: app.button_scale / 4, 5
                source: 'data/up.png'
                on_release: screenManager.go_previous()
            ImageButton:
                size_hint: 1, 1
                text: "Next Screen"
                padding: app.button_scale / 4, 0
                halign: 'left'
                image_halign: 'right'
                image_padding: app.button_scale / 4, 5
                source: 'data/down.png'
                on_release: screenManager.go_next()
    ScreenManagerBase:
        player: app.player
        id: screenManager
"""

theme_blank = {
    "button_down": [0, 0, 0, 1],
    "button_up": [0, 0, 0, 1],
    "text": [0, 0, 0, 1],
    "selected": [0, 0, 0, 1],
    "active": [0, 0, 0, 1],
    "background": [0, 0, 0, 1],
}

themes = [
    {
        "name": "Blue And Green",
        "button_down": [0.58, 0.69, 0.72, 1.0],
        "button_up": [0.35, 0.39, 0.53, 1.0],
        "text": [0.9, 0.9, 0.9, 1],
        "selected": [0.4, 0.6, 0.4, 0.5],
        "active": [1.0, 0.239, 0.344, 0.5],
        "background": [0., 0.2, 0.2, 1.0],
    },
    {
        "name": "Clean And Bright",
        "button_down": [0.6, 0.6, 0.6, 1.0],
        "button_up": [0.8, 0.8, 0.8, 1.0],
        "text": [0.0, 0.011, 0.0, 1.0],
        "selected": [0.739, 0.75, 0.444, 0.5],
        "active": [1.0, 0.239, 0.344, 0.5],
        "background": [0.65, 0.65, 0.65, 1],
    },
    {
        "name": "Very Bright",
        "button_down": [0.4, 0.4, 0.4, 1.0],
        "button_up": [1, 1, 1, 1.0],
        "text": [0.1, 0.1, 0.1, 1.0],
        "selected": [0.75, 0.75, 0.1, 0.5],
        "active": [1.0, 0.239, 0.344, 0.5],
        "background": [0.8, 0.8, 0.8, 1],
    },
    {
        "name": "Bright Pink",
        "button_down": [0.4, 0.4, 0.4, 1.0],
        "button_up": [1, 0.9, 0.9, 1.0],
        "text": [0.1, 0.1, 0.1, 1.0],
        "selected": [0.739, 0.45, 0.444, 0.5],
        "active": [1.0, 0.239, 0.344, 0.5],
        "background": [1, 0.8, 0.8, 1],
    },
    {
        "name": "Bright Blue",
        "button_down": [0.5, 0.5, 0.6, 1.0],
        "button_up": [1, 1, 1, 1.0],
        "text": [0.1, 0.1, 0.1, 1.0],
        "selected": [0.4, 0.8, 0.6, 0.5],
        "active": [1.0, 0.239, 0.344, 0.5],
        "background": [0.8, 0.9, 1, 1],
    },
    {
        "name": "Dark Blue",
        "button_down": [0.2, 0.2, 0.4, 1.0],
        "button_up": [0.3, 0.3, 0.5, 1.0],
        "text": [0.9, 0.9, 0.9, 1],
        "selected": [0.7, 0.5, 0.5, 0.5],
        "active": [0.8, 0.3, 0.3, 0.5],
        "background": [0.1, 0.1, 0.1, 1.0],
    },
    {
        "name": "Dark Red",
        "button_down": [0.4, 0.2, 0.2, 1.0],
        "button_up": [0.7, 0.3, 0.3, 1.0],
        "text": [0.9, 0.9, 0.9, 1],
        "selected": [0.7, 0.5, 0.7, 0.5],
        "active": [1.0, 0.3, 0.3, 0.5],
        "background": [0.2, 0.1, 0.1, 1.0],
    },
    {
        "name": "In The Trees",
        "button_down": [0.4, 0.3, 0.2, 1.0],
        "button_up": [0.5, 0.3, 0.1, 1.0],
        "text": [0.9, 0.9, 0.9, 1],
        "selected": [0.3, 0.7, 0.3, 0.5],
        "active": [1.0, 0.3, 0.3, 0.5],
        "background": [0.1, 0.2, 0.1, 1.0],
    },
    {
        "name": "Dark Green",
        "button_down": [0.2, 0.4, 0.2, 1.0],
        "button_up": [0.3, 0.5, 0.3, 1.0],
        "text": [0.9, 0.9, 0.9, 1],
        "selected": [0.5, 0.5, 0.7, 0.5],
        "active": [1.0, 0.3, 0.3, 0.5],
        "background": [0.0, 0.2, 0.1, 1.0],
    },
    {
        "name": "Low Light",
        "button_down": [0.1, 0.1, 0.15, 1.0],
        "button_up": [0.2, 0.2, 0.25, 1.0],
        "text": [0.6, 0.6, 0.6, 1],
        "selected": [0.1, 0.1, 0.3, 0.5],
        "active": [0.5, 0.3, 0.3, 0.5],
        "background": [0, 0, 0, 1.0],
    },
    {
        "name": "Gameboy",
        "button_down": [0.059, 0.22, 0.059, 1.0],
        "button_up": [0.188, 0.384, 0.188, 1.0],
        "text": [0.708, 0.837, 0.159, 1],
        "selected": [0.545, 0.675, 0.059, 1.0],
        "active": [0.545, 0.675, 0.059, 1.0],
        "background": [0.059, 0.22, 0.059, 1.0],
    },
    {
        "name": "Reminder Of Winamp",
        "button_down": [0.61, 0.61, 0.63, 1.0],
        "button_up": [0.25, 0.25, 0.35, 1.0],
        "text": [1, 1, 1, 1],
        "selected": [0.01, 0.91, 0.01, 0.5],
        "active": [1.0, 0.3, 0.3, 0.5],
        "background": [0, 0, 0, 1.0],
    }
]


def remove_file(file):
    try:
        os.remove(file)
        return True
    except:
        return False


class WakeLock(EventDispatcher):
    tag = 'ResoundingDatastreamWakeLockTag'
    powermanager = ObjectProperty()
    powerservice = ObjectProperty()
    wakelock = ObjectProperty(allownone=True)
    wake_type = StringProperty('None')
    states = {'Keep Screen On': 'SCREEN_DIM_WAKE_LOCK', 'Background': 'PARTIAL_WAKE_LOCK'}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup()

    def on_wake_type(self, *_):
        if platform != 'android':
            return
        if self.wake_type not in self.states.keys():
            self.release()
        else:
            self.request()

    def setup(self):
        if platform != 'android':
            return
        context = autoclass('android.content.Context')
        self.powermanager = autoclass('android.os.PowerManager')
        pythonactivity = autoclass('org.kivy.android.PythonActivity')
        activity = pythonactivity.mActivity
        self.powerservice = activity.getSystemService(context.POWER_SERVICE)
        self.wakelock = None

    def request(self):
        self.release()
        self.request_wakelock_permission()
        if self.wake_type in self.states.keys():
            wake_name = self.states[self.wake_type]
            wake_type = getattr(self.powermanager, wake_name)
            self.wakelock = self.powerservice.newWakeLock(wake_type, self.tag)
            self.wakelock.acquire()

    def release(self):
        if self.wakelock and self.wakelock.isHeld():
            self.wakelock.release()
            self.wakelock = None

    def request_wakelock_permission(self):
        if platform != 'android':
            return
        can_wakelock = check_permission(Permission.WAKE_LOCK)
        if not can_wakelock:
            request_permission(Permission.WAKE_LOCK)


def to_bool(text):
    if text.lower() in ['1', 'true', 't', 'yes']:
        return True
    return False


class ButtonBoxLayout(ButtonBehavior, BoxLayout):
    pass


class InfoLabel2(NormalLabel):
    """Special label widget that automatically displays a message from the app class and blinks when the text is changed."""

    image_height = NumericProperty(10)
    image_width = NumericProperty(10)
    bgcolor = ListProperty([1, 1, 0, 0])
    blinker = ObjectProperty()
    bg_alpha = NumericProperty(1)

    def on_text(self, instance, text):
        del instance
        app = App.get_running_app()
        if self.blinker:
            self.stop_blinking()
        if text:
            self.bg_alpha = 0
            no_bg = [.5, .5, .5, 0]
            yes_bg = app.theme.selected
            self.blinker = Animation(bgcolor=yes_bg, duration=0.33) + Animation(bgcolor=no_bg, duration=0.33)
            self.blinker.start(self)
        else:
            self.bg_alpha = 1

    def stop_blinking(self, *_):
        if self.blinker:
            self.blinker.cancel(self)
        self.bgcolor = [1, 1, 0, 0]


class InfoPopup(AnimatedModalView):
    pass


class CachePopup(AnimatedModalView):
    songs = ListProperty()
    progress = NumericProperty(0.01)
    want_cancel = BooleanProperty(False)
    cache_thread = None
    completed_info = StringProperty('')

    def on_dimiss(self, *_):
        self.cancel()

    def on_open(self, *_):
        self.cache_thread = threading.Thread(target=self.cache)
        self.cache_thread.start()

    def cancel(self):
        self.want_cancel = True

    def cancel_finish(self):
        self.cache_thread = None
        self.dismiss()
        app = App.get_running_app()
        app.load_local_cache_songs()
        app.cache_popup = None

    def cache(self):
        app = App.get_running_app()
        is_default, cache_folder = app.get_cache_folder()
        if not os.path.exists(cache_folder):
            os.makedirs(cache_folder)
        songs_to_download = []
        total_size = 0
        total_songs = len(self.songs)
        utc_offset = get_utc_offset()
        self.completed_info = 'Preparing to download '+str(total_songs)+' songs'
        for song in self.songs:
            if self.want_cancel:
                self.cancel_finish()
                return
            try:
                song_size = song['duration'] * song['bitRate']
            except:
                song_size = 34560
            song['size'] = song_size
            cached = app.cached_file(song['id'], song['created'], utc_offset)
            if not cached:
                total_size += song_size
                songs_to_download.append(song)
        database = app.player.database
        downloaded_size = 0
        downloaded = 0
        total_songs = len(songs_to_download)
        for song in songs_to_download:
            if self.want_cancel:
                self.cancel_finish()
                return
            self.completed_info = 'Downloading '+str(downloaded+1)+' of '+str(total_songs)
            song_filename = os.path.join(cache_folder, app.get_cache_file(song))
            if os.path.isfile(song_filename):
                try:
                    os.remove(song_filename)
                except:
                    continue
            song_data = database.get_download(song['id'])
            if song_data is not None:
                downloaded += 1
                with open(song_filename, 'wb') as file:
                    file.write(song_data)
            song_copy = {}
            for key in song_keys:
                song_copy[key] = song[key]
            app.local_cache_info[song['id']] = song_copy
            downloaded_size += song['size']
            self.progress = downloaded_size / total_size
        app.message('Downloaded '+str(downloaded)+' songs')
        self.cancel_finish()


class NotConnectedPopup(AnimatedModalView):
    reconnect_countdown_text = StringProperty()
    reconnect_countdown = NumericProperty(5)
    reconnect_counter = ObjectProperty(allownone=True)

    def on_open(self, *_):
        self.start_reconnect()

    def start_reconnect(self):
        self.reconnect_countdown = 6
        self.update_reconnect()

    @mainthread
    def update_reconnect(self, *_):
        app = App.get_running_app()
        if not self._is_open:
            return
        if app.server_settings_popup and app.server_settings_popup._is_open:
            self.reconnect_counter = Clock.schedule_once(self.update_reconnect, 1)
            return
        if app.connection_status is None:
            self.reconnect_countdown_text = ''
            return
        elif app.connection_status:
            self.reconnect_countdown_text = ''
            return
        self.reconnect_countdown -= 1
        if self.reconnect_countdown <= 0:
            self.reconnect_countdown = 6
            self.reconnect_countdown_text = "Connecting..."
            app.load_player()
        else:
            self.reconnect_countdown_text = "Attempting to connect again in: "+str(self.reconnect_countdown)
        self.reconnect_counter = Clock.schedule_once(self.update_reconnect, 1)


class LoadingPopup(AnimatedModalView):
    pass


class ResoundingDatastream(NormalApp):
    test = BooleanProperty(False)
    animation_length = 0.333
    desktop = BooleanProperty(True)
    switch_screens = BooleanProperty(True)
    osc_port = 30107
    session = None
    session_callback = None
    not_connected_popup = ObjectProperty(allownone=True)
    loading_popup = ObjectProperty(allownone=True)
    server_settings_popup = ObjectProperty(allownone=True)
    screen_manager = ObjectProperty()
    current_screen_name = StringProperty("Screen")
    screen_presets = DictProperty()
    scale_amount = 15
    player = None
    blocking_threads = DictProperty()
    background_threads = DictProperty()
    cancel_threads = BooleanProperty(False)
    speak_threads = ListProperty()
    wakelock = ObjectProperty()
    connection_message = StringProperty('Connecting...')
    connection_status = BooleanProperty(allownone=True)
    connection_retries = NumericProperty(2)
    connection_timeout = NumericProperty(3)

    color_theme = StringProperty()
    speak_screen = BooleanProperty(False)
    speak_setting = BooleanProperty(False)
    autoload_queue = BooleanProperty(True)
    autoplay = BooleanProperty(False)
    infotext_history = ListProperty()
    infotext_dropdown = ObjectProperty(allownone=True)
    popup_size_hint_x = 1
    about_text = StringProperty()
    queue_max_amount = NumericProperty(100)
    queue_selected_only = BooleanProperty(True)
    queue_play_immediately = BooleanProperty(True)
    queue_mode = StringProperty('replace')
    queue_mode_names = {'replace': 'Replace All', 'next': 'Add After Current', 'end': 'Add At End', 'start': 'Add At Start'}
    last_playlist_name = StringProperty()
    last_playlist_id = StringProperty()

    database_rescan_status = StringProperty()
    database_rescan_tracker = ObjectProperty(allownone=True)
    database_rescan_tracker_fails = 0

    sort_mode_song = StringProperty('name')
    sort_mode_artist = StringProperty('name')
    sort_mode_other = StringProperty('name')
    sort_mode_playlist = StringProperty('original')
    sort_reverse = BooleanProperty(False)

    settings_cls = MusicPlayerSettings

    local_cache = {}
    local_cache_info = {}
    local_cache_lists = {}
    cache_info = StringProperty()
    cache_popup = ObjectProperty(allownone=True)
    cache_location = StringProperty()
    cache_songlists = BooleanProperty(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme = SimpleTheme()
        self.theme.data_to_theme(theme_blank)

    def run_test(self):
        self.message(str(self.player.song_queue.verify_song_queue()))

    @run_on_ui_thread
    def start_bluetooth_button(self, *_):
        from bluetoothcontroller import CallbackWrapper, start_media_session
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        activity = PythonActivity.mActivity
        self.session_callback = CallbackWrapper()
        self.session_callback.receive_play_toggle = self.bt_play_toggle
        self.session_callback.receive_stop = self.bt_stop
        self.session_callback.receive_next = self.bt_next
        self.session_callback.receive_previous = self.bt_previous
        self.session = start_media_session(activity, self.session_callback)

    def bt_play_toggle(self, *_):
        self.player.song_queue.play_toggle()

    def bt_stop(self, *_):
        self.player.song_queue.stop()

    def bt_next(self, *_):
        self.player.song_queue.next()

    def bt_previous(self, *_):
        self.player.song_queue.previous()

    def open_list_popup(self, queue, close_text):
        self.dismiss_popup()
        queue.player = self.player
        self.popup = AnimatedModalView(size_hint=(1, 0.85), background_color=(0, 0, 0, 0), overlay_color=self.theme.menu_background[:3]+[0.85])
        box = BoxLayout(orientation='vertical')
        box.add_widget(queue)
        button = WideButton(text=close_text)
        button.bind(on_release=self.dismiss_popup)
        box.add_widget(button)
        self.popup.add_widget(box)
        self.popup.open()

    def open_queue_popup(self):
        queue = WidgetListQueue()
        close_text = 'Close Queue'
        self.open_list_popup(queue, close_text)

    def open_database_popup(self):
        queue = WidgetDatabase()
        close_text = 'Close Database'
        self.open_list_popup(queue, close_text)

    def get_default_cache_folders(self):
        caches = [['songcache', "App Folder Storage"]]
        if platform == 'android':
            from jnius import autoclass
            pythonactivity = autoclass('org.kivy.android.PythonActivity')
            activity = pythonactivity.mActivity
            context = activity.getApplicationContext()
            cache_dirs = context.getExternalCacheDirs()
            for cache_dir in cache_dirs:
                dir_string = str(cache_dir.toPath().toAbsolutePath().toString())
                if 'emulated' in dir_string:
                    caches.append([dir_string, "Internal Storage"])
                else:
                    caches.append([dir_string, "External Storage"])
        return caches

    def get_cache_folder(self, force_local=False):
        default_cache = 'songcache'
        if not force_local and self.cache_location and self.cache_location != default_cache:
            is_dir = os.path.isdir(self.cache_location)
            if not is_dir:
                self.message("Cache directory is not valid, using default")
            else:
                return False, self.cache_location
        return True, default_cache

    def update_cache_info(self):
        self.cache_info = "Stored files: "+str(len(self.local_cache.keys()))

    def get_cache_list_folder(self, force_local=False):
        is_default, cache_folder = self.get_cache_folder(force_local=force_local)
        list_folder = os.path.join(cache_folder, "lists")
        return list_folder

    def get_cached_list(self, listtype, listid):
        #listtype may be: artists, artist_albums, artist_songs, album_songs, genre_songs, genre_albums, genres,
        #   songs_favorites, albums_favorites, albums, playlist_songs, playlists, songs,
        if self.cache_songlists:
            #songlist cacheing enabled
            filename = listtype + '_' + listid
            if filename in self.local_cache_lists.keys():
                #songlist is cached
                data = self.local_cache_lists[filename]
                if data is None:
                    list_folder = self.get_cache_list_folder()
                    try:
                        fullpath = os.path.join(list_folder, filename)
                        with open(fullpath) as file:
                            data = json.load(file)
                    except:
                        data = None
                return data
        return None

    def add_cached_list(self, listtype, listid, data):
        list_folder = self.get_cache_list_folder()
        if not os.path.exists(list_folder):
            os.makedirs(list_folder)
        filename = listtype+'_'+listid
        filepath = os.path.join(list_folder, filename)
        remove_file(filepath)
        if not data and filename in self.local_cache_lists.keys():
            del self.local_cache_lists[filename]
            return
        self.local_cache_lists[filename] = data
        try:
            with open(filepath, 'w') as file:
                json.dump(data, file, indent=2)
        except Exception as e:
            pass

    def load_local_cache_lists(self, *_):
        local_cache = {}
        list_folder = self.get_cache_list_folder()
        for root, dirs, files in os.walk(list_folder):
            for filename in files:
                local_cache[filename] = None
            break
        self.local_cache_lists = local_cache

    def clean_cache_lists(self):
        list_folder = self.get_cache_list_folder()
        for root, dirs, files in os.walk(list_folder):
            for file in files:
                fullpath = os.path.join(root, file)
                remove_file(fullpath)
            break
        self.local_cache_lists = {}

    def save_local_cache_info(self):
        try:
            #conf_dir = self.get_local_conf_folder()
            is_default, cache_folder = self.get_cache_folder()
            info_folder = os.path.join(cache_folder, 'cache_info')
            if not os.path.exists(info_folder):
                os.makedirs(info_folder)
            filename = os.path.join(info_folder, 'local_cache_info.json')
            with open(filename, 'w') as file:
                json.dump(self.local_cache_info, file, indent=2)
        except Exception as e:
            pass

    def load_local_cache_info(self, *_):
        self.local_cache_info = {}
        try:
            #conf_dir = self.get_local_conf_folder()
            is_default, cache_folder = self.get_cache_folder()
            info_folder = os.path.join(cache_folder, 'cache_info')
            if not os.path.exists(info_folder):
                os.makedirs(info_folder)
            filename = os.path.join(info_folder, 'local_cache_info.json')
            with open(filename) as file:
                data = json.load(file)
            self.local_cache_info = data
        except Exception as e:
            self.local_cache_info = {}

    def load_local_cache_songs(self):
        local_cache = {}
        start_time = time.time()
        is_default, cache_folder = self.get_cache_folder()
        files = os.listdir(cache_folder)  #this is actually a bit faster than os.walk
        files.remove('cache_info')
        files.remove('lists')
        for file in files:
            fullpath = os.path.join(cache_folder, file)
            modified_date = None
            songid = os.path.splitext(file)[0]
            data = [fullpath, modified_date]
            local_cache[songid] = data

        total_time = time.time() - start_time
        self.local_cache = local_cache
        if local_cache.keys():
            message = 'Loaded local cache in '+str(round(total_time, 4))+' seconds'
            Clock.schedule_once(lambda x: self.message(message))
        self.update_cache_info()
        if self.player:
            self.player.song_queue_set_queue()
        return

    def get_cache_file(self, song):
        return song['id']+'.'+song['suffix']

    def clean_cache(self, total=False):
        self.add_blocking_thread('Clean Cache', self.clean_cache_process, (total, ))

    def remove_cache_file(self, song_id):
        if song_id in self.local_cache.keys():
            filename, modified_date = self.local_cache[song_id]
            remove_file(filename)
            del self.local_cache[song_id]
        if song_id in self.local_cache_info.keys():
            del self.local_cache_info[song_id]

    def clean_cache_process(self, total, timeout):
        is_default, cache_folder = self.get_cache_folder()
        if not is_default and total:
            #clear out default app directory cache as well
            is_def, local_cache_folder = self.get_cache_folder(force_local=True)
            for root, dirs, files in os.walk(local_cache_folder):
                for filename in files:
                    fullpath = os.path.join(root, filename)
                    remove_file(fullpath)

        removed = 0
        failed_remove = 0
        utc_offset = get_utc_offset()
        if not total:
            #get a list of all song ids
            all_songs = self.player.database_get_search_song(query='', timeout=timeout)
            if all_songs is None:
                return False
            all_songs_dict = {}
            for song in all_songs:
                all_songs_dict[song['id']] = song
        else:
            self.clean_cache_lists()
            all_songs_dict = {}
        for songid in self.local_cache.keys():
            songdata = self.local_cache[songid]
            filename, modified_date = songdata
            if songid not in all_songs_dict.keys():
                #song file is not in all songs list, delete it
                if songid in self.local_cache_info.keys():
                    del self.local_cache_info[songid]
                did_remove = remove_file(filename)
                if did_remove:
                    removed += 1
                else:
                    failed_remove += 1
                continue
            song = all_songs_dict[songid]
            database_timestamp = parse_song_created(song['created'], utc_offset)
            if database_timestamp is None:
                #cant determine databse timestamp, delete files
                if songid in self.local_cache_info.keys():
                    del self.local_cache_info[songid]
                did_remove = remove_file(filename)
                if did_remove:
                    removed += 1
                else:
                    failed_remove += 1
                continue
            if modified_date is None:
                modified_date = os.path.getmtime(filename)
            if modified_date is None:
                cache_newer = False
            else:
                cache_newer = modified_date > database_timestamp
            if not cache_newer:
                #file is outdated, delete
                if songid in self.local_cache_info.keys():
                    del self.local_cache_info[songid]
                did_remove = remove_file(filename)
                if did_remove:
                    removed += 1
                else:
                    failed_remove += 1
                continue
        if failed_remove > 0:
            failed = ', could not remove '+str(failed_remove)
        else:
            failed = ''
        self.message("Cleaned cache, removed "+str(removed)+" files"+failed)
        self.load_local_cache_songs()
        self.player.set_playlist_changed('cache')
        return True

    @mainthread
    def cache_songs(self, songs):
        if self.cache_popup:
            return
        self.cache_popup = CachePopup(songs=songs)
        self.cache_popup.open()

    def cached_file(self, song_id, song_created, utc_offset=None):
        #Checks if song is in local cache and is not outdated, returns path if it is
        if song_id in self.local_cache.keys():
            song_data = self.local_cache[song_id]
            filename, modified_date = song_data
            if modified_date is None:
                modified_date = os.path.getmtime(filename)
                self.local_cache[song_id][1] = modified_date
            database_timestamp = parse_song_created(song_created, utc_offset)
            if database_timestamp is None:
                return None
            cache_newer = modified_date > database_timestamp
            if cache_newer:
                return filename
        return None

    def hook_keyboard(self, window, scancode, *_):
        """This function receives keyboard events"""

        #self.message(str(scancode))
        playpause = [1073742085]
        if scancode in playpause:
            self.player.playtoggle()
            return True
        if scancode == 27:
            settings_closed = self.close_settings()
            if settings_closed:
                return True
            if self.cache_popup:
                self.cache_popup.cancel()
                return True
            if self.loading_popup:
                return True
            screen = self.screen_manager.current_screen
            if screen:
                for child in screen.generated_widgets:
                    if child.widget_type == 'BrowseDatabaseOpener':
                        return child.go_up()
            return False

    @mainthread
    def update_connection_status(self, status, message):
        self.connection_status = status
        self.connection_message = message

    def is_blocking_thread(self, name):
        return name in self.blocking_threads.keys()

    def add_background_thread(self, name, function, args=()):
        if name in self.background_threads.keys():
            return False
        thread = threading.Thread(target=function, args=args)
        self.background_threads[name] = thread
        thread.start()
        return True

    def end_background_thread(self, name):
        try:
            del self.background_threads[name]
        except:
            pass

    def add_blocking_thread(self, name, function, args=()):
        self.open_loading_popup()
        if name in self.blocking_threads.keys():
            self.message(name+' already running!')
            return False
        args = (name, function) + args
        thread = threading.Thread(target=self.blocking_thread_function, args=args)
        self.blocking_threads[name] = thread
        thread.start()
        return True

    def add_blocking_thread_single(self, name, function, args=()):
        self.open_loading_popup()
        if name in self.blocking_threads.keys():
            self.message(name+' already running!')
            return False
        args = (name, function) + args
        thread = threading.Thread(target=self.blocking_thread_function_single, args=args)
        self.blocking_threads[name] = thread
        thread.start()
        return True

    def blocking_thread_function_single(self, name, function, *args):
        completed = function(*args)
        if completed:
            self.update_connection_status(True, "")
        else:
            self.update_connection_status(False, "Unable To "+name)
        self.end_blocking_thread(name)

    def blocking_thread_function(self, name, function, *args):
        completed = False
        timeout = max(1, self.connection_timeout)
        max_retries = max(1, self.connection_retries)
        retries = 0
        while retries < max_retries:
            function_args = args + (timeout, )
            completed = function(*function_args)
            if completed:
                break
            retries += 1
            timeout += 1
        if name not in ['Update Database']:
            if completed:
                self.update_connection_status(True, "")
            else:
                status = "Unable To "+name
                self.update_connection_status(False, status)
        self.end_blocking_thread(name)

    def end_blocking_thread(self, name):
        try:
            del self.blocking_threads[name]
        except:
            pass
        if not self.blocking_threads.keys():
            self.close_loading_popup()

    def speak(self, text, category='setting'):
        if category == 'setting' and self.speak_setting:
            text = text
        elif self.speak_screen:
            if not text.strip().lower().endswith('screen'):
                text = text+' screen'
        else:
            text = None
        if text:
            if len(self.speak_threads) > 2:
                return
            speak = threading.Thread(target=self.speak_process, args=(text,))
            self.speak_threads.append(speak)
            speak.start()

    def speak_process(self, text):
        try:
            tts.speak(text)
        except:
            pass
        self.speak_threads.pop(0)

    def dismiss_popup(self, *_):
        if self.popup:
            self.popup.dismiss()
            self.popup = None

    def load_theme(self, theme):
        try:
            self.color_theme = theme['name']
        except:
            pass
        super().load_theme(theme)

    def find_theme_index(self, theme_name):
        for index, theme in enumerate(themes):
            if theme['name'] == theme_name:
                return index
        return 0

    @mainthread
    def message(self, text, timeout=6):
        self.infotext_history.insert(0, {'text': text})
        super().message(text, timeout)

    def dismiss_info(self, *_):
        if self.infotext_dropdown:
            self.infotext_dropdown.dismiss()
            self.infotext_dropdown = None

    def show_info(self, button):
        self.dismiss_info()
        self.infotext_dropdown = InfoPopup()
        self.infotext_dropdown.open(button)

    def on_config_change(self, config, section, key, value):
        """Called when the configuration file is changed"""
        super().on_config_change(config, section, key, value)
        self.load_settings()
        if section == 'Settings' and key == 'cache_location':
            self.load_local_cache_songs()
        self.setup_player()
        self.load_screen_presets()
        self.generate_screens()
        theme_index = self.find_theme_index(self.color_theme)
        self.load_theme(themes[theme_index])

    def save_settings(self):
        #save all settings into config files
        self.config.set("Settings", "color_theme", self.color_theme)
        self.config.set("Settings", "speak_screen", str(int(self.speak_screen)))
        self.config.set("Settings", "speak_setting", str(int(self.speak_setting)))
        self.config.set("Settings", "random_size", str(int(self.player.random_amount)))
        self.config.set("Settings", "volume", str(self.player.volume))
        self.config.set("Settings", "play_mode", self.player.play_mode)
        self.config.set("Settings", "autoplay", str(int(self.autoplay)))
        self.config.set("Settings", "queue_max_amount", str(int(self.queue_max_amount)))
        self.config.set("Settings", "queue_selected_only", str(int(self.queue_selected_only)))
        self.config.set("Settings", "queue_play_immediately", str(int(self.queue_play_immediately)))
        self.config.set("Settings", "queue_mode", self.queue_mode)
        self.config.set("Settings", "sort_mode_song", self.sort_mode_song)
        self.config.set("Settings", "sort_mode_artist", self.sort_mode_artist)
        self.config.set("Settings", "sort_mode_other", self.sort_mode_other)
        self.config.set("Settings", "sort_mode_playlist", self.sort_mode_playlist)
        self.config.set("Settings", "sort_reverse", str(int(self.sort_reverse)))
        self.config.set("Settings", "wakelock", self.wakelock.wake_type)
        self.config.set("Settings", "skiponestar", str(int(self.player.skiponestar)))
        self.config.set("Settings", "scrobbletime", str(self.player.scrobbletime))
        self.config.set("Settings", "cache_location", self.cache_location)
        self.config.set("Settings", "cache_songlists", str(int(self.cache_songlists)))
        self.config.set("Queue", "autoload_queue", str(int(self.autoload_queue)))
        self.config.set("Queue", "queue_type", self.player.queue_type)
        self.config.set("Queue", "queue_id", self.player.queue_id)
        self.save_server_presets()
        self.save_screen_presets()
        self.save_local_cache_info()
        if not self.not_connected_popup:
            self.save_queue_local()
            if self.autoload_queue:
                self.player.queue_save(self)

    def load_settings(self):
        #load in settings from config files
        self.color_theme = self.config.get('Settings', 'color_theme')
        self.speak_screen = self.config.getboolean("Settings", "speak_screen")
        self.speak_setting = self.config.getboolean("Settings", "speak_setting")
        self.queue_max_amount = self.config.getint("Settings", "queue_max_amount")
        self.queue_selected_only = self.config.getboolean("Settings", "queue_selected_only")
        self.queue_play_immediately = self.config.getboolean("Settings", "queue_play_immediately")
        self.cache_location = self.config.get("Settings", "cache_location")
        self.cache_songlists = self.config.getboolean("Settings", "cache_songlists")
        queue_mode = self.config.get("Settings", "queue_mode").lower()
        if queue_mode in self.queue_mode_names.keys():
            self.queue_mode = queue_mode
        else:
            self.queue_mode = 'replace'
        self.sort_mode_song = self.config.get('Settings', 'sort_mode_song')
        self.sort_mode_artist = self.config.get('Settings', 'sort_mode_artist')
        self.sort_mode_other = self.config.get('Settings', 'sort_mode_other')
        self.sort_mode_playlist = self.config.get('Settings', 'sort_mode_playlist')
        self.sort_reverse = self.config.getboolean('Settings', 'sort_reverse')
        self.wakelock.wake_type = self.config.get("Settings", "wakelock")

    def save_screen_presets(self):
        self.config.remove_section("Screens")
        self.config.add_section("Screens")
        for screen in self.screen_manager.screens:
            data = screen.generate_preset()
            self.config.set("Screens", screen.name, data)
        self.config.set("Settings", "current_screen_name", self.screen_manager.current)

    def load_screen_presets(self):
        self.screen_presets = {}
        self.current_screen_name = self.config.get("Settings", "current_screen_name")
        try:
            screen_names = self.config.items("Screens")
        except:
            screen_names = [['screen', ""]]
        for name, data in screen_names:
            self.screen_presets[name] = data

    @mainthread
    def generate_screens(self):
        self.screen_manager.clear_widgets()
        names = []
        for screen_name in sorted(self.screen_presets.keys()):
            screen_preset = self.screen_presets[screen_name]
            screen = ScreenBase(name=screen_name, screen_manager=self.screen_manager, player=self.player)
            screen.load_preset(screen_preset)
            while screen.name in names:
                screen.name = screen.name+'.1'
            names.append(screen.name)
            screen.generate_widgets()
            self.screen_manager.add_widget(screen)
        if self.current_screen_name in names:
            self.screen_manager.current = self.current_screen_name
        if not names:
            screen = ScreenBase(name="Screen", screen_manager=self.screen_manager, player=self.player)
            screen.generate_widgets()
            self.screen_manager.add_widget(screen)
        if len(names) <= 1:
            self.switch_screens = False
        else:
            self.switch_screens = True

    def load_server_presets(self):
        servers = []
        datas = self.config.get("Server", "servers")
        datas = datas.split('|')
        for data in datas:
            setting = self.parse_server_data(data)
            if setting is not None:
                servers.append(setting)
        return servers

    def parse_server_data(self, server_data):
        datas = server_data.split(':')
        if len(datas) >= 8:
            name, ip, port, suburl, use_ssh, username, password, salt = datas
            if not suburl:
                suburl = 'rest'
            use_ssh = to_bool(use_ssh)
            setting = ServerSettings(name=name, ip=ip, port=port, username=username, password=password, salt=salt, suburl=suburl, use_ssh=use_ssh)
            return setting
        return None

    def save_server_presets(self):
        self.config.set("Server", "connection_timeout", str(self.connection_timeout))
        self.config.set("Server", "connection_retries", str(self.connection_retries))
        self.config.set("Server", "current_index", str(self.player.server_current))
        servers = self.player.servers
        presets = []
        for server in servers:
            data = self.generate_server_data(server)
            presets.append(data)
        presets_data = '|'.join(presets)
        self.config.set("Server", "servers", presets_data)

    def generate_server_data(self, settings):
        if settings.suburl == 'rest':
            suburl = ''
        else:
            suburl = settings.suburl
        string = ":".join([settings.name, settings.ip, settings.port, suburl, str(settings.use_ssh), settings.username, settings.password, settings.salt])
        return string

    def get_local_conf_folder(self):
        conf_file = self.get_application_config()
        conf_dir = os.path.split(conf_file)[0]
        return conf_dir

    def get_local_queue_file(self, filename='queue'):
        conf_dir = self.get_local_conf_folder()
        queue_file = os.path.join(conf_dir, filename+'.json')
        return queue_file

    def load_queue_local(self, queue_filename=None, play=True, background=False):
        try:
            if queue_filename is None:
                queue_filename = self.get_local_queue_file()
            if not os.path.isfile(queue_filename):
                return
            with open(queue_filename) as file:
                data = json.load(file)
            if data:
                self.player.queue_load_local(data, play=play, background=background)
        except:
            if not background:
                self.message("Unable to load local queue.")

    def save_queue_local(self, queue_filename=None):
        try:
            if queue_filename is None:
                queue_filename = self.get_local_queue_file()
            data = self.player.queue_save_local()
            with open(queue_filename, 'w') as file:
                json.dump(data, file, indent=2)
        except:
            self.message('Unable to save local queue.')

    def save_temp_queue(self):
        #saves current queue to a temp queue file
        self.save_queue_local(queue_filename=self.get_local_queue_file(filename='temp'))

    def load_temp_queue(self):
        #loads temp queue file into current queue, if it exists
        self.load_queue_local(queue_filename=self.get_local_queue_file(filename='temp'), play=self.player.playing)

    def create_player(self):
        self.player = Player()

    def setup_player(self):
        self.player.use_player_cache = False
        self.player.servers = []
        self.player.servers = self.load_server_presets()
        self.connection_timeout = self.config.getint("Server", "connection_timeout")
        self.connection_retries = self.config.getint("Server", "connection_retries")
        self.player.server_current = self.config.getint("Server", "current_index")
        self.player.volume = self.config.getfloat("Settings", "volume")
        self.player.mode_set(self.config.get("Settings", "play_mode"))
        self.player.set_scrobbletime(self.config.getfloat("Settings", "scrobbletime"))
        self.player.random_amount = self.config.getint("Settings", "random_size")
        self.player.queue_type = self.config.get("Queue", "queue_type")
        self.player.queue_id = self.config.get("Queue", "queue_id")
        self.player.skiponestar_set(self.config.getboolean("Settings", "skiponestar"))
        self.autoload_queue = self.config.getboolean("Queue", "autoload_queue")
        self.autoplay = self.config.getboolean("Settings", "autoplay")

    @mainthread
    def load_player(self):
        database_created, message = self.player.setup()
        self.connection_status = database_created
        self.connection_message = message
        if not database_created:
            self.open_not_connected_popup()
        else:
            self.database_created()

    def open_loading_popup(self):
        if self.loading_popup is None:
            self.loading_popup = LoadingPopup()
            self.loading_popup.open()

    def close_loading_popup(self):
        if self.loading_popup:
            self.loading_popup.dismiss()
            self.loading_popup = None

    def open_not_connected_popup(self):
        if self.not_connected_popup is None:
            self.not_connected_popup = NotConnectedPopup()
            self.not_connected_popup.open()

    def close_not_connected_popup(self):
        if self.not_connected_popup:
            self.not_connected_popup.dismiss()
            self.not_connected_popup = None

    def database_created(self):
        self.close_not_connected_popup()
        if self.autoload_queue:
            self.load_queue_local(False, background=True)
            self.player.queue_load(self.autoplay)
        else:
            self.player.database.get_ping()
            self.load_queue_local(self.autoplay)

    def build(self):
        """Called when app is initialized, kv files are not loaded, but other data is"""

        global desktop
        self.desktop = desktop
        self.wakelock = WakeLock()
        self.load_settings()
        self.load_local_cache_songs()
        self.load_local_cache_info()
        self.load_local_cache_lists()
        self.create_player()
        return Builder.load_string(KV)

    def build_config(self, config):
        """Setup config file if it is not found"""

        config.setdefaults(
            'Settings', {
                'remember_window': 1,
                'buttonsize': 100,
                'textsize': 100,
                'scrollersize': 100,
                'window_maximized': 0 if desktop else 1,
                'window_top': 50,
                'window_left': 100,
                'window_width': 800,
                'window_height': 600,
                'scrobbletime': 30,
                'wakelock': 'Background',
                'cache_location': '',
                'color_theme': '',
                'speak_screen': 0,
                'speak_setting': 0,
                'random_size': 20,
                'cache_songlists': 1,
                'volume': 1,
                'play_mode': 'in order',
                'current_screen_name': '',
                'autoplay': 0,
                'queue_max_amount': 100,
                'queue_selected_only': 1,
                'queue_mode': 'replace',
                'queue_play_immediately': 1,
                'sort_mode_song': 'name',
                'sort_mode_artist': 'name',
                'sort_mode_other': 'name',
                'sort_mode_playlist': 'original',
                'sort_reverse': 0,
                'skiponestar': 0,
            })
        config.setdefaults(
            'Queue', {
                'autoload_queue': 0,
                'queue_type': '',
                'queue_id': '',
            })
        config.setdefaults(
            'Server', {
                'current_index': 0,
                'connection_retries': 2,
                'connection_timeout': 3,
                'servers': '',
            })

    def build_settings(self, settings):
        """Kivy settings dialog panel
        settings types: title, bool, numeric, options, string, path"""

        caches = self.get_default_cache_folders()
        theme_names = []
        for theme in themes:
            theme_names.append(theme['name'])

        settingspanel = []
        settingspanel.append({
            "type": "aboutbutton",
            "title": "",
            "section": "Settings",
            "key": "buttonsize"
        })

        settingspanel.append({
            "type": "title",
            "title": "Server Settings"
        })
        settingspanel.append({
            "type": "rescandatabase",
            "section": "Settings",
            "key": "buttonsize"
        })
        settingspanel.append({
            "type": "serverpresets",
            "section": "Settings",
            "key": "buttonsize"
        })
        settingspanel.append({
            "type": "numeric",
            "title": "Connection Retries",
            "desc": "How many times to attempt to reconnect to server",
            "section": "Server",
            "key": "connection_retries"
        })
        settingspanel.append({
            "type": "numeric",
            "title": "Connection Timeout",
            "desc": "How many seconds before a connection attempt times out",
            "section": "Server",
            "key": "connection_timeout"
        })
        settingspanel.append({
            "type": "cache",
            "section": "Settings",
            "key": "buttonsize"
        })
        settingspanel.append({
            "type": "listcache",
            "section": "Settings",
            "key": "buttonsize"
        })
        settingspanel.append({
            "type": "compositeoptions",
            "title": "Cache Location",
            "desc": "Where to store locally cached songs",
            "options": caches,
            "section": "Settings",
            "key": "cache_location",
        })
        settingspanel.append({
            "type": "bool",
            "title": "Use Cache Songlists When Offline",
            "desc": "If unable to connect, use a locally stored copy of song list if available",
            "section": "Settings",
            "key": "cache_songlists"
        })

        settingspanel.append({
            "type": "title",
            "title": "Interface Settings"
        })
        settingspanel.append({
            "type": "screens",
            "section": "Settings",
            "key": "buttonsize"
        })
        settingspanel.append({
            "type": "options",
            "title": "Theme",
            "desc": "Colors of the interface",
            "options": theme_names,
            "section": "Settings",
            "key": "color_theme"
        })
        if platform == 'android':
            settingspanel.append({
                "type": "options",
                "title": "Keep Device Awake",
                "desc": "Mode to use to keep the device awake when playing music.  Defaults to 'Background' which plays with screen off.",
                "options": ['Keep Screen On', 'Background', 'None'],
                "section": "Settings",
                "key": "wakelock"
            })
        settingspanel.append({
            "type": "bool",
            "title": "Speak Screen Name",
            "desc": "When screen changed with swipe, speak the name using text to speach",
            "section": "Settings",
            "key": "speak_screen"
        })
        settingspanel.append({
            "type": "bool",
            "title": "Speak Swipe Actions",
            "desc": "When changing settings or values with swipe, speak the change using text to speach",
            "section": "Settings",
            "key": "speak_setting"
        })
        settingspanel.append({
            "type": "numeric",
            "title": "Button Scale",
            "desc": "Button Scale Percent",
            "section": "Settings",
            "key": "buttonsize"
        })

        settingspanel.append({
            "type": "title",
            "title": "Behavior Settings"
        })
        settingspanel.append({
            "type": "numeric",
            "title": "Playback Time Before Scrobble",
            "desc": "Playback time in seconds before song is registered as played with server.",
            "section": "Settings",
            "key": "scrobbletime"
        })
        settingspanel.append({
            "type": "bool",
            "title": "Skip Playing One Star Songs",
            "desc": "Do not automatically play one-star rated songs in queue, songs can still be played manually",
            "section": "Settings",
            "key": "skiponestar"
        })
        settingspanel.append({
            "type": "bool",
            "title": "Save/Load Queue Remotely",
            "desc": "Save and load the playback queue on the remote server",
            "section": "Queue",
            "key": "autoload_queue"
        })
        settingspanel.append({
            "type": "bool",
            "title": "Autoplay On Startup",
            "desc": "Start playing queue automatically when app is run",
            "section": "Settings",
            "key": "autoplay"
        })
        settingspanel.append({
            "type": "numeric",
            "title": "Random Playlist Size",
            "desc": "Number of songs to load at once when generating random playlists",
            "section": "Settings",
            "key": "random_size"
        })
        settings.add_json_panel('Snu Music Player Settings', self.config, data=json.dumps(settingspanel))

    def rescan_database(self, full=None):
        result = self.player.rescan_database(full)
        if self.database_rescan_tracker is None:
            self.database_rescan_tracker = Clock.schedule_interval(self.rescan_database_update, 1)
            self.database_rescan_tracker_fails = 0

    def rescan_database_update_stop(self):
        if self.database_rescan_tracker:
            self.database_rescan_tracker.cancel()
            self.database_rescan_tracker = None

    def rescan_database_update(self, *_):
        status = self.player.rescan_database_status()
        if status is None:
            if self.database_rescan_tracker_fails >= 10:
                self.rescan_database_update_stop()
            self.database_rescan_tracker_fails += 1
            self.database_rescan_status = "Unable To Connect"
        else:
            self.database_rescan_tracker_fails = 0
            scanning = status['scanning']
            if scanning:
                self.database_rescan_status = "Scanning: "+str(status['count'])+" Files"
            else:
                self.database_rescan_status = str(status['count'])+" Files Scanned"
                self.rescan_database_update_stop()

    def on_start(self):
        """Called when the app is started, after kv files are loaded"""

        if platform == 'android':
            self.start_bluetooth_button()
        EventLoop.window.bind(on_keyboard=self.hook_keyboard)
        self.set_window_size()
        self.screen_manager = self.root.ids.screenManager
        self.start_keyboard_navigation()
        self.setup_player()
        self.load_player()
        self.load_screen_presets()
        self.generate_screens()
        about_file = open(resource_find('about.txt'), 'r')
        self.about_text = about_file.read()
        about_file.close()
        Window.softinput_mode = 'below_target'
        Clock.schedule_once(self.load_current_theme, 1)

    def load_current_theme(self, *_):
        theme_index = self.find_theme_index(self.color_theme)
        self.load_theme(themes[theme_index])

    def on_pause(self):
        """Called when the app is suspended or paused, need to make sure things are saved because it might not come back"""

        self.save_settings()
        self.config.write()
        if self.player:
            self.player.close()
        self.wakelock.release()
        return True

    def on_resume(self):
        if self.player:
            self.player.setup()
            if self.player.playing:
                self.wakelock.request()

    def on_stop(self):
        """Called when the app is about to be ended"""
        self.wakelock.release()
        try:
            self.player.database.cancel_load = True
        except:
            pass
        self.cancel_threads = True
        self.save_settings()
        self.config.write()
        if self.session:
            self.session.release()
        if self.player:
            self.player.close(service=True)

    def open_server_settings(self):
        from settings import ServerSettingsPopup
        self.close_server_settings()
        self.server_settings_popup = ServerSettingsPopup(player=self.player)
        self.server_settings_popup.open()

    def close_server_settings(self):
        if self.server_settings_popup:
            self.server_settings_popup.clear_server_list()
            self.server_settings_popup.dismiss()

    def open_screen_settings(self):
        from settings import ScreenSettingsPopup
        self.dismiss_popup()
        self.popup = ScreenSettingsPopup()
        self.popup.open()

    def get_crashlog_file(self):
        """Returns the crashlog file path and name"""

        savefolder_loc = os.path.split(self.get_application_config())[0]
        crashlog = os.path.join(savefolder_loc, 'crashlog.txt')
        return crashlog


if __name__ == '__main__':
    try:
        ResoundingDatastream().run()
    except Exception as e:
        try:
            ResoundingDatastream().save_crashlog()
        except:
            pass
        os._exit(-1)
