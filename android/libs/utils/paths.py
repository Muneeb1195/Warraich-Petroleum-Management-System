import sys
import os
from pathlib import Path


def _is_frozen():
    return getattr(sys, "frozen", False)


def _app_dir():
    try:
        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        context = PythonActivity.mActivity
        return Path(context.getFilesDir().getAbsolutePath())
    except Exception:
        pass
    return Path(__file__).resolve().parent.parent


def app_root():
    if _is_frozen():
        return Path(sys.executable).resolve().parent
    return _app_dir()


def data_dir():
    base = _app_dir()
    return base / "data"


def config_dir():
    base = _app_dir()
    return base / "config"


def docs_dir():
    base = _app_dir()
    (base / "reports").mkdir(parents=True, exist_ok=True)
    return base / "reports"


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
    p = config_dir() / name
    if p.exists():
        return p
    return app_root() / name
