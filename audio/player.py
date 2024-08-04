from kivy.utils import platform
if platform == 'android':
    #from .songqueue import SongQueue
    from .songqueueandroid import SongQueueAndroid as SongQueue
else:
    from .songqueue import SongQueue

