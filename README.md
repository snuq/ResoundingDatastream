# Resounding Datastream  
A Subsonic and Navidrome music player client  

This program is released under the GNU General Public License  


Note: This is still in beta and has some issues that need to be fixed, especially on android.

Current Todo (Before release):
* need to reduce how often lists are downloaded, especially complete song list
* need to figure out how to receive wired headset media key on android
* needs to announce playing song title/artist to android - partially implemented, does not auto-update
* implement music folder support in interface - use database.get_music_folders(), set database.music_folder
* bluetooth pause needs to be able to resume when app is not active
* May have issues with foreground service in android 14+, need to specify service type
    * https://developer.android.com/develop/background-work/services/fgs/service-types#media
    * needs a service type? "android:foregroundServiceType mediaPlayback", probably needs to be called in manifest file somewhere?
    * need permission "FOREGROUND_SERVICE_MEDIA_PLAYBACK"?
    * maybe need to edit .buildozer/android/platform/python-for-android/pythonforandroid/bootstraps/common/build/src/main/java/org/kivy/android to pass in "FOREGROUND_SERVICE_TYPE_MEDIA_PLAYBACK" to the "startForeground" function call... somehow
* oh yeah, and make a proper readme too...


Programmed in Python  
Artwork created in Blender, Gimp and Inkscape  

Libraries Used:  
* Kivy framework  


Created by Hudson Barkley (Snu/snuq/Aritodo)  
