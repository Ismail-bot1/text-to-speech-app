[app]
title = Text to Speech
package.name = texttospeech
package.domain = org.texttospeech
source.dir = .
source.main = android_app.py
source.include_exts = py,png,jpg,kv,atlas,mp3
version = 1.0

requirements = python3,kivy==2.2.1,kivymd==1.1.1,edge-tts==6.1.9

orientation = portrait
fullscreen = 0
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 31
android.minapi = 21
android.ndk = 23b
android.sdk = 31

android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 0