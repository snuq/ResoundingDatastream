from io import BytesIO

from kivy.clock import mainthread, Clock
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.slider import Slider
from kivy.uix.modalview import ModalView
from kivy.animation import Animation
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.core.image import Image as CoreImage
from kivy.properties import *
from kivy.uix.behaviors import ButtonBehavior
from snu.label import TickerLabel, NormalLabel, ShortLabel
from snu.button import WideButton, WideToggle, NormalDropDown, MenuButton, WideMenuStarter
from snu.smoothsetting import SmoothSetting
from basicscroller import ScrollBarY

from kivy.lang.builder import Builder
Builder.load_string("""
<-SliderThemed>:
    scale_factor: min(self.height, self.width/3)
    padding: self.scale_factor * 0.5
    background_width: self.scale_factor / 8
    line_color: app.theme.button_down
    cursor_color: app.theme.button_up
    cursor_image: 'data/movecircle.png'
    cursor_size: self.scale_factor * 0.825, self.scale_factor * 0.825
    value_track: True
    value_track_color: app.theme.selected
    value_track_width: max(1, self.scale_factor / 4)
    canvas:
        Color:
            rgba: root.value_track_color[:3]+([0.25] if root.cached else [0])
        Line:
            width: self.value_track_width
            points: self.x+self.padding, self.center_y, self.x+self.width-self.padding, self.center_y
        Color:
            rgb: root.line_color
        BorderImage:
            border: self.border_horizontal if self.orientation == 'horizontal' else self.border_vertical
            pos: (self.x + self.padding, self.center_y - self.background_width / 2) if self.orientation == 'horizontal' else (self.center_x - self.background_width / 2, self.y + self.padding)
            size: (self.width - self.padding * 2, self.background_width) if self.orientation == 'horizontal' else (self.background_width, self.height - self.padding * 2)
            source: (self.background_disabled_horizontal if self.orientation == 'horizontal' else self.background_disabled_vertical) if self.disabled else (self.background_horizontal if self.orientation == 'horizontal' else self.background_vertical)
        Color:
            rgba: root.value_track_color if self.value_track and self.orientation == 'horizontal' else [1, 1, 1, 0]
        Line:
            width: self.value_track_width
            points: self.x + self.padding, self.center_y, self.value_pos[0], self.center_y
        Color:
            rgba: root.value_track_color if self.value_track and self.orientation == 'vertical' else [1, 1, 1, 0]
        Line:
            width: self.value_track_width
            points: self.center_x, self.y + self.padding, self.center_x, self.value_pos[1]
        Color:
            rgb: 1, 1, 1
    Image:
        color: root.cursor_color if not root.cached else root.value_track_color[:3]
        pos: (root.value_pos[0] - root.cursor_width / 2, root.center_y - root.cursor_height / 2) if root.orientation == 'horizontal' else (root.center_x - root.cursor_width / 2, root.value_pos[1] - root.cursor_height / 2)
        size: root.cursor_size
        source: root.cursor_disabled_image if root.disabled else root.cursor_image
        fit_mode: "fill"

<-CustomScrollbar>:
    rounding: 7
    _handle_y_pos: self.x, self.y + self.height * self.vbar[0]
    _handle_y_size: self.width, self.height * self.vbar[1]
    canvas:
        Color:
            rgba: app.theme.slider_background
        RoundedRectangle:
            radius: [self.rounding]
            size: self.size
            pos: self.pos
        Color:
            rgba: self._bar_color if (self.viewport_size[1] > self.scroller_size[1]) else [0, 0, 0, 0]
        RoundedRectangle:
            radius: [self.rounding]
            pos: root._handle_y_pos or (0, 0)
            size: root._handle_y_size or (0, 0)
        Color:
            rgba: app.theme.selected[:3]+[0.5 if root.show_selected_point else 0]
        Rectangle:
            pos: self.x, self.y + (self.height * (1 - self.selected_point)) - ((app.button_scale / 8) * (1 - self.selected_point))
            size: self.width, app.button_scale / 8
        Color:
            rgba: 0, 0, 0, .1
        Line:
            width: 2
            rounded_rectangle: (self.x, self.y, self.width, self.height, self.rounding)
    size_hint_x: None
    bar_width: app.button_scale
    orientation: 'vertical'
    bar_color: app.theme.scroller_selected
    bar_inactive_color: app.theme.scroller
    size_hint: None, 1
    hidden: self.viewport_size[1] <= self.scroller_size[1]
    opacity: 0 if self.hidden else 1
    width: 0 if self.hidden else self.bar_width

<AlphabetSelect>:
    gradient_transparency: 0
    content: ['#', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']

<ImageButton>:
    canvas.after:
        Color:
            rgba: app.theme.text
        Rectangle:
            size: self.height - self.image_padding[1] * 2, self.height - self.image_padding[1] * 2
            pos: self.image_pos_x, self.y + self.image_padding[1]
            source: self.source

<ElementButton>:
    scale: min(self.height, self.width / 3)
    padding: self.scale / 4
    font_size: self.scale/3
    size_hint: 1, 1

<ElementButtonToggle>:
    scale: min(self.height, self.width / 3)
    padding: self.scale / 4
    font_size: self.scale/3
    size_hint: 1, 1

<ElementLabel>:
    ticker_delay: 3
    ticker_amount: 0.333
    scale: min(self.height, self.width / root.h_divisor)
    padding: self.scale / 8
    font_size: self.scale / 3
    size_hint: 1, 1
    text_size: None, self.size[1]
    valign: 'middle'

<ElementWidget>:
    canvas.after:
        Color:
            rgba: app.theme.selected[:3]+[0.3] if root.selected else [0, 0, 0, 0]
        Rectangle:
            size: self.size
            pos: self.pos

<WidgetLog>:
    bypass_swipe: [rvview]
    swipe_mode: 'none'
    cols: 1
    NormalRecycleView:
        id: rvview
        scroll_distance: 10
        scroll_timeout: 400
        data: app.infotext_history
        viewclass: 'LogLabel'
        SelectableRecycleGridLayout2:
            id: rvbox
            cols: 1
            size_hint: 1, None
            height: self.minimum_height
            default_size: None, app.button_scale * 0.5
            default_size_hint: 1, None

<LogLabel@ElementLabel>:
    font_size: self.scale * 0.85

<WidgetNoScreenSelected>:
    swipe_mode: 'none'
    cols: 1
    Widget:
    NormalLabel:
        text: 'No screen selected.  Select a screen from the menu on the left, or create a new screen using the buttons in the bottom-left.  Create a blank screen with the "New Screen" button, or start with a screen preset by clicking the "Add Screen" button.'
        text_size: self.width, None
        size_hint_y: None
        height: self.texture_size[1] + 20
    Widget:

<WidgetNoScreen>:
    swipe_mode: 'none'
    cols: 1
    Widget:
    NormalLabel:
        text: 'Screen not set up.'
    ElementButton:
        scale: min(self.height, self.width / 8)
        text: "Open Screen Settings"
        on_release: app.open_screen_settings()
    Widget:

<WidgetNoScreenInfo>:
    swipe_mode: 'none'
    cols: 1
    Widget:
    NormalLabel:
        text: 'No widgets on screen.  Add widgets using the "Add New Widget" button below, or start by adding a new screen preset using the "Add Screen" menu in the bottom-left.  If you do not want this screeen, delete it by clicking the red "X" button above.'
        text_size: self.width, None
        size_hint_y: None
        height: self.texture_size[1] + 20
    Widget:

<WidgetSongInfo>:
    swipe_mode: 'song'
    activate_tap: True
    cols: 1
    ElementLabel:
        text: root.song_artist + ' - ' + root.song_title
        valign: 'bottom'
    ElementLabel:
        text: root.song_album
        valign: 'top'

<WidgetSongInfoNext>:
    swipe_mode: 'song'
    activate_tap: True
    cols: 1
    ElementLabel:
        scale: min(self.height, self.width / self.h_divisor)
        font_size: self.scale / 3
        text: "Next Song: " + root.next_song_artist + ' - ' + root.next_song_title
        valign: 'middle'

<WidgetSongTime>:
    swipe_mode: 'song'
    activate_tap: True
    cols: 1
    padding: self.height/12, 0
    NormalLabel:
        size_hint: 1, 1
        font_size: min(self.width / 9, self.height - self.padding[0])
        text: root.song_position_formatted + '/' + root.song_duration_formatted
        text_size: None, self.size[1]
        valign: 'middle'

<WidgetSongPosition>:
    bypass_swipe: [slider]
    swipe_mode: 'song'
    cols: 1
    padding: self.height / 16
    ElementSlider:
        cached: root.cached
        id: slider
        max: root.song_duration
        value: root.song_position

<WidgetSongControlsFull>:
    bypass_swipe: [slider]
    swipe_mode: 'song'
    cols: 4
    padding: self.height/12, 0
    ImageButton:
        size_hint: None, 1
        width: min(self.height, self.parent.width / 4)
        image_padding: self.height/6, self.height/6
        source: 'data/left.png'
        on_release: root.player.previous()
    ImageButton:
        size_hint: None, 1
        width: min(self.height, self.parent.width / 4)
        image_padding: self.height/6, self.height/6
        source: 'data/pause.png' if root.playing else 'data/play.png'
        on_release: root.player.playtoggle()
    ElementSlider:
        cached: root.cached
        id: slider
        max: root.song_duration
        value: root.song_position
    ImageButton:
        size_hint: None, 1
        width: min(self.height, self.parent.width / 4)
        image_padding: self.height/6, self.height/6
        source: 'data/right.png'
        on_release: root.player.next()

<WidgetSongControls>:
    swipe_mode: 'song'
    cols: 1
    Widget:
        size_hint_y: None
        height: max(0, (root.height - buttons.width/3)/2)
    GridLayout:
        id: buttons
        cols: 5
        Widget:
            size_hint_x: None
            width: max(0, (root.width - buttons.height*3)/2)
        ImageButton:
            size_hint: 1, 1
            image_padding: self.height/6, self.height/6
            source: 'data/left.png'
            on_release: root.player.previous()
        ImageButton:
            size_hint: 1, 1
            image_padding: self.height/6, self.height/6
            source: 'data/pause.png' if root.playing else 'data/play.png'
            on_release: root.player.playtoggle()
        ImageButton:
            size_hint: 1, 1
            image_padding: self.height/6, self.height/6
            source: 'data/right.png'
            on_release: root.player.next()
        Widget:
            size_hint_x: None
            width: max(0, (root.width - buttons.height*3)/2)
    Widget:
        size_hint_y: None
        height: max(0, (root.height - buttons.width/3)/2)

<WidgetPlayerModeToggle>:
    swipe_mode: 'mode'
    cols: 2
    ShortLabel:
        font_size: self.height/3
        size_hint_y: 1
        text: 'Play Mode: '
    ElementButton:
        text: root.play_mode_caps
        on_release: root.next_mode()

<WidgetPlayerMode>:
    swipe_mode: 'mode'
    cols: 2
    ElementButtonToggle:
        state: 'down' if root.play_mode == 'in order' else 'normal'
        text: 'In Order'
        on_release: root.mode_set('in order')
    ElementButtonToggle:
        state: 'down' if root.play_mode == 'repeat all' else 'normal'
        text: 'Repeat All'
        on_release: root.mode_set('repeat all')
    ElementButtonToggle:
        state: 'down' if root.play_mode == 'repeat one' else 'normal'
        text: 'Repeat One'
        on_release: root.mode_set('repeat one')
    ElementButtonToggle:
        state: 'down' if root.play_mode == 'shuffle' else 'normal'
        text: 'Shuffle'
        on_release: root.mode_set('shuffle')

<ElementRating>:
    canvas:
        Color:
            rgb: app.theme.selected if root.rating > 0 else app.theme.button_down
        Rectangle:
            size: self.star_size, self.star_size
            pos: self.x, self.y_pos
            source: 'data/star.png'
        Color:
            rgb: app.theme.selected if root.rating > 1 else app.theme.button_down
        Rectangle:
            size: self.star_size, self.star_size
            pos: self.x + self.star_size, self.y_pos
            source: 'data/star.png'
        Color:
            rgb: app.theme.selected if root.rating > 2 else app.theme.button_down
        Rectangle:
            size: self.star_size, self.star_size
            pos: self.x + self.star_size*2, self.y_pos
            source: 'data/star.png'
        Color:
            rgb: app.theme.selected if root.rating > 3 else app.theme.button_down
        Rectangle:
            size: self.star_size, self.star_size
            pos: self.x + self.star_size*3, self.y_pos
            source: 'data/star.png'
        Color:
            rgb: app.theme.selected if root.rating > 4 else app.theme.button_down
        Rectangle:
            size: self.star_size, self.star_size
            pos: self.x + self.star_size*4, self.y_pos
            source: 'data/star.png'
    star_size: self.width / 5
    y_pos: (self.height - self.star_size)/2 + self.y

<ElementFavorite>:
    color: app.theme.button_toggle_true if self.song_favorite else app.theme.button_disabled
    source: 'data/heart.png'

<WidgetSongRating>:
    swipe_mode: 'song'
    cols: 3
    Widget:
        size_hint_x: 0.1
    ElementRating:
        size_hint_max_x: self.height * 5
        size_hint_x: 5
        element_type: 'song'
        rating: root.song_rating
        player: root.player
        song_id: root.song_id
    Widget:
        size_hint_x: 0.1

<WidgetSongRatingSafe>:
    canvas.after:
        Color:
            rgba: app.theme.active if root.block_first_blocking else [0, 0, 0, 0]
        Line:
            rounded_rectangle: self.x+3, self.y+3, self.width-6, self.height-6, 5
            width: 3
    block_first: True
    swipe_mode: 'none'

<WidgetSongFavorite>:
    swipe_mode: 'favorite'
    cols: 1
    ElementFavorite:
        element_type: 'song'
        song_favorite: root.song_favorite
        song_id: root.song_id
        player: root.player

<WidgetSongFavoriteSafe>:
    canvas.after:
        Color:
            rgba: app.theme.active if root.block_first_blocking else [0, 0, 0, 0]
        Line:
            rounded_rectangle: self.x+3, self.y+3, self.width-6, self.height-6, 5
            width: 3
    block_first: True
    swipe_mode: 'none'

<WidgetSongRatingFavorite>:
    swipe_mode: 'rating'
    cols: 3
    ElementRating:
        element_type: 'song'
        rating: root.song_rating
        size_hint_x: 5
        size_hint_max_x: self.height * 5
        song_id: root.song_id
        player: root.player
    Widget:
        size_hint_x: 0.333
    ElementFavorite:
        element_type: 'song'
        song_favorite: root.song_favorite
        song_id: root.song_id
        player: root.player

<WidgetSongRatingFavoriteSafe>:
    canvas.after:
        Color:
            rgba: app.theme.active if root.block_first_blocking else [0, 0, 0, 0]
        Line:
            rounded_rectangle: self.x+3, self.y+3, self.width-6, self.height-6, 5
            width: 3
    block_first: True
    swipe_mode: 'none'

<WidgetPlayerVolume>:
    swipe_mode: 'volume'
    bypass_swipe: [slider]
    cols: 2
    padding: self.height / 16
    ShortLabel:
        font_size: self.height/3
        size_hint_y: 1
        text: 'Volume: '
    ElementSlider:
        id: slider
        value_track_color: app.theme.button_down
        max: 1
        value: root.volume
        on_value: root.player.volume_set(self.value)

<WidgetSongArt>:
    activate_tap: True
    cols: 1
    Image:
        id: image
        opacity: root.image_opacity
        center_x: self.width / 2
        fit_mode: 'contain'
        source: 'data/musicnote.png'
        color: root.image_color if root.image_color else app.theme.text

<QueuePresetsMenu>:
    MenuButton:
        text: "Favorite Songs"
        on_release: root.player.queue_preset('Favorite')
        on_release: root.dismiss()
    MenuButton:
        text: "5 Star Songs"
        on_release: root.player.queue_preset('5 Star')
        on_release: root.dismiss()
    MenuButton:
        text: "4 And 5 Star Songs"
        on_release: root.player.queue_preset('4 And 5 Star')
        on_release: root.dismiss()
    MenuButton:
        text: "Most Played Songs"
        on_release: root.player.queue_preset('Most Played')
        on_release: root.dismiss()
    MenuButton:
        text: "Recently Played Songs"
        on_release: root.player.queue_preset('Recently Played')
        on_release: root.dismiss()
    MenuButton:
        text: "Random Unplayed Songs"
        on_release: root.player.queue_preset('Random Unplayed')
        on_release: root.dismiss()
    MenuButton:
        text: "Newest Songs"
        on_release: root.player.queue_preset('Newest')
        on_release: root.dismiss()
    MenuButton:
        text: "Random Genre"
        on_release: root.player.queue_random_genre()
        on_release: root.dismiss()
    MenuButton:
        text: "Random Artist"
        on_release: root.player.queue_random_artist()
        on_release: root.dismiss()
    MenuButton:
        text: "Random Album"
        on_release: root.player.queue_random_album()
        on_release: root.dismiss()
    MenuButton:
        text: "Random Songs"
        on_release: root.player.queue_random(keepcurrent=False)
        on_release: root.dismiss()

<WidgetQueuePresets>:
    cols: 1
    WideMenuStarter:
        scale: min(self.height, self.width / 6)
        padding: self.scale / 4
        font_size: self.scale / 3
        player: root.player
        size_hint: 1, 1
        text: 'Quick Queue Presets...'
        on_release: root.open_presets_menu(self)

<WidgetPlaylistUndo>:
    swipe_mode: 'none'
    cols: 2
    ElementButton:
        text: "Undo Queue Change"
        on_release: root.player.queue_undo()
        disabled: not root.queue_history

<WidgetPlaylistLoads>:
    swipe_mode: 'none'
    cols: 3
    ElementButton:
        text: "Queue Playing Genre"
        on_release: root.player.queue_same_genre()
        disabled: not root.song_id or not root.song_genre
    ElementButton:
        text: "Queue Playing Artist"
        on_release: root.player.queue_same_artist()
        disabled: not root.song_id or not root.song_artist_id
    ElementButton:
        text: "Queue Playing Album"
        on_release: root.player.queue_same_album()
        disabled: not root.song_id or not root.song_album_id

<WidgetPlaylistLoadsRandom>:
    swipe_mode: 'none'
    cols: 3
    ElementLabel:
        scale: min(self.height, self.width / 3)
        text: "Queue Random:"
    ElementButton:
        text: "Genre"
        on_release: root.player.queue_random_genre()
    ElementButton:
        text: "Artist"
        on_release: root.player.queue_random_artist()
    ElementButton:
        text: "Album"
        on_release: root.player.queue_random_album()
    ElementButton:
        text: "Songs"
        on_release: root.player.queue_random(keepcurrent=False)
    ElementButton:
        text: "Undo"
        on_release: root.player.queue_undo()
        disabled: not root.queue_history

<WidgetQueueSimilar>:
    swipe_mode: 'queue same'
    cols: 2
    ElementButton:
        scale: min(self.height, self.width / 4.5)
        text: "Queue Previous Similar"
        on_release: root.player.queue_same_previous()
        disabled: not root.queue_id or not root.queue_type
    ElementButton:
        scale: min(self.height, self.width / 4.5)
        text: "Queue Next Similar"
        on_release: root.player.queue_same_next()
        disabled: not root.queue_id or not root.queue_type

<WidgetAddToPlaylist>:
    cols: 1
    WideMenuStarter:
        scale: min(self.height, self.width / 6)
        padding: self.scale / 4
        font_size: self.scale/3
        size_hint: 1, 1
        text: 'Add Current Song To Playlist...'
        on_release: root.open_playlist_menu(self)

<WidgetQueuePlaylist>:
    cols: 1
    WideMenuStarter:
        scale: min(self.height, self.width / 6)
        padding: self.scale / 4
        font_size: self.scale/3
        player: root.player
        size_hint: 1, 1
        text: 'Quick Queue Playlist...'
        on_release: root.open_playlist_menu(self)
""")


def timecode_hours(seconds):
    all_minutes, final_seconds = divmod(seconds, 60)
    all_hours, final_minutes = divmod(all_minutes, 60)
    time_text = str(int(all_hours)).zfill(2) + ':' + str(int(final_minutes)).zfill(2) + ':' + str(int(round(final_seconds)))
    return time_text


def timecode(seconds):
    all_minutes, final_seconds = divmod(seconds, 60)
    time_text = str(int(all_minutes)).zfill(2) + ':' + '{:05.2f}'.format(final_seconds)
    return time_text


def check_swipe(touch, swipe_distance):
    x_delta = touch.opos[0] - touch.pos[0]
    y_delta = touch.opos[1] - touch.pos[1]
    swipe = None

    if abs(x_delta) > abs(y_delta):
        if x_delta > swipe_distance:
            swipe = 'left'
        elif x_delta < 0 - swipe_distance:
            swipe = 'right'
    else:
        if y_delta > swipe_distance:
            swipe = 'down'
        elif y_delta < 0 - swipe_distance:
            swipe = 'up'
    return swipe


class CustomScrollbar(ScrollBarY):
    bar_width = NumericProperty()
    show_selected_point = BooleanProperty(False)
    selected_point = NumericProperty(0)

    def _get_vbar(self):
        if self.height > 0:
            min_height = self.width / self.height  #prevent scroller size from being too small
        else:
            min_height = 0
        vh = self.viewport_size[1]
        h = self.scroller_size[1]
        if vh < h or vh == 0:
            return 0, 1.
        ph = max(min_height, h / float(vh))
        sy = min(1.0, max(0.0, self.scroll))
        py = (1. - ph) * sy
        return (py, ph)
    vbar = AliasProperty(_get_vbar, bind=('scroller_size', 'scroll', 'viewport_size', 'height'), cache=True)

    def in_vbar(self, pos_y):
        local_y = pos_y - self.y
        local_per = local_y / self.height
        vbar = self.vbar
        vbar_top = vbar[0] + vbar[1]
        vbar_bottom = vbar[0]
        half_vbar_height = vbar[1] / 2
        if local_per > vbar_top:
            return local_per - vbar_top + half_vbar_height
        elif local_per < vbar_bottom:
            return local_per - vbar_bottom - half_vbar_height
        else:  #vbar_top > local_per > vbar_bottom:
            return 0

    def on_touch_down(self, touch):
        if not self.disabled and self.collide_point(*touch.pos):
            position = self.in_vbar(touch.pos[1])
            self.scroller.scroll_y += position
            touch.grab(self)
            if 'button' in touch.profile and touch.button.startswith('scroll'):
                btn = touch.button
                scroll_direction = ''
                if btn in ('scrollup', 'scrollright'):
                    scroll_direction = 'up'
                elif btn in ('scrolldown', 'scrollleft'):
                    scroll_direction = 'down'
                return self.wheel_scroll(scroll_direction)

            self.do_touch_scroll(touch)
            return True


class AlphabetSelect(SmoothSetting):
    letters = "#ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    scrollview = ObjectProperty()
    skip_next_active = False

    def touch_letter(self, index):
        letter = self.letters[index]
        return letter

    def get_sort_key(self, data_mode):
        app = App.get_running_app()
        if data_mode == 'song':
            sort_mode = app.sort_mode_song
        elif data_mode == 'artist':
            sort_mode = app.sort_mode_artist
        elif data_mode == 'playlistsong':
            sort_mode = app.sort_mode_playlist
        else:
            sort_mode = app.sort_mode_other
        if sort_mode == 'name' and data_mode in ['song', 'playlistsong']:
            sort_mode = 'title'
        return sort_mode

    def item_index(self, letter, data, data_mode):
        letter = letter.lower()
        app = App.get_running_app()
        length = len(data)
        sort_reverse = app.sort_reverse
        sort_key = self.get_sort_key(data_mode)
        if sort_key not in ['album', 'artist', 'title', 'name']:
            return -1
        if sort_reverse:
            data = reversed(data)
        for index, item in enumerate(data):
            if letter == '#':
                try:
                    number = int(item[sort_key][0])
                    return index / length
                except:
                    pass
            if item[sort_key].lower().startswith(letter):
                return index / length
        return -1

    def scroll_to_per(self, per):
        #scroll self to the letter at the given percentage of the scrollview
        per = max(min(per, 1), 0)
        app = App.get_running_app()
        data = self.scrollview.data
        length = len(data)
        data_mode = self.scrollview.owner.data_mode
        sort_reverse = app.sort_reverse
        sort_key = self.get_sort_key(data_mode)
        if sort_key not in ['album', 'artist', 'title', 'name']:
            return
        if not sort_reverse:
            index = length - 1 - int((length - 1) * per)
        else:
            index = int((length - 1) * per)
        try:
            current = data[index]
            text = current[sort_key]
            letter = text[0].upper()
        except:
            return
        try:
            int(letter)
            letter = '#'
        except:
            pass
        try:
            index = self.letters.index(letter)
            if index != self.active:
                self.skip_next_active = True
                self.ids.scrollerArea.active = index
                self.ids.scrollerArea.scroll_to_element(index, instant=True)
        except:
            pass

    def scroll_to_letter(self, letter):
        app = App.get_running_app()
        data_mode = self.scrollview.owner.data_mode
        data = self.scrollview.data
        per = self.item_index(letter, data, data_mode)
        if per != -1:
            offset = self.scrollview.height / self.scrollview.viewport_size[1]
            offset = per * offset
            if app.sort_reverse:
                self.scrollview.scroll_y = per + offset
            else:
                self.scrollview.scroll_y = 1 - per - offset

    def scroll_to_index(self, index):
        #scroll the scrollview to the given index
        letter = self.touch_letter(index)
        self.scroll_to_letter(letter)

    def on_active(self, *_):
        if self.skip_next_active:
            self.skip_next_active = False
            return
        if not self.scrollview:
            return
        if self.disabled:
            return
        self.scroll_to_index(self.active)

    def set_active(self, active):
        self.scroll_to_element(active)


class AnimatedModalView(ModalView):
    delay = NumericProperty(0)
    anim = ObjectProperty(allownone=True)
    angle = NumericProperty(0)
    angle_anim = ObjectProperty(allownone=True)

    def open(self, *args, **kwargs):
        super().open(*args, **kwargs)
        app = App.get_running_app()
        self.opacity = 0
        self.angle = 0
        self.angle_anim = Animation(angle=360, duration=2)+Animation(angle=0, duration=0)
        self.angle_anim.repeat = True
        self.angle_anim.start(self)
        self.anim = Animation(duration=self.delay)+Animation(opacity=1, duration=app.animation_length)
        self.anim.start(self)

    def dismiss(self, *args, **kwargs):
        app = App.get_running_app()
        if self.anim:
            self.anim.cancel(self)
        if self.angle_anim:
            self.angle_anim.cancel(self)
        anim = Animation(opacity=0, duration=app.animation_length)
        anim.start(self)
        anim.bind(on_complete=self.finish_dismiss)

    def finish_dismiss(self, *_):
        super().dismiss()


class PlaylistMenuButton(MenuButton):
    owner = ObjectProperty()
    playlistid = StringProperty()

    def on_release(self, *_):
        self.owner.add_playlist(self.playlistid)


class QueuePresetsMenu(NormalDropDown):
    player = ObjectProperty()


class ImageButton(WideButton):
    image_padding = ListProperty([5, 5])
    source = StringProperty()
    image_halign = StringProperty('center')

    def get_image_pos_x(self):
        if self.image_halign == 'left':
            return self.x + self.image_padding[0]
        elif self.image_halign == 'right':
            return self.x + self.width - self.height
        else:  #center
            return self.x + self.image_padding[0] + self.width / 2 - self.height / 2
    image_pos_x = AliasProperty(get_image_pos_x, bind=['x', 'width', 'height', 'image_padding', 'image_halign'])


class ElementLabel(TickerLabel):
    scale = NumericProperty()
    h_divisor = NumericProperty(8)


class ElementWidget(GridLayout):
    widget_type = StringProperty('')
    index = NumericProperty(0)
    selected = BooleanProperty(False)
    bypass_swipes = BooleanProperty(False)
    blocked = BooleanProperty(False)
    bypass_swipe = ListProperty()
    screen_manager = ObjectProperty()
    screen = ObjectProperty()
    player = ObjectProperty()
    swipe_mode = StringProperty("song")
    swipe_distance = 50
    swipe_time = NumericProperty(0.2)
    activate_tap = BooleanProperty(False)
    block_first = BooleanProperty(False)
    block_first_blocking = BooleanProperty(True)
    toggle_block_first = None

    def reload(self):
        pass

    def tap(self):
        if self.blocked:
            return
        if self.swipe_mode in ['song', 'skip']:
            self.player.playtoggle()
        elif self.swipe_mode == 'favorite':
            self.player.favorite_toggle()

    def swipe(self, direction):
        app = App.get_running_app()
        if direction == 'up':
            screen_name = self.screen_manager.go_previous()
            app.speak(screen_name, 'screen')
            return
        if direction == 'down':
            screen_name = self.screen_manager.go_next()
            app.speak(screen_name, 'screen')
            return

        mode = self.swipe_mode
        player = self.player
        if mode == 'song':
            if direction == 'right':
                player.next()
            else:
                player.previous()
        elif mode == 'rating':
            if direction == 'right':
                rating = player.rating_up()
            else:
                rating = player.rating_down()
            if rating is not None:
                app.speak("set rating to "+str(rating))
        elif mode == 'volume':
            if direction == 'right':
                player.volume_up()
            else:
                player.volume_down()
        elif mode == 'favorite':
            favorite = direction == 'right'
            player.favorite_set(favorite=favorite)
            if favorite:
                app.speak('set favorite')
            else:
                app.speak('unset favorite')
        elif mode == 'queue same':
            if direction == 'right':
                player.queue_same_next()
                app.speak('queue next same')
            else:
                player.queue_same_previous()
                app.speak('queue previous same')
        elif mode == 'mode':
            if direction == 'right':
                mode_set = player.mode_next()
            else:
                mode_set = player.mode_previous()
            app.speak('play mode '+mode_set)
        elif mode == 'skip':
            if direction == 'right':
                player.position_forward()
            else:
                player.position_back()
        elif mode == 'queue shuffle':
            if direction == 'right':
                player.queue_shuffle()
                app.speak('shuffled queue')
            else:
                player.queue_undo()
                app.speak('undo queue change')
        elif mode == 'queue random':
            if direction == 'right':
                player.queue_random()
                app.speak("queue "+str(player.random_amount)+" random songs")
            else:
                player.queue_undo()
                app.speak('undo queue change')
        elif mode == 'queue genre':
            if direction == 'right':
                player.queue_same_genre()
                app.speak('queue songs from genre '+player.song_genre)
            else:
                player.queue_undo()
                app.speak('undo queue change')
        elif mode == 'queue artist':
            if direction == 'right':
                player.queue_same_artist()
                app.speak('queue songs from artist '+player.song_artist)
            else:
                player.queue_undo()
                app.speak('undo queue change')
        elif mode == 'queue album':
            if direction == 'right':
                player.queue_same_album()
                app.speak('queue album '+player.song_album)
            else:
                player.queue_undo()
                app.speak('undo queue change')

    def end_block_first(self, *_):
        self.block_first_blocking = True
        self.toggle_block_first = None

    def on_touch_down(self, touch):
        if self.bypass_swipes and not self.blocked:
            return super().on_touch_down(touch)
        if self.collide_point(*touch.pos):
            if self.screen:
                self.screen.select(self)
            if self.blocked:
                return

            if self.block_first:
                if self.block_first_blocking:
                    self.block_first_blocking = False
                    self.toggle_block_first = Clock.schedule_once(self.end_block_first, 3)
                    return True
                else:
                    if self.toggle_block_first:
                        self.toggle_block_first.cancel()
                        self.toggle_block_first = None
                    self.block_first_blocking = True

            touch.grab(self)
            super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.blocked:
            return
        if self.bypass_swipes:
            return super().on_touch_up(touch)
        if touch.grab_current is self:
            touch.ungrab(self)
            #if self.swipe_mode == 'none':
            #    return super().on_touch_up(touch)
            for child in self.bypass_swipe:
                if child.collide_point(*touch.opos):
                    return super().on_touch_up(touch)
            touch_time = touch.time_end - touch.time_start
            if touch_time <= self.swipe_time:
                swipe = check_swipe(touch, self.swipe_distance)
                if swipe is not None:
                    self.swipe(swipe)
                    touch.move([-1, -1, [1, 1]])  #move touch away to prevent it from releasing on buttons
                    return True
            if self.activate_tap:
                self.tap()
            return super().on_touch_up(touch)


class ElementButton(WideButton):
    pass


class ElementButtonToggle(WideToggle):
    pass


class SliderThemed(Slider):
    cached = BooleanProperty(False)
    line_color = ColorProperty((1, 1, 1, 1))
    cursor_color = ColorProperty((1, 1, 1, 1))


class ElementSlider(SliderThemed):
    swipe_distance = NumericProperty(50)
    swipe_time = NumericProperty(0.2)
    value_before_touch = NumericProperty()

    def on_touch_down(self, touch):
        if self.disabled or not self.collide_point(*touch.pos):
            return
        self.value_before_touch = self.value
        touch.grab(self)
        self.parent.adjusting = True
        #self.value_pos = touch.pos
        return True

    def on_touch_move(self, touch):
        if touch.grab_current == self:
            self.value_pos = touch.pos
            return True

    def on_touch_up(self, touch):
        self.parent.adjusting = False
        if touch.grab_current == self:
            touch_time = touch.time_end - touch.time_start
            if touch_time <= self.swipe_time:
                swipe = check_swipe(touch, self.swipe_distance)
                if swipe is not None:
                    self.value = self.value_before_touch
                    self.parent.swipe(swipe)
                    return True
            self.value_pos = touch.pos
            self.parent.slider_value(self.value)
            return True


class ElementRating(Widget):
    song_id = StringProperty()
    player = ObjectProperty()
    star_size = NumericProperty(0)
    y_pos = NumericProperty(0)
    rating = NumericProperty(0)
    blocked = BooleanProperty(False)
    element_type = StringProperty('song')

    def __init__(self, **kwargs):
        self.register_event_type('on_set_rating')
        super().__init__(**kwargs)

    def on_set_rating(self, widget):
        pass

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            return True

    def on_touch_up(self, touch):
        if self.blocked:
            return True
        if self.collide_point(*touch.pos) and touch.grab_current == self:
            x = touch.pos[0] - self.x
            rating = int((x/self.width)*5) + 1
            if rating == self.rating:
                rating = 0
            self.player.rating_set(rating, self.song_id, element_type=self.element_type)
            self.dispatch('on_set_rating', widget=self)


class ElementFavorite(Image):
    song_id = StringProperty()
    player = ObjectProperty()
    song_favorite = BooleanProperty(False)
    blocked = BooleanProperty(False)
    element_type = StringProperty('song')

    def __init__(self, **kwargs):
        self.register_event_type('on_set_favorite')
        super().__init__(**kwargs)

    def on_set_favorite(self, widget):
        pass

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            return True

    def on_touch_up(self, touch):
        if self.blocked:
            return True
        if self.collide_point(*touch.pos) and touch.grab_current == self:
            if touch.grab_current == self:
                touch.ungrab(self)
                song_favorite = not self.song_favorite
                self.player.favorite_set(self.song_id, favorite=song_favorite, element_type=self.element_type)
                self.dispatch('on_set_favorite', widget=self)


#Helper and specialized widgets
class WidgetLog(ElementWidget):
    pass


class WidgetEmpty(ElementWidget):
    pass


class WidgetNoScreenSelected(ElementWidget):
    pass


class WidgetNoScreen(ElementWidget):
    pass


class WidgetNoScreenInfo(ElementWidget):
    pass


#Song Display - widgets that only display information and respond to swipes
class WidgetSongArt(ElementWidget):
    #Displays the track or album art for the currently playing song.
    song_id = StringProperty()
    song_art = ObjectProperty(b'')
    image_opacity = NumericProperty(1)
    image_color = ListProperty(allownone=True)

    def on_song_id(self, *_):
        if self.song_id:
            self.player.load_song_art(self)

    @mainthread
    def set_song_art(self, song_art):
        if song_art:
            self.song_art = song_art
            self.update_image()
            self.image_color = [1, 1, 1, 1]
            return
        self.image_color = None

    def update_image(self):
        if self.song_art:
            try:
                image_bytes = BytesIO(self.song_art)
                core_image = CoreImage(image_bytes, ext='png')
                image = self.ids['image']
                image.texture = core_image.texture
            except Exception as e:
                print(e)

    def on_player(self, *_):
        self.song_id = self.player.song_id
        self.player.bind(song_id=self.setter('song_id'))


class WidgetSongInfo(ElementWidget):
    #Displays artist, album and title of the currently playing song.
    song_artist = StringProperty()
    song_title = StringProperty()
    song_album = StringProperty()

    def on_player(self, *_):
        self.song_artist = self.player.song_artist
        self.song_title = self.player.song_title
        self.song_album = self.player.song_album
        self.player.bind(song_artist=self.setter('song_artist'))
        self.player.bind(song_title=self.setter('song_title'))
        self.player.bind(song_album=self.setter('song_album'))


class WidgetSongInfoNext(ElementWidget):
    #Displays artist and title for next song in the play queue.
    next_song_artist = StringProperty()
    next_song_title = StringProperty()
    next_song_album = StringProperty()

    def on_player(self, *_):
        self.next_song_artist = self.player.next_song_artist
        self.next_song_title = self.player.next_song_title
        self.next_song_album = self.player.next_song_album
        self.player.bind(next_song_artist=self.setter('next_song_artist'))
        self.player.bind(next_song_title=self.setter('next_song_title'))
        self.player.bind(next_song_album=self.setter('next_song_album'))


#Song Play - widgets that control the current song
class WidgetSongControlsFull(ElementWidget):
    #Displays standard buttons for controlling playback and switching songs along with progress bar and time index.
    playing = BooleanProperty(False)
    cached = BooleanProperty(False)
    song_duration = NumericProperty()
    song_position = NumericProperty()
    song_position_formatted = StringProperty('00:00.00')
    song_duration_formatted = StringProperty('00:00.00')
    adjusting = BooleanProperty(False)

    def slider_value(self, value):
        self.player.position_set(value)

    def set_song_position(self, instance, value):
        if not self.adjusting:
            self.song_position = value
        self.song_position_formatted = timecode(value)

    def set_song_duration(self, instance, value):
        self.song_duration = value
        self.song_duration_formatted = timecode(value)

    def on_player(self, *_):
        self.song_position = self.player.song_position
        self.song_duration = self.player.song_duration
        self.song_duration_formatted = timecode(self.song_duration)
        self.song_position_formatted = timecode(self.song_position)
        self.cached = self.player.current_is_cached
        self.player.bind(song_duration=self.set_song_duration)
        self.player.bind(song_position=self.set_song_position)
        self.playing = self.player.playing
        self.player.bind(playing=self.setter('playing'))
        self.player.bind(current_is_cached=self.setter('cached'))


class WidgetSongControls(ElementWidget):
    #Displays standard buttons for controlling playback and switching songs.
    playing = BooleanProperty(False)

    def on_player(self, *_):
        self.playing = self.player.playing
        self.player.bind(playing=self.setter('playing'))


class WidgetSongTime(ElementWidget):
    #Displays the playback time and total length of the current song
    song_duration = NumericProperty()
    song_position = NumericProperty()
    song_position_formatted = StringProperty('00:00.00')
    song_duration_formatted = StringProperty('00:00.00')

    def set_song_position(self, instance, value):
        self.song_position = value
        self.song_position_formatted = timecode(value)

    def set_song_duration(self, instance, value):
        self.song_duration = value
        self.song_duration_formatted = timecode(value)

    def on_player(self, *_):
        self.song_position = self.player.song_position
        self.song_duration = self.player.song_duration
        self.song_duration_formatted = timecode(self.song_duration)
        self.song_position_formatted = timecode(self.song_position)
        self.player.bind(song_duration=self.set_song_duration)
        self.player.bind(song_position=self.set_song_position)


class WidgetSongPosition(ElementWidget):
    #Displays the playback position of the current song and allows selecting position with a scroller.
    song_duration = NumericProperty()
    song_position = NumericProperty()
    adjusting = BooleanProperty(False)
    cached = BooleanProperty(False)

    def slider_value(self, value):
        self.player.position_set(value)

    def set_song_position(self, instance, value):
        if not self.adjusting:
            self.song_position = value

    def set_song_duration(self, instance, value):
        self.song_duration = value

    def on_player(self, *_):
        self.song_position = self.player.song_position
        self.song_duration = self.player.song_duration
        self.cached = self.player.current_is_cached
        self.player.bind(song_duration=self.set_song_duration)
        self.player.bind(song_position=self.set_song_position)
        self.player.bind(current_is_cached=self.setter('cached'))


class WidgetSongRating(ElementWidget):
    #Displays the rating of the currently playing song and allows it to be set or removed.
    song_rating = NumericProperty(0)
    song_id = StringProperty()

    def on_player(self, *_):
        self.song_id = self.player.song_id
        self.song_rating = self.player.song_rating
        self.player.bind(song_id=self.setter('song_id'))
        self.player.bind(song_rating=self.setter('song_rating'))


class WidgetSongRatingSafe(WidgetSongRating):
    pass


class WidgetSongFavorite(ButtonBehavior, ElementWidget):
    #Displays and changes the favorite tag of the current song.
    song_favorite = BooleanProperty(False)
    song_id = StringProperty()

    def on_player(self, *_):
        self.song_id = self.player.song_id
        self.song_favorite = self.player.song_favorite
        self.player.bind(song_id=self.setter('song_id'))
        self.player.bind(song_favorite=self.setter('song_favorite'))


class WidgetSongFavoriteSafe(WidgetSongFavorite):
    pass


class WidgetSongRatingFavorite(ElementWidget):
    #Displays and edits the rating and favorite tags of the current song.
    song_rating = NumericProperty(0)
    song_favorite = BooleanProperty(False)
    song_id = StringProperty()

    def on_player(self, *_):
        self.song_id = self.player.song_id
        self.song_rating = self.player.song_rating
        self.song_favorite = self.player.song_favorite
        self.player.bind(song_id=self.setter('song_id'))
        self.player.bind(song_rating=self.setter('song_rating'))
        self.player.bind(song_favorite=self.setter('song_favorite'))


class WidgetSongRatingFavoriteSafe(WidgetSongRatingFavorite):
    pass


#Player - widgets that change player and queue settings
class WidgetAddToPlaylist(ElementWidget):
    playlist_menu = None

    def add_playlist(self, playlistid):
        self.playlist_menu.dismiss()
        self.playlist_menu = None
        self.player.playlist_add_current_song(playlistid)

    def open_playlist_menu(self, button):
        if self.playlist_menu:
            self.playlist_menu.dismiss()
        self.playlist_menu = NormalDropDown()
        playlists = self.player.get_playlists()
        for playlist in playlists:
            menu_button = PlaylistMenuButton(owner=self, playlistid=playlist['id'], text=playlist['name'])
            self.playlist_menu.add_widget(menu_button)
        self.playlist_menu.open(button)


class WidgetPlayerVolume(ElementWidget):
    #Displays and changes the volume of the playback.
    volume = NumericProperty(0)

    def slider_value(self, value):
        pass

    def on_player(self, *_):
        self.volume = self.player.volume
        self.player.bind(volume=self.setter('volume'))


class WidgetPlayerModeToggle(ElementWidget):
    #Displays and changes playback mode by toggling between modes
    play_mode = StringProperty()
    play_mode_caps = StringProperty()

    def next_mode(self):
        self.player.mode_next()

    def on_play_mode(self, *_):
        self.play_mode_caps = self.play_mode.title()

    def on_player(self, *_):
        self.play_mode = self.player.play_mode
        self.player.bind(play_mode=self.setter('play_mode'))


class WidgetPlayerMode(ElementWidget):
    #Displays and changes the playback mode between various repeat and shuffle options.
    play_mode = StringProperty()

    def mode_set(self, play_mode):
        self.player.mode_set(play_mode)
        self.reset_buttons()

    def on_play_mode(self, *_):
        self.reset_buttons()

    def reset_buttons(self):
        for child in self.children:
            if child.text.lower() == self.play_mode:
                child.state = 'down'
            else:
                child.state = 'normal'

    def on_player(self, *_):
        self.play_mode = self.player.play_mode
        self.player.bind(play_mode=self.setter('play_mode'))
        self.reset_buttons()


class WidgetPlaylistUndo(ElementWidget):
    #Undo queue changes
    queue_history = ListProperty()

    def on_player(self, *_):
        self.queue_history = self.player.queue_history
        self.player.bind(queue_history=self.setter('queue_history'))


class WidgetPlaylistLoads(ElementWidget):
    #Has options to load various queue presets relating to the current song.
    song_id = StringProperty()
    song_genre = StringProperty()
    song_album_id = StringProperty()
    song_artist_id = StringProperty()
    queue_history = ListProperty()

    def on_player(self, *_):
        self.queue_history = self.player.queue_history
        self.song_id = self.player.song_id
        self.song_genre = self.player.song_genre
        self.song_album_id = self.player.song_album_id
        self.song_artist_id = self.player.song_artist_id
        self.player.bind(queue_history=self.setter('queue_history'))
        self.player.bind(song_id=self.setter('song_id'))
        self.player.bind(song_genre=self.setter('song_genre'))
        self.player.bind(song_album_id=self.setter('song_album_id'))
        self.player.bind(song_artist_id=self.setter('song_artist_id'))


class WidgetPlaylistLoadsRandom(ElementWidget):
    #Has options to load randomized queue contents relating to a common element.
    queue_history = ListProperty()

    def on_player(self, *_):
        self.queue_history = self.player.queue_history
        self.player.bind(queue_history=self.setter('queue_history'))


class WidgetQueueSimilar(ElementWidget):
    #Loads the alphabetically adjacent similar queue to what is currently loaded such as the next/previous album, artist or genre.
    queue_type = StringProperty()
    queue_id = StringProperty()

    def on_player(self, *_):
        self.queue_type = self.player.queue_type
        self.queue_id = self.player.queue_id
        self.player.bind(queue_type=self.setter('queue_type'))
        self.player.bind(queue_id=self.setter('queue_id'))


class WidgetQueuePlaylist(ElementWidget):
    playlist_menu = None

    def add_playlist(self, playlistid):
        self.playlist_menu.dismiss()
        self.playlist_menu = None
        self.player.queue_playlist(playlistid)

    def open_playlist_menu(self, button):
        if self.playlist_menu:
            self.playlist_menu.dismiss()
        self.playlist_menu = NormalDropDown()
        playlists = self.player.get_playlists()
        for playlist in playlists:
            menu_button = PlaylistMenuButton(owner=self, playlistid=playlist['id'], text=playlist['name'])
            self.playlist_menu.add_widget(menu_button)
        self.playlist_menu.open(button)


class WidgetQueuePresets(ElementWidget):
    presets_menu = None

    def open_presets_menu(self, button):
        if self.presets_menu:
            self.presets_menu.dismiss()
        self.presets_menu = QueuePresetsMenu(player=self.player)
        self.presets_menu.open(button)
