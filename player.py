import random
import threading

import logging
from kivy.app import App
from kivy.event import EventDispatcher
from kivy.properties import *
from kivy.clock import Clock, mainthread
from audio.player import SongQueue
from databases.subsonic import Database, verify_song, verify_song_list, verify_playlist_list


class Player(EventDispatcher):
    #Variables that should probably only be internal
    play_modes = ['in order', 'repeat all', 'repeat one', 'shuffle']
    database = None
    servers = []
    server_current = NumericProperty(0)

    use_player_cache = False
    song_queue = None
    current_is_cached = BooleanProperty(False)
    queue_index = NumericProperty(0)
    song = DictProperty()
    song_id = StringProperty()
    queue_init = True
    song_art_loaded = False
    random_amount = 20
    list_amount = 500
    queue_type = StringProperty()  #can be: random, playlist, artist, album, genre, rating, ''
    queue_id = StringProperty()  #id of the currently queued list
    database_list = ListProperty()
    playlists = ListProperty()
    scrobble_timer = ObjectProperty(allownone=True)
    skiponestar = BooleanProperty(False)
    scrobbletime = NumericProperty(30)
    last_scrobble = StringProperty()

    #Variables useful to widgets
    queue_changed = BooleanProperty(False)
    queue_history = ListProperty()
    volume = NumericProperty(1)
    play_mode = StringProperty('in order')
    playing = BooleanProperty(False)
    song_art = ObjectProperty(b'')
    song_title = StringProperty()
    song_album = StringProperty()
    song_artist = StringProperty()
    song_track = NumericProperty()
    song_year = NumericProperty()
    song_genre = StringProperty()
    song_favorite = BooleanProperty(False)
    song_duration = NumericProperty()
    song_position = NumericProperty()
    song_play_count = NumericProperty()
    song_disc_number = NumericProperty()
    song_album_id = StringProperty()
    song_artist_id = StringProperty()
    song_rating = NumericProperty()
    queue = ListProperty()
    next_song_index = NumericProperty()
    next_song_id = StringProperty()
    next_song_title = StringProperty()
    next_song_artist = StringProperty()
    next_song_album = StringProperty()
    playlist_changed = StringProperty()

    #Functions called by app
    def setup(self):
        database_created = [True, ""]
        if not self.database:
            database_created = self.setup_database()
            if not database_created[0]:
                return database_created
        if not self.song_id:
            self.song_set(None)
        if not self.song_queue:
            self.song_queue = SongQueue()
            self.song_queue.use_player_cache = self.use_player_cache
            self.song_queue.on_song_position_function = self.set_song_position
            self.song_queue.on_queue_index_function = self.set_queue_index
            self.song_queue.on_next_queue_index_function = self.queue_next
            self.song_queue.on_playing_function = self.set_playing
            self.song_queue.on_play_function = self.start_play
            self.song_queue.set_volume(self.volume)
            self.song_queue.set_playback_mode(self.play_mode)
            self.song_queue.set_skiponestar(self.skiponestar)
            self.song_queue.set_scrobbletime(self.scrobbletime)
            #self.play_mode = self.song_queue.play_mode
            self.song_queue_set_queue()
            self.song_queue.update_index(self.queue_index)
        else:
            is_now_playing = self.song_queue.verify_song_queue()
            if self.playing and not is_now_playing:
                self.song_queue.end()
        song_queue_setup = self.song_queue.setup()
        if not song_queue_setup[0]:
            self.song_queue.close()
            self.song_queue = None
            return song_queue_setup
        return database_created

    def close(self, service=False):
        if self.song_queue:
            self.song_queue.close(service)

    #Functions that should probably only be internal
    @mainthread
    def set_playlist_changed(self, playlistid):
        self.playlist_changed = playlistid

    def set_scrobbletime(self, scrobbletime):
        self.scrobbletime = scrobbletime
        if self.song_queue:
            self.song_queue.set_scrobbletime(self.scrobbletime)

    def scrobble_timer_start(self, *_):
        self.scrobble_timer_stop()
        self.scrobble_timer = Clock.schedule_once(self.scrobble, self.scrobbletime)

    def scrobble_timer_stop(self):
        if self.scrobble_timer:
            self.scrobble_timer.cancel()

    def scrobble(self, *_):
        if self.playing and self.song_id and self.song_id != self.last_scrobble:
            app = App.get_running_app()
            app.message("Scrobbled song: "+self.song_title)
            self.database.set_scrobble(self.song_id)
            self.last_scrobble = self.song_id  #Store scrobble so it doesnt accidentally get set twice in a row

    def start_play(self, *_):
        self.scrobble_timer_start()

    def set_playing(self, playing):
        self.playing = playing

    @mainthread
    def set_queue_index(self, index):
        self.queue_index = index
        self.play_queue()

    def song_queue_set_queue(self):
        if self.song_queue:
            self.song_queue.set_queue(self.song_queue_list_generate())

    def song_queue_list_generate(self):
        app = App.get_running_app()
        urls = []
        ratings = []
        for song in self.queue:
            cached_file = app.cached_file(song['id'], song['created'])
            if cached_file:
                urls.append(cached_file)
            else:
                url = self.database.get_stream_url(song['id'])
                urls.append(url)
            ratings.append(song['userRating'])
        return [urls, ratings, self.queue.copy()]

    def loop_list_index(self, index, itemlist):
        length = len(itemlist)
        if index >= length:
            index = 0
        elif index < 0:
            index = length - 1
        return index

    def get_queue_song(self, queue_index):
        #gets the song data at the given queue index, also wraps queue index around if necessary and returns refined index
        length = len(self.queue)
        if length == 0 or queue_index == -1:
            return 0, verify_song({}, strict=False)
        #queue_index = self.loop_list_index(queue_index, self.queue)
        return queue_index, self.queue[queue_index]

    def queue_next(self, new_index):
        #populates variables for next song

        self.next_song_index = new_index
        queue_index, next_song = self.get_queue_song(new_index)
        self.next_song_id = next_song['id']
        self.next_song_title = next_song['title']
        self.next_song_artist = next_song['artist']
        self.next_song_album = next_song['album']

    def setup_database(self):
        if not self.servers:
            return None, "Unable to connect: No servers configured."
        try:
            settings = self.servers[self.server_current]
        except:
            settings = self.servers[0]
        self.database = Database(settings=settings)
        return True, "Database created"

    @mainthread
    def set_song_position(self, pos):
        self.song_position = pos

    def list_queue(self):
        queue = []
        for song in self.queue:
            queue.append(song['id'])
        return queue

    def get_key_index(self, itemid, itemlist, key='id', allownone=False):
        item_index = None
        for index, item in enumerate(itemlist):
            if item[key] == itemid:
                item_index = index
                break
        if item_index is None and not allownone:
            return 0
        return item_index

    def queue_undo_store(self):
        if not self.queue_init:
            queue = self.queue.copy()
            self.queue_history.append([queue, self.queue_index, self.song_position, self.queue_type, self.queue_id])
            self.queue_history = self.queue_history[-10:]

    def queue_load(self, play=False, keep_queue_type=False):
        App.get_running_app().add_blocking_thread('Load Remote Queue', self.queue_load_process, (play, keep_queue_type, ))

    def queue_load_process(self, play, keep_queue_type, timeout):
        app = App.get_running_app()
        was_playing = self.playing or play
        self.stop()
        songs, current_id, position = self.database.get_queue(timeout=timeout)
        if songs is None:
            return False
        if songs:
            current_index = self.get_key_index(current_id, songs)
            if keep_queue_type:
                queue_type = self.queue_type
                queue_id = self.queue_id
            else:
                queue_type = 'playlist'
                queue_id = 'none'
            self.queue_set(songs, queue_type, queue_id, current_song=current_index, was_playing=was_playing, mode='init')
            self.set_song_position(position)
            self.queue_changed = True
            app.message('Loaded remote queue')
        return True

    def queue_save(self, app):
        app.add_background_thread('queue save', self.queue_save_process)

    def queue_save_process(self):
        songids = self.list_queue()
        currentsong = self.get_current_queue_song()
        currentsongid = currentsong['id']
        self.database.set_queue(songids, currentsongid, self.song_position)
        try:
            App.get_running_app().end_background_thread('queue save')
        except:
            pass

    def queue_save_local(self):
        data = [self.queue.copy(), self.queue_index, self.song_position]
        return data

    def queue_load_local(self, data, play=False, background=False, keep_queue_type=False):
        app = App.get_running_app()
        was_playing = self.playing
        songs, queue_index, song_position = data
        if keep_queue_type:
            queue_type = self.queue_type
            queue_id = self.queue_id
        else:
            queue_type = 'playlist'
            queue_id = 'none'
        self.queue_set(songs, queue_type, queue_id, current_song=queue_index, mode='init')
        if not background:
            app.message('Loaded local queue')
            if play or was_playing:
                self.play()

    def set_values(self, songid, valuename, value):
        #run through all queue and history items to update given value
        self.songlist_set_value(self.queue, songid, valuename, value)
        self.songlist_set_value(self.database_list, songid, valuename, value)
        for history in self.queue_history:
            queue = history[0]
            self.songlist_set_value(queue, songid, valuename, value)

    def songlist_set_value(self, queue, songid, valuename, value):
        for song in queue:
            if song['id'] == songid:
                song[valuename] = value

    #Functions useful to widgets
    def get_playlists(self):
        if not self.playlists:
            playlists = self.database_get_playlist_list()
            if playlists is None:
                playlists = []
            self.playlists = playlists
        return self.playlists

    def set_preview_info(self):
        #sets widget variables to default presets that can preview widget functions

        def generate_dummy_song(index):
            return {'id': 'a', 'title': "Song "+str(index), 'album': "Song Album", 'artist': "Song Artist", 'track': index, 'year': 2000, 'genre': 'Genre', 'starred': index == 1, 'duration': random.randint(120, 200), 'playCount': 0, 'discNumber': 0, 'albumId': 'a', 'artistId': 'a', 'userRating': random.randint(0, 5)}

        self.song_art = b''
        self.song_art_loaded = False
        self.song_id = "a"
        self.song_title = "Song Title"
        self.song_album = "Song Album"
        self.song_artist = "Song Artist"
        self.song_track = 1
        self.song_year = 2000
        self.song_genre = "Genre"
        self.song_favorite = True
        self.song_duration = 180
        self.song_play_count = 1
        self.song_disc_number = 1
        self.song_album_id = "a"
        self.song_artist_id = "a"
        self.song_rating = 3
        self.next_song_index = 1
        self.next_song_id = "a"
        self.next_song_title = "Next Song Title"
        self.next_song_artist = "Next Song Artist"
        self.next_song_album = "Next Song Album"
        self.queue_id = "a"
        self.queue_type = 'random'
        self.set_song_position(0)
        self.queue = []
        for index in range(1, 11):
            self.queue.append(generate_dummy_song(index))

    def rescan_database(self, full=None):
        result = self.database.set_start_scan(fullscan=full)
        return result

    def rescan_database_status(self):
        return self.database.get_scan_status()

    def load_song_art(self, songartwidget):
        App.get_running_app().add_background_thread('song art', self.load_song_art_process, args=(songartwidget, ))

    def load_song_art_process(self, songartwidget):
        app = App.get_running_app()
        if not self.database:
            return
        if self.song_id:
            if self.song_art_loaded:
                return self.song_art
            art = self.database.get_cover_art(self.song_id)
            if art is not None:
                self.song_art = art
            else:
                self.song_art = b''
            self.song_art_loaded = True
        try:
            songartwidget.set_song_art(self.song_art)
        except:
            pass
        app.end_background_thread('song art')

    @mainthread
    def song_set(self, song):  #must be mainthread, will cause weird crashes on android if not
        if song is None:
            song = verify_song({}, strict=False)

        self.song = song
        self.song_art = b''
        self.song_art_loaded = False
        self.song_id = song['id']
        self.song_title = song['title']
        self.song_album = song['album']
        self.song_artist = song['artist']
        self.song_track = song['track']
        self.song_year = song['year']
        self.song_genre = song['genre']
        self.song_favorite = song['starred']
        self.song_duration = song['duration']
        self.song_play_count = song['playCount']
        self.song_disc_number = song['discNumber']
        self.song_album_id = song['albumId']
        self.song_artist_id = song['artistId']
        self.song_rating = song['userRating']
        if self.song_queue:
            url = self.song_queue.get_url()
            self.current_is_cached = not url.startswith('http')
        else:
            self.current_is_cached = False

        if not self.song_id:
            self.stop()

    def queue_set(self, queue, queue_type, queue_id, current_song=None, mode='replace', set_index=0, was_playing=None):
        #current_song is the index of the currently playing song, if set, will update index without changing playback
        #mode can be: replace, init (like replace but does not skip to random), prepend/start, append/end, next/insert (or any other)
        if was_playing is None:
            was_playing = self.playing
        self.stop()
        if not queue:
            if mode not in ['replace', 'init']:
                return
            queue_type = ''
            queue_id = ''
        self.queue_init = False
        if mode in ['replace', 'init']:
            self.queue = queue
        elif mode in ['prepend', 'start']:
            if current_song is not None:
                current_song = len(queue) + current_song
            self.queue = queue + self.queue
        elif mode in ['append', 'end']:
            self.queue = self.queue + queue
        else:  #mode in ['next', 'insert']
            insert_point = self.queue_index + 1
            self.queue[insert_point:insert_point] = queue

        self.song_queue_set_queue()
        if current_song is not None:
            self.queue_index = current_song
            if self.song_queue:
                self.song_queue.update_index(self.queue_index)
        else:
            self.queue_index = set_index
            if self.song_queue:
                self.song_queue.set_index(self.queue_index)
        if mode == 'replace' and self.play_mode == 'shuffle':
            self.next()
        self.queue_type = queue_type
        self.queue_id = queue_id
        self.play_queue()
        if was_playing:
            self.play()

    def get_current_queue_song(self):
        new_index, song = self.get_queue_song(self.loop_list_index(self.queue_index, self.queue))
        self.queue_index = new_index
        return song

    def play_queue(self, index=None):
        #convenience function to set the current song, also sets index if index is provided
        if index is None:
            self.song_set(self.get_current_queue_song())
        else:
            new_index, song = self.get_queue_song(self.loop_list_index(index, self.queue))
            self.queue_index = new_index
            self.song_set(song)

    def replay(self, *_):
        self.stop(release=False)
        if self.song_queue:
            self.song_queue.play()

    def play(self, *_):
        if not self.song_id:
            return
        app = App.get_running_app()
        app.wakelock.request()
        #self.set_song_position(self.song_position)
        if self.song_queue:
            self.song_queue.play()

    def playtoggle(self):
        if not self.song_id:
            return
        if self.playing:
            self.pause()
        else:
            self.play()

    def pause(self):
        self.scrobble_timer_stop()
        if self.song_queue:
            self.song_queue.pause()
        app = App.get_running_app()
        app.wakelock.release()

    def stop(self, release=True):
        self.scrobble_timer_stop()
        if self.song_queue:
            self.song_queue.stop()
        self.set_song_position(0)
        if release:
            app = App.get_running_app()
            app.wakelock.release()

    def position_set(self, position):
        if position > self.song_duration:
            position = self.song_duration
        elif position < 0:
            position = 0
        if self.song_queue:
            self.song_queue.set_position(position)
        if not self.playing:  #if song is playing, song_queue will auto-update the song position on next frame
            self.set_song_position(position)

    def position_forward(self, amount=10):
        self.position_set(self.song_position + amount)

    def position_back(self, amount=10):
        self.position_set(self.song_position - amount)

    def next(self):
        self.scrobble_timer_stop()
        if self.song_queue:
            self.song_queue.next()

    def previous(self):
        self.scrobble_timer_stop()
        if self.song_queue:
            self.song_queue.previous()

    def rating_set(self, rating, songid=None, element_type='song'):
        app = App.get_running_app()
        if songid is None:
            songid = self.song_id
        if not songid:
            app.message('Unable to set rating')
            return
        App.get_running_app().add_background_thread('rating '+songid, self.rating_set_process, args=(rating, songid, element_type))

    def rating_set_process(self, rating, songid, element_type):
        app = App.get_running_app()
        rating = int(round(rating))
        if rating > 5:
            rating = 5
        elif rating < 0:
            rating = 0
        result = self.database.set_rating(songid, rating)
        if result is not None:
            self.song_rating = rating
            self.set_values(songid, 'userRating', rating)
            app.message('Set rating on '+element_type+': '+songid)
            if element_type == 'album':
                app.add_cached_list('albums', "", None)
            else:
                app.add_cached_list('songs', "", None)
        else:
            app.message('Unable to set rating on: '+songid)
        self.queue_changed = True
        app.end_background_thread('rating '+songid)

    def rating_up(self, rating=None, songid=None):
        if songid is None or rating is None:
            rating = self.song_rating + 1
            if rating > 5:
                rating = 5
            songid = self.song_id
        self.rating_set(rating, songid=songid)
        return rating

    def rating_down(self, rating=None, songid=None):
        if songid is None or rating is None:
            rating = self.song_rating - 1
            if rating < 0:
                rating = 0
            songid = self.song_id
        self.rating_set(rating, songid=songid)
        return rating

    def favorite_toggle(self, songid=None):
        if self.song_favorite:
            self.favorite_set(songid, favorite=False)
        else:
            self.favorite_set(songid, favorite=True)

    def favorite_set(self, songid=None, favorite=True, element_type='song'):
        if songid is None:
            songid = self.song_id
        App.get_running_app().add_background_thread('favorite '+songid, self.favorite_set_process, args=(songid, favorite, element_type))

    def favorite_set_process(self, songid, favorite, element_type):
        app = App.get_running_app()
        if favorite:
            result = self.database.set_favorite(songid)
            mode = 'favorite'
        else:
            result = self.database.set_unfavorite(songid)
            mode = 'unfavorite'
        if result is not None:
            app.message("Set "+mode+" on: "+songid)
            self.song_favorite = favorite
            self.set_values(songid, 'starred', favorite)
            if element_type == 'album':
                app.add_cached_list("albums_favorites", "", None)
            else:
                app.add_cached_list("songs_favorites", "", None)
        else:
            app.message("Unable to set "+mode+" on: "+songid)
        self.queue_changed = True
        app.end_background_thread('favorite '+songid)

    def skiponestar_set(self, skiponestar):
        self.skiponestar = skiponestar
        if self.song_queue:
            self.song_queue.set_skiponestar(skiponestar)

    def mode_set(self, play_mode):
        if self.song_queue:
            self.song_queue.set_playback_mode(play_mode)
        self.play_mode = play_mode
        return self.play_mode

    def mode_next(self):
        mode_index = self.play_modes.index(self.play_mode) + 1
        if mode_index >= len(self.play_modes):
            mode_index = 0
        return self.mode_set(self.play_modes[mode_index])

    def mode_previous(self):
        mode_index = self.play_modes.index(self.play_mode) - 1
        if mode_index < 0:
            mode_index = len(self.play_modes) - 1
        return self.mode_set(self.play_modes[mode_index])

    def queue_undo(self):
        app = App.get_running_app()
        if len(self.queue_history) > 0:
            was_playing = self.playing
            queue_history = self.queue_history.pop(-1)
            queue, index, position, queue_type, queue_id = queue_history
            #if currently playing song is in restored queue, leave it playing
            song_change = True
            for song_index, song in enumerate(queue):
                if song['id'] == self.song_id:
                    index = song_index
                    song_change = False
                    break
            if not song_change:
                self.queue_set(queue, queue_type, queue_id, current_song=index)
            else:
                self.stop()
                self.queue_set(queue, queue_type, queue_id, current_song=index)
                if self.song_queue:
                    self.song_queue.set_index(index)
                    self.song_queue.set_position(position)
                if was_playing:
                    self.play()

            app.message("Undo last queue change.")

    def move_indexes(self, songlist, indexes, moveby, queue_index):
        moved_indexes = []
        data = list(enumerate(songlist))
        if moveby > 0:
            data = list(reversed(data))
        length = len(data)
        old_queue_index = queue_index
        for index, item in data:
            if index in indexes:
                new_index = index + moveby
                new_index = max(min(new_index, length - 1), 0)
                if new_index not in moved_indexes:
                    if index == old_queue_index:
                        queue_index = new_index
                    elif queue_index == new_index:
                        queue_index -= moveby
                    moved_indexes.append(new_index)
                    songlist.insert(new_index, songlist.pop(index))
                else:
                    moved_indexes.append(index)
        return songlist, queue_index, moved_indexes

    def queue_move_indexes(self, indexes, moveby):
        if not indexes or moveby == 0:
            return []
        self.queue_undo_store()
        indexes = sorted(indexes)
        self.queue, queue_index, moved_indexes = self.move_indexes(self.queue, indexes, moveby, self.queue_index)
        self.song_queue_set_queue()
        self.queue_index = queue_index
        if self.song_queue:
            self.song_queue.update_index(queue_index)
        return moved_indexes

    def queue_remove_indexes(self, songindexes):
        if not songindexes:
            return
        songindexes.sort(reverse=True)
        app = App.get_running_app()
        self.queue_undo_store()
        queue_index = self.queue_index
        in_queue = False
        if queue_index in songindexes:
            in_queue = True
        queue = self.queue.copy()  #faster this way, doesnt possibly trigger updates of kivy property?
        for songindex in songindexes:
            queue.pop(songindex)
            if self.queue_index > songindex:
                queue_index -= 1
        if queue_index < 0:
            queue_index = 0
        self.queue = queue
        self.song_queue_set_queue()
        self.queue_index = queue_index
        if self.song_queue:
            self.song_queue.update_index(queue_index)
        if in_queue:
            if self.playing:
                self.stop()
                self.play_queue()
                self.play()
            else:
                self.stop()
                self.play_queue()
        app.message("Removed "+str(len(songindexes))+" songs from queue.")

    def queue_remove_index(self, songindex):
        app = App.get_running_app()
        self.queue_undo_store()
        self.queue.pop(songindex)
        self.song_queue_set_queue()
        if self.queue_index > songindex:
            self.queue_index -= 1
            if self.song_queue:
                self.song_queue.update_index(self.queue_index)
        elif self.queue_index == songindex:
            if self.playing:
                self.stop()
                self.play_queue()
                self.play()
            else:
                self.stop()
                self.play_queue()
        else:
            pass
        app.message("Removed one song from queue.")

    def queue_shuffle(self):
        self.queue_sort('shuffle')

    def queue_sort(self, mode):
        #mode == shuffle, reversed, track, title, artist, album, rating, playcount
        app = App.get_running_app()
        self.queue_undo_store()
        if mode == 'shuffle':
            self.queue.sort(key=lambda x: random.random())
            #random.shuffle(self.queue)
            app.message("Randomized queue")
        elif mode == 'reversed':
            self.queue.reverse()
            app.message("Reversed queue")
        elif mode == 'track':
            self.queue.sort(key=lambda a: a['track'])
        elif mode == 'artist':
            self.queue.sort(key=lambda a: a['artist'])
        elif mode == 'album':
            self.queue.sort(key=lambda a: a['album'])
        elif mode == 'rating':
            self.queue.sort(key=lambda a: a['userRating'])
        elif mode == 'playcount':
            self.queue.sort(key=lambda a: a['playCount'])
        else:
            self.queue.sort(key=lambda a: a['title'])
        if self.song_id:
            self.queue_index = self.get_key_index(self.song_id, self.queue)
        self.song_queue_set_queue()
        if self.song_queue:
            self.song_queue.update_index(self.queue_index)
        self.queue_changed = True

    def queue_clear(self):
        self.queue_undo_store()
        self.stop(release=True)
        self.queue_set([], '', '')

    def volume_set(self, volume):
        if volume < 0:
            volume = 0
        elif volume > 1:
            volume = 1
        self.volume = volume
        if self.song_queue:
            self.song_queue.set_volume(volume)

    def volume_up(self):
        self.volume_set(self.volume + 0.1)

    def volume_down(self):
        self.volume_set(self.volume - 0.1)

    def queue_preset(self, preset):
        App.get_running_app().add_blocking_thread("Queue Preset", self.queue_preset_process, (preset, ))

    def queue_preset_process(self, preset, timeout):
        #preset may be one of: 'Favorite', '5 Star', '4 And 5 Star', 'Most Played', 'Recently Played', 'Random Unplayed', 'Newest'
        app = App.get_running_app()
        queue_type = 'random'
        queue_id = ''
        if preset == '5 Star':
            data = self.database_get_search_song(query='', timeout=timeout)
            queue_type = 'rating'
            queue_id = '5'
            data = [song for song in data if song['userRating'] == 5]
        elif preset == '4 And 5 Star':
            data = self.database_get_search_song(query='', timeout=timeout)
            queue_type = 'rating'
            queue_id = '4'
            data = [song for song in data if song['userRating'] in [4, 5]]
        elif preset == 'Most Played':
            data = self.database_get_search_song(query='', timeout=timeout)
            data = sorted(data, key=lambda x: x['playCount'], reverse=True)[:40]
        elif preset == 'Random Unplayed':
            data = self.database_get_search_song(query='', timeout=timeout)
            data = [song for song in data if song['playCount'] == 0]
            data = sorted(data, key=lambda x: random.random())[:self.random_amount]
        elif preset == 'Recently Played':
            data = self.database_get_search_song(query='', timeout=timeout)
            data = [song for song in data if 'played' in song.keys()]
            data = sorted(data, key=lambda x: x['played'], reverse=True)[:self.random_amount]
        elif preset == 'Newest':
            data = self.database_get_search_song(query='', timeout=timeout)
            data = [song for song in data if 'created' in song.keys()]
            data = sorted(data, key=lambda x: x['created'], reverse=True)[:self.random_amount]
        else:  #preset == 'Favorite':
            data = self.database_get_song_list_favorite(timeout=timeout)
            queue_type = 'rating'
            queue_id = 'star'
        if data is None:
            return False
        self.queue_undo_store()
        self.queue_set(data, queue_type, queue_id)
        app.message("Queued "+preset+" Songs")
        return True

    def queue_playlist(self, playlistid):
        App.get_running_app().add_blocking_thread('Queue Playlist', self.queue_playlist_process, (playlistid, ))

    def queue_playlist_process(self, playlistid, timeout):
        app = App.get_running_app()
        playlist_data = self.database.get_playlist(playlistid, timeout=timeout)
        if playlist_data is None:
            return False
        self.queue_undo_store()
        self.queue_set(playlist_data[1], 'playlist', playlistid)
        app.message("Queued Playlist: "+playlist_data[0]['name'])
        return True

    def queue_random(self, keepcurrent=True, amount=None):
        App.get_running_app().add_blocking_thread('Queue Random Songs', self.queue_random_process, (keepcurrent, amount, ))

    def queue_random_process(self, keepcurrent, amount, timeout):
        app = App.get_running_app()
        if amount is None or amount == 0:
            amount = self.random_amount
        songs = self.database_get_song_list_random(amount, timeout=timeout)
        if songs is None:
            return False
        if keepcurrent:
            current_song = self.get_current_queue_song()
            if current_song['id']:
                songs.insert(0, current_song)
        self.queue_undo_store()
        self.queue_set(songs, 'random', 'none')
        app.message("Queued "+str(amount)+" random songs.")
        return True

    def queue_random_artist(self):
        App.get_running_app().add_blocking_thread('Queue Random Artist', self.queue_random_artist_process)

    def queue_random_artist_process(self, timeout):
        app = App.get_running_app()
        artists = self.database_get_search_artist("", timeout=timeout)
        if artists is None:
            return False
        if not artists:
            return True
        artistid = random.choice(artists)['id']
        songs = self.database_get_song_list_artist(artistid, timeout=timeout)
        if songs is None:
            return False
        if songs:
            artist = songs[0]['artist']
            self.queue_undo_store()
            self.queue_set(songs, 'artist', artistid)
            app.message("Queued "+str(len(songs))+" songs from artist: "+artist)
        return True

    def queue_random_album(self):
        App.get_running_app().add_blocking_thread('Queue Random Album', self.queue_random_album_process)

    def queue_random_album_process(self, timeout):
        app = App.get_running_app()
        albums = self.database_get_album_list_random(amount=1, timeout=timeout)
        if albums is None:
            return False
        if not albums:
            return True
        albumid = albums[0]['id']
        album_name = albums[0]['name']
        album_artist = albums[0]['artist']
        songs = self.database_get_song_list_album(albumid, timeout=timeout)
        if songs is None:
            return False
        self.queue_undo_store()
        self.queue_set(songs, 'album', albumid)
        app.message("Queued "+str(len(songs))+" songs in the album '"+album_name+"' by "+album_artist)
        return True

    def queue_random_genre(self):
        App.get_running_app().add_blocking_thread('Queue Random Genre', self.queue_random_genre_process)

    def queue_random_genre_process(self, timeout):
        app = App.get_running_app()
        genres = self.database_get_genre_list(timeout=timeout)
        if genres is None:
            return False
        if not genres:
            return True
        genre = random.choice(genres)['value']
        songs = self.database_get_song_list_genre(genre=genre, timeout=timeout)
        if songs is None:
            return False
        self.queue_undo_store()
        self.queue_set(songs, 'genre', genre)
        app.message("Queued "+str(len(songs))+" songs with the genre: "+genre)
        return True

    def queue_same_genre(self, keepcurrent=True):
        App.get_running_app().add_blocking_thread('Queue Same Genre', self.queue_same_genre_process, args=(keepcurrent, ))

    def queue_same_genre_process(self, keepcurrent, timeout):
        app = App.get_running_app()
        if self.song_id and self.song_genre:
            genre = self.song_genre
            songs = self.database_get_song_list_genre(genre=genre, timeout=timeout)
            if songs is None:
                return False
            index = 0
            if keepcurrent:
                index = self.get_key_index(self.song_id, songs)
            self.queue_undo_store()
            self.queue_set(songs, 'genre', genre, current_song=index)
            app.message("Queued "+str(len(songs))+" songs with the genre: "+genre)
        return True

    def queue_same_artist(self, keepcurrent=True):
        App.get_running_app().add_blocking_thread('Queue Same Artist', self.queue_same_artist_process, args=(keepcurrent,))

    def queue_same_artist_process(self, keepcurrent, timeout):
        app = App.get_running_app()
        if self.song_id and self.song_artist_id:
            artistid = self.song_artist_id
            songs = self.database_get_song_list_artist(artistid, timeout=timeout)
            index = 0
            if songs is None:
                return False
            if songs:
                if keepcurrent:
                    index = self.get_key_index(self.song_id, songs)
                self.queue_undo_store()
                self.queue_set(songs, 'artist', artistid, current_song=index)
                app.message("Queued "+str(len(songs))+" songs from artist: "+self.song_artist)
        return True

    def queue_same_album(self, keepcurrent=True):
        App.get_running_app().add_blocking_thread('Queue Same Album', self.queue_same_album_process, args=(keepcurrent,))

    def queue_same_album_process(self, keepcurrent, timeout):
        app = App.get_running_app()
        if self.song_id and self.song_album_id:
            albumid = self.song_album_id
            album_name = self.song_album
            songs = self.database_get_song_list_album(albumid, timeout=timeout)
            if songs is None:
                songs = []
            index = 0
            if keepcurrent:
                index = self.get_key_index(self.song_id, songs)
            self.queue_undo_store()
            self.queue_set(songs, 'album', albumid, current_song=index)
            app.message("Queued " + str(len(songs)) + " songs from album: "+album_name)
        return True

    def queue_same(self, mode='next'):
        App.get_running_app().add_blocking_thread('Queue Same', self.queue_same_process, args=(mode,))

    def queue_same_process(self, mode, timeout):
        app = App.get_running_app()
        #use self.queue_type and self.queue_id to set a new queue
        #can be: random, playlist, artist, album, genre, rating, none

        def random_omit(upper, omits):
            indexes = list(range(0, upper))
            omits = set(omits)
            omits = [x for x in omits if x is not None]
            for omit in reversed(sorted(omits)):
                try:
                    indexes.pop(omit)
                except:
                    pass
            if indexes:
                return random.choice(indexes)
            else:
                return 0

        def get_new_index(items, current, advance_by):
            if advance_by == 0:
                return random_omit(len(items), [current])
            elif current is None:
                return 0
            else:
                return self.loop_list_index(current+advance_by, items)

        if mode == 'next':
            advance = 1
            modifier_name = 'next'
        elif mode == 'random':
            advance = 0
            modifier_name = 'random'
        else:
            advance = -1
            modifier_name = 'previous'

        if self.queue_type == 'playlist':
            playlists = self.database_get_playlist_list(timeout=timeout)
            if playlists is None:
                return False
            self.playlists = playlists.copy()
            if not playlists:
                return True
            playlists.insert(0, {'id': 'none', 'name': 'queue', 'songCount': 0})  #insert dummy playlist to take the place of the queue
            current_index = self.get_key_index(self.queue_id, playlists, allownone=True)
            if current_index is None:
                #playlist not found, assume queue is loaded
                current_index = 0

            if advance == 0:
                #random index
                new_index = random_omit(len(playlists), [0, current_index])
            else:
                new_index = current_index + advance  #unrefined new index
                new_index = self.loop_list_index(new_index, playlists)  #looped index
            if new_index == 0:
                self.queue_undo_store()
                self.queue_load()
                item_name = 'saved queue'
            else:
                playlistid = playlists[new_index]['id']
                item_name = playlists[new_index]['name']
                songs = self.database_get_song_list_playlist(playlistid, timeout=timeout)
                if songs is None:
                    return False
                self.queue_undo_store()
                self.queue_set(songs, 'playlist', playlistid)
        elif self.queue_type == 'artist':
            artists = self.database_get_search_artist("")
            if artists is None:
                return False
            if not artists:
                return True
            artists.sort(key=lambda x: x['name'])
            current_index = self.get_key_index(self.queue_id, artists, allownone=True)
            new_index = get_new_index(artists, current_index, advance)
            artistid = artists[new_index]['id']
            item_name = artists[new_index]['name']
            songs = self.database_get_song_list_artist(artistid, timeout=timeout)
            if songs is None:
                return False
            self.queue_undo_store()
            self.queue_set(songs, 'artist', artistid)
        elif self.queue_type == 'album':
            albums = self.database_get_search_album("", timeout=timeout)
            if albums is None:
                return False
            if not albums:
                return True
            albums = sorted(albums, key=lambda album: album['artist'])
            current_index = self.get_key_index(self.queue_id, albums, allownone=True)
            new_index = get_new_index(albums, current_index, advance)
            albumid = albums[new_index]['id']
            item_name = albums[new_index]['name']
            songs = self.database_get_song_list_album(albumid, timeout=timeout)
            if songs is None:
                return False
            self.queue_undo_store()
            self.queue_set(songs, 'album', albumid)
        elif self.queue_type == 'genre':
            genres = self.database_get_genre_list(timeout=timeout)
            if genres is None:
                return False
            if not genres:
                return True
            genres = sorted(genres, key=lambda genre: genre['value'])
            current_index = self.get_key_index(self.queue_id, genres, key='value', allownone=True)
            new_index = get_new_index(genres, current_index, advance)
            new_genre = genres[new_index]['value']
            item_name = new_genre
            songs = self.database_get_song_list_genre(genre=new_genre, timeout=timeout)
            if songs is None:
                return False
            self.queue_undo_store()
            self.queue_set(songs, 'genre', new_genre)
        elif self.queue_type == 'rating':
            ratings = ['star', '5', '4', '3', '2', '1', '0']
            if self.queue_id not in ratings:
                return True
            current_index = ratings.index(self.queue_id)
            new_index = get_new_index(ratings, current_index, advance)
            new_rating = ratings[new_index]
            item_name = str(new_rating)
            if new_rating == 'star':
                songs = self.database_get_song_list_favorite(timeout=timeout)
            else:
                songs = self.database_get_song_list_rating(rating=new_rating, timeout=timeout)
            if songs is None:
                return False
            self.queue_undo_store()
            self.queue_set(songs, 'rating', new_rating)
        else:  #self.queue_type == 'random' or others
            random_amount = len(self.queue)
            item_name = 'songs'
            if random_amount == 0:
                random_amount = self.random_amount
            songs = self.database_get_song_list_random(random_amount, timeout=timeout)
            if songs is None:
                return False
            self.queue_undo_store()
            self.queue_set(songs, 'random', 'none')
        app.message("Queued songs with "+modifier_name+" "+self.queue_type+" type, '"+item_name+"'")
        return True

    def queue_same_next(self):
        self.queue_same()

    def queue_same_previous(self):
        self.queue_same(mode='previous')

    def queue_same_random(self):
        self.queue_same(mode='random')

    def playlist_remove_song(self, playlistid, index, timeout=None, message=True):
        if isinstance(index, type(1)):
            amount = '1'
        else:
            amount = str(len(index))
        app = App.get_running_app()
        result = self.database.set_playlist_remove_index(playlistid, index, timeout=timeout)
        if result:
            app.update_connection_status(True, "")
            if message:
                app.message("Removed "+amount+" song(s) from playlist")
                self.playlist_changed = playlistid
                app.add_cached_list('playlist', playlistid, None)
        else:
            app.update_connection_status(False, "Unable To Remove Songs")
            if message:
                app.message("Unable to remove song(s) from playlist")
        return result

    def playlist_remove(self, playlistid, timeout):
        app = App.get_running_app()
        result = self.database.set_playlist_delete(playlistid, timeout=timeout)
        app.add_cached_list('playlist', playlistid, None)
        if result:
            app.update_connection_status(True, "")
            app.message("Removed playlist")
        else:
            app.update_connection_status(False, "Unable To Delete Playlist")
        return result

    def playlist_create(self, name, timeout):
        app = App.get_running_app()
        result = None
        if name:
            result = self.database.set_playlist_new(name, timeout=timeout)
            if result:
                app.message("Created playlist: "+name)
                return result
        return result

    def playlist_add_songs(self, playlistid, songids=None, timeout=None, check_dup=True, message=True):
        app = App.get_running_app()
        if not songids:
            return None
        if isinstance(songids, type('')):
            songids = [songids]
        if check_dup:
            playlist = self.database.get_playlist(playlistid)
            if playlist is None:
                if message:
                    app.message("Unable to find playlist")
                return None
            playlist_songids = []
            playlist_songs = playlist[1]
            for song in playlist_songs:
                playlist_songids.append(song['id'])
            songids_to_add = []
            songids_already = []
            for songid in songids:
                if songid in playlist_songids:
                    songids_already.append(songid)
                else:
                    songids_to_add.append(songid)
        else:
            songids_already = []
            songids_to_add = songids
        if songids_to_add:
            result = self.database.set_playlist_add_song(playlistid, songids_to_add, timeout=timeout)
            app.add_cached_list('playlist', playlistid, None)
            if result:
                #some songs added
                if message:
                    self.playlist_changed = playlistid
                    if songids_already:
                        app.message("Added "+str(len(songids_to_add))+" song(s), "+str(len(songids_already))+" already added")
                    else:
                        app.message("Added song(s) to playlist")
                return result
            else:
                #adding failed
                if message:
                    app.message("Unable to add song(s) to playlist")
        else:
            #songs aready added
            if message:
                app.message("Song(s) already in playlist")
        return None

    def playlist_add_current_song(self, playlistid):
        app = App.get_running_app()
        songid = self.song_id
        result = self.playlist_add_songs(playlistid, songid)
        if result:
            app.update_connection_status(True, "")
        else:
            app.update_connection_status(False, "Unable To Add Song")

    def playlist_rename(self, playlistid, name, timeout):
        app = App.get_running_app()
        result = self.database.set_playlist_name(playlistid, name, timeout=timeout)
        if result:
            app.update_connection_status(True, "")
            app.message('Renamed playlist to: '+name)
        else:
            app.update_connection_status(False, "Unable To Rename Playlist")
            app.message('Unable to rename playlist')
        return result

    #database return data functions
    def database_get_album_list_artist(self, artistid, timeout=None):
        app = App.get_running_app()
        songs = self.database.get_album_list_artist(artistid, timeout=timeout)
        if songs is None:
            app.update_connection_status(False, "Unable To Load Database")
            songs = app.get_cached_list('artist_albums', artistid)
        else:
            app.update_connection_status(True, "")
            app.add_cached_list('artist_albums', artistid, songs)
        return songs

    def database_get_song_list_artist(self, artistid, timeout=None):
        app = App.get_running_app()
        songs = self.database.get_song_list_artist(artistid, timeout=timeout)
        if songs is None:
            app.update_connection_status(False, "Unable To Load Database")
            songs = app.get_cached_list('artist_songs', artistid)
        else:
            app.update_connection_status(True, "")
            app.add_cached_list('artist_songs', artistid, songs)
        return songs

    def database_get_song_list_album(self, albumid, timeout=None):
        app = App.get_running_app()
        songs = self.database.get_song_list_album(albumid, timeout=timeout)
        if songs is None:
            app.update_connection_status(False, "Unable To Load Database")
            songs = app.get_cached_list('album_songs', albumid)
        else:
            app.update_connection_status(True, "")
            app.add_cached_list('album_songs', albumid, songs)
        return songs

    def database_get_song_list_genre(self, genre, timeout=None):
        app = App.get_running_app()
        songs = self.database.get_full_list(self.database.get_song_list_genre, genre=genre, timeout=timeout)
        if songs is None:
            app.update_connection_status(False, "Unable To Load Database")
            songs = app.get_cached_list('genre_songs', genre)
        else:
            app.update_connection_status(True, "")
            app.add_cached_list('genre_songs', genre, songs)
        return songs

    def database_get_album_list_genre(self, genre, timeout=None):
        app = App.get_running_app()
        songs = self.database.get_full_list(self.database.get_album_list_genre, genre=genre, timeout=timeout)
        if songs is None:
            app.update_connection_status(False, "Unable To Load Database")
            songs = app.get_cached_list('genre_albums', genre)
        else:
            app.update_connection_status(True, "")
            app.add_cached_list('genre_albums', genre, songs)
        return songs

    def database_get_genre_list(self, timeout=None):
        app = App.get_running_app()
        songs = self.database.get_genre_list(timeout=timeout)
        if songs is None:
            app.update_connection_status(False, "Unable To Load Database")
            songs = app.get_cached_list('genres', "")
        else:
            app.update_connection_status(True, "")
            app.add_cached_list('genres', "", songs)
        return songs

    def database_get_song_list_favorite(self, timeout=None):
        app = App.get_running_app()
        songs = self.database.get_song_list_favorite(timeout=timeout)
        if songs is None:
            app.update_connection_status(False, "Unable To Load Database")
            songs = app.get_cached_list('songs_favorites', "")
        else:
            app.update_connection_status(True, "")
            app.add_cached_list('songs_favorites', "", songs)
        return songs

    def database_get_song_list_rating(self, rating, timeout=None):
        songs = self.database_get_search_song(query='', timeout=timeout)
        rating_int = int(rating)
        songs = [song for song in songs if song['userRating'] == rating_int]
        return songs

    def database_get_album_list_favorite(self, timeout=None):
        app = App.get_running_app()
        songs = self.database.get_album_list_favorite(timeout=timeout)
        if songs is None:
            app.update_connection_status(False, "Unable To Load Database")
            songs = app.get_cached_list('albums_favorites', "")
        else:
            app.update_connection_status(True, "")
            app.add_cached_list('albums_favorites', "", songs)
        return songs

    def database_get_song_list_playlist(self, playlistid, timeout=None):
        app = App.get_running_app()

        playlist_data = self.database.get_playlist(playlistid, timeout=timeout)
        if playlist_data is None:
            app.update_connection_status(False, "Unable To Load Database")
            songs = app.get_cached_list('playlist_songs', playlistid)
        else:
            songs = playlist_data[1]
            app.update_connection_status(True, "")
            app.add_cached_list('playlist_songs', playlistid, songs)
        return songs

    def database_get_playlist_list(self, timeout=None):
        app = App.get_running_app()
        playlists = self.database.get_playlist_list(timeout=timeout)
        playlists = verify_playlist_list(playlists)
        if playlists is None:
            app.update_connection_status(False, "Unable To Load Database")
            playlists = app.get_cached_list('playlists', "")
        else:
            app.update_connection_status(True, "")
            app.add_cached_list('playlists', "", playlists)
        if playlists is not None:
            self.playlists = playlists.copy()
        else:
            self.playlists = []
        return playlists

    def database_get_search_song(self, query, timeout=None):
        if not query:
            app = App.get_running_app()
            songs = self.database.get_full_list(self.database.get_search_song, query=query, timeout=timeout)
            if songs is None:
                app.update_connection_status(False, "Unable To Load Database")
                songs = app.get_cached_list('songs', query)
            else:
                app.update_connection_status(True, "")
                app.add_cached_list('songs', query, songs)
        else:
            songs = self.database.get_full_list(self.database.get_search_song, query=query, timeout=timeout)
        return songs

    def database_get_search_album(self, query, timeout=None):
        if not query:
            app = App.get_running_app()
            songs = self.database.get_full_list(self.database.get_search_album, query=query, timeout=timeout)
            if songs is None:
                app.update_connection_status(False, "Unable To Load Database")
                songs = app.get_cached_list('albums', "")
            else:
                app.update_connection_status(True, "")
                app.add_cached_list('albums', "", songs)
        else:
            songs = self.database.get_full_list(self.database.get_search_album, query=query, timeout=timeout)
        return songs

    def database_get_search_artist(self, query, timeout=None):
        if not query:
            app = App.get_running_app()
            songs = self.database.get_full_list(self.database.get_search_artist, query=query, timeout=timeout)
            if songs is None:
                app.update_connection_status(False, "Unable To Load Database")
                songs = app.get_cached_list("artists", "")
            else:
                app.update_connection_status(True, "")
                app.add_cached_list("artists", "", songs)
        else:
            songs = self.database.get_full_list(self.database.get_search_artist, query=query, timeout=timeout)
        return songs

    def database_get_album_list(self, list_type='alphabeticalByName', size=None, offset=None, from_year=None, to_year=None, genre=None, timeout=None):
        return self.database.get_album_list(list_type=list_type, size=size, offset=offset, from_year=from_year, to_year=to_year, genre=genre, timeout=timeout)

    def database_get_song_list_random(self, amount, timeout=None):
        return self.database.get_song_list_random(amount, timeout=timeout)

    def database_get_album_list_random(self, amount, timeout=None):
        return self.database.get_album_list_random(size=amount, timeout=timeout)

    def get_local_cached(self):
        app = App.get_running_app()
        songs = []
        for song_id in app.local_cache.keys():
            if song_id in app.local_cache_info.keys():
                song = verify_song(app.local_cache_info[song_id].copy(), strict=False)
            else:
                song = verify_song({'id': song_id}, strict=False)
            songs.append(song)
        return songs
