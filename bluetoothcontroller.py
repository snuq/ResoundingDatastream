from jnius import autoclass, PythonJavaClass, java_method


class CallbackWrapper(PythonJavaClass):
    __javacontext__ = "app"
    __javainterfaces__ = ["org/kivy/CallbackWrapper"]

    receive_play_toggle = None
    receive_stop = None
    receive_next = None
    receive_previous = None
    receive_forward = None
    receive_backward = None

    @java_method("(Ljava/lang/String;)V")
    def button_pressed(self, button):
        #button may be one of: play, pause, stop, next, previous, forward, backward
        if button in ['play', 'pause'] and self.receive_play_toggle:
            self.receive_play_toggle()
        elif button == 'stop' and self.receive_stop:
            self.receive_stop()
        elif button == 'next' and self.receive_next:
            self.receive_next()
        elif button == 'previous' and self.receive_previous:
            self.receive_previous()
        elif button == 'forward' and self.receive_forward:
            self.receive_forward()


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


def run_function_on_android_thread(function, *args, **kwargs):
    HandlerThread = autoclass("android.os.HandlerThread")
    Handler = autoclass("android.os.Handler")
    read_thread = HandlerThread("")
    read_thread.start()
    looper = read_thread.getLooper()
    handler = Handler(looper)
    handler.post(Runnable(function, read_thread, *args, **kwargs))


def start_media_session(activity, main_callback=None):
    if main_callback is None:
        main_callback = CallbackWrapper()

    #set up media session and required elements to be able to receive media button events
    MediaSession = autoclass('android.media.session.MediaSession')
    session = MediaSession(activity, "MediaButtonsTest")
    CustomMediaSessionCallback = autoclass('org.kivy.CustomMediaCallback')
    callback = CustomMediaSessionCallback(main_callback)
    session.setCallback(callback)

    #set up playback state to receive media buttons
    PlaybackState = autoclass('android.media.session.PlaybackState')
    PlaybackStateBuilder = autoclass('android.media.session.PlaybackState$Builder')
    playback_state = PlaybackStateBuilder()
    playback_state.setActions(PlaybackState.ACTION_PLAY + PlaybackState.ACTION_STOP + PlaybackState.ACTION_PAUSE + PlaybackState.ACTION_PLAY_PAUSE + PlaybackState.ACTION_SKIP_TO_NEXT + PlaybackState.ACTION_SKIP_TO_PREVIOUS + PlaybackState.ACTION_REWIND + PlaybackState.ACTION_FAST_FORWARD)
    playback_state.setState(PlaybackState.STATE_PLAYING, 0, 1.0)
    playback_state = playback_state.build()
    session.setPlaybackState(playback_state)

    session.setActive(True)
    return session
