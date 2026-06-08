[app]

title = Warraich Petroleum
package.name = WarraichPetroleum
package.domain = com.warraichpetroleum

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,otf
source.exclude_exts = spec
source.exclude_dirs = tests, venv, __pycache__, .git

version = 1.0.0

requirements = python3,kivy==2.2.0,openpyxl,requests

presplash.filename = assets/splash.png
icon.filename = assets/icon.png

orientation = landscape
osx.package_name = WarraichPetroleum

android.permissions = INTERNET
android.api = 34
android.minapi = 21
android.sdk = 34
android.ndk = 25
android.ndk_version = 25.2.9519653
android.archs = arm64-v8a
android.accept_sdk_license = True
android.install_from_store = True
android.enable_p4a = True
# android.gradle_dependencies =

ios.codesign.debug = auto
ios.codesign.release = auto

[buildozer]

log_level = 2
warn_on_root = 1
