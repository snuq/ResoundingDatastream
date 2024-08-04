[app]
title = Resounding Datastream
package.name = resoundingdatastream
package.domain = com.snuq
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt
#source.exclude_exts = spec
source.exclude_dirs = src, temp, .git, .idea
version = 0.9
requirements = python3,kivy,plyer,oscpy
presplash.filename = %(source.dir)s/data/splash.png
icon.filename = %(source.dir)s/data/icon.png
orientation = portrait
services = resoundingdatastreamservice:backgroundservice.py:foreground
fullscreen = 0
android.presplash_color = #000000
#icon.adaptive_foreground.filename = %(source.dir)s/data/icon_fg.png
#icon.adaptive_background.filename = %(source.dir)s/data/icon_bg.png
android.permissions = android.permission.INTERNET, android.permission.WAKE_LOCK, android.permission.FOREGROUND_SERVICE
android.add_resources = data/iconbw.png:drawable/iconbw.png
android.add_src = java
android.api = 34
#android.minapi = 21
#android.sdk = 20
#android.ndk = 23b
#android.ndk_api = 21
android.archs = arm64-v8a, armeabi-v7a

#   hopefully at some point python for android can fix the broken manifest variables, and can use this setting... until then, need to edit:
#       .buildozer/android/platform/build-arm64-v8a_armeabi-v7a/dists/resoundingdatastream/templates/AndroidManifest.tmpl.xml
#       and add: android:usesCleartextTraffic="true"
#       inside <application> tag variables
#android.extra_manifest_application_arguments = applicationmanifestextras.txt


[buildozer]
log_level = 2
warn_on_root = 1
