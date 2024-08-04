from snu.settings import *
from snu.label import ShortLabel
from screens import ScreenBase
from player import Player
from snu.button import *
from kivy.uix.modalview import ModalView
from kivy.properties import *
from kivy.lang.builder import Builder
from databases.subsonic import ServerSettings
from widgets import AnimatedModalView

screen_presets = {
    "Main Screen": ["main screen", "WidgetSongInfo::|WidgetSongTime::0.5|WidgetSongControls::|WidgetSongPosition::0.5|WidgetSongInfoNext::0.5|WidgetSongRatingFavorite::0.5|WidgetPlayerMode::"],
    "Main Screen Simple": ["main simple", "WidgetSongArt::2.0|WidgetSongInfo::|WidgetSongTime::0.5|WidgetSongControlsFull::0.5|WidgetSongInfoNext::0.5|WidgetSongRatingFavorite::0.5"],
    "Main Screen Extra": ["main extra", "WidgetSongInfo::|WidgetSongTime::0.5|WidgetSongControls::|WidgetSongPosition::0.5|WidgetSongInfoNext::0.5|WidgetSongRatingFavorite::0.5|WidgetAddToPlaylist::0.5|WidgetPlayerMode::|WidgetListBrowseQueue::0.5|WidgetBrowseDatabase::0.5"],
    "Queue Browser": ["queue screen", "WidgetListBrowseQueue::3.0|WidgetSongControls::0.5"],
    "Queue Browser Extra": ["queue extra", "WidgetListBrowseQueue::4.0|WidgetSongControlsFull::0.5|WidgetPlaylistLoads::|WidgetPlaylistLoadsRandom::|WidgetQueueSimilar::0.5"],
    "Database": ["database", "WidgetBrowseDatabase:::"],
    "Queue Options": ["queue options", "WidgetListBrowseQueue::0.5|WidgetQueueSimilar::0.5|WidgetPlaylistRandom::0.5|WidgetPlaylistLoads::|WidgetPlaylistLoadsRandom::|WidgetQueuePresets::0.5|WidgetQueuePlaylist::0.5"]}

Builder.load_string("""
<ScreenSettingsPopup>:
    screen_preview: screenPreview
    background: 'data/buttonflat.png'
    background_color: app.theme.background
    BoxLayout:
        orientation: 'vertical'
        Header:
            HeaderLabel:
                text: "Screens"
            NormalButton:
                text: 'Save'
                on_release: root.save_presets()
            NormalButton:
                text: 'Cancel'
                warn: True
                on_release: root.dismiss()
        GridLayout:
            canvas.before:
                Color:
                    rgb: app.theme.button_down[:3]
                Rectangle:
                    size: self.size
                    pos: self.pos
            cols: 2
            GridLayout:
                size_hint_x: 0.5
                cols: 1
                NormalLabel:
                    text: "Screens:"
                NormalRecycleView:
                    viewclass: 'ScreenPresetButton'
                    data: root.screen_presets
                    RecycleBoxLayout:
                        default_size_hint: 1, None
                        default_size: None, app.button_scale
                        orientation: 'vertical'
                        size_hint_y: None
                        height: self.minimum_height
                WideButton:
                    text: 'New Screen'
                    on_release: root.new_screen()
                WideMenuStarter:
                    text: 'Add Screen'
                    on_release: root.open_add_screen_menu(self)
            BoxLayout:
                orientation: 'vertical'
                Holder:
                    NormalInput:
                        text: root.current_screen
                        multiline: False
                        on_focus: root.set_screen_name(self.focus, self.text)
                    NormalButton:
                        text: "X"
                        disabled: not root.current_screen
                        on_release: root.delete_screen()
                        warn: True
                        width: app.button_scale
                BoxLayout:
                    canvas.before:
                        Color:
                            rgb: app.theme.main_background
                        BorderImage:
                            display_border: [app.display_border, app.display_border, app.display_border, app.display_border]
                            size: self.width, self.height
                            pos: self.pos
                            source: 'data/buttonflat.png'
                    size_hint_y: None
                    height: self.width * ((root.height - app.button_scale*2) / root.width)
                    ScreenBase:
                        blocked: True
                        id: screenPreview
                        screen_manager: root
                GridLayout:
                    cols: 1
                    WideMenuStarter:
                        disabled: not root.screen_preview.selected_widget
                        size_hint: 1, 1
                        text: 'Swipe Mode: '+root.screen_preview.selected_widget_swipe_mode
                        on_release: root.screen_preview.swipe_mode_menu_open(self)
                    BoxLayout:
                        disabled: not root.screen_preview.selected_widget
                        padding: self.height / 16
                        ShortLabel:
                            size_hint_y: 1
                            text: 'Scale: ' + str(round(float(scaleSlider.value), 1))
                        SliderThemed:
                            id: scaleSlider
                            value_track_color: app.theme.button_down
                            min: 0.5
                            max: 7
                            step: 0.1
                            value: root.screen_preview.selected_widget.size_hint_y if root.screen_preview.selected_widget else 1
                            on_value: root.screen_preview.selected_set_size_hint(self.value)
                    BoxLayout:
                        disabled: not root.screen_preview.selected_widget
                        WideButton:
                            size_hint_y: 1
                            text: 'Move Up'
                            on_release: root.screen_preview.selected_move_up()
                        WideButton:
                            size_hint_y: 1
                            text: 'Move Down'
                            on_release: root.screen_preview.selected_move_down()
                    WideButton:
                        disabled: not root.screen_preview.selected_widget
                        size_hint: 1, 1
                        text: 'Remove Widget'
                        warn: True
                        on_release: root.screen_preview.selected_remove()
                    WideMenuStarter:
                        disabled: not root.current_screen
                        size_hint: 1, 1
                        text: 'Add New Widget...'
                        on_release: root.screen_preview.add_new_widget_menu_open(self)

<AddScreenDropDown>:
    auto_width: False
    size_hint_x: 1

<ScreenPresetButton>:
    on_release: self.owner.select_screen(self.text)

<ServerSettingsPopup>:
    background: 'data/buttonflat.png'
    background_color: app.theme.background
    BoxLayout:
        orientation: 'vertical'
        Header:
            HeaderLabel:
                text: "Servers"
            NormalButton:
                text: 'Close'
                on_release: root.dismiss()
        WideButton:
            text: "Add New Preset"
            on_release: root.add()
        Scroller:
            GridLayout:
                padding: app.button_scale / 4
                spacing: app.button_scale / 4
                id: presetArea
                size_hint_y: None
                height: self.minimum_height
                cols: 1 if root.height > root.width else 2

<SettingsCache>:
    label_size_hint_x: 0.5
    title: 'Local File Cache'
    desc: app.cache_info
    WideButton:
        text: "Clean"
        size: root.size
        font_size: '15sp'
        on_release: app.clean_cache()
    WideButton:
        text: "Clear All"
        size: root.size
        font_size: '15sp'
        on_release: app.clean_cache(total=True)

<SettingsListCache>:
    label_size_hint_x: 0.5
    title: 'Local Songlist Cache'
    desc: app.cache_info
    WideButton:
        text: "Clear All"
        size: root.size
        font_size: '15sp'
        on_release: app.clean_cache_lists()

<SettingsRescan>:
    label_size_hint_x: 0.5
    title: 'Database Rescan'
    desc: app.database_rescan_status
    WideButton:
        text: "Quick"
        size: root.size
        font_size: '15sp'
        on_release: app.rescan_database()
    WideButton:
        text: "Full"
        size: root.size
        font_size: '15sp'
        on_release: app.rescan_database(full=True)

<SettingsServerPresets>:
    label_size_hint_x: 0
    title: ''
    desc: ''
    WideButton:
        text: "Set Up Server Connections"
        size: root.size
        font_size: '15sp'
        on_release: app.open_server_settings()

<SettingsCompositeOptions>:
    label_size_hint_x: 0.5
    Label:
        text: root.text or ''
        pos: root.pos
        font_size: '15sp'
        color: app.theme.text

<SettingsScreens>:
    label_size_hint_x: 0
    title: ''
    desc: ''
    WideButton:
        text: "Set Up Screens"
        size: root.size
        font_size: '15sp'
        on_release: app.open_screen_settings()
""")


class SettingsCompositeOptionsButton(WideToggle):
    data = ObjectProperty(allownone=True)


class SettingsCompositeOptions(SettingItem, Navigation):
    """Modified version of SettingOption to allow displaying element 1 of options list while setting element 0"""
    text = StringProperty()
    options = ListProperty([])
    popup = ObjectProperty(None, allownone=True)

    def on_navigation_activate(self):
        self._create_popup(self)

    def on_value(self, instance, value):
        super().on_value(instance, value)
        for item in self.options:
            if item[0] == self.value:
                self.text = item[1]

    def on_panel(self, instance, value):
        if value is None:
            return
        self.fbind('on_release', self._create_popup)

    def _dismiss(self, *_):
        app = App.get_running_app()
        if app.popup:
            app.popup.dismiss()

    def _set_option(self, instance):
        self.value = instance.data[0]
        self.text = instance.text
        self._dismiss()

    def _create_popup(self, instance):
        app = App.get_running_app()
        if app.popup:
            app.popup.dismiss()
        content = BoxLayout(orientation='vertical')
        scroller = Scroller()
        content.add_widget(scroller)
        options_holder = BoxLayout(orientation='vertical', size_hint_y=None, height=len(self.options) * app.button_scale)
        for option in self.options:
            button = SettingsCompositeOptionsButton(text=option[1], data=option)
            if self.value == option:
                button.state = 'down'
            options_holder.add_widget(button)
            button.bind(on_release=self._set_option)
        scroller.add_widget(options_holder)
        cancel_button = WideButton(text='Cancel')
        cancel_button.bind(on_release=self._dismiss)
        content.add_widget(cancel_button)
        max_height = app.root.height - (app.button_scale * 3)
        height = min((len(self.options) + 3) * app.button_scale, max_height)
        app.popup = NormalPopup(title=self.title, content=content, size_hint=(None, None), size=(app.popup_x, height))
        app.popup.open()


class ScreenSettingsPopup(AnimatedModalView):
    screen_presets = ListProperty()
    current_screen = StringProperty()
    screen_presets_edited = DictProperty()
    add_screen_menu = ObjectProperty(allownone=True)
    screen_preview = ObjectProperty()

    def refine_name(self, name):
        while name in self.screen_presets_edited.keys():
            name = name + '.1'
        return name

    def new_screen(self, name='', preset=None):
        if not name:
            name = 'screen'
        name = self.refine_name(name)
        preset_data = ''
        if preset is not None:
            preset_data = preset
        self.screen_presets_edited[name] = preset_data
        self.set_screen_names()
        self.select_screen(name)

    def set_screen_name(self, focus, name):
        if focus:
            return
        name = name.lower().strip()
        name = self.refine_name(name)
        self.screen_presets_edited[name] = self.screen_presets_edited.pop(self.current_screen)
        self.current_screen = name
        self.set_screen_names()

    def on_open(self, *_):
        self.setup()
        self.select_screen()

    def setup(self):
        app = App.get_running_app()
        self.screen_presets_edited = app.screen_presets.copy()
        self.screen_preview.player = Player()
        self.screen_preview.player.set_preview_info()
        self.set_screen_names()

    def set_screen_names(self):
        self.screen_presets = []
        screen_names = sorted(self.screen_presets_edited.keys())
        for name in screen_names:
            self.screen_presets.append({'text': name, 'owner': self})

    def save_current_screen(self):
        if self.current_screen:
            screen_preset = self.screen_preview.generate_preset()
            self.screen_presets_edited[self.current_screen] = screen_preset

    def select_screen(self, screen=None):
        self.save_current_screen()
        if screen is None or not screen:
            self.current_screen = ''
            self.screen_preview.noscreen = True
        else:
            self.current_screen = screen
            screen_preset = self.screen_presets_edited[screen]
            self.screen_preview.noscreen = False
            self.screen_preview.load_preset(screen_preset)
        self.screen_preview.generate_widgets()

    def delete_screen(self):
        if self.current_screen in self.screen_presets_edited.keys():
            del self.screen_presets_edited[self.current_screen]
            self.current_screen = ''
            self.set_screen_names()
            self.select_screen()

    def on_dismiss(self):
        pass

    def open_add_screen_menu(self, widget):
        self.add_screen_menu = AddScreenDropDown(owner=self)

        for preset_name in screen_presets.keys():
            preset_data = screen_presets[preset_name]
            button = AddScreenMenuButton(text=preset_name, preset_data=preset_data, owner=self, menu=self.add_screen_menu)
            self.add_screen_menu.add_widget(button)

        self.add_screen_menu.open(widget)

    def save_presets(self):
        app = App.get_running_app()
        self.save_current_screen()
        app.screen_presets = self.screen_presets_edited
        app.generate_screens()
        self.dismiss()


class AddScreenDropDown(NormalDropDown):
    owner = ObjectProperty()


class ScreenPresetButton(NormalButton):
    owner = ObjectProperty()


class AddScreenMenuButton(MenuButton):
    preset_data = ListProperty()
    owner = ObjectProperty()
    menu = ObjectProperty()

    def on_release(self, *_):
        self.owner.new_screen(name=self.preset_data[0], preset=self.preset_data[1])
        self.menu.dismiss()


class ServerSettingsPopup(AnimatedModalView):
    player = ObjectProperty()

    def connect(self, index):
        app = App.get_running_app()
        self.save_all()
        self.player.server_current = index
        self.player.setup_database()
        self.dismiss()
        app.close_settings()
        app.load_player()

    def save_all(self):
        preset_area = self.ids['presetArea']
        for server_widget in preset_area.children:
            server_settings = server_widget.save_settings()
            self.player.servers[server_widget.index] = server_settings

    def delete(self, index):
        self.player.servers.pop(index)
        if self.player.server_current >= index:
            self.player.server_current -= 1
        self.reload_server_list()

    def add(self):
        self.player.servers.insert(0, ServerSettings())
        self.player.server_current += 1
        self.reload_server_list()

    def on_open(self, *_):
        self.reload_server_list()

    def clear_server_list(self):
        preset_area = self.ids['presetArea']
        preset_area.clear_widgets()

    def reload_server_list(self):
        from databases.serversettingswidget import ServerSettingsWidget
        preset_area = self.ids['presetArea']
        preset_area.clear_widgets()
        for index, server in enumerate(self.player.servers):
            server_widget = ServerSettingsWidget()
            server_widget.load_settings(server)
            server_widget.index = index
            server_widget.owner = self
            preset_area.add_widget(server_widget)

    def on_dismiss(self):
        self.save_all()
        self.clear_server_list()


class SettingsCache(SettingItem):
    pass


class SettingsRescan(SettingItem):
    pass


class SettingsServerPresets(SettingItem):
    pass


class SettingsScreens(SettingItem):
    pass


class SettingsListCache(SettingItem):
    pass


class MusicPlayerSettings(AppSettings):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_type("compositeoptions", SettingsCompositeOptions)
        self.register_type("rescandatabase", SettingsRescan)
        self.register_type("serverpresets", SettingsServerPresets)
        self.register_type('screens', SettingsScreens)
        self.register_type('cache', SettingsCache)
        self.register_type('listcache', SettingsListCache)
