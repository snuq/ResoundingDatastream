import time
from kivy.app import App
from kivy.clock import mainthread
from jnius import autoclass
from oscpy.server import OSCThreadServer
from oscpy.client import OSCClient
from .songqueue import queue_next


class SongQueueAndroid:
    #class that looks like SongQueue to the player, but actually sends/receives data from a service, does not play anything itself
    on_song_position_function = None
    on_queue_index_function = None
    on_next_queue_index_function = None
    on_playing_function = None
    on_stop_function = None
    on_play_function = None
    osc_server = None
    osc_client = None
    background_service = None
    song_queue = None
    random_history = []
    playing = False
    scrobbletime = 30

    queue = []
    queue_ratings = []
    queue_index = 0
    next_queue_index = 0
    next_queue_index_backup = 0
    skiponestar = False
    play_mode = 'in order'
    volume = 1
    song_position = 0
    got_ping = False

    def setup(self):
        try:
            app = App.get_running_app()
            self.osc_client = OSCClient("localhost", app.osc_port + 1)
            self.osc_server = OSCThreadServer(encoding="utf8")
            self.osc_server.listen("localhost", port=app.osc_port, default=True)
            self.osc_server.bind(b"/on_stop", self.stop_service)
            self.osc_server.bind(b"/on_song_position", self.on_song_position)
            self.osc_server.bind(b"/on_queue_index", self.on_queue_index)
            self.osc_server.bind(b"/on_next_queue_index", self.on_next_queue_index)
            self.osc_server.bind(b"/on_playing", self.on_playing)
            self.osc_server.bind(b"/on_started", self.on_started)
            self.osc_server.bind(b"/on_play", self.on_play)
            self.osc_server.bind(b"/on_ping", self.on_ping)
            self.send_message(b'/resend', '')
            return True, ""
        except Exception as e:
            self.close()
            return False, str(e)

    def close(self, service=False):
        if service:
            self.stop_service()
            self.stop_service_support()

    def verify_song_queue(self):
        self.got_ping = False
        self.osc_client.send_message(b"/ping", '')
        start_time = time.time()
        while not self.got_ping:
            if time.time() - start_time > 0.2:
                break
            time.sleep(0.01)
        return self.got_ping

    def on_ping(self, *_):
        self.got_ping = True

    def get_url(self, index=None):
        if index is None:
            index = self.queue_index
        try:
            url = self.queue[index]
            return url
        except:
            return ''

    def reset_random_history(self):
        self.random_history = []

    def queue_next(self):
        if self.skiponestar:
            ratings = self.queue_ratings
        else:
            ratings = None
        new_index = queue_next(self.queue, self.queue_index, self.play_mode, ratings)
        self.next_queue_index = new_index
        self.on_next_queue_index(self.next_queue_index)

    @mainthread
    def start_service(self):
        if not self.background_service:
            self.background_service = autoclass('com.snuq.resoundingdatastream.ServiceResoundingdatastreamservice')
            m_activity = autoclass('org.kivy.android.PythonActivity').mActivity
            self.background_service.start(m_activity, 'iconbw', 'Streaming music playing', '', '')

    def on_started(self, *_):
        self.send_queue()
        self.send_update_index()
        self.send_set_position()
        self.send_set_volume()
        self.send_playback_mode()
        self.send_skiponestar()
        self.send_scrobbletime()
        self.send_next_queue_index()
        self.send_message(b'/play', '')

    def stop_service(self, *_):
        if self.background_service:
            m_activity = autoclass('org.kivy.android.PythonActivity').mActivity
            self.background_service.stop(m_activity)
            self.background_service = None

    @mainthread
    def stop_service_support(self):
        if self.osc_server:
            self.osc_server.stop_all()  # Stop all sockets
            self.osc_server.terminate_server()  # Request the handler thread to stop looping
            self.osc_server.join_server()
            self.osc_server = None
        if self.osc_client:
            self.osc_client = None

    def send_message(self, channel, message):
        if self.osc_client:
            self.osc_client.send_message(channel, [message.encode("utf8")])

    #Functions to set data to player
    def set_queue(self, data):
        queue, ratings = data
        self.queue = queue
        self.queue_ratings = ratings
        self.send_queue()
        self.reset_random_history()

    def send_queue(self):
        app = App.get_running_app()
        max_size = 100
        queue_string = ' | '.join(self.queue[:max_size])
        rating_string = ' | '.join(str(rating) for rating in self.queue_ratings[:max_size])
        send_data = queue_string + ' || ' + rating_string
        try:
            self.send_message(b'/set_queue', send_data)
        except:
            app.message('Unable to send queue to Service')
            return
        if len(self.queue) > max_size:
            segment = 1
            while True:
                index_split = max_size * segment
                next_index_split = max_size * (segment + 1)
                split_queue = self.queue[index_split:next_index_split]
                split_rating = self.queue_ratings[index_split:next_index_split]
                if not split_queue:
                    break
                queue_string = ' | '.join(split_queue)
                rating_string = ' | '.join(str(rating) for rating in split_rating)
                send_data = queue_string + ' || ' + rating_string
                self.send_message(b'/add_queue', send_data)
                segment += 1

    def update_index(self, index):
        self.queue_index = index
        if self.background_service:
            self.send_update_index()
        else:
            self.queue_next()

    def send_update_index(self):
        self.send_message(b'/update_index', str(self.queue_index))

    def set_index(self, index):
        self.queue_index = index
        if self.background_service:
            self.send_set_index()
        else:
            self.queue_next()

    def send_set_index(self):
        self.send_message(b'/set_index', str(self.queue_index))

    def set_position(self, position):
        self.song_position = position
        self.send_set_position()

    def send_set_position(self):
        self.send_message(b'/set_position', str(self.song_position))

    def set_volume(self, volume):
        self.volume = volume
        self.send_set_volume()

    def send_set_volume(self):
        self.send_message(b'/set_volume', str(self.volume))

    def set_playback_mode(self, mode):
        self.play_mode = mode
        self.reset_random_history()
        if self.background_service:
            self.send_playback_mode()
        else:
            self.queue_next()

    def send_playback_mode(self):
        self.send_message(b'/set_playback_mode', self.play_mode)

    def set_skiponestar(self, skiponestar):
        self.skiponestar = skiponestar
        if self.background_service:
            self.send_skiponestar()
        else:
            self.queue_next()

    def send_skiponestar(self):
        self.send_message(b'/set_skiponestar', str(self.skiponestar))

    def set_scrobbletime(self, scrobbletime):
        self.scrobbletime = scrobbletime
        self.send_scrobbletime()

    def send_scrobbletime(self):
        self.send_message(b'/set_scrobbletime', str(self.scrobbletime))

    def send_next_queue_index(self):
        self.send_message(b'/set_next_queue_index', str(self.next_queue_index_backup))

    #Functions to control playback
    def play(self):
        self.next_queue_index_backup = self.next_queue_index
        self.start_service()
        self.send_message(b'/play', '')

    def pause(self):
        self.send_message(b'/pause', '')
        self.stop_service()
        self.on_playing(False)

    def play_toggle(self, *_):
        if self.playing:
            self.pause()
        else:
            self.play()

    def stop(self):
        self.send_message(b'/stop', '')
        self.stop_service()
        self.song_position = 0
        self.on_song_position(0)
        self.on_playing(False)

    def next(self, auto=False):
        if self.background_service:
            if auto:
                self.send_message(b'/next_auto', '')
            else:
                self.send_message(b'/next', '')
        else:
            if self.play_mode == 'shuffle':
                self.random_history.append(self.queue_index)
            if self.next_queue_index == -1:
                self.queue_index = 0
            else:
                self.queue_index = self.next_queue_index
            self.on_queue_index(self.queue_index)
            self.set_position(0)
            self.on_song_position(0)
            self.queue_next()

    def previous(self):
        if self.background_service:
            self.send_message(b'/previous', '')
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
                    self.queue_index = 0
                else:
                    self.queue_index = new_index
            self.on_queue_index(self.queue_index)
            self.set_position(0)
            self.on_song_position(0)
            self.queue_next()

    def end(self):
        #simulate playback queue finishing
        self.stop()
        if self.play_mode == 'in order':
            self.queue_index = len(self.queue) - 1
            self.on_queue_index(self.queue_index)
            self.queue_next()

    #Functions to communicate back
    def on_song_position(self, song_position):
        self.song_position = float(song_position)
        if self.on_song_position_function:
            self.on_song_position_function(self.song_position)

    def on_queue_index(self, queue_index):
        self.queue_index = int(queue_index)
        if self.on_queue_index_function:
            self.on_queue_index_function(self.queue_index)

    def on_next_queue_index(self, next_queue_index):
        self.next_queue_index = int(next_queue_index)
        if self.on_next_queue_index_function:
            self.on_next_queue_index_function(self.next_queue_index)

    def on_playing(self, playing):
        playing = playing == 'True'
        self.playing = playing
        if self.on_playing_function:
            self.on_playing_function(playing)

    def on_stop(self, *_):
        if self.on_stop_function:
            self.on_stop_function('')

    def on_play(self, *_):
        if self.on_play_function:
            self.on_play_function()
