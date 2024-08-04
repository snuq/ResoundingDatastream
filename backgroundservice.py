import time
from oscpy.server import OSCThreadServer
from oscpy.client import OSCClient
from jnius import autoclass
from audio.songqueue import SongQueue

NativeInvocationHandler = autoclass('org.jnius.NativeInvocationHandler')
function_queue = []
osc_port = 30107

app_paused = False
from android.broadcast import BroadcastReceiver
Intent = autoclass('android.content.Intent')

stopping = False


def log(*message):
    #print(*message)
    pass


log('init')
last_play = time.time()
plays = 0


def on_song_position(message):
    #log('send on song position', message)
    osc_client.send_message(b"/on_song_position", [str(message).encode("utf8")])


def on_queue_index(message):
    log('send on queue index', message)
    osc_client.send_message(b"/on_queue_index", [str(message).encode("utf8")])


def on_next_queue_index(message):
    log('send on next queue index', message)
    osc_client.send_message(b"/on_next_queue_index", [str(message).encode("utf8")])


def on_playing(message):
    log('send on playing', message)
    osc_client.send_message(b"/on_playing", [str(message).encode("utf8")])


def on_stop(*_):
    log('send on stop')
    osc_client.send_message(b"/on_stop", [''.encode("utf8")])
    global stopping
    stopping = True


def on_play(*_):
    log('send on play')
    osc_client.send_message(b"/on_play", [''.encode("utf8")])


song_queue = SongQueue()
song_queue.autoupdate = False
song_queue.setup()
song_queue.on_song_position_function = on_song_position
song_queue.on_queue_index_function = on_queue_index
song_queue.on_next_queue_index_function = on_next_queue_index
song_queue.on_playing_function = on_playing
song_queue.on_stop_function = on_stop
song_queue.on_play_function = on_play


def receive_set_queue(message):
    global song_queue
    global function_queue
    queue_string, rating_string = message.split(' || ')
    queue = queue_string.split(' | ')
    ratings = rating_string.split(' | ')
    ratings = [int(rating) for rating in ratings]
    log('receive set queue', len(queue))
    function_queue.append([song_queue.set_queue, [queue, ratings], None])


def receive_add_queue(message):
    global song_queue
    global function_queue
    queue_string, rating_string = message.split(' || ')
    queue = queue_string.split(' | ')
    ratings = rating_string.split(' | ')
    ratings = [int(rating) for rating in ratings]
    log('receive set queue', len(queue))
    function_queue.append([song_queue.add_queue, [queue, ratings], None])


def receive_update_index(message):
    global song_queue
    global function_queue
    log('receive update index', message)
    function_queue.append([song_queue.update_index, int(message), None])


def receive_set_index(message):
    global song_queue
    global function_queue
    log('receive set index', message)
    function_queue.append([song_queue.set_index, int(message), None])


def receive_set_position(message):
    global song_queue
    global function_queue
    log('receive set position', message)
    function_queue.append([song_queue.set_position, float(message), None])


def receive_set_volume(message):
    global song_queue
    global function_queue
    log('receive set volume', message)
    function_queue.append([song_queue.set_volume, float(message), None])


def receive_set_playback_mode(message):
    global song_queue
    global function_queue
    log('receive set playback mode', message)
    function_queue.append([song_queue.set_playback_mode, message, None])


def receive_set_skiponestar(message):
    global song_queue
    global function_queue
    log('receive set skiponestar', message)
    skiponestar = message == 'True'
    function_queue.append([song_queue.set_skiponestar, skiponestar, None])


def receive_set_scrobbletime(message):
    global song_queue
    global function_queue
    log('receive set scrobbletime', message)
    function_queue.append([song_queue.set_scrobbletime, float(message), None])


def receive_set_next_queue_index(message):
    global song_queue
    global function_queue
    log('receive set next queue index', message)
    function_queue.append([song_queue.set_next_queue_index, int(message), None])


def receive_play(message=None):
    global song_queue
    global function_queue
    global last_play
    global plays
    plays += 1
    last_play = time.time()
    log('receive play')
    function_queue.append([song_queue.play, None, None])


def receive_play_toggle(message=None):
    global song_queue
    global function_queue
    log('receive play toggle')
    function_queue.append([song_queue.play_toggle, None, None])


def receive_pause(message=None):
    global song_queue
    global function_queue
    log('receive pause')
    function_queue.append([song_queue.pause, None, 'pause'])


def receive_stop(message=None):
    global song_queue
    global function_queue
    log('receive stop')
    function_queue.append([song_queue.stop, None, 'stop'])


def receive_next(message=None):
    global song_queue
    global function_queue
    log('receive next')
    function_queue.append([song_queue.next, False, None])


def receive_next_auto(message=None):
    global song_queue
    global function_queue
    log('receive next auto')
    function_queue.append([song_queue.next, True, None])


def receive_previous(message=None):
    global song_queue
    global function_queue
    log('receive previous')
    function_queue.append([song_queue.previous, None, None])


def receive_resend(message=None):
    global song_queue
    global function_queue
    log('receive resend')
    function_queue.append([song_queue.resend, None, None])


def receive_ping(*_):
    osc_client.send_message(b"/on_ping", [''.encode("utf8")])


osc_client = OSCClient("localhost", osc_port)
osc_server = OSCThreadServer(encoding="utf8")
osc_server.listen("localhost", port=osc_port + 1, default=True)
osc_server.bind(b"/set_queue", receive_set_queue)
osc_server.bind(b"/add_queue", receive_add_queue)
osc_server.bind(b"/update_index", receive_update_index)
osc_server.bind(b"/set_index", receive_set_index)
osc_server.bind(b"/set_position", receive_set_position)
osc_server.bind(b"/set_volume", receive_set_volume)
osc_server.bind(b"/set_playback_mode", receive_set_playback_mode)
osc_server.bind(b"/set_skiponestar", receive_set_skiponestar)
osc_server.bind(b"/set_scrobbletime", receive_set_scrobbletime)
osc_server.bind(b"/set_next_queue_index", receive_set_next_queue_index)
osc_server.bind(b"/play", receive_play)
osc_server.bind(b"/pause", receive_pause)
osc_server.bind(b"/stop", receive_stop)
osc_server.bind(b"/next", receive_next)
osc_server.bind(b"/next_auto", receive_next_auto)
osc_server.bind(b"/previous", receive_previous)
osc_server.bind(b"/resend", receive_resend)
osc_server.bind(b"/ping", receive_ping)

osc_client.send_message(b"/on_started", [''.encode("utf8")])


def on_headset_plug(context, intent):
    state = intent.getIntExtra("state", -1)
    global last_play
    global plays
    time_since_play = time.time() - last_play
    if time_since_play > 0.5 and plays == 1:  #unplug gets triggered right after first play for some reason?? dont pause if play just started
        if state == 0:
            log('headset unplugged')
            function_queue.append([song_queue.pause, None, 'pause'])
        else:
            log('headset plugged')


headset_plug_broadcaster = BroadcastReceiver(on_headset_plug, actions=[Intent.ACTION_HEADSET_PLUG])
headset_plug_broadcaster.start()


while not stopping:
    while function_queue:
        function, argument, extra = function_queue.pop(0)
        function(argument)
    song_queue.update()
    time.sleep(0.1)

stop_start_time = time.time()
while True:
    #wait for service to be stopped so it doesnt crash
    if time.time() - stop_start_time > 1:
        #try to resume the main app so it can end the service
        pythonactivity = autoclass("org.kivy.android.PythonService")
        m_service = pythonactivity.mService
        context = m_service.getApplicationContext()
        package_name = context.getPackageName()
        package_manager = context.getPackageManager()
        intent = package_manager.getLaunchIntentForPackage(package_name)
        context.startActivity(intent)

        on_stop()
        on_playing(False)
        on_song_position(0)
        on_queue_index(song_queue.queue_index)
        on_next_queue_index(song_queue.next_queue_index)
        m_service.stopSelf()  #ends the service
    time.sleep(0.1)
