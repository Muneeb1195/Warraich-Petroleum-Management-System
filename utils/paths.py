import sys
import os
from pathlib import Path

APP_NAME = "WarraichPetroleum"


def _is_frozen():
    return getattr(sys, "frozen", False)


def app_root():
    if _is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def data_dir():
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return base / APP_NAME / "data"
    base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / APP_NAME


def config_dir():
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return base / APP_NAME / "config"
    base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / APP_NAME.lower()


def docs_dir():
    if sys.platform == "win32":
        base = Path(os.environ.get("USERPROFILE", Path.home())) / "Documents"
    else:
        base = Path.home() / "Documents"
    return base / APP_NAME


def resource_path(name):
    if _is_frozen():
        p = Path(sys._MEIPASS) / name
        if p.exists():
            return p
    p = app_root() / name
    if p.exists():
        return p
    return app_root() / name


def user_file_path(name):
    if _is_frozen():
        p = app_root() / name
        if p.exists():
            return p
    p = config_dir() / name
    if p.exists():
        return p
    return app_root() / name
