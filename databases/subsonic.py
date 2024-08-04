import requests
import time
import datetime
import json
from kivy.utils import platform
from kivy.properties import *
from kivy.event import EventDispatcher
from kivy.clock import mainthread


#possible keys: id, name, albumCount, coverArt, artistImageUrl, album
artist_keys = ['id', 'name', 'albumCount']
artist_defaults = [None, None, 0]

#possible keys: id, parent, isDir, title, name, album, artist, year, genre, coverArt, starred, duration, playCount, created, artistId, userRating, songCount, isVideo, played, bpm, comment, sortName, mediaType, musicBrainzId, genres, replayGain
album_keys = ['id', 'name', 'artist', 'year', 'genre', 'starred', 'duration', 'playCount', 'artistId', 'userRating', 'songCount']
album_defaults = [None, None, '', 0, '', '', 0, 0, '', 0, 0]

#possible keys: id, parent, isDir, title, album, atist, track, year, genre, coverArt, size, contentType, suffix, starred, duration, bitRate, path, playCount, discNumber, created, albumId, artistId, type, userRating, isVideo, played, bpm, comment, sortName, mediaType, musicBrainzId, genres, replayGain
song_keys = ['id', 'title', 'album', 'artist', 'track', 'year', 'genre', 'starred', 'duration', 'playCount', 'discNumber', 'albumId', 'artistId', 'userRating', 'created']
song_defaults = [None, None, '', '', 0, 0, '', '', 0, 0, 0, '', '', 0, '']

#possible keys: id, name, comment, songCount, duration, public, owner, created, changed, coverArt
playlist_keys = ['id', 'name', 'songCount', 'duration']
playlist_defaults = [None, None, 0, 0]


def get_utc_offset():
    current_time = time.time()
    utc_offset = datetime.datetime.fromtimestamp(current_time) - datetime.datetime.utcfromtimestamp(current_time)
    return utc_offset


def parse_song_created(song_created, utc_offset=None):
    try:
        database_date_orig = song_created
        database_date = database_date_orig.split('.')[0]
        if database_date_orig.endswith('Z'):
            database_date = database_date + '+00:00'
        database_date_utc = datetime.datetime.fromisoformat(database_date)
        if utc_offset is None:
            utc_offset = get_utc_offset()
        database_date = database_date_utc + utc_offset
        database_timestamp = database_date.timestamp()
        return database_timestamp
    except:
        return None


def add_to_dict_list(dict_list, adding):
    for element in dict_list:
        for to_add in adding:
            element[to_add[0]] = to_add[1]
    return dict_list


def verify_dict(dictionary, elements, defaults=None, strict=True, remove=None):
    if dictionary is None:
        return None
    if remove is None:
        remove = []
    for element in remove:
        if element in dictionary.keys():
            del dictionary[element]
    if defaults is None:
        #no defaults, just check if all required elements are present
        if all(element in dictionary for element in elements):
            return dictionary
        return None
    else:
        for index, element in enumerate(elements):
            if element not in dictionary.keys():
                default = defaults[index]
                if default is None:
                    if strict:
                        return None
                    else:
                        default = ''
                dictionary[element] = default
        return dictionary


def verify_list(dict_list, elements, defaults=None, strict=True, remove=None):
    #checks all list items to verify that they have all dictionary elements
    #if defaults is provided, will replace missing elements with defaults, unless default is set to None, then list item is removed
    verified_list = []
    if dict_list is None:
        return None
    for item in dict_list:
        new_item = verify_dict(item, elements, defaults, strict=strict, remove=remove)
        if new_item is not None:
            verified_list.append(new_item)
    return verified_list


def verify_artist(dictionary, strict=True):
    return verify_dict(dictionary, artist_keys, defaults=artist_defaults, strict=strict)


def verify_artist_list(dict_list, strict=True):
    return verify_list(dict_list, artist_keys, defaults=artist_defaults, strict=strict)


def verify_album(dictionary, strict=True):
    return verify_dict(dictionary, album_keys, defaults=album_defaults, strict=strict)


def verify_album_list(dict_list, strict=True):
    return verify_list(dict_list, album_keys, defaults=album_defaults, strict=strict, remove=['parent'])


def verify_song(dictionary, strict=True):
    return verify_dict(dictionary, song_keys, defaults=song_defaults, strict=strict, remove=['parent', 'size'])


def verify_song_list(dict_list, strict=True):
    return verify_list(dict_list, song_keys, defaults=song_defaults, strict=strict, remove=['parent', 'size'])


def verify_playlist_list(dict_list, strict=True):
    return verify_list(dict_list, playlist_keys, defaults=playlist_defaults, strict=strict)


class ServerSettings:
    name = ''
    ip = '127.0.0.1'
    port = '4040'
    username = 'user'
    salt = ''
    password = ''
    suburl = 'rest'
    use_ssh = False

    def __init__(self, name='', ip='127.0.0.1', port='4040', username='user', password='', salt='', suburl='', use_ssh=False):
        self.name = name
        self.ip = ip
        self.port = port
        self.username = username
        self.salt = salt
        self.password = password
        self.suburl = suburl
        self.use_ssh = use_ssh


class Database(EventDispatcher):
    timeout = 4
    ident_string = 'ResoundingDatastream'
    version = '1.16.1'
    settings = ObjectProperty(allownone=True)
    status = StringProperty()
    cancel_load = BooleanProperty(False)
    allow_cancel = BooleanProperty(False)
    loading_status = StringProperty('')

    @mainthread
    def set_allow_cancel(self, status):
        self.allow_cancel = status

    def get_password(self):
        return self.settings.password

    def get_salt(self):
        return self.settings.salt

    def generate_url(self):
        if self.settings.use_ssh:
            starter = 'https://'
        else:
            starter = 'http://'
        return starter+self.settings.ip+':'+self.settings.port+'/'+self.settings.suburl+'/'

    def generate_params(self, params=None):
        if params is None:
            params = {}
        params['u'] = self.settings.username
        params['t'] = self.get_password()
        params['s'] = self.get_salt()
        params['v'] = self.version
        params['c'] = self.ident_string
        params['f'] = 'json'
        return params

    def get_request(self, request, params=None, stream=False, binary=False, timeout=None):
        if timeout is None:
            timeout = self.timeout
        params = self.generate_params(params)
        url = self.generate_url()
        try:
            if stream:
                response = requests.get(url+request, params=params, timeout=timeout, stream=True)
                response.raise_for_status()
                data = response
                error = None
            else:
                response = requests.get(url+request, params=params, timeout=timeout)
                response.raise_for_status()
                if binary:
                    data = response.content
                else:
                    data = response.text
                error = None
        except requests.exceptions.HTTPError:
            data = None
            error = 'Failed HTTP Request: '+str(response.status_code)
        except requests.exceptions.Timeout:
            data = None
            error = 'Connection Timed Out (Incorrect IP?)'
        except requests.exceptions.TooManyRedirects:
            data = None
            error = 'Too Many Redirections'
        except requests.exceptions.ConnectionError:
            data = None
            error = 'DNS Error Or Refused Connection (Incorrect Port?)'
        except Exception as e:
            data = None
            error = str(e)
        return error, data

    def send_request(self, request, params=None, timeout=None):
        result = self.get_request_format(request, params=params, timeout=timeout)
        if result is not None:
            result = result['status']
        return result

    def get_request_format(self, request, elements=None, params=None, timeout=None):
        if elements is None:
            elements = []
        error, data = self.get_request(request, params=params, timeout=timeout)
        if error is not None:
            self.status = error
            return None
        else:
            try:
                data = json.loads(data)  #convert to json from a string
                data = list(data.values())[0]  #strip out the root response, should be 'subsonic-response', but might not
                status = data['status']
                if status.lower() != 'ok':
                    error = "Error "+str(data['error']['code'])+': '+data['error']['message']
                    self.status = error
                    return None
                for element in elements:
                    data = data[element]
                self.status = 'Completed Request: '+request
                return data
            except Exception as e:
                self.status = 'Unable To Parse Response: '+str(e)
                return None

    def verify_params(self, param_names, values):
        params = {}
        for index, param in enumerate(param_names):
            if values[index] is not None:
                params[param] = values[index]
        return params

    def list_combine(self, start_data, subelement):
        data = []
        if start_data is None:
            return None
        for sublist in start_data:
            data.extend(sublist[subelement])
        return data

    #Server send communication functions
    def set_start_scan(self, fullscan=None, timeout=None):  #startScan
        result = self.send_request('startScan', params=self.verify_params(['fullScan'], [fullscan]), timeout=timeout)
        return result

    def set_favorite(self, id, timeout=None):  #star
        #id may be a string or a list of strings
        result = self.send_request('star', params={'id': id}, timeout=timeout)
        return result

    def set_unfavorite(self, id, timeout=None):  #unstar
        #id may be a string or a list of strings
        result = self.send_request('unstar', params={'id': id}, timeout=timeout)
        return result

    def set_rating(self, id, rating, timeout=None):  #setRating
        rating = int(round(rating))
        if rating > 5:
            rating = 5
        if rating < 0:
            rating = 0
        result = self.send_request('setRating', params={'id': id, 'rating': rating}, timeout=timeout)
        return result

    def set_playlist_add_song(self, playlistid, songid, timeout=None):  #updatePlaylist
        #songid may be a string or a list of strings
        result = self.send_request('updatePlaylist', params={'playlistId': playlistid, 'songIdToAdd': songid}, timeout=timeout)
        return result

    def set_playlist_remove_index(self, playlistid, songindex, timeout=None):  #updatePlaylist
        #songindex may be an integer or a list of integers
        result = self.send_request('updatePlaylist', params={'playlistId': playlistid, 'songIndexToRemove': songindex}, timeout=timeout)
        return result

    def set_playlist_name(self, playlistid, name, timeout=None):  #updatePlaylist
        result = self.send_request('updatePlaylist', params={'playlistId': playlistid, 'name': name}, timeout=timeout)
        return result

    def set_playlist_comment(self, playlistid, comment, timeout=None):  #updatePlaylist
        result = self.send_request('updatePlaylist', params={'playlistId': playlistid, 'comment': comment}, timeout=timeout)
        return result

    def set_playlist_public(self, playlistid, public_status, timeout=None):  #updatePlaylist
        result = self.send_request('updatePlaylist', params={'playlistId': playlistid, 'public': public_status}, timeout=timeout)
        return result

    def set_playlist_new(self, name, timeout=None):  #createPlaylist
        result = self.send_request('createPlaylist', params={'name': name}, timeout=timeout)
        return result

    def set_playlist_delete(self, playlistid, timeout=None):  #deletePlaylist
        result = self.send_request('deletePlaylist', params={'id': playlistid}, timeout=timeout)
        return result

    def set_scrobble(self, songid, timeout=None):  #scrobble
        #should be called whenever a song is streamed (after a few seconds)
        result = self.send_request('scrobble', params={'id': songid, 'submission': True}, timeout=timeout)
        return result

    def set_queue(self, songids, currentsongid, currentsongpos=0, timeout=None):  #savePlayQueue
        result = self.send_request('savePlayQueue', params={'id': songids, 'current': currentsongid, 'position': currentsongpos*1000}, timeout=timeout)
        return result

    #server get communication functions
    def get_queue(self, timeout=None):  #getPlayQueue
        #Returns a list of song dict items (queue list), a song id (current song id), and an integer (playback position)
        data = self.get_request_format('getPlayQueue', ['playQueue'], timeout=timeout)
        songs = None
        position = 0
        current = ''
        if data is not None:
            if 'entry' in data.keys():
                songs = verify_song_list(data['entry'])
            if 'position' in data.keys():
                position = data['position']
            if 'current' in data.keys():
                current = data['current']
        return songs, current, position

    def get_download(self, songid, timeout=None):
        error, response = self.get_request('download', binary=True, params={'id': songid}, timeout=timeout)
        if error is not None:
            self.status = error
            return None
        return response

    def get_stream_url(self, songid):
        if platform == 'android':
            format_option = '&format=mp3'  #force mp3 reencoding since android media player wont play ogg
        else:
            format_option = ''
        url = self.generate_url()+'stream?u='+self.settings.username+'&t='+self.get_password()+'&s='+self.get_salt()+'&v='+self.version+'&c='+self.ident_string+'&id='+songid+format_option
        return url

    def get_stream(self, songid, timeout=None):  #stream
        error, response = self.get_request('stream', params={'id': songid}, stream=True, timeout=timeout)
        if error is not None:
            self.status = error
            return None
        return response

    def get_search(self, query, song_size=None, song_offset=None, artist_size=None, artist_offset=None, album_size=None, album_offset=None, timeout=None):  #search3
        data = self.get_request_format('search3', ['searchResult3'], params=self.verify_params(['query', 'artistCount', 'artistOffset', 'albumCount', 'albumOffset', 'songCount', 'songOffset'], [query, artist_size, artist_offset, album_size, album_offset, song_size, song_offset]), timeout=timeout)
        return data

    def get_search_artist(self, query, size=20, offset=0, timeout=None):
        data = self.get_search(query, song_size=0, album_size=0, artist_size=size, artist_offset=offset, timeout=timeout)
        if data is None:
            return None
        if data and 'artist' in data.keys():
            data = data['artist']
        else:
            data = []
        return verify_artist_list(data)

    def get_search_album(self, query, size=20, offset=0, timeout=None):
        data = self.get_search(query, song_size=0, album_size=size, artist_size=0, album_offset=offset, timeout=timeout)
        if data is None:
            return None
        if data and 'album' in data.keys():
            data = data['album']
        else:
            data = []
        return verify_album_list(data)

    def get_search_song(self, query, size=20, offset=0, timeout=None):
        data = self.get_search(query, song_size=size, album_size=0, artist_size=0, song_offset=offset, timeout=timeout)
        if data is None:
            return None
        if data and 'song' in data.keys():
            data = data['song']
        else:
            data = []
        return verify_song_list(data)

    def get_modified(self, timeout=None):
        newest_album = self.get_album_list_newest(size=1, timeout=timeout)
        try:
            created = newest_album[0]['created']
            modified_timestamp = parse_song_created(created)
            return modified_timestamp
        except:
            pass
        return None

    def get_ping(self, timeout=None):  #ping
        data = self.get_request_format('ping', timeout=timeout)
        return data

    def get_cover_art(self, id, timeout=None):
        #can get album, song or artist
        data = self.get_request('getCoverArt', params={'id': id}, binary=True, timeout=timeout)
        data = data[1]
        return data

    def get_scan_status(self, timeout=None):  #getScanStatus
        data = self.get_request_format('getScanStatus', ['scanStatus'], timeout=timeout)
        verified = verify_dict(data, ['scanning', 'count', 'folderCount', 'lastScan'])
        if verified:
            return data
        else:
            self.status = 'Scan Status Response Malformed'

    def get_genre_list(self, timeout=None):  #getGenres
        #list of dict, keys:
        #   *value: genre name
        #   *songCount: songs with genre
        #   *albumCount: albums with genre
        data = self.get_request_format('getGenres', ['genres', 'genre'], timeout=timeout)
        return verify_list(data, ['value', 'songCount', 'albumCount'])

    def get_playlist_list(self, timeout=None):  #getPlaylists
        data = self.get_request_format('getPlaylists', ['playlists', 'playlist'], timeout=timeout)
        return verify_playlist_list(data)

    def get_artist_list(self, timeout=None):  #getArtists
        #list of artist dict
        data = self.get_request_format('getArtists', ['artists', 'index'], timeout=timeout)
        data = self.list_combine(data, 'artist')
        return verify_artist_list(data)

    def get_album_list(self, list_type='alphabeticalByName', size=None, offset=None, from_year=None, to_year=None, genre=None, timeout=None):  #getAlbumList2
        #returns list of album dict elements
        #list_type must be: random, newest, frequent, recent, starred, alphabeticalByName, alphabeticalByArtist, byYear, byGenre
        data = self.get_request_format('getAlbumList2', ['albumList2', 'album'], params=self.verify_params(['type', 'size', 'offset', 'fromYear', 'toYear', 'genre'], [list_type, size, offset, from_year, to_year, genre]), timeout=timeout)
        return verify_album_list(data)

    def get_full_list(self, get_function, max_size=500, **kwargs):
        #grabs a full list by calling get_function multiple times if needed
        offset = 0
        chunk = 1
        list_items = []
        self.cancel_load = False
        self.set_allow_cancel(True)
        while True:
            self.loading_status = 'Loading items part '+str(chunk)
            if self.cancel_load:
                return None
            data = get_function(size=max_size, offset=offset, **kwargs)
            if data is None:
                return None
            list_items.extend(data)
            if len(data) != max_size:
                break
            offset = offset + max_size
            chunk += 1
        self.loading_status = ''
        self.set_allow_cancel(False)
        return list_items

    def get_album_list_genre(self, genre, size=None, offset=None, timeout=None):
        return self.get_album_list(list_type='byGenre', genre=genre, size=size, offset=offset, timeout=timeout)

    def get_album_list_random(self, size=None, offset=None, timeout=None):
        return self.get_album_list(list_type='random', size=size, offset=offset, timeout=timeout)

    def get_album_list_newest(self, size=None, offset=None, timeout=None):
        return self.get_album_list(list_type='newest', size=size, offset=offset, timeout=timeout)

    def get_album_list_frequent(self, size=None, offset=None, timeout=None):
        return self.get_album_list(list_type='frequent', size=size, offset=offset, timeout=timeout)

    def get_album_list_recent(self, size=None, offset=None, timeout=None):
        return self.get_album_list(list_type='recent', size=size, offset=offset, timeout=timeout)

    def get_album_list_favorite(self, timeout=None):
        #list of album dict
        data = self.get_request_format('getStarred2', ['starred2', 'album'], timeout=timeout)
        return verify_album_list(data)

    def get_album_list_artist(self, artistid, timeout=None):
        artist_info = self.get_artist_info(artistid, timeout=timeout)
        if artist_info is None:
            return None
        if 'album' in artist_info.keys():
            albums = artist_info['album']
            return verify_album_list(albums)
        return []

    def get_playlist(self, playlistid, timeout=None):  #getPlaylist
        #returns a playlist element, and list of song dict elements
        data = self.get_request_format('getPlaylist', ['playlist'], params={'id': playlistid}, timeout=timeout)
        if not data:
            return None
        if 'entry' in data.keys():
            songs = data['entry']
        else:  #if playlist is empty, 'entry' key will not exist
            songs = []
        songs = verify_song_list(songs)
        playlist = verify_dict(data, playlist_keys, defaults=playlist_defaults, strict=True, remove=['entry'])
        return playlist, songs

    def get_song_list_random(self, size=None, from_year=None, to_year=None, genre=None, timeout=None):  #getRandomSongs
        #list of song dict
        data = self.get_request_format('getRandomSongs', ['randomSongs', 'song'], params=self.verify_params(['size', 'genre', 'fromYear', 'toYear'], [size, genre, from_year, to_year]), timeout=timeout)
        return verify_song_list(data)

    def get_song_list_genre(self, genre, size=None, offset=None, timeout=None):  #getSongsByGenre
        #returns list of song dicts
        data = self.get_request_format('getSongsByGenre', ['songsByGenre', 'song'], params=self.verify_params(['genre', 'count', 'offset'], [genre, size, offset]), timeout=timeout)
        return verify_song_list(data)

    def get_song_list_favorite(self, timeout=None):  #getStarred2
        #list of song dict
        data = self.get_request_format('getStarred2', ['starred2', 'song'], timeout=timeout)
        return verify_song_list(data)

    def get_song_list_artist(self, artistid, timeout=None):
        artist_info = self.get_artist_info(artistid, timeout=timeout)
        if artist_info is None:
            return None
        if not artist_info or 'album' not in artist_info.keys():
            return []
        albums = verify_album_list(artist_info['album'])
        if albums is None:
            albums = []
        albums = sorted(albums, key=lambda a: a['name'])
        songs = []
        for album in albums:
            album_info = self.get_album_info(album['id'])
            if album_info is None:
                return None
            if 'song' in album_info.keys():
                songs.extend(album_info['song'])
        return verify_song_list(songs)

    def get_song_list_album(self, albumid, timeout=None):
        albumdata = self.get_album_info(albumid, timeout=timeout)
        if albumdata is None:
            return None
        if albumdata and 'song' in albumdata.keys():
            songs = albumdata['song']
            return verify_song_list(songs)
        return []

    def get_song_info(self, songid, timeout=None):  #getSong
        #returns song type dictionary
        data = self.get_request_format('getSong', ['song'], params={'id': songid}, timeout=timeout)
        return verify_song(data)

    def get_artist_info(self, artistid, timeout=None):  #getArtist
        #returns artist type dictionary, also includes 'album' key with a list of album dictionary elements that this artist has
        data = self.get_request_format('getArtist', ['artist'], params={'id': artistid}, timeout=timeout)
        return verify_artist(data)

    def get_album_info(self, albumid, timeout=None):  #getAlbum
        #returns album type dictionary, also includes 'song' key with a list of song dictionary elements in this album
        data = self.get_request_format('getAlbum', ['album'], params={'id': albumid}, timeout=timeout)
        return verify_album(data)
