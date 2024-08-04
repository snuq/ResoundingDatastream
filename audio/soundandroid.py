#from kivy.core.audio.audio_android import SoundAndroidPlayer as SoundPlayer


class AudioPlayer:
    failedload = False
    audio = None
    volume = 1
    url = ''
    position = 0

    def close(self):
        if self.audio:
            self.stop()
            self.audio.unload()

    def new_song(self, url):
        if url != self.url:
            if self.audio:
                self.audio.stop()
                self.audio.unload()
                self.audio = None
            self.url = url

    def play(self):
        if not self.audio:
            self.audio = SoundPlayer()
            self.audio.volume = self.volume
            self.audio.source = self.url
            self.failedload = self.audio.failedload
            if self.failedload:
                self.audio.unload()
                self.audio = None
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


from jnius import autoclass, java_method, PythonJavaClass
from android import api_version
from kivy.core.audio import Sound
from kivy.properties import BooleanProperty


MediaPlayer = autoclass("android.media.MediaPlayer")
AudioManager = autoclass("android.media.AudioManager")
if api_version >= 21:
    AudioAttributesBuilder = autoclass("android.media.AudioAttributes$Builder")


class OnCompletionListener(PythonJavaClass):
    __javainterfaces__ = ["android/media/MediaPlayer$OnCompletionListener"]
    __javacontext__ = "app"

    def __init__(self, callback, **kwargs):
        super().__init__(**kwargs)
        self.callback = callback

    @java_method("(Landroid/media/MediaPlayer;)V")
    def onCompletion(self, mp):
        self.callback()


class SoundPlayer(Sound):
    failedload = BooleanProperty(False)

    @staticmethod
    def extensions():
        return ("mp3", "mp4", "aac", "3gp", "flac", "mkv", "wav", "ogg", "m4a",
                "gsm", "mid", "xmf", "mxmf", "rtttl", "rtx", "ota", "imy")

    def __init__(self, **kwargs):
        self._mediaplayer = None
        self._completion_listener = None
        super().__init__(**kwargs)

    def load(self):
        self.unload()
        self._mediaplayer = MediaPlayer()
        if api_version >= 21:
            self._mediaplayer.setAudioAttributes(
                AudioAttributesBuilder()
                .setLegacyStreamType(AudioManager.STREAM_MUSIC)
                .build())
        else:
            self._mediaplayer.setAudioStreamType(AudioManager.STREAM_MUSIC)
        self._mediaplayer.setDataSource(self.source)
        self._completion_listener = OnCompletionListener(self._completion_callback)
        self._mediaplayer.setOnCompletionListener(self._completion_listener)
        try:  #edit to prevent crashes when fail to load
            self._mediaplayer.prepare()
            self.failedload = False
        except:
            self.stop()
            self.unload()
            self.failedload = True

    def unload(self):
        if self._mediaplayer:
            self._mediaplayer.release()
            self._mediaplayer = None

    def play(self):
        if not self._mediaplayer:
            return
        self._mediaplayer.start()
        super().play()

    def stop(self):
        if not self._mediaplayer:
            return
        if self._mediaplayer.isPlaying():  #edit to prevent crashes when fail to load
            self._mediaplayer.stop()
            self._mediaplayer.prepare()
        super().stop()

    def seek(self, position):
        if not self._mediaplayer:
            return
        self._mediaplayer.seekTo(float(position) * 1000)

    def get_pos(self):
        if self._mediaplayer:
            return self._mediaplayer.getCurrentPosition() / 1000.
        return super().get_pos()

    def on_volume(self, instance, volume):
        if self._mediaplayer:
            volume = float(volume)
            self._mediaplayer.setVolume(volume, volume)

    def _completion_callback(self):
        super().stop()

    def _get_length(self):
        if self._mediaplayer:
            return self._mediaplayer.getDuration() / 1000.
        return super()._get_length()

    def on_loop(self, instance, loop):
        if self._mediaplayer:
            self._mediaplayer.setLooping(loop)
