from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.uix.modalview import ModalView
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import mainthread
from kivy.properties import *
from snu.button import WideButton, NormalButton, NormalDropDown, MenuButton, NormalMenuStarter
from widgets import *
from playlists import WidgetBrowseDatabase, WidgetListBrowseQueue

widget_types = ['WidgetSongArt', 'WidgetSongInfo', 'WidgetSongTime', 'WidgetSongInfoNext',
                'WidgetSongControls', 'WidgetSongPosition', 'WidgetSongControlsFull', 'WidgetPlayerVolume', 'WidgetPlayerMode', 'WidgetPlayerModeToggle',
                'WidgetSongRating', 'WidgetSongRatingSafe', 'WidgetSongFavorite', 'WidgetSongFavoriteSafe', 'WidgetSongRatingFavorite', 'WidgetSongRatingFavoriteSafe', 'WidgetAddToPlaylist',
                'WidgetBrowseDatabase', 'WidgetListBrowseQueue', 'WidgetQueuePresets', 'WidgetQueuePlaylist', 'WidgetPlaylistUndo', 'WidgetPlaylistLoads', 'WidgetPlaylistLoadsRandom', 'WidgetQueueSimilar',
                'WidgetEmpty', 'WidgetNoScreen', 'WidgetLog']
swipe_modes = ['none', 'song', 'volume', 'favorite', 'mode', 'skip', 'queue shuffle', 'queue random', 'queue genre', 'queue artist', 'queue album', 'queue same']

from kivy.lang.builder import Builder
Builder.load_string("""
<AddWidgetDropDown>:
    auto_width: False
    size_hint_x: 1
    NormalLabel:
        text: "Song Info"
    MenuButton:
        text: "Song Art"
        on_release: root.owner.add_new_widget("WidgetSongArt")
    MenuButton:
        text: "Title, Artist, Album"
        on_release: root.owner.add_new_widget("WidgetSongInfo")
    MenuButton:
        text: "Time And Duration"
        on_release: root.owner.add_new_widget("WidgetSongTime")
    MenuButton:
        text: "Next Song Title, Artist"
        on_release: root.owner.add_new_widget("WidgetSongInfoNext")

    NormalLabel:
        text: "Player Controls"
    MenuButton:
        text: "Playback Controls"
        on_release: root.owner.add_new_widget("WidgetSongControls")
    MenuButton:
        text: "Position Seeker"
        on_release: root.owner.add_new_widget("WidgetSongPosition")
    MenuButton:
        text: "Playback Controls And Position"
        on_release: root.owner.add_new_widget("WidgetSongControlsFull")
    MenuButton:
        text: "Player Volume Control"
        on_release: root.owner.add_new_widget("WidgetPlayerVolume")
    MenuButton:
        text: "Playback Shuffle/Repeat Control"
        on_release: root.owner.add_new_widget("WidgetPlayerMode")
    MenuButton:
        text: "Playback Shuffle/Repeat Toggle"
        on_release: root.owner.add_new_widget("WidgetPlayerModeToggle")

    NormalLabel:
        text: "Song Modifications"
    MenuButton:
        text: "Song Rating Setting"
        on_release: root.owner.add_new_widget("WidgetSongRating")
    MenuButton:
        text: "Touch-Safe Song Rating Setting"
        on_release: root.owner.add_new_widget("WidgetSongRatingSafe")
    MenuButton:
        text: "Song Favorite Setting"
        on_release: root.owner.add_new_widget("WidgetSongFavorite")
    MenuButton:
        text: "Touch-Safe Song Favorite Setting"
        on_release: root.owner.add_new_widget("WidgetSongFavoriteSafe")
    MenuButton:
        text: "Song Rating And Favorite"
        on_release: root.owner.add_new_widget("WidgetSongRatingFavorite")
    MenuButton:
        text: "Touch-Safe Rating And Favorite"
        on_release: root.owner.add_new_widget("WidgetSongRatingFavoriteSafe")
    MenuButton:
        text: "Add Current Song To Playlist"
        on_release: root.owner.add_new_widget("WidgetAddToPlaylist")

    NormalLabel:
        text: "Queue And Database"
    MenuButton:
        text: "Database Browser"
        on_release: root.owner.add_new_widget("WidgetBrowseDatabase")
    MenuButton:
        text: "Current Queue Browser"
        on_release: root.owner.add_new_widget("WidgetListBrowseQueue")
    MenuButton:
        text: "Quick Queue Presets Menu"
        on_release: root.owner.add_new_widget("WidgetQueuePresets")
    MenuButton:
        text: "Queue Playlist Menu"
        on_release: root.owner.add_new_widget("WidgetQueuePlaylist")
    MenuButton:
        text: "Queue Playing Genre/Artist/Album"
        on_release: root.owner.add_new_widget("WidgetPlaylistLoads")
    MenuButton:
        text: "Queue Random Songs/Genre/Artist/Album"
        on_release: root.owner.add_new_widget("WidgetPlaylistLoadsRandom")
    MenuButton:
        text: "Queue Similar To Last Queue"
        on_release: root.owner.add_new_widget("WidgetQueueSimilar")
    MenuButton:
        text: "Undo Queue Changes"
        on_release: root.owner.add_new_widget("WidgetPlaylistUndo")

    NormalLabel:
        text: "Other"
    MenuButton:
        text: "Empty Space"
        on_release: root.owner.add_new_widget("WidgetEmpty")
    MenuButton:
        text: "App Message Log"
        on_release: root.owner.add_new_widget("WidgetLog")


<SwipeModeDropDown>:
    auto_width: False
    size_hint_x: 1
    MenuButton:
        text: "Default"
        on_release: root.owner.selected_swipe_mode('default')
    MenuButton:
        text: "None"
        on_release: root.owner.selected_swipe_mode('none')
    MenuButton:
        text: "Song Change"
        on_release: root.owner.selected_swipe_mode('song')
    #MenuButton:
    #    text: "Rating Change"
    #    on_release: root.owner.selected_swipe_mode('rating')
    MenuButton:
        text: "Volume Change"
        on_release: root.owner.selected_swipe_mode('volume')
    MenuButton:
        text: "Set/Remove Favorite"
        on_release: root.owner.selected_swipe_mode('favorite')
    MenuButton:
        text: "Playback Mode Change"
        on_release: root.owner.selected_swipe_mode('mode')
    MenuButton:
        text: "Skip Song Position"
        on_release: root.owner.selected_swipe_mode('skip')
    MenuButton:
        text: "Shuffle Queue"
        on_release: root.owner.selected_swipe_mode('queue shuffle')
    MenuButton:
        text: "Queue Up Random Songs"
        on_release: root.owner.selected_swipe_mode('queue random')
    MenuButton:
        text: "Queue Up Random Genre"
        on_release: root.owner.selected_swipe_mode('queue genre')
    MenuButton:
        text: "Queue Up Random Artist"
        on_release: root.owner.selected_swipe_mode('queue artist')
    MenuButton:
        text: "Queue Up Random Album"
        on_release: root.owner.selected_swipe_mode('queue album')
    MenuButton:
        text: "Queue Up Simlar To Last"
        on_release: root.owner.selected_swipe_mode('queue same')

<SwitchLayout>:
    widget_left: left_holder
    widget_right: right_holder
    BoxLayout:
        orientation: 'vertical'
        id: left_holder
    BoxLayout:
        orientation: 'vertical'
        id: right_holder
""")


class AddWidgetDropDown(NormalDropDown):
    owner = ObjectProperty()


class SwipeModeDropDown(NormalDropDown):
    owner = ObjectProperty()


class SwitchLayout(BoxLayout):
    blocked = BooleanProperty(False)
    widgets = ListProperty()
    widget_left = ObjectProperty()
    widget_right = ObjectProperty()
    is_wide = None

    def on_size(self, *_):
        last_wide = self.is_wide
        self.is_wide = self.width >= self.height
        if self.is_wide != last_wide:
            self.update_widgets()

    def add_layout_widget(self, widget):
        widget.blocked = self.blocked
        self.widgets.append(widget)
        #self.update_widgets()

    def update_widgets(self):
        if not self.widgets:
            return
        self.widget_left.clear_widgets()
        self.widget_right.clear_widgets()
        single_row = False

        #check if any widget has a size_hint_y that sets its height over 75% of the total
        size_hint_total = 0
        for widget in self.widgets:
            size_hint_total += widget.size_hint_y
        size_hint_average = size_hint_total / len(self.widgets)
        for widget in self.widgets:
            adjusted_size = widget.size_hint_y / size_hint_total
            if adjusted_size > 0.75:
                single_row = True
        if len(self.widgets) <= 1:
            single_row = True

        #layout widgets
        if not self.is_wide or single_row:
            self.widget_right.size_hint_x = 0.001
            for widget in self.widgets:
                self.widget_left.add_widget(widget)
        else:
            self.widget_right.size_hint_x = 1
            size_hint_so_far = 0
            size_hint_halfway = size_hint_total / 2
            for widget in self.widgets:
                if size_hint_so_far >= size_hint_halfway:
                    self.widget_right.add_widget(widget)
                else:
                    self.widget_left.add_widget(widget)
                size_hint_so_far += widget.size_hint_y


class ScreenBase(Screen):
    noscreen = BooleanProperty(False)
    blocked = BooleanProperty(False)
    screen_manager = ObjectProperty()
    player = ObjectProperty()
    widget_presets = ListProperty()  #List of dictionaries with the keys: name, swipe_mode, size_hint_y
    generated_widgets = ListProperty()
    selected_widget = ObjectProperty(allownone=True)
    selected_widget_swipe_mode = StringProperty('default')
    swipe_mode_menu = ObjectProperty(allownone=True)
    add_new_widget_menu = ObjectProperty(allownone=True)

    def on_enter(self, *_):
        if not self.blocked:
            for widget in self.generated_widgets:
                widget.reload()

    def selected_set_size_hint(self, size_hint_y):
        if not self.selected_widget:
            return
        self.selected_widget.size_hint_y = size_hint_y
        self.widget_presets[self.selected_widget.index]['size_hint_y'] = size_hint_y

    @mainthread
    def selected_move_up(self):
        index = self.selected_widget.index
        new_index = index-1
        if new_index < 0:
            new_index = len(self.widget_presets) - 1
        self.widget_presets.insert(new_index, self.widget_presets.pop(index))
        self.generate_widgets()
        self.select(self.generated_widgets[new_index])

    @mainthread
    def selected_move_down(self):
        index = self.selected_widget.index
        new_index = index+1
        if new_index > len(self.widget_presets) - 1:
            new_index = 0
        self.widget_presets.insert(new_index, self.widget_presets.pop(index))
        self.generate_widgets()
        self.select(self.generated_widgets[new_index])

    @mainthread
    def selected_remove(self):
        self.widget_presets.pop(self.selected_widget.index)
        self.generate_widgets()

    def add_new_widget_menu_open(self, button):
        self.add_new_widget_menu_close()
        self.add_new_widget_menu = AddWidgetDropDown(owner=self)
        self.add_new_widget_menu.open(button)

    def add_new_widget_menu_close(self):
        if self.add_new_widget_menu:
            self.add_new_widget_menu.dismiss()
            self.add_new_widget_menu = None

    @mainthread
    def add_new_widget(self, widget_type):
        self.add_new_widget_menu_close()
        widget_preset = {'name': widget_type, 'swipe_mode': '', 'size_hint_y': 1}
        if self.selected_widget:
            new_index = self.selected_widget.index + 1
            self.widget_presets.insert(new_index, widget_preset)
        else:
            new_index = len(self.widget_presets)
            self.widget_presets.append(widget_preset)
        self.generate_widgets()
        self.select(self.generated_widgets[new_index])

    def swipe_mode_menu_open(self, button):
        self.swipe_mode_menu_close()
        self.swipe_mode_menu = SwipeModeDropDown(owner=self)
        self.swipe_mode_menu.open(button)

    def swipe_mode_menu_close(self):
        if self.swipe_mode_menu:
            self.swipe_mode_menu.dismiss()
            self.swipe_mode_menu = None

    def selected_swipe_mode(self, swipe_mode):
        self.swipe_mode_menu_close()
        if not self.selected_widget:
            return
        self.selected_widget.swipe_mode = swipe_mode
        self.selected_widget_swipe_mode = swipe_mode
        if swipe_mode == 'default':
            self.widget_presets[self.selected_widget.index]['swipe_mode'] = ''
        else:
            self.widget_presets[self.selected_widget.index]['swipe_mode'] = swipe_mode

    def select(self, selected_widget):
        if not self.blocked:
            return
        self.selected_widget = None
        for widget in self.generated_widgets:
            if widget == selected_widget:
                self.selected_widget = selected_widget
                widget.selected = True
                self.selected_widget_swipe_mode = selected_widget.swipe_mode
            else:
                widget.selected = False

    def generate_preset(self):
        widgets = []
        for widget in self.widget_presets:
            swipe_mode = widget['swipe_mode']
            if swipe_mode not in swipe_modes:
                swipe_mode = ''
            size_hint_y = widget['size_hint_y']
            if size_hint_y == 1:
                size_hint_y = ''
            else:
                size_hint_y = str(size_hint_y)
            string = ":".join([widget['name'], swipe_mode, size_hint_y])
            widgets.append(string)
        widgets_string = "|".join(widgets)
        return widgets_string

    def parse_preset(self, preset_string):
        widget_presets = []
        if not preset_string:
            return []
        try:
            preset = preset_string.split('|')
        except:
            return []
        for widget_text in preset:
            widget = {}
            widget_data = widget_text.split(":")
            if not widget_data:
                continue
            name = widget_data[0]
            if name not in widget_types:
                continue
            widget['name'] = name
            try:
                swipe_mode = widget_data[1]
                if swipe_mode in swipe_modes:
                    widget['swipe_mode'] = swipe_mode
                else:
                    widget['swipe_mode'] = 'default'
            except:
                widget['swipe_mode'] = 'default'
            try:
                size_hint_y = widget_data[2]
                size_hint_y = float(size_hint_y)
            except:
                size_hint_y = 1
            widget['size_hint_y'] = size_hint_y
            widget_presets.append(widget)
        return widget_presets

    def load_preset(self, preset_string):
        preset_data = self.parse_preset(preset_string)
        self.widget_presets = preset_data

    def generate_widgets(self):
        def setup_widget(w, i=0):
            w.blocked = self.blocked
            w.screen_manager = self.screen_manager
            w.screen = self
            w.player = self.player
            w.index = i
            return w

        self.clear_widgets()
        self.generated_widgets = []
        self.selected_widget = None
        self.selected_widget_swipe_mode = 'default'
        layout = SwitchLayout(blocked=self.blocked)
        if self.noscreen:
            widget = setup_widget(WidgetNoScreenSelected())
            layout.add_layout_widget(widget)
        else:
            if not self.widget_presets:
                if not self.blocked:
                    widget = setup_widget(WidgetNoScreen())
                    layout.add_layout_widget(widget)
                else:
                    widget = WidgetNoScreenInfo()
                    layout.add_layout_widget(widget)
            else:
                for index, preset in enumerate(self.widget_presets):
                    widget = eval(preset['name']+'()')
                    widget = setup_widget(widget, index)
                    widget.size_hint_y = preset['size_hint_y']
                    swipe_mode = preset['swipe_mode']
                    if swipe_mode in swipe_modes:
                        widget.swipe_mode = swipe_mode
                    layout.add_layout_widget(widget)
                    self.generated_widgets.append(widget)
        self.add_widget(layout)


class ScreenManagerBase(ScreenManager):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.transition = SlideTransition(duration=0)

    def go_first(self):
        first_screen = self.screens[0].name
        if first_screen != self.current:
            self.transition = SlideTransition(direction='up')
            self.current = first_screen
        return self.current

    def go_next(self):
        next_screen = self.next()
        if next_screen != self.current:
            self.transition = SlideTransition(direction='down')
            self.current = next_screen
        return self.current

    def go_previous(self):
        prev_screen = self.previous()
        if prev_screen != self.current:
            self.transition = SlideTransition(direction='up')
            self.current = prev_screen
        return self.current
