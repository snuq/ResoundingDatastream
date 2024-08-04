import random
import threading
import time
from kivy.clock import Clock, mainthread
from kivy.utils import platform
if platform == 'android':
    from .soundandroid import AudioPlayer
else:
    from .soundffpyplayer import AudioPlayer


def random_queue_index(queue, tried, randoms_avoid):
    #picks a random index, not including current self.queue_index
    not_tried = [i for i in range(0, len(queue)) if i not in tried]
    if not_tried:
        avoided = [i for i in not_tried if i not in randoms_avoid]
        if avoided:
            return random.choice(avoided)
        else:
            return random.choice(not_tried)
    else:
        return -1


def loop_list_index(index, itemlist):
    #return an index that is looped to be inside of the list range
    length = len(itemlist)
    if index >= length:
        index = 0
    elif index < 0:
        index = length - 1
    return index


def queue_next(queue, queue_index, play_mode, ratings=None, previous=False, random_history=None):
    if random_history:
        if len(random_history) > 1:
            randoms_avoid = list(reversed(random_history))[:int(len(queue) / 2)]
        else:
            randoms_avoid = random_history.copy()
    else:
        randoms_avoid = []
    if previous:
        add_index = -1
    else:
        add_index = 1
    if queue:
        tried = [queue_index]
        if ratings:
            #skip 1 star songs
            for index, item in enumerate(queue):
                if ratings[index] == 1:
                    tried.append(index)

        if play_mode == 'shuffle':
            new_index = random_queue_index(queue, tried, randoms_avoid)
            return new_index

        new_index = queue_index
        while True:
            new_index = loop_list_index(new_index + add_index, queue)
            if new_index == queue_index:
                return -1
            if new_index not in tried:
                return new_index
    else:
        new_index = 0
    return new_index


class SongQueue:
    #class that stores and handles all basic logic and audio playback necessary to finish playing queue with current settings
    play_modes = ['in order', 'repeat all', 'repeat one', 'shuffle']
    on_song_position_function = None
    on_queue_index_function = None
    on_next_queue_index_function = None
    on_playing_function = None
    on_stop_function = None
    on_play_function = None

    use_player_cache = False
    player_cache = {}
    max_cache = 10
    cache_song_start_thread = None
    next_cache_timer = None

    autoupdate = True
    autoupdater = None
    audio = None
    random_history = []
    playing = False
    scrobbletime = 30

    queue = []
    queue_ratings = []
    queue_index = 0
    next_queue_index = 0
    skiponestar = False
    play_mode = 'in order'
    volume = 1
    song_position = 0

    def setup(self):
        return True, ""

    def close(self, *_):
        self.stop()
        if self.audio:
            self.audio.close()
        self.cache_clear()

    def verify_song_queue(self):
        return True

    def get_url(self, index=None):
        if index is None:
            index = self.queue_index
        try:
            url = self.queue[index]
            return url
        except:
            return ''

    def resend(self, *_):
        #calls all on_ functions to ensure data is up-to-date
        self.on_queue_index()
        self.on_next_queue_index()
        self.on_song_position()
        self.on_playing()

    def start_autoupdate(self):
        self.stop_autoupdate()
        if self.autoupdate:
            self.autoupdater = Clock.schedule_interval(self.update, 0.03)

    def stop_autoupdate(self):
        if self.autoupdater:
            self.autoupdater.cancel()
            self.autoupdater = None

    #player cache functions
    def cache_next(self):
        #start a timed function to cache next song to make switching quicker
        if self.next_cache_timer is not None:
            self.next_cache_timer.cancel()
        self.next_cache_timer = Clock.schedule_once(self.cache_next_song, 20)

    def cache_next_song(self, *_):
        if self.song_position < 5:  #current song hasnt played enough yet, cancel cache because connection is horrible
            return
        url = self.get_url(self.next_queue_index)
        if url.startswith('http'):
            self.cache_start_play(url)

    def cache_clear(self):
        for player_key in self.player_cache.keys():
            audio = self.player_cache[player_key][1]
            if audio != self.audio:
                audio.close()

    def cache_add(self, url, audio=None):
        if url:
            if url not in self.player_cache.keys():
                if audio is None:
                    audio = AudioPlayer()
                    audio.new_song(url)
                self.player_cache[url] = [time.time(), audio, False]
                self.cache_prune()
                return self.player_cache[url]
            else:
                self.player_cache[url][0] = time.time()
                return self.player_cache[url]

    def cache_start_play(self, url):
        if not self.cache_song_start_thread:
            self.cache_song_start_thread = threading.Thread(target=self.cache_threaded_start_song, args=(url,))
            self.cache_song_start_thread.start()

    def cache_threaded_start_song(self, url):
        self.cache_add(url)
        audio = self.player_cache[url][1]
        audio.play()
        if url != self.get_url():
            audio.stop()
        self.cache_song_start_thread = None

    def cache_get(self, url, ensure=False):
        if not url:
            return None
        if url in self.player_cache.keys():
            return self.player_cache[url]
        else:
            if ensure:
                return self.cache_add(url)
            else:
                return None

    def cache_prune(self):
        cached_audio = []
        for key in self.player_cache.keys():
            item = self.player_cache[key]
            cached_audio.append([item[0], key])
        cached_audio.sort(key=lambda x: x[0])
        to_remove = cached_audio[:-self.max_cache]
        for item in to_remove:
            del self.player_cache[item[1]]

    def new_song_cache(self):
        if not self.queue:
            return
        url = self.queue[self.queue_index]
        if self.audio:  #ensure previous audio is cached
            #self.audio.new_song(url)
            if self.audio.url and self.audio.url != url:
                self.audio.set_position(0)
                self.audio.stop()
                status, position = self.audio.get_status()
                if status == 'stop' and position != 0:
                    #breaks cache, but is necessary to work around a bug in ffpyplayer that prevents replaying song
                    self.audio.new_song(self.audio.url)
            self.cache_add(self.audio.url, self.audio)
            self.audio = None
        new_audio = self.cache_get(url, True)
        if new_audio:
            self.audio = new_audio[1]
            self.audio.set_volume(self.volume)

    def new_song_uncached(self):
        if not self.queue:
            return
        url = self.queue[self.queue_index]
        if not self.audio:
            self.audio = AudioPlayer()
            self.audio.new_song(url)
        elif self.audio.url != url:
            self.audio.new_song(url)
            self.audio.set_position(0)
            self.audio.stop()
        else:
            if platform != 'android':
                self.audio.new_song(url)  #workaround for a bug in ffpyplayer when playing same song

    def new_song(self):
        if self.use_player_cache:
            self.new_song_cache()
        else:
            self.new_song_uncached()

    def reset_random_history(self):
        self.random_history = []

    def update(self, *_):  #update loop
        if self.audio:
            state, position = self.audio.get_status()
            if state == 'stop':
                if self.playing:
                    #song has ended, but queue should continue
                    self.next(auto=True)
                else:
                    #song has ended after being told to stop
                    pass
            if self.playing and self.song_position != position:
                #song is still playing, update position if it has changed
                self.song_position = position
                self.on_song_position()

    def queue_next(self):
        if self.skiponestar:
            ratings = self.queue_ratings
        else:
            ratings = None
        new_index = queue_next(self.queue, self.queue_index, self.play_mode, ratings, random_history=self.random_history)
        self.next_queue_index = new_index
        self.on_next_queue_index()

    #Functions to set data in player
    def set_queue(self, data):
        self.cache_clear()
        queue, ratings = data
        self.queue = queue
        self.queue_ratings = ratings
        self.reset_random_history()

    def add_queue(self, data):
        queue, ratings = data
        self.queue.extend(queue)
        self.queue_ratings.extend(ratings)
        self.reset_random_history()

    def update_index(self, index):
        #index has changed, but playing song has not, just update index without touching song
        self.queue_index = index
        self.queue_next()

    def set_index(self, index):
        if index != self.queue_index:
            #song has changed, need to update self.audio and play if needed
            self.queue_index = index
            #self.new_song()
        self.queue_next()

    def set_position(self, position):
        self.song_position = position
        if self.audio:
            self.audio.set_position(position)

    def set_volume(self, volume):
        self.volume = volume
        if self.audio:
            self.audio.set_volume(volume)

    def set_playback_mode(self, mode):
        self.play_mode = mode
        self.reset_random_history()
        self.queue_next()

    def set_skiponestar(self, skiponestar):
        self.skiponestar = skiponestar
        self.queue_next()

    def set_scrobbletime(self, scrobbletime):
        self.scrobbletime = scrobbletime

    def set_next_queue_index(self, next_queue_index):
        self.next_queue_index = next_queue_index
        self.on_next_queue_index()

    #Functions to control playback
    def play(self, *_):
        if self.use_player_cache:
            self.cache_next()
        if self.playing:
            self.set_position(0)
            self.audio.play()
        else:
            self.new_song()
            if self.audio:
                self.audio.play()
                self.set_position(self.song_position)
                if not self.audio.failedload:
                    self.playing = True
                    self.start_autoupdate()
                else:
                    self.playing = False
                    self.stop_autoupdate()
                self.on_play()
                self.on_playing()

    def pause(self, *_):
        self.stop_autoupdate()
        if self.audio:
            self.audio.stop()
        self.playing = False
        self.on_playing()
        self.on_stop()

    def play_toggle(self, *_):
        if self.playing:
            self.pause()
        else:
            self.play()

    def stop(self, *_):
        self.pause()
        self.set_position(0)
        self.on_song_position()

    def next(self, auto=False):
        if self.play_mode == 'shuffle':
            self.random_history.append(self.queue_index)
        if self.next_queue_index == -1:
            self.stop()
            self.on_stop()
            self.queue_index = 0
        elif self.play_mode == 'repeat one' and auto:
            pass
        elif self.next_queue_index < self.queue_index:
            if auto and self.play_mode == 'in order':
                self.stop()
                self.on_stop()
                return
            else:
                self.queue_index = self.next_queue_index
        else:
            self.queue_index = self.next_queue_index
        self.on_queue_index()
        self.new_song()
        self.set_position(0)
        self.on_song_position()
        self.queue_next()
        if self.playing:
            self.on_play()
            self.play()

    def previous(self, *_):
        if self.song_position > 3:
            self.set_position(0)
            self.on_song_position()
            return
        else:
            if self.play_mode == 'shuffle' and self.random_history:
                self.queue_index = self.random_history.pop(-1)
            else:
                if self.skiponestar:
                    ratings = self.queue_ratings
                else:
                    ratings = None
                new_index = queue_next(self.queue, self.queue_index, self.play_mode, ratings, previous=True)
                if new_index == -1:
                    self.stop()
                    self.on_stop()
                    self.queue_index = 0
                else:
                    self.queue_index = new_index
        self.on_queue_index()
        self.new_song()
        self.set_position(0)
        self.on_song_position()
        if self.playing:
            self.on_play()
            self.play()
        self.queue_next()

    def end(self):
        #simulate playback queue finishing
        self.stop()
        if self.play_mode == 'in order':
            self.queue_index = len(self.queue) - 1
            self.on_queue_index()
            self.new_song()
            self.queue_next()

    #Functions to communicate back
    def on_song_position(self, *_):
        if self.on_song_position_function:
            self.on_song_position_function(self.song_position)

    def on_queue_index(self, *_):
        if self.on_queue_index_function:
            self.on_queue_index_function(self.queue_index)

    def on_next_queue_index(self, *_):
        if self.on_next_queue_index_function:
            self.on_next_queue_index_function(self.next_queue_index)

    def on_playing(self, *_):
        if self.on_playing_function:
            self.on_playing_function(self.playing)

    def on_stop(self, *_):
        if self.on_stop_function:
            self.on_stop_function()

    def on_play(self, *_):
        if self.on_play_function:
            self.on_play_function()
