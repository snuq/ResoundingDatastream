import threading
import time
import random
from operator import itemgetter
from threading import Thread

from kivy.uix.behaviors import DragBehavior
from kivy.clock import mainthread, Clock
from kivy.app import App
from kivy.core.window import Window
from kivy.properties import *
from kivy.uix.boxlayout import BoxLayout
from snu.recycleview import SelectableRecycleLayout, RecycleItem, RecycleGridLayout
from snu.button import NormalDropDown, WideButton, MenuButton
from snu.label import NormalLabel, LeftNormalLabel
from snu.popup import NormalPopup, ConfirmPopupContent, InputPopupContent
from kivy.uix.gridlayout import GridLayout
from widgets import ElementWidget, ElementRating, ImageButton, timecode, timecode_hours, ElementButton, AnimatedModalView, AlphabetSelect
from databases.subsonic import verify_song, add_to_dict_list

from kivy.lang.builder import Builder
Builder.load_string("""
#:import SlideTransition kivy.uix.screenmanager.SlideTransition

<NormalDropDown>:
    canvas:
        StencilPop
        Color:
            rgba: 0, 0, 0, 0.5
        Rectangle:
            size: app.root.size
            pos: 0, 0
        StencilPush
        Rectangle:
            pos: self.pos
            size: self.size
        StencilUse

<SortDropDown>:
    auto_width: False
    size_hint_x: 1
    MenuButton:
        text: "Shuffle"
        on_release: root.sort('shuffle')
    MenuButton:
        text: "Track Number"
        on_release: root.sort('track')
    MenuButton:
        text: "Title"
        on_release: root.sort('title')
    MenuButton:
        text: "Artist"
        on_release: root.sort('artist')
    MenuButton:
        text: "Album"
        on_release: root.sort('album')
    MenuButton:
        text: "Rating"
        on_release: root.sort('rating')
    MenuButton:
        text: "Play Count"
        on_release: root.sort('playcount')
    MenuButton:
        text: "Reversed"
        on_release: root.sort('reversed')

<AddToDropDown>:
    auto_width: False
    size_hint_x: 1
    Holder:
        WideMenuStarter:
            text: app.queue_mode_names[app.queue_mode]
            on_release: root.open_queue_mode_menu(self)
        NormalToggle:
            text: "Play Now"
            state: 'down' if app.queue_play_immediately else 'normal'
            on_release: app.queue_play_immediately = self.state == 'down'
        NormalButton:
            menu: True
            text: "Add Queue"
            on_release: root.queue_add()
    Holder:
        WideMenuStarter:
            text: "Select Playlist..." if not app.last_playlist_name else app.last_playlist_name
            on_release: root.open_playlists_menu(self)
        NormalButton:
            menu: True
            text: "Add Playlist"
            on_release: root.playlist_add()
    Holder:
        ShortLabel:
            text: "Max Songs To Add: "
        IntegerInput:
            hint_text_color: app.theme.text
            allow_negative: False
            hint_text: 'No Limit'
            text: str(app.queue_max_amount) if app.queue_max_amount > 0 else ''
            size_hint_x: 1
            on_text: app.queue_max_amount = int(self.text) if self.text else 0
    WideToggle:
        text: 'Only Add Selected' if app.queue_selected_only else 'Add All Songs'
        state: 'down' if app.queue_selected_only else 'normal'
        on_release: app.queue_selected_only = self.state == 'down'

<AddToPlaylistDropDown>:
    auto_width: False
    size_hint_x: 1
    WideMenuStarter:
        text: "Select Playlist..." if not app.last_playlist_name else app.last_playlist_name
        on_release: root.open_playlists_menu(self)
    WideButton:
        menu: True
        text: "Add Selected To Playlist"
        on_release: root.playlist_add_current()
    WideButton:
        menu: True
        text: "Add All To Playlist"
        on_release: root.playlist_add_all()

<SortDatabaseSongDropDown>:
    auto_width: False
    size_hint_x: 1
    NormalLabel:
        text: "Current Sort Mode: "+root.current_sort.title()+(' Reversed' if app.sort_reverse else '')
    MenuButton:
        text: "Shuffle"
        on_release: root.sort('shuffle')
    MenuButton:
        text: "Name"
        on_release: root.sort('name')
    MenuButton:
        text: "Track"
        on_release: root.sort('track')
    MenuButton:
        text: "Album"
        on_release: root.sort('album')
    MenuButton:
        text: "Artist"
        on_release: root.sort('artist')
    MenuButton:
        text: "Length"
        on_release: root.sort('length')
    #MenuButton:
    #    text: "Genre"
    #    on_release: root.sort('genre')
    MenuButton:
        text: "Plays"
        on_release: root.sort('plays')
    WideButton:
        text: "Sort Reverse" if root.sort_reverse else "Sort Forward"
        on_release: root.sort_reverse = not root.sort_reverse

<SortDatabaseArtistDropDown>:
    auto_width: False
    size_hint_x: 1
    NormalLabel:
        text: "Current Sort Mode: "+root.current_sort.title()+(' Reversed' if app.sort_reverse else '')
    MenuButton:
        text: "Shuffle"
        on_release: root.sort('shuffle')
    MenuButton:
        text: "Name"
        on_release: root.sort('name')
    MenuButton:
        text: "Album Amount"
        on_release: root.sort('album amount')
    #MenuButton:
    #    text: "Song Amount"
    #    on_release: root.sort('song amount')
    WideButton:
        text: "Sort Reverse" if root.sort_reverse else "Sort Forward"
        on_release: root.sort_reverse = not root.sort_reverse

<SortDatabaseOtherDropDown>:
    auto_width: False
    size_hint_x: 1
    NormalLabel:
        text: "Current Sort Mode: "+root.current_sort.title()+(' Reversed' if app.sort_reverse else '')
    MenuButton:
        text: "Shuffle"
        on_release: root.sort('shuffle')
    MenuButton:
        text: "Name"
        on_release: root.sort('name')
    MenuButton:
        text: "Song Amount"
        on_release: root.sort('song amount')
    WideButton:
        text: "Sort Reverse" if root.sort_reverse else "Sort Forward"
        on_release: root.sort_reverse = not root.sort_reverse

<SortDatabasePlaylistDropDown>:
    auto_width: False
    size_hint_x: 1
    NormalLabel:
        text: "Current Sort Mode: "+root.current_sort.title()+(' Reversed' if app.sort_reverse else '')
    MenuButton:
        text: "Original"
        on_release: root.sort('original')
    MenuButton:
        text: "Shuffle"
        on_release: root.sort('shuffle')
    MenuButton:
        text: "Title"
        on_release: root.sort('name')
    MenuButton:
        text: "Track"
        on_release: root.sort('track')
    MenuButton:
        text: "Album"
        on_release: root.sort('album')
    MenuButton:
        text: "Artist"
        on_release: root.sort('artist')
    MenuButton:
        text: "Length"
        on_release: root.sort('length')
    WideButton:
        text: "Sort Reverse" if root.sort_reverse else "Sort Forward"
        on_release: root.sort_reverse = not root.sort_reverse

<WidgetListBrowse>:
    swipe_mode: 'none'
    bypass_swipes: True

<WidgetListBrowseQueue>:
    swipe_mode: 'none'
    bypass_swipes: True
    cols: 1

<WidgetListQueue>:
    scale: 0.66 if self.blocked else 1
    button_scale: app.button_scale * self.scale
    text_scale: app.text_scale * self.scale
    canvas.before:
        Color:
            rgba: app.theme.selected if root.edit_mode else app.theme.button_up
        BorderImage:
            display_border: [app.display_border, app.display_border, app.display_border, app.display_border]
            size: root.width, root.height
            pos: root.pos
            source: 'data/buttonflat.png'
    cols: 1
    BoxLayout:
        RecycleView:
            id: rvview
            scroll_distance: 10
            scroll_timeout: 400
            bar_width: 0
            bar_margin: 0
            scroll_type: ['content']
            bar_color: 0, 0, 0, 0
            bar_inactive_color: 0, 0, 0, 0
            data: root.queue_modified
            viewclass: 'SongPlaylistElement'
            SelectableRecycleGridLayout2:
                padding: self.spacing[0], 0, self.spacing[0], 0
                spacing: root.button_scale / 8
                multiselect: True if root.edit_mode else False
                id: rvlayout
                cols: 1
                default_size: None, root.button_scale
                default_size_hint: 1, None
                size_hint_y: None
                height: self.minimum_height
                on_click_node: root.click_node(self.selected)
                on_long_click_node: root.toggle_edit_mode(self.long_click)
        CustomScrollbar:
            show_selected_point: True
            selected_point: root.queue_index / (len(root.queue) - 1) if len(root.queue) > 1 else 0
            bar_width: root.button_scale
            scroller: rvview
    ScreenManager:
        current: '' if not self.has_screen('normal') else 'select' if root.edit_mode else 'normal'
        size_hint_y: None
        height: (root.button_scale * 2) if self.current == 'select' else root.button_scale
        transition: SlideTransition(direction='down')
        Screen:
            name: 'normal'
            BoxLayout:
                WideButton:
                    font_size: root.text_scale
                    size_hint_y: 1
                    text: 'Undo'
                    on_release: root.player.queue_undo()
                    disabled: not root.queue_history
                NormalLabel:
                    font_size: root.text_scale
                    size_hint_y: 1
                    size_hint_x: 2
                    text: str(len(root.queue))+' Songs ('+root.queue_duration_formatted+')'
                WideButton:
                    font_size: root.text_scale
                    disabled: not root.queue
                    size_hint_y: 1
                    text: 'Edit'
                    on_release: root.edit_mode = True
        Screen:
            name: 'select'
            GridLayout:
                rows: 2
                BoxLayout:
                    ImageButton:
                        disabled: not rvlayout.selects
                        size_hint: 0.5, 1
                        width: self.height
                        image_padding: [root.button_scale / 8]*4
                        source: 'data/up.png'
                        on_release: root.move_selected_up()
                    ImageButton:
                        disabled: not rvlayout.selects
                        size_hint: 0.5, 1
                        width: self.height
                        image_padding: [root.button_scale / 8]*4
                        source: 'data/down.png'
                        on_release: root.move_selected_down()
                    WideButton:
                        font_size: root.text_scale
                        size_hint_y: 1
                        text: "Deselect" if rvlayout.selects else "Select All"
                        on_release: rvlayout.toggle_select()
                    WideMenuStarter:
                        font_size: root.text_scale
                        size_hint_y: 1
                        text: 'Sort'
                        on_release: root.sort_menu_open(self)
                    WideButton:
                        font_size: root.text_scale
                        disabled: not rvlayout.selects
                        size_hint_y: 1
                        text: "Delete"
                        on_release: root.delete_selected()
                BoxLayout:
                    WideButton:
                        font_size: root.text_scale
                        size_hint_y: 1
                        text: 'Undo'
                        on_release: root.player.queue_undo()
                        disabled: not root.queue_history
                    WideMenuStarter:
                        font_size: root.text_scale
                        size_hint_y: 1
                        size_hint_x: 2
                        text: 'Add To'
                        disabled: not root.queue
                        on_release: root.queue_menu_open(self)
                        width: self.texture_size[0] + (root.button_scale * 1.1)
                    WideButton:
                        font_size: root.text_scale
                        size_hint_y: 1
                        text: "Done"
                        on_release: root.edit_mode = False

<WidgetBrowseDatabase>:
    swipe_mode: 'none'
    bypass_swipes: True
    cols: 1

<WidgetDatabase>:
    scale: 0.66 if self.blocked else 1
    button_scale: app.button_scale * self.scale
    text_scale: app.text_scale * self.scale
    canvas.before:
        Color:
            rgba: app.theme.selected if root.edit_mode else app.theme.button_up
        BorderImage:
            display_border: [app.display_border, app.display_border, app.display_border, app.display_border]
            size: root.width, root.height
            pos: root.pos
            source: 'data/buttonflat.png'
    cols: 1
    padding: 0, root.button_scale / 8
    BoxLayout:
        size_hint_y: None
        height: root.button_scale
        ImageButton:
            size_hint: None, 1
            width: self.height
            source: 'data/left.png'
            disabled: not root.data_levels
            on_release: root.go_up()
        TickerLabel:
            font_size: root.text_scale
            size_hint_y: 1
            text: "  "+root.database_levels+("  ("+str(len(root.data))+" items)" if (root.data_mode != 'category' and root.data) else '')
        NormalButton:
            font_size: root.text_scale
            hidden: not bool(rvlayout.selected)
            size_hint_y: 1
            text: '' if self.hidden else 'Deselect'
            size_hint_x: 0.001 if self.hidden else None
            opacity: 0 if self.hidden else 1
            disabled: self.hidden
            on_release: rvlayout.deselect_all()
        NormalMenuStarter:
            font_size: root.text_scale
            size_hint_y: 1
            text: 'Add To'
            disabled: not root.allow_queue or not root.data
            on_release: root.queue_menu_open(self)
            width: self.texture_size[0] + (root.button_scale * 1.1)
    BoxLayout:
        size_hint_y: None
        height: self.minimum_height
        Widget:
        NormalButton:
            font_size: root.text_scale
            hidden: not root.allow_edit_cache
            text: '' if self.hidden else 'Clean Cache'
            height: 0 if self.hidden else root.button_scale
            size_hint_x: 0.001 if self.hidden else None
            opacity: 0 if self.hidden else 1
            disabled: self.hidden
            on_release: root.clean_cache(total=False)
        NormalButton:
            font_size: root.text_scale
            hidden: not root.allow_edit_cache
            text: '' if self.hidden else 'Clear Cache'
            height: 0 if self.hidden else root.button_scale
            size_hint_x: 0.001 if self.hidden else None
            opacity: 0 if self.hidden else 1
            disabled: self.hidden
            on_release: root.clean_cache(total=True)
        NormalButton:
            font_size: root.text_scale
            hidden: not root.allow_cache
            text: '' if self.hidden else 'Cache Files'
            height: 0 if self.hidden else root.button_scale
            size_hint_x: 0.001 if self.hidden else None
            opacity: 0 if self.hidden else 1
            disabled: self.hidden
            on_release: root.cache()
        NormalButton:
            font_size: root.text_scale
            hidden: not root.allow_add_playlist
            text: '' if self.hidden else 'New Playlist'
            height: 0 if self.hidden else root.button_scale
            size_hint_x: 0.001 if self.hidden else None
            opacity: 0 if self.hidden else 1
            disabled: self.hidden
            on_release: root.add_playlist()
        NormalButton:
            font_size: root.text_scale
            hidden: not root.allow_rename_playlist
            text: '' if self.hidden else 'Rename Playlist'
            height: 0 if self.hidden else root.button_scale
            size_hint_x: 0.001 if self.hidden else None
            opacity: 0 if self.hidden else 1
            disabled: self.hidden
            on_release: root.rename_playlist()
    BoxLayout:
        padding: root.button_scale / 8
        hidden: not root.can_alphaselect
        size_hint_y: None
        height: 0 if self.hidden else root.button_scale
        disabled: self.hidden
        opacity: 0 if self.hidden else 1
        AlphabetSelect:
            id: alphaSelect
            scrollview: rvview
    BoxLayout:
        RecycleView:
            id: rvview
            owner: root
            do_scroll_x: False
            on_scroll_y: root.scroll_database(self.scroll_y)
            scroll_type: ['content']
            bar_color: 0, 0, 0, 0
            bar_width: 0
            bar_inactive_color: 0, 0, 0, 0
            scroll_distance: 10
            scroll_timeout: 400
            data: root.data
            key_viewclass: 'widget'
            SelectableRecycleGridLayout2:
                padding: self.spacing[0], 0, self.spacing[0], 0
                spacing: root.button_scale / 8
                id: rvlayout
                cols: 1
                multiselect: True if root.select_mode == 'song' else False
                default_size: None, root.button_scale
                default_size_hint: 1, None
                size_hint_y: None
                height: self.minimum_height
                on_click_node: root.click_node(self.selected)
                on_long_click_node: root.toggle_edit_mode()
        CustomScrollbar:
            bar_width: root.button_scale
            scroller: rvview
    ScreenManager:
        current: '' if not self.has_screen('normal') else 'select' if root.edit_mode else 'normal'
        size_hint_y: None
        height: root.button_scale
        transition: SlideTransition(direction='down')
        Screen:
            name: 'normal'
            BoxLayout:
                size_hint_y: None
                height: root.button_scale
                NormalInput:
                    canvas.after:
                        Color:
                            rgba: [0, 0, 0, 0] if (root.allow_search and root.use_search) else app.theme.active[:3]+[0.4]
                        Rectangle:
                            size: self.size
                            pos: self.pos
                    font_size: root.text_scale
                    size_hint_y: 1
                    size_hint_x: 1
                    write_tab: False
                    multiline: False
                    hint_text: 'Filter By...'
                    text: root.search_text
                    on_focus: root.set_search(self.focus, self.text)
                NormalToggle:
                    font_size: root.text_scale
                    size_hint_y: 1
                    text: '  Filter  ' if self.state == 'down' else 'No Filter'
                    state: 'down' if root.use_search else 'normal'
                    on_release: root.set_use_search(True if self.state == 'down' else False)
                    disabled: not root.allow_search
                NormalMenuStarter:
                    font_size: root.text_scale
                    size_hint_y: 1
                    text: 'Sort'
                    disabled: not root.allow_sort
                    on_release: root.sort_menu_open(self)
                    width: self.texture_size[0] + (root.button_scale * 1.2)
                NormalButton:
                    font_size: root.text_scale
                    disabled: not root.allow_edit
                    opacity: 0 if self.disabled else 1
                    width: 0 if self.disabled else self.texture_size[0] + root.button_scale
                    size_hint_y: 1
                    text: 'Edit'
                    on_release: root.toggle_edit_mode()
        Screen:
            name: 'select'
            BoxLayout:
                ImageButton:
                    disabled: not root.queue
                    size_hint: None, 1
                    width: self.height
                    image_padding: [root.button_scale / 8]*4
                    source: 'data/up.png'
                    on_release: root.move_selected_up()
                ImageButton:
                    disabled: not root.queue
                    size_hint: None, 1
                    width: self.height
                    image_padding: [root.button_scale / 8]*4
                    source: 'data/down.png'
                    on_release: root.move_selected_down()
                WideButton:
                    font_size: root.text_scale
                    disabled: not root.queue
                    size_hint_y: 1
                    text: "Delete"
                    on_release: root.delete_selected()
                WideButton:
                    font_size: root.text_scale
                    disabled: not root.queue
                    size_hint_y: 1
                    text: "Deselect" if rvlayout.selects else "Select All"
                    on_release: rvlayout.toggle_select()
                WideButton:
                    font_size: root.text_scale
                    size_hint_y: 1
                    text: "Done"
                    on_release: root.toggle_edit_mode()

<PlaylistElement>:
    canvas.before:
        Color:
            rgba: app.theme.selected[:3]+[0.333] if root.selected else app.theme.background
        BorderImage:
            display_border: [app.display_border, app.display_border, app.display_border, app.display_border]
            size: root.width, root.height
            pos: root.pos
            source: 'data/buttonflat.png'
    canvas.after:
        Color:
            rgba: app.theme.text[:3]+[0.33]
        Line:
            rounded_rectangle: self.x, self.y, self.width, self.height, 5
            width: 1

<BasicPlaylistElement>:
    canvas.after:
        Color:
            rgba: app.theme.text[:3]+[0.33]
        Line:
            rounded_rectangle: self.x, self.y, self.width, self.height, 5
            width: 1
    ElementLabel:
        h_divisor: 1
        text: root.name

<SongPlaylistElement>:
    canvas.after:
        Color:
            rgba: app.theme.text[:3]+[0.33]
        Line:
            rounded_rectangle: self.x, self.y, self.width, self.height, 5
            width: 1
    orientation: 'horizontal'
    padding: 0, 0, 0, 0
    RelativeLayout:
        BoxLayout:
            orientation: 'vertical'
            ElementLabel:
                h_divisor: 1
                font_size: self.scale * .75
                text: root.artist+" - "+root.title
            LeftNormalLabel:
                size_hint_y: 1
                scale: min(self.height, self.width / 8)
                padding: self.scale / 8
                font_size: self.scale / 2
                text: "  #"+str(root.track)+", "+root.album
        BoxLayout:
            canvas.before:
                Color:
                    rgba: app.theme.button_up
                Rectangle:
                    size: self.size
                    pos: self.pos
            id: ratingHolder
            size_hint_y: 1 if root.show_ratings else 0.001
            opacity: 1 if root.show_ratings else 0
            disabled: not root.show_ratings
            orientation: 'horizontal'
            Widget:
            ElementFavorite:
                element_type: 'song'
                size_hint_x: None
                width: min(ratingHolder.height, ratingHolder.width / 6)
                song_id: root.id
                song_favorite: root.starred
                player: app.player
            ElementRating:
                element_type: 'song'
                player: app.player
                song_id: root.id
                size_hint_x: None
                width: min(ratingHolder.height * 5, ratingHolder.width / 1.2)
                rating: root.userRating
    ButtonBase:
        canvas.after:
            Color:
                rgba: self.background_color
            BorderImage:
                display_border: [app.display_border, app.display_border, app.display_border, app.display_border]
                border: self.border
                pos: self.pos
                size: self.size
                source: self.disabled_image if self.disabled else self.state_image
            Color:
                rgb: app.theme.button_toggle_true if root.starred else app.theme.button_disabled
            Rectangle:
                size: self.height / 2, self.height / 2
                pos: self.x + (self.height / 2) - (self.width / 2), self.y + self.height / 2
                source: 'data/heart.png'
            Color:
                rgb: app.theme.button_toggle_true if root.userRating > 0 else app.theme.button_disabled
            Rectangle:
                size: self.height / 2, self.height / 2
                pos: self.x + self.width - (self.height / 2), self.y
                source: 'data/star.png'
            Color:
                rgb: app.theme.button_toggle_true if root.userRating > 0 else app.theme.button_disabled
            Rectangle:
                texture: self.texture
                size: self.texture_size
                pos: int(self.center_x - self.texture_size[0] / 2.) - self.width / 4, int(self.center_y - self.texture_size[1] / 2.) - self.height / 4
        text: str(root.userRating)
        color: app.theme.button_toggle_true if root.userRating > 0 else app.theme.button_disabled
        background_normal: 'data/buttonflat.png'
        background_down: 'data/buttonflat.png'
        size_hint_y: 1
        size_hint_x: None
        width: self.height * .75
        on_release: root.show_ratings = not root.show_ratings

<AlbumPlaylistElement>:
    canvas.after:
        Color:
            rgba: app.theme.text[:3]+[0.33]
        Line:
            rounded_rectangle: self.x, self.y, self.width, self.height, 5
            width: 1
    RelativeLayout:
        BoxLayout:
            orientation: 'vertical'
            BoxLayout:
                ElementLabel:
                    h_divisor: 1
                    font_size: self.scale * .75
                    text: root.name
                ShortLabel:
                    size_hint_y: 1
                    font_size: self.height / 2
                    text: str(root.songCount)+' '+('songs' if root.songCount != 1 else 'song')
            ElementLabel:
                h_divisor: 1
                font_size: self.scale * .75
                text: root.artist
        BoxLayout:
            canvas.before:
                Color:
                    rgba: app.theme.background
                Rectangle:
                    size: self.size
                    pos: self.pos
            id: ratingHolder
            size_hint_y: 1 if root.show_ratings else 0.001
            opacity: 1 if root.show_ratings else 0
            disabled: not root.show_ratings
            orientation: 'horizontal'
            ElementFavorite:
                element_type: 'album'
                size_hint_x: None
                width: min(ratingHolder.height, ratingHolder.width / 6)
                song_id: root.id
                song_favorite: root.starred
                player: app.player
            Widget:
            ElementRating:
                element_type: 'album'
                player: app.player
                song_id: root.id
                size_hint_x: None
                width: min(ratingHolder.height * 5, ratingHolder.width / 1.2)
                rating: root.userRating
    ButtonBase:
        canvas.after:
            Color:
                rgba: self.background_color
            BorderImage:
                display_border: [app.display_border, app.display_border, app.display_border, app.display_border]
                border: self.border
                pos: self.pos
                size: self.size
                source: self.disabled_image if self.disabled else self.state_image
            Color:
                rgb: app.theme.button_toggle_true if root.starred else app.theme.button_disabled
            Rectangle:
                size: self.height / 2, self.height / 2
                pos: self.x + (self.height / 2) - (self.width / 2), self.y + self.height / 2
                source: 'data/heart.png'
            Color:
                rgb: app.theme.button_toggle_true if root.userRating > 0 else app.theme.button_disabled
            Rectangle:
                size: self.height / 2, self.height / 2
                pos: self.x + self.width - (self.height / 2), self.y
                source: 'data/star.png'
            Color:
                rgb: app.theme.button_toggle_true if root.userRating > 0 else app.theme.button_disabled
            Rectangle:
                texture: self.texture
                size: self.texture_size
                pos: int(self.center_x - self.texture_size[0] / 2.) - self.width / 4, int(self.center_y - self.texture_size[1] / 2.) - self.height / 4
        text: str(root.userRating)
        color: app.theme.button_toggle_true if root.userRating > 0 else app.theme.button_disabled
        background_normal: 'data/buttonflat.png'
        background_down: 'data/buttonflat.png'
        size_hint_y: 1
        size_hint_x: None
        width: self.height * .75
        on_release: root.show_ratings = not root.show_ratings

<SongCacheElement>:
    canvas.after:
        Color:
            rgba: app.theme.text[:3]+[0.33]
        Line:
            rounded_rectangle: self.x, self.y, self.width, self.height, 5
            width: 1
    cols: 3
    ButtonBase:
        background_normal: 'data/buttonflat.png'
        background_down: 'data/buttonflat.png'
        size_hint_y: 1
        size_hint_x: None
        width: self.height * 0.75
        text: 'X'
        font_size: root.height / 3
        warn: True
        on_release: root.remove()
    GridLayout:
        cols: 1
        ElementLabel:
            h_divisor: 1
            font_size: self.scale * .75
            text: root.artist+' - '+root.title
        ElementLabel:
            text: root.id
            h_divisor: 1
            font_size: self.scale * .5

<PlaylistPlaylistElement>:
    canvas.after:
        Color:
            rgba: app.theme.text[:3]+[0.33]
        Line:
            rounded_rectangle: self.x, self.y, self.width, self.height, 5
            width: 1
    cols: 3
    ButtonBase:
        background_normal: 'data/buttonflat.png'
        background_down: 'data/buttonflat.png'
        size_hint_y: 1
        size_hint_x: None
        width: self.height * 0.75
        text: 'X'
        font_size: root.height / 3
        warn: True
        on_release: root.remove()
    ElementLabel:
        h_divisor: 1
        text: root.name
    BoxLayout:
        orientation: 'vertical'
        size_hint_x: None
        width: max(songslabel.width, lengthlabel.width)
        NormalLabel:
            id: songslabel
            size_hint_y: 1
            font_size: self.height / 2
            text: str(root.songCount)+' '+('songs' if root.songCount != 1 else 'song')
            width: self.texture_size[0]+10
        NormalLabel:
            id: lengthlabel
            size_hint_y: 1
            font_size: self.height / 2
            text: root.timecode(root.duration)
            width: self.texture_size[0]+10

<GenrePlaylistElement>:
    canvas.after:
        Color:
            rgba: app.theme.text[:3]+[0.33]
        Line:
            rounded_rectangle: self.x, self.y, self.width, self.height, 5
            width: 1
    cols: 2
    ElementLabel:
        h_divisor: 1
        text: root.name
    ShortLabel:
        size_hint_y: 1
        font_size: self.height / 4
        text: str(root.songCount)+' '+('songs' if root.songCount != 1 else 'song')

<ArtistPlaylistElement>:
    canvas.after:
        Color:
            rgba: app.theme.text[:3]+[0.33]
        Line:
            rounded_rectangle: self.x, self.y, self.width, self.height, 5
            width: 1
    cols: 2
    ElementLabel:
        h_divisor: 1
        text: root.name
    ShortLabel:
        size_hint_y: 1
        font_size: self.height / 4
        text: str(root.albumCount)+' '+('albums' if root.albumCount != 1 else 'album')

""")


class MenuSelect(MenuButton):
    data = ObjectProperty(allownone=True)
    function = ObjectProperty()

    def on_release(self, *_):
        self.function(self.data)


class AddToDropDown(NormalDropDown):
    owner = ObjectProperty()
    player = ObjectProperty()
    playlist_menu = None
    queue_mode_menu = None

    def select_queue_mode(self, mode):
        app = App.get_running_app()
        app.queue_mode = mode
        if self.queue_mode_menu:
            self.queue_mode_menu.dismiss()
            self.queue_mode_menu = None

    def open_queue_mode_menu(self, button):
        app = App.get_running_app()
        if self.queue_mode_menu:
            self.queue_mode_menu.dismiss()
            self.queue_mode_menu = None
        self.queue_mode_menu = NormalDropDown(auto_width=False, size_hint_x=1)
        modes = app.queue_mode_names.keys()
        for mode in modes:
            menu_button = MenuSelect(function=self.select_queue_mode, data=mode, text=app.queue_mode_names[mode])
            self.queue_mode_menu.add_widget(menu_button)
        self.queue_mode_menu.open(button)

    def select_playlist(self, playlist):
        app = App.get_running_app()
        app.last_playlist_id = playlist['id']
        app.last_playlist_name = playlist['name']
        if self.playlist_menu:
            self.playlist_menu.dismiss()
            self.playlist_menu = None

    def open_playlists_menu(self, button):
        if self.playlist_menu:
            self.playlist_menu.dismiss()
            self.playlist_menu = None
        self.playlist_menu = NormalDropDown(auto_width=False, size_hint_x=1)
        playlists = self.player.get_playlists()
        for playlist in playlists:
            menu_button = MenuSelect(function=self.select_playlist, data=playlist, text=playlist['name'])
            self.playlist_menu.add_widget(menu_button)
        self.playlist_menu.open(button)

    def queue_add(self):
        self.dismiss()
        app = App.get_running_app()
        queue_mode = app.queue_mode
        self.owner.queue(queue_mode)

    def playlist_add(self):
        self.dismiss()
        app = App.get_running_app()
        playlist_id = app.last_playlist_id
        if not playlist_id:
            return
        self.owner.add_to_playlist(playlist_id)


class AddToPlaylistDropDown(NormalDropDown):
    owner = ObjectProperty()
    player = ObjectProperty()
    playlist_menu = None

    def select_playlist(self, playlist):
        app = App.get_running_app()
        app.last_playlist_id = playlist['id']
        app.last_playlist_name = playlist['name']
        if self.playlist_menu:
            self.playlist_menu.dismiss()
            self.playlist_menu = None

    def open_playlists_menu(self, button):
        if self.playlist_menu:
            self.playlist_menu.dismiss()
            self.playlist_menu = None
        self.playlist_menu = NormalDropDown(auto_width=False, size_hint_x=1)
        playlists = self.player.get_playlists()
        for playlist in playlists:
            menu_button = MenuSelect(function=self.select_playlist, data=playlist, text=playlist['name'])
            self.playlist_menu.add_widget(menu_button)
        self.playlist_menu.open(button)

    def playlist_add_current(self):
        self.dismiss()
        app = App.get_running_app()
        playlist_id = app.last_playlist_id
        if not playlist_id:
            return
        self.owner.add_to_playlist(playlist_id, selected=True)

    def playlist_add_all(self):
        self.dismiss()
        app = App.get_running_app()
        playlist_id = app.last_playlist_id
        if not playlist_id:
            return
        self.owner.add_to_playlist(playlist_id, selected=False)


class SortDropDown(NormalDropDown):
    owner = ObjectProperty()

    def sort(self, mode):
        self.owner.sort(mode)
        self.dismiss()


class SortDatabaseDropDown(NormalDropDown):
    owner = ObjectProperty()
    current_sort = StringProperty()
    sort_reverse = BooleanProperty(False)

    def sort(self, mode):
        self.owner.set_sort(mode, self.sort_reverse)
        self.dismiss()


class SortDatabaseSongDropDown(SortDatabaseDropDown):
    pass


class SortDatabaseArtistDropDown(SortDatabaseDropDown):
    pass


class SortDatabaseOtherDropDown(SortDatabaseDropDown):
    pass


class SortDatabasePlaylistDropDown(SortDatabaseDropDown):
    pass


class SelectableRecycleGridLayout2(SelectableRecycleLayout, RecycleGridLayout):
    long_click = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_event_type('on_long_click_node')

    def refresh_selects(self):
        self.selects = []
        data = self.parent.data
        for node in data:
            if node['selected']:
                self.selects.append(node)

    def long_click_node(self, node):
        self.long_click = node.data
        self.dispatch('on_long_click_node', node)

    def on_long_click_node(self, *_):
        pass


class PlaylistElement(RecycleItem, BoxLayout):
    id = StringProperty()
    touch_timer = None

    def long_press(self, *_):
        if self.parent:
            self.parent.long_click_node(self)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if not self.selectable:
                return super().on_touch_down(touch)
            if self.touch_timer:
                self.touch_timer.cancel()
            self.touch_timer = Clock.schedule_once(self.long_press, 1)
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.touch_timer:
            self.touch_timer.cancel()
        if touch.grab_current == self:
            if self.collide_point(*touch.pos):
                touch.ungrab(self)
                if time.time() - touch.time_start >= 1:
                    return True
                if touch.button == 'right':
                    self.parent.long_click_node(self)
                    return True
                self.parent.click_node(self)
                if 'shift' in Window.modifiers:
                    self.parent.select_range(self.index, touch)
                return True


class BasicPlaylistElement(PlaylistElement):
    name = StringProperty()
    owner = ObjectProperty()


class SongPlaylistElement(PlaylistElement):
    title = StringProperty()
    album = StringProperty()
    artist = StringProperty()
    track = NumericProperty()
    year = NumericProperty()
    genre = StringProperty()
    duration = NumericProperty()
    playCount = NumericProperty()
    discNumber = NumericProperty()
    starred = BooleanProperty()
    userRating = NumericProperty()
    show_ratings = BooleanProperty(False)

    def refresh_view_attrs(self, rv, index, data):
        self.show_ratings = False
        return super().refresh_view_attrs(rv, index, data)


class AlbumPlaylistElement(PlaylistElement):
    name = StringProperty()
    artist = StringProperty()
    year = NumericProperty()
    genre = StringProperty()
    starred = BooleanProperty()
    duration = NumericProperty()
    playCount = NumericProperty()
    userRating = NumericProperty()
    songCount = NumericProperty()
    show_ratings = BooleanProperty(False)

    def refresh_view_attrs(self, rv, index, data):
        self.show_ratings = False
        return super().refresh_view_attrs(rv, index, data)


class GenrePlaylistElement(PlaylistElement):
    name = StringProperty()
    songCount = NumericProperty()
    albumCount = NumericProperty()


class SongCacheElement(PlaylistElement):
    title = StringProperty()
    album = StringProperty()
    artist = StringProperty()

    def delete(self):
        self.owner.delete_element(data=self.data)

    def remove_finish(self, *_):
        self.animation = None
        self.opacity = self.o_opacity
        self.pos = self.o_pos
        self.delete()


class PlaylistPlaylistElement(PlaylistElement):
    name = StringProperty()
    duration = NumericProperty()
    songCount = NumericProperty()

    def delete(self):
        self.owner.delete_element(data=self.data)

    def remove_finish(self, *_):
        self.animation = None
        self.opacity = self.o_opacity
        self.pos = self.o_pos
        self.delete()

    def timecode(self, seconds):
        all_minutes, final_seconds = divmod(seconds, 60)
        all_hours, final_minutes = divmod(all_minutes, 60)
        time_text = str(int(final_minutes)).zfill(2)+':'+str(int(final_seconds)).zfill(2)
        if all_hours > 0:
            time_text = str(int(all_hours))+':'+time_text
        return time_text


class ArtistPlaylistElement(PlaylistElement):
    name = StringProperty()
    albumCount = NumericProperty()


class WidgetListBrowse(ElementWidget):
    scale = NumericProperty(1)
    blocked = BooleanProperty(False)


class WidgetOpener(ElementWidget):
    show_queue = BooleanProperty(False)
    close_text = 'Close'
    open_text = 'Open'

    def get_item_to_open(self):
        return ElementWidget()

    def open_queue(self):
        pass

    def on_size(self, *_):
        if self.height < self.screen.height / 4:
            self.show_queue = False
        else:
            self.show_queue = True

    def on_show_queue(self, *_):
        self.load()

    def on_player(self, *_):
        self.load()

    def load(self):
        if not self.player:
            return
        self.clear_widgets()
        if self.show_queue:
            queue = self.get_item_to_open()
            queue.blocked = self.blocked
            self.add_widget(queue)
            queue.player = self.player
        else:
            button = WidgetOpenerButton(owner=self, text=self.open_text)
            self.add_widget(button)


class WidgetOpenerButton(ElementButton):
    owner = ObjectProperty()

    def on_release(self, *_):
        self.owner.open_queue()


class WidgetBrowseDatabase(WidgetOpener):
    widget_type = StringProperty('BrowseDatabaseOpener')
    open_text = 'Open Database'

    def go_up(self):
        if self.show_queue:
            return self.children[0].go_up()
        return False

    def open_queue(self):
        app = App.get_running_app()
        app.open_database_popup()

    def get_item_to_open(self):
        return WidgetDatabase()


class WidgetDatabase(WidgetListBrowse):
    widget_type = StringProperty('BrowseDatabase')
    data = ListProperty()
    data_unfiltered = ListProperty()
    data_levels = ListProperty()
    queue_type = StringProperty()
    queue_id = StringProperty()
    data_mode = StringProperty()  #may be category, song, album, artist, genre, playlist, playlistsong, cache
    select_mode = StringProperty('normal')  #Determines what happens on clicking node, queueing, and some of the interface elements being usable
    search_text = StringProperty()
    use_search = BooleanProperty(True)
    allow_search = BooleanProperty(False)  #Enable search box in interface
    allow_sort = BooleanProperty(False)  #Enable sort menu in interface
    allow_queue = BooleanProperty(False)  #Enable queue menu in interface
    allow_filter = BooleanProperty(False)  #Enables filtering function
    data_levels_names = ListProperty()
    database_levels = StringProperty()
    queue_changed = BooleanProperty(False)
    allow_cache = BooleanProperty(False)
    allow_add_playlist = BooleanProperty(False)
    allow_rename_playlist = BooleanProperty(False)
    allow_edit_cache = BooleanProperty(False)
    can_alphaselect = BooleanProperty(False)
    edit_mode = BooleanProperty(False)
    allow_edit = BooleanProperty(False)
    playlist_changed = StringProperty()
    to_select = []

    def cache(self):
        App.get_running_app().add_blocking_thread('Cache Songs', self.cache_process)

    def cache_process(self, timeout):
        songs = self.get_songs(timeout)
        if songs is not True and songs is not False:
            app = App.get_running_app()
            app.cache_songs(songs[0])
        return True

    def clean_cache(self, total):
        app = App.get_running_app()
        app.clean_cache(total=total)

    @mainthread
    def set_variable(self, variable_name, value):
        setattr(self, variable_name, value)

    def to_select_activate(self):
        for index, item in enumerate(self.data):
            if index in self.to_select:
                item['selected'] = True
            else:
                item['selected'] = False
        self.to_select = []

    def toggle_edit_mode(self):
        if self.allow_edit:
            self.edit_mode = not self.edit_mode
        self.filter_database()
        self.sort_database()

    def move_selected(self, moveby):
        app = App.get_running_app()
        playlistid = self.data_levels[-1]
        playlist = self.data_unfiltered.copy()
        selected = self.get_selected()
        playlist, index, moved = self.player.move_indexes(playlist, selected, moveby, 0)
        new_ids = []
        self.to_select = moved
        remove_indexes = list(range(0, len(playlist)))
        for song in playlist:
            new_ids.append(song['id'])
        timeout = 3
        max_retries = 5
        retries = 0
        while retries <= max_retries:
            completed = self.player.playlist_add_songs(playlistid, new_ids, timeout, check_dup=False, message=False)
            if completed:
                break
            retries += 1
            timeout += 1
        if completed is None:
            app.message('Unable to reposition songs')
            return
        timeout = 3
        max_retries = 5
        retries = 0
        while retries <= max_retries:
            completed = self.player.playlist_remove_song(playlistid, remove_indexes, timeout, message=False)
            if completed:
                break
            retries += 1
            timeout += 1
        self.player.playlist_changed = playlistid
        if completed:
            app.message('Moved songs in playlist')
        else:
            app.message("Unable to reposition songs, playlist may be damaged!")

    def move_selected_up(self):
        app = App.get_running_app()
        app.add_blocking_thread_single("Move Playlist Songs", self.move_selected, args=(-1, ))

    def move_selected_down(self):
        app = App.get_running_app()
        app.add_blocking_thread_single("Move Playlist Songs", self.move_selected, args=(1, ))

    def delete_selected(self):
        selected = self.get_selected()
        self.delete_element(data=None, index=selected)

    def get_selected(self):
        indexes = []
        rvview = self.ids.rvview
        for item in rvview.data:
            if item['selected']:
                indexes.append(item['index'])
        return indexes

    def scroll_database(self, scroll_per):
        alpha_select = self.ids.alphaSelect
        alpha_select.scroll_to_per(scroll_per)

    @mainthread
    def set_can_alphaselect(self, can_alphaselect):
        if can_alphaselect and len(self.data) > 100:
            self.can_alphaselect = True
        else:
            self.can_alphaselect = False
            self.ids.alphaSelect.scroll_to_element(0, instant=True)

    def rename_playlist(self):
        app = App.get_running_app()

        def rename_playlist_confirm(popup_content, answer):
            app.dismiss_popup()
            if answer == 'yes':
                plname = popup_content.input_text.strip()
                old_name, plid = popup_content.data
                if old_name != plname:
                    app.add_blocking_thread('Rename Playlist', self.rename_playlist_process, (plid, plname, ))

        playlistid = self.data_levels[-1]
        current_name = self.data_levels_names[-1]
        content = InputPopupContent(text="Enter Playlist Name:", input_allow_mode='url', input_text=current_name, data=[current_name, playlistid])
        content.bind(on_answer=rename_playlist_confirm)
        app.popup = NormalPopup(title="Rename This Playlist", content=content, size_hint=(0.9, None), height=4*app.button_scale)
        app.popup.open()

    def rename_playlist_process(self, playlistid, playlistname, timeout):
        result = self.player.playlist_rename(playlistid, playlistname, timeout=timeout)
        if result is None:
            return False
        if result:
            self.go_up()
        return True

    def add_playlist(self):
        app = App.get_running_app()

        def add_playlist_confirm(popup_content, answer):
            app.dismiss_popup()
            if answer == 'yes':
                playlist_name = popup_content.input_text.strip()
                app.add_blocking_thread('Create Playlist', self.add_playlist_process, (playlist_name, ))

        content = InputPopupContent(text="Enter Playlist Name:", input_allow_mode='url')
        content.bind(on_answer=add_playlist_confirm)
        app.popup = NormalPopup(title="Create New Playlist", content=content, size_hint=(0.9, None), height=4*app.button_scale)
        app.popup.open()

    def add_playlist_process(self, playlist_name, timeout):
        result = self.player.playlist_create(playlist_name, timeout=timeout)
        if result is None:
            return False
        if result:
            self.update()
        return True

    def delete_element(self, data=None, index=None):
        app = App.get_running_app()

        def delete_element_answer(popup_content, answer):
            app.dismiss_popup()
            if answer == 'yes':
                self.delete_element_confirm(*popup_content.data)

        if self.data_mode == 'playlistsong':
            playlistid = self.data_levels[-1]
            if index is None:
                return
        elif self.data_mode == 'playlist':
            if data is None:
                return
            playlistid = data['id']
        elif self.data_mode == 'cache':
            app.remove_cache_file(data['id'])
            self.update_process()
            return
        else:
            return

        if self.data_mode == 'playlist':
            content = ConfirmPopupContent(text='Remove the playlist "'+data['name']+'"?', yes_text='Remove', no_text='Keep', warn_yes=True, data=[playlistid, index])
            content.bind(on_answer=delete_element_answer)
            app.popup = NormalPopup(title="Remove Playlist?", content=content, size_hint=(0.9, None), height=4*app.button_scale)
            app.popup.open()
        else:
            self.delete_element_confirm(playlistid, index)

    def delete_element_confirm(self, playlistid, index):
        App.get_running_app().add_blocking_thread('Delete Playlist Song', self.delete_element_process, (playlistid, index))

    def delete_element_process(self, playlistid, index, timeout):
        if index is None:
            result = self.player.playlist_remove(playlistid, timeout=timeout)
        else:
            result = self.player.playlist_remove_song(playlistid, index, timeout=timeout)
        if result is None:
            return False
        self.update_process()
        return True

    @mainthread
    def on_data_mode(self, *_):
        #have to split this out because it crashes kivy if its not set in the main thread (in self.update_process)
        self.allow_add_playlist = self.data_mode == 'playlist'
        self.allow_rename_playlist = self.data_mode == 'playlistsong'
        self.allow_edit = self.data_mode == 'playlistsong'

    def set_use_search(self, use_search):
        self.use_search = use_search
        self.refresh_database()

    def refresh_database(self):
        if not self.allow_search or not self.allow_filter:
            self.update()
            return
        if self.use_search:
            self.filter_database()
        else:
            self.data = self.data_unfiltered
        self.sort_database()

    def queue(self, mode):
        App.get_running_app().add_blocking_thread('Queue', self.queue_process, (mode, ))

    def get_songs(self, timeout):
        app = App.get_running_app()
        queue_id = self.queue_id
        max_amount = app.queue_max_amount
        selected_only = app.queue_selected_only
        selected_index = None  #index in the songs to be added that the first selected song is
        #deal with data_mode types: song, album, artist, genre, playlistsong
        if self.data_mode in ['song', 'playlistsong']:
            songs = self.data.copy()
            selected_songs = []
            for index, song in enumerate(songs):
                if song['selected']:
                    if selected_index is None:
                        selected_index = index
                    selected_songs.append(song)
            if selected_only and selected_songs:
                songs = selected_songs
                selected_index = 0
        elif self.data_mode == 'album':
            selected_data = [item for item in self.data if item['selected']]
            if selected_data and selected_only:
                albums = selected_data
            else:
                albums = self.data
            songs = []
            for albumdata in albums:
                albumid = albumdata['id']
                albumsongs = self.player.database_get_song_list_album(albumid, timeout=timeout)
                if albumsongs is None:
                    return False
                songs.extend(albumsongs)
                queue_id = albumid
        elif self.data_mode == 'artist':
            songs = []
            for artist in self.data:
                artistid = artist['id']
                queue_id = artistid
                artistsongs = self.player.database_get_song_list_artist(artistid, timeout=timeout)
                if artistsongs is None:
                    return False
                songs.extend(artistsongs)
        elif self.data_mode == 'genre':
            songs = []
            for genredata in self.data:
                genre = genredata['value']
                queue_id = genre
                genresongs = self.player.database_get_song_list_genre(genre=genre, timeout=timeout)
                if genresongs is None:
                    return False
                songs.extend(genresongs)
        else:
            return True
        if max_amount > 0:
            songs = songs[:max_amount]
        if selected_index is None:
            selected_index = 0
        for song in songs:
            if 'owner' in song.keys():
                del song['owner']
        return songs, queue_id, selected_index

    def queue_process(self, mode, timeout):
        #mode: replace, next, end, start
        app = App.get_running_app()
        play_immediately = app.queue_play_immediately
        queue_type = self.queue_type

        songs, queue_id, selected_index = self.get_songs(timeout)

        self.player.queue_undo_store()
        if not play_immediately and mode != 'replace':
            #keep playing current song
            current_song = self.player.queue_index
            self.player.queue_set(songs, queue_type, queue_id, current_song=current_song, mode=mode)
        else:
            was_playing = self.player.playing
            self.player.stop()
            if mode in ['replace', 'start']:
                current_song = selected_index
            elif mode == 'next':
                if self.player.queue:
                    current_song = selected_index + self.player.queue_index + 1
                else:
                    current_song = selected_index
            else:  #mode == 'end'
                current_song = selected_index + len(self.player.queue)
            self.player.queue_set(songs, queue_type, queue_id, mode=mode, set_index=current_song)
            if play_immediately or was_playing:
                Clock.schedule_once(self.player.play)  #needs to be delayed because song_set is maithread, so hasnt happened yet
        return True

    def add_to_playlist(self, playlist_id):
        #add songs to given playlist id
        App.get_running_app().add_blocking_thread('Add To Playlist', self.add_to_playlist_process, (playlist_id, ))

    def add_to_playlist_process(self, playlist_id, timeout):
        songs, queue_id, selected_index = self.get_songs(timeout)
        songids = []
        if not songs:
            return True
        for song in songs:
            songids.append(song['id'])
        result = self.player.playlist_add_songs(playlist_id, songids, timeout)
        return result

    def set_sort(self, mode, sort_reverse):
        app = App.get_running_app()
        app.sort_reverse = sort_reverse
        if self.data_mode == 'song':
            app.sort_mode_song = mode
        elif self.data_mode == 'artist':
            app.sort_mode_artist = mode
        elif self.data_mode == 'playlistsong':
            app.sort_mode_playlist = mode
        else:
            app.sort_mode_other = mode
        self.sort_database()

    def sort_database(self):
        can_alphaselect = False
        if not self.allow_sort or self.edit_mode:
            self.set_can_alphaselect(can_alphaselect)
            return

        app = App.get_running_app()

        def sort_by_key(key, reverse=False):
            if reverse:
                self.data.sort(key=lambda a: a[key], reverse=not app.sort_reverse)
            else:
                self.data.sort(key=lambda a: a[key], reverse=app.sort_reverse)

        if self.data_mode == 'song':
            sm = app.sort_mode_song
            try:
                if sm == 'shuffle':
                    self.data.sort(key=lambda x: random.random())
                elif sm == 'track':
                    sort_by_key('track')
                elif sm == 'album':
                    self.data.sort(key=itemgetter('album', 'track'), reverse=app.sort_reverse)
                    can_alphaselect = True
                elif sm == 'artist':
                    self.data.sort(key=itemgetter('artist', 'title'), reverse=app.sort_reverse)
                    can_alphaselect = True
                elif sm == 'length':
                    sort_by_key('duration', reverse=True)
                elif sm == 'genre':
                    sort_by_key('genre')
                elif sm == 'plays':
                    sort_by_key('playCount', reverse=True)
                else:
                    sort_by_key('title')
                    can_alphaselect = True
            except:
                sort_by_key('title')
        elif self.data_mode == 'artist':
            sm = app.sort_mode_artist
            try:
                if sm == 'shuffle':
                    self.data.sort(key=lambda x: random.random())
                elif sm == 'album amount':
                    sort_by_key('albumCount', reverse=True)
                elif sm == 'song amount':
                    sort_by_key('songCount', reverse=True)
                else:
                    sort_by_key('name')
                    can_alphaselect = True
            except:
                sort_by_key('name')
        elif self.data_mode == 'playlistsong':
            sm = app.sort_mode_playlist
            try:
                if sm == 'shuffle':
                    self.data.sort(key=lambda x: random.random())
                elif sm == 'name':
                    sort_by_key('title')
                    can_alphaselect = True
                elif sm == 'track':
                    sort_by_key('track')
                elif sm == 'album':
                    self.data.sort(key=itemgetter('album', 'track'), reverse=app.sort_reverse)
                    can_alphaselect = True
                elif sm == 'artist':
                    self.data.sort(key=itemgetter('artist', 'title'), reverse=app.sort_reverse)
                    can_alphaselect = True
                elif sm == 'length':
                    sort_by_key('duration', reverse=True)
                else:
                    self.filter_database()
                    if app.sort_reverse:
                        self.data.reverse()
            except:
                self.filter_database()
                if app.sort_reverse:
                    self.data.reverse()
        else:  #self.data_mode == 'other'
            sm = app.sort_mode_other
            try:
                if sm == 'shuffle':
                    self.data.sort(key=lambda x: random.random())
                elif sm == 'song amount':
                    sort_by_key('songCount', reverse=True)
                else:
                    sort_by_key('name')
                    can_alphaselect = True
            except:
                sort_by_key('name')
        self.set_can_alphaselect(can_alphaselect)

    def queue_menu_open(self, button):
        queue_menu = AddToDropDown(owner=self, player=self.player)
        queue_menu.open(button)

    def sort_menu_open(self, button):
        app = App.get_running_app()
        if self.data_mode == 'song':
            sort_menu = SortDatabaseSongDropDown(owner=self, current_sort=app.sort_mode_song, sort_reverse=app.sort_reverse)
        elif self.data_mode == 'artist':
            sort_menu = SortDatabaseArtistDropDown(owner=self, current_sort=app.sort_mode_artist, sort_reverse=app.sort_reverse)
        elif self.data_mode == 'playlistsong':
            sort_menu = SortDatabasePlaylistDropDown(owner=self, current_sort=app.sort_mode_playlist, sort_reverse=app.sort_reverse)
        else:
            sort_menu = SortDatabaseOtherDropDown(owner=self, current_sort=app.sort_mode_other, sort_reverse=app.sort_reverse)
        sort_menu.open(button)

    def on_player(self, *_):
        self.playlist_changed = ''
        self.player.bind(playlist_changed=self.setter('playlist_changed'))
        self.queue_changed = False
        self.player.bind(queue_changed=self.setter('queue_changed'))
        self.update()

    def on_playlist_changed(self, *_):
        if self.playlist_changed:
            if not self.data_levels:
                return
            if self.data_levels[0] == 'Local Cache':
                self.update()
            elif self.data_levels[-1] == self.playlist_changed or self.data_levels[-1] == 'Playlists':
                self.update()
            self.player.playlist_changed = ''

    def set_search(self, focus, text):
        if not focus:
            self.use_search = True
            self.search_text = text
            self.refresh_database()

    def go_up(self):
        if self.data_levels:
            self.edit_mode = False
            self.data_levels.pop(-1)
            self.data_levels_names.pop(-1)
            self.update()
            return True
        else:
            return False

    def filter_database(self):
        if self.edit_mode:
            self.data = self.data_unfiltered
            return
        search = self.search_text.lower()
        if not search or not self.use_search:
            return
        #update self.data from self.data_unfiltered based on self.search_text
        if self.data_mode == 'genre':
            if search:
                self.allow_queue = True
            else:
                self.allow_queue = False
        if self.data_mode in ['song', 'playlistsong']:
            self.data = [item for item in self.data_unfiltered if (search in item['artist'].lower() or search in item['title'].lower())]
        else:
            self.data = [item for item in self.data_unfiltered if search in item['name'].lower()]

    def on_queue_changed(self, *_):
        self.data = self.player.database_list
        self.data_unfiltered = self.data
        if self.allow_filter and self.use_search:
            self.filter_database()
        self.sort_database()
        self.ids['rvview'].refresh_from_data()

    def reload(self):
        self.update()

    @mainthread
    def update(self):
        app = App.get_running_app()
        rvview = self.ids['rvview']
        rvlayout = self.ids['rvlayout']
        rvlayout.deselect_all()
        rvview.scroll_y = 1
        while app.is_blocking_thread('database update'):
            time.sleep(0.1)
        app.add_blocking_thread('Update Database', self.update_process)

    def update_process(self, timeout=4):
        #Completely refreshes database
        #widget variable types: BasicPlaylistElement, ArtistPlaylistElement, AlbumPlaylistElement, SongPlaylistElement

        def set_mode(data_mode, select_mode='normal'):
            self.data_mode = data_mode
            self.select_mode = select_mode
            if data_mode in ['category', 'cache']:
                if data_mode == 'cache':
                    self.set_variable('allow_edit_cache', True)
                else:
                    self.set_variable('allow_edit_cache', False)
                self.allow_sort = False
                self.allow_search = False
                self.allow_queue = False
                self.allow_filter = False
                self.set_variable('allow_cache', False)
            else:
                self.set_variable('allow_edit_cache', False)
                if data_mode in ['playlist']:
                    self.allow_queue = False
                    self.set_variable('allow_cache', False)
                else:
                    self.allow_queue = True
                    self.set_variable('allow_cache', True)
                self.allow_search = True
                self.allow_sort = True
                self.allow_filter = True

        def categories_list(options):
            category_list = []
            for option in options:
                category_list.append({'id': option, 'name': option, 'owner': self, 'widget': 'BasicPlaylistElement'})
            return category_list

        if self.use_search:
            search_text = self.search_text
        else:
            search_text = ''
        self.data = []
        levels = self.data_levels
        length = len(self.data_levels)
        self.queue_type = ''
        self.queue_id = ''
        data = None
        if not levels:  #Root
            data = categories_list(['Songs', 'Albums', 'Artists', 'Genres', 'Playlists', 'Local Cache'])
            set_mode('category')
        elif levels[0] == 'Songs':
            if length == 1:  #Songs root categories
                data = categories_list(['All Songs', 'Favorites', '5 Star', '4 Star', '3 Star', '2 Star', '1 Star', "Recently Added", "Recently Played", "Most Played"])
                set_mode('category')
            else:
                if levels[1] == "All Songs":
                    data = self.player.database_get_search_song(query=search_text, timeout=timeout)
                    if data is None:
                        return False
                    data = add_to_dict_list(data, [['widget', 'SongPlaylistElement'], ['selectable', True], ['selected', False], ['owner', self]])
                    set_mode('song', 'song')
                    self.queue_type = 'random'
                    self.allow_filter = False
                elif levels[1] == 'Favorites':  #Songs with Favorite rating
                    data = self.player.database_get_song_list_favorite(timeout=timeout)
                    if data is None:
                        return False
                    data = add_to_dict_list(data, [['widget', 'SongPlaylistElement'], ['selectable', True], ['selected', False], ['owner', self]])
                    set_mode('song', 'song')
                    self.queue_type = 'rating'
                    self.queue_id = 'star'
                elif levels[1] == 'Recently Added':
                    data = self.player.database_get_search_song(query=search_text, timeout=timeout)
                    if data is None:
                        return False
                    data = add_to_dict_list(data, [['widget', 'SongPlaylistElement'], ['selectable', True], ['selected', False], ['owner', self]])
                    set_mode('song', 'song')
                    self.allow_filter = False
                    self.allow_sort = False
                    self.allow_search = False
                    self.queue_type = 'random'
                    data = [song for song in data if 'created' in song.keys()]
                    data = sorted(data, key=lambda x: x['created'], reverse=True)[:40]
                elif levels[1] == 'Recently Played':
                    data = self.player.database_get_search_song(query=search_text, timeout=timeout)
                    if data is None:
                        return False
                    data = add_to_dict_list(data, [['widget', 'SongPlaylistElement'], ['selectable', True], ['selected', False], ['owner', self]])
                    set_mode('song', 'song')
                    self.allow_filter = False
                    self.allow_sort = False
                    self.allow_search = False
                    self.queue_type = 'random'
                    data = [song for song in data if 'played' in song.keys()]
                    data = sorted(data, key=lambda x: x['played'], reverse=True)[:40]
                elif levels[1] == 'Most Played':
                    data = self.player.database_get_search_song(query=search_text, timeout=timeout)
                    if data is None:
                        return False
                    data = add_to_dict_list(data, [['widget', 'SongPlaylistElement'], ['selectable', True], ['selected', False], ['owner', self]])
                    set_mode('song', 'song')
                    self.allow_filter = False
                    self.allow_sort = False
                    self.allow_search = False
                    self.queue_type = 'random'
                    data = sorted(data, key=lambda x: x['playCount'], reverse=True)[:40]
                else:  #Songs with star ratings
                    data = self.player.database_get_search_song(query=search_text, timeout=timeout)
                    if data is None:
                        return False
                    data = add_to_dict_list(data, [['widget', 'SongPlaylistElement'], ['selectable', True], ['selected', False], ['owner', self]])
                    set_mode('song', 'song')
                    self.allow_filter = False
                    rating = levels[1][0]
                    rating_int = int(rating)
                    self.queue_type = 'rating'
                    self.queue_id = rating
                    data = [song for song in data if song['userRating'] == rating_int]
        elif levels[0] == 'Albums':
            if length == 1:
                data = categories_list(["All Albums", 'Favorites', '5 Star', '4 Star', '3 Star', '2 Star', '1 Star', "Recently Added", "Recently Played", "Most Played"])
                set_mode('category')
            elif length == 2:
                if levels[1] == "All Albums":
                    data = self.player.database_get_search_album(query=search_text, timeout=timeout)
                    if data is None:
                        return False
                    data = add_to_dict_list(data, [['widget', 'AlbumPlaylistElement'], ['selectable', True], ['selected', False]])
                    set_mode('album')
                    self.allow_filter = False
                    if not search_text:
                        self.allow_queue = False
                elif levels[1] == 'Favorites':
                    data = self.player.database_get_album_list_favorite(timeout=timeout)
                    if data is None:
                        return False
                    data = add_to_dict_list(data, [['widget', 'AlbumPlaylistElement'], ['selectable', True], ['selected', False]])
                    set_mode('album', 'song')
                elif levels[1] == 'Recently Added':
                    data = self.player.database_get_album_list(list_type='newest', size=20, timeout=timeout)
                    if data is None:
                        return False
                    data = add_to_dict_list(data, [['widget', 'AlbumPlaylistElement'], ['selectable', True], ['selected', False]])
                    set_mode('album')
                    self.allow_sort = False
                    self.allow_search = False
                    self.allow_filter = False
                elif levels[1] == 'Recently Played':
                    data = self.player.database_get_album_list(list_type='recent', size=20, timeout=timeout)
                    if data is None:
                        return False
                    data = add_to_dict_list(data, [['widget', 'AlbumPlaylistElement'], ['selectable', True], ['selected', False]])
                    set_mode('album')
                    self.allow_sort = False
                    self.allow_search = False
                    self.allow_filter = False
                elif levels[1] == 'Most Played':
                    data = self.player.database_get_album_list(list_type='frequent', size=20, timeout=timeout)
                    if data is None:
                        return False
                    data = add_to_dict_list(data, [['widget', 'AlbumPlaylistElement'], ['selectable', True], ['selected', False]])
                    set_mode('album')
                    self.allow_sort = False
                    self.allow_search = False
                    self.allow_filter = False
                else:  #Albums with star ratings
                    data = self.player.database_get_search_album(query=search_text, timeout=timeout)
                    if data is None:
                        return False
                    data = add_to_dict_list(data, [['widget', 'AlbumPlaylistElement'], ['selectable', True], ['selected', False]])
                    self.allow_filter = False
                    rating = int(levels[1][0])
                    data = [album for album in data if album['userRating'] == rating]
                    set_mode('album', 'song')
                self.queue_type = 'album'
            else:  #Single album
                albumid = levels[-1]
                data = self.player.database_get_song_list_album(albumid, timeout=timeout)
                if data is None:
                    return False
                data = add_to_dict_list(data, [['widget', 'SongPlaylistElement'], ['selectable', True], ['selected', False], ['owner', self]])
                set_mode('song', 'song')
                self.queue_type = 'album'
                self.queue_id = albumid
        elif levels[0] == 'Artists':
            if length == 1:  #All artists
                data = self.player.database_get_search_artist(query=search_text, timeout=timeout)
                if data is None:
                    return False
                data = add_to_dict_list(data, [['widget', 'ArtistPlaylistElement'], ['selectable', True], ['selected', False]])
                set_mode('artist')
                self.queue_type = 'random'
                self.allow_filter = False
                if not search_text:
                    self.allow_queue = False
            elif length == 2:  #Categories: songs or albums
                data = categories_list(['Songs', 'Albums'])
                set_mode('category')
            elif length == 3:
                if levels[2] == 'Songs':  #Songs by artist
                    artistid = levels[1]
                    data = self.player.database_get_song_list_artist(artistid, timeout=timeout)
                    if data is None:
                        return False
                    data = add_to_dict_list(data, [['widget', 'SongPlaylistElement'], ['selectable', True], ['selected', False], ['owner', self]])
                    set_mode('song', 'song')
                    self.queue_type = 'artist'
                    self.queue_id = artistid
                else:  #levels[2] == 'Albums'  #Albums by one artist
                    artistid = levels[1]
                    data = self.player.database_get_album_list_artist(artistid, timeout=timeout)
                    if data is None:
                        return False
                    data = add_to_dict_list(data, [['widget', 'AlbumPlaylistElement'], ['selectable', True], ['selected', False]])
                    set_mode('album', 'song')
                    self.queue_type = 'album'
        elif levels[0] == 'Genres':
            if length == 1:  #All genres
                data = self.player.database_get_genre_list(timeout=timeout)
                if data is None:
                    return False
                data = add_to_dict_list(data, [['widget', 'GenrePlaylistElement'], ['selectable', True], ['selected', False]])
                set_mode('genre')
                self.queue_type = 'random'
                for element in data:
                    element['id'] = element['value']
                    element['name'] = element['value']
            elif length == 2:  #Genre categories
                data = categories_list(['Songs', 'Albums'])
                set_mode('category')
            elif length == 3:
                if levels[2] == 'Songs':  #Songs from genre
                    genre = levels[1]
                    data = self.player.database_get_song_list_genre(genre=genre, timeout=timeout)
                    if data is None:
                        return False
                    data = add_to_dict_list(data, [['widget', 'SongPlaylistElement'], ['selectable', True], ['selected', False], ['owner', self]])
                    set_mode('song', 'song')
                    self.queue_type = 'genre'
                    self.queue_id = genre
                elif levels[2] == 'Albums':  #Album list with genre
                    genre = levels[1]
                    data = self.player.database_get_album_list_genre(genre=genre, timeout=timeout)
                    if data is None:
                        return False
                    data = add_to_dict_list(data, [['widget', 'AlbumPlaylistElement'], ['selectable', True], ['selected', False]])
                    set_mode('album', 'song')
                    self.queue_type = 'album'
        elif levels[0] == 'Playlists':
            if length == 1:  #Playlist list
                data = self.player.database_get_playlist_list(timeout=timeout)
                if data is None:
                    return False
                data = add_to_dict_list(data, [['widget', 'PlaylistPlaylistElement'], ['selectable', True], ['selected', False], ['owner', self]])
                set_mode('playlist')
            else:  #Playlist songs
                playlistid = levels[-1]
                data = self.player.database_get_song_list_playlist(playlistid, timeout=timeout)
                if data is None:
                    return False
                data = add_to_dict_list(data, [['widget', 'SongPlaylistElement'], ['selectable', True], ['selected', False], ['owner', self]])
                for index, song in enumerate(data):
                    song['index'] = index
                set_mode('playlistsong', 'song')
                self.queue_type = 'playlist'
                self.queue_id = playlistid
        elif levels[0] == 'Local Cache':
            data = self.player.get_local_cached()
            if data is None:
                return False
            data = add_to_dict_list(data, [['widget', 'SongCacheElement'], ['selectable', False], ['selected', False], ['owner', self]])
            for index, song in enumerate(data):
                song['index'] = index
            set_mode('cache', 'cache')
        self.player.database_list = data
        self.data = data
        self.data_unfiltered = data
        if self.allow_filter and self.use_search:
            self.filter_database()
        self.sort_database()
        self.database_levels = '/'.join(self.data_levels_names)
        self.to_select_activate()
        return True

    def click_node(self, data):
        if self.select_mode in ['song', 'cache']:
            pass
        else:
            self.edit_mode = False
            if self.data_levels and self.search_text:
                self.use_search = False
            self.data_levels.append(data['id'])
            self.data_levels_names.append(data['name'])
            self.update()


class WidgetListBrowseQueue(WidgetOpener):
    open_text = 'Open Queue'

    def open_queue(self):
        app = App.get_running_app()
        app.open_queue_popup()

    def get_item_to_open(self):
        return WidgetListQueue()


class WidgetListQueue(WidgetListBrowse):
    widget_type = StringProperty('BrowseQueue')
    queue = ListProperty()
    queue_duration_formatted = StringProperty('00:00.00')
    queue_history = ListProperty()
    queue_changed = BooleanProperty(False)
    queue_modified = ListProperty()
    queue_index = NumericProperty()
    song_id = StringProperty()
    edit_mode = BooleanProperty(False)
    to_select = []

    def queue_menu_open(self, button):
        queue_menu = AddToPlaylistDropDown(owner=self, player=self.player)
        queue_menu.open(button)

    def add_to_playlist(self, playlist_id, selected=False):
        #add songs to given playlist id
        App.get_running_app().add_blocking_thread('Add To Playlist', self.add_to_playlist_process, (playlist_id, selected, ))

    def add_to_playlist_process(self, playlist_id, selected, timeout):
        songids = []
        rvview = self.ids.rvview
        for song in rvview.data:
            if song['selected'] or not selected:
                songids.append(song['id'])
        if not songids:
            return True
        result = self.player.playlist_add_songs(playlist_id, songids=songids, timeout=timeout)
        return result

    def toggle_edit_mode(self, data):
        self.to_select = [data['index']]
        self.edit_mode = not self.edit_mode

    def on_edit_mode(self, *_):
        rvlayout = self.ids.rvlayout
        rvlayout.deselect_all()
        if not self.edit_mode:
            self.to_select = []
            self.on_queue()
        else:
            self.to_select_activate()
            rvlayout.refresh_selection()
            rvlayout.refresh_selects()

    def get_selected(self):
        indexes = []
        rvview = self.ids.rvview
        for item in rvview.data:
            if item['selected']:
                indexes.append(item['index'])
        return indexes

    def to_select_activate(self):
        rvlayout = self.ids.rvlayout
        rvlayout.selects = []
        for index, item in enumerate(self.queue_modified):
            if index in self.to_select:
                item['selected'] = True
                rvlayout.selects.append(item)
            else:
                item['selected'] = False

    def move_selected_up(self):
        indexes = self.get_selected()
        self.to_select = self.player.queue_move_indexes(indexes, -1)
        self.to_select_activate()

    def move_selected_down(self):
        indexes = self.get_selected()
        self.to_select = self.player.queue_move_indexes(indexes, 1)
        self.to_select_activate()

    def delete_selected(self):
        indexes = self.get_selected()
        self.player.queue_remove_indexes(indexes)

    def delete_element(self, data=None, index=None):
        if data is None:
            return
        self.player.queue_remove_index(data['index'])

    def sort_menu_open(self, button):
        sort_menu = SortDropDown(owner=self)
        sort_menu.open(button)

    def sort(self, mode):
        self.player.queue_sort(mode)

    def on_queue(self, *_):
        duration = 0
        remove = ['parent', 'size']
        queue_modified = []
        rvlayout = self.ids['rvlayout']
        for index, item in enumerate(self.queue):
            duration += item['duration']
            item_modified = item.copy()
            item_modified['owner'] = self
            item_modified['index'] = index
            for key in remove:
                if key in item_modified.keys():
                    del item_modified[key]
            item_modified['selectable'] = True
            if not self.edit_mode:
                if index == self.queue_index:
                    item_modified['selected'] = True
                    rvlayout.selected = item_modified
                else:
                    item_modified['selected'] = False
            else:
                item_modified['selected'] = False
            queue_modified.append(item_modified)
        self.queue_modified = queue_modified
        self.player.queue_changed = False
        rvlayout = self.ids.rvlayout
        rvlayout.refresh_selection()
        rvlayout.refresh_selects()
        self.queue_duration_formatted = timecode_hours(duration)

    def on_queue_index(self, *_):
        rvlayout = self.ids['rvlayout']
        for item in self.queue_modified:
            if item['index'] == self.queue_index and not self.edit_mode:
                item['selected'] = True
            else:
                item['selected'] = False
        rvlayout.refresh_selection()

    def on_player(self, *_):
        self.song_id = self.player.song_id
        self.queue_history = self.player.queue_history
        self.queue = self.player.queue
        self.queue_changed = False
        self.queue_index = self.player.queue_index
        self.player.bind(queue_history=self.setter('queue_history'))
        self.player.bind(queue_changed=self.setter('queue_changed'))
        self.player.bind(song_id=self.setter('song_id'))
        self.player.bind(queue=self.setter('queue'))
        self.player.bind(queue_index=self.setter('queue_index'))

    def on_queue_changed(self, *_):
        if self.player.queue_changed:
            self.queue = []
            self.queue = self.player.queue
            #self.on_queue()

    def click_node(self, songdata):
        if not self.edit_mode:
            song_valid = verify_song(songdata)
            if song_valid:
                self.player.stop()
                self.player.play_queue(songdata['index'])
                self.player.song_queue.set_index(songdata['index'])
                self.player.play()
