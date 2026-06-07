import json
import os
import tempfile
from pathlib import Path
from datetime import datetime
import threading

from pydrive2.auth import GoogleAuth, ClientRedirectServer, ClientRedirectHandler
from pydrive2.drive import GoogleDrive

from database.settings import settings
from utils.paths import config_dir

TOKEN_PATH = config_dir() / "cloud_token.json"
BACKUP_FOLDER_NAME = "Warraich Petroleum Backups"

_CLIENT_CONFIG_HEX = (
    "2c431b1c121d02043c00105055174716015b555c40080816505b4b505d645642475e"
    "5553435f0a1d595133054a1756510905641447065f54091803544407056f0a47020d"
    "075a04224b15021f1f4b12025d575e512212170002060d1c350b005c0c0308574110"
    "40405b3d0411063e00074a6a4703131d1e041c0e5a1d425123131d1e041c0e4a7c47"
    "15071b043a001f5b1208163f15060212534c473106171d1a02110643555f5d533b04"
    "5c110e044c077f0a15071b04575a0c47445a167b43061d0a0c0d3725171d50554e0d"
    "01194243081b780e130715015146370a1b150309040504411e515b3a4e061d0a0c0d"
    "4a7c4715071b043a051f5d465b5032132d0a54595a3733000606301917194f08125a"
    "40231101484e46141f274b131d000b09100c4259411a340e1f5d0e08161c38575b04"
    "5e4306101f4643101875021e1b04071737230017000a18474f4f757f716707395f39"
    "2d393558020d2e013c3b54330453710662333701161008111c330d565e4d1e001104"
    "405551400814001b124b5933720d00061f564a5a015d5353583f0e010643341e15"
)
_CLIENT_CONFIG_KEY = b"WarraichPetroleum2024"


def _decode_client_config():
    raw = bytes.fromhex(_CLIENT_CONFIG_HEX)
    key = _CLIENT_CONFIG_KEY
    decoded = bytes(b ^ key[i % len(key)] for i, b in enumerate(raw))
    return json.loads(decoded.decode())


def _load_gauth_with_config():
    config = _decode_client_config()
    fd, path = tempfile.mkstemp(suffix=".json")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(config, f)
        gauth = GoogleAuth()
        gauth.LoadClientConfig(path)
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
    return gauth


def start_auth_flow():
    """Start Google OAuth with a local callback server.

    Returns (gauth, auth_url, server). When the user visits auth_url
    and grants access, the redirect is caught by the local server.
    Check server.query_params for the authorization code.
    """
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)

    gauth = _load_gauth_with_config()
    gauth.GetFlow()

    port = 8080
    while port <= 8090:
        try:
            httpd = ClientRedirectServer(("127.0.0.1", port), ClientRedirectHandler)
            break
        except OSError:
            port += 1
    else:
        raise RuntimeError("Could not find a free port for the callback server")

    httpd.query_params = None
    oauth_callback = f"http://127.0.0.1:{port}/"
    gauth.flow.redirect_uri = oauth_callback
    url = gauth.GetAuthUrl()

    def _handle():
        httpd.handle_request()

    threading.Thread(target=_handle, daemon=True).start()

    return gauth, url, httpd


def authenticate(gauth, auth_code):
    """Complete authentication with authorization code from user."""
    gauth.Auth(auth_code)
    gauth.SaveCredentialsFile(str(TOKEN_PATH))
    return GoogleDrive(gauth)


def _get_drive():
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    gauth = _load_gauth_with_config()

    if TOKEN_PATH.exists():
        gauth.LoadCredentialsFile(str(TOKEN_PATH))

    if gauth.credentials is None:
        raise RuntimeError(
            "Not authenticated. Go to Settings → Cloud Backup and connect your Google account.")
    elif gauth.access_token_expired:
        gauth.Refresh()
        gauth.SaveCredentialsFile(str(TOKEN_PATH))
    else:
        gauth.Authorize()

    return GoogleDrive(gauth)


def upload_to_drive(local_path):
    try:
        drive = _get_drive()
        folder_id = _ensure_backup_folder(drive)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"WarraichPetroleum_{timestamp}.db"

        file_drive = drive.CreateFile({
            "title": filename,
            "parents": [{"id": folder_id}],
        })
        file_drive.SetContentFile(str(local_path))
        file_drive.Upload()

        settings.set("Cloud", "last_cloud_backup", datetime.now().isoformat())
        settings.save()

        return True, filename
    except Exception as e:
        return False, str(e)


def _ensure_backup_folder(drive):
    query = f"title='{BACKUP_FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    file_list = drive.ListFile({"q": query}).GetList()
    if file_list:
        return file_list[0]["id"]

    folder = drive.CreateFile({
        "title": BACKUP_FOLDER_NAME,
        "mimeType": "application/vnd.google-apps.folder",
    })
    folder.Upload()
    return folder["id"]


def is_connected():
    return TOKEN_PATH.exists()


def has_secrets():
    return True


def disconnect():
    if TOKEN_PATH.exists():
        TOKEN_PATH.unlink()
    settings.set("Cloud", "last_cloud_backup", "")
    settings.save()
