import time
import threading
from kivy.core.audio.audio_ffpyplayer import SoundFFPy
from kivy.properties import BooleanProperty


class AudioPlayer:
    failedload = False
    audio = None
    volume = 1
    url = ''
    position = 0

    def close(self):
        if self.audio:
            self.stop()
            self.cleanup(self.audio)

    def new_song(self, url):
        if self.audio:
            self.cleanup(self.audio)
        self.audio = None
        self.url = url
        self.audio = SoundPlayer(source=self.url, volume=self.volume)
        self.failedload = self.audio.failedload

    def cleanup(self, audio):  #offload the audio cleanup to a thread to try and prevent crashes and freezes
        def cleanup_process(audio_data):
            time.sleep(0.3)  #without this delay, unload() can cause freeze or crash, setting this too low will amplify problems on android too
            audio_data.unload()

        cleanup_thread = threading.Thread(target=cleanup_process, args=(audio, ))
        cleanup_thread.start()

    def play(self):
        if self.audio:
            self.audio.play()

    def stop(self):
        if self.audio:
            self.audio.stop()

    def set_volume(self, volume):
        if self.audio:
            self.audio.volume = volume
        self.volume = volume

    def set_position(self, pos):
        self.position = pos
        if self.audio:
            self.audio.seek(pos)

    def get_status(self):
        if self.audio:
            position = self.audio.get_pos()
            state = self.audio.state
        else:
            position = 0
            state = 'stop'
        return state, position


class SoundPlayer(SoundFFPy):
    failedload = BooleanProperty(False)

    #modified version of kivy.core.audio.audio_ffpyplayer.SoundFFPy to add a couple options and hopefully prevent loading crashes
    def load(self):
        self.unload()
        ff_opts = {'vn': True, 'sn': True, 'autoexit': True, 'infbuf': True}
        from ffpyplayer.player import MediaPlayer
        self._ffplayer = MediaPlayer(self.source, callback=self._player_callback, loglevel='info', ff_opts=ff_opts)
        player = self._ffplayer
        player.set_volume(self.volume)
        player.toggle_pause()
        self._state = 'paused'
        # wait until loaded or failed, shouldn't take long, but just to make sure metadata is available.
        s = time.perf_counter()
        while (player.get_metadata()['duration'] is None and not self.quitted and time.perf_counter() - s < 10.):
            time.sleep(0.005)
        if player.get_metadata()['duration'] is None:
            self._ffplayer = None
            self.failedload = True
        else:
            self.failedload = False

    def play(self):
        if self._state == 'playing':
            super().play()
            return
        if not self._ffplayer:
            self.load()
        if not self._ffplayer:
            self.stop()
            return
        self._ffplayer.toggle_pause()
        self._state = 'playing'
        self.state = 'play'
        super().play()
