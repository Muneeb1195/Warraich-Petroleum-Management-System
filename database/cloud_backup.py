from pathlib import Path
from datetime import datetime
import http.server
import threading
import urllib.parse

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

from database.settings import settings
from utils.paths import config_dir, app_root

TOKEN_PATH = config_dir() / "cloud_token.json"
CLIENT_SECRETS_PATH = app_root() / "client_secrets.json"
BACKUP_FOLDER_NAME = "Warraich Petroleum Backups"


class _OAuthHandler(http.server.BaseHTTPRequestHandler):
    server_version = "OAuthCallback/1.0"

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        code = params.get("code", [None])[0]
        if code:
            self.server.auth_code = code

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Connection", "close")
        self.end_headers()
        if code:
            self.wfile.write(
                b"<html><body style='font-family:sans-serif;text-align:center;padding:40px;'>"
                b"<h2>Authorization complete!</h2>"
                b"<p>You can close this window and return to the app.</p>"
                b"</body></html>"
            )
        else:
            self.wfile.write(
                b"<html><body style='font-family:sans-serif;text-align:center;padding:40px;'>"
                b"<h2>No authorization code found</h2>"
                b"<p>Close this window and try again.</p>"
                b"</body></html>"
            )

    def log_message(self, format, *args):
        pass


def start_auth_flow():
    """Start Google OAuth with a local callback server.

    Returns (gauth, auth_url, server). When the user visits auth_url
    and grants access, the redirect is caught by the local server.
    Check server.auth_code for the result, then call shutdown().
    """
    if not CLIENT_SECRETS_PATH.exists():
        raise FileNotFoundError(
            f"client_secrets.json not found.\n\n"
            f"Set up Google Drive API:\n"
            f"1. Go to https://console.cloud.google.com/\n"
            f"2. Enable Google Drive API\n"
            f"3. Create OAuth credentials (Desktop app type)\n"
            f"4. Download JSON → save as:\n"
            f"   {CLIENT_SECRETS_PATH}\n\n"
            f"5. In Google Cloud Console → OAuth consent screen →\n"
            f"   Add your email as a Test user"
        )

    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)

    server = http.server.HTTPServer(("127.0.0.1", 0), _OAuthHandler)
    server.auth_code = None
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    redirect_uri = f"http://127.0.0.1:{port}/"
    gauth = GoogleAuth()
    gauth.redirect_uri = redirect_uri
    url = gauth.GetAuthUrl()

    return gauth, url, server


def authenticate(gauth, auth_code):
    """Complete authentication with authorization code from user."""
    gauth.Auth(auth_code)
    gauth.SaveCredentialsFile(str(TOKEN_PATH))
    return GoogleDrive(gauth)


def _get_drive():
    if not CLIENT_SECRETS_PATH.exists():
        raise FileNotFoundError(
            f"client_secrets.json not found.\n\n"
            f"Set up Google Drive API:\n"
            f"1. Go to https://console.cloud.google.com/\n"
            f"2. Enable Google Drive API\n"
            f"3. Create OAuth credentials (Desktop app type)\n"
            f"4. Download JSON → save as:\n"
            f"   {CLIENT_SECRETS_PATH}\n\n"
            f"5. In Google Cloud Console → OAuth consent screen →\n"
            f"   Add your email as a Test user"
        )

    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    gauth = GoogleAuth()

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
    if not CLIENT_SECRETS_PATH.exists():
        return False, "client_secrets.json not found. Set up in Settings → Cloud Backup."
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
    return CLIENT_SECRETS_PATH.exists()


def disconnect():
    if TOKEN_PATH.exists():
        TOKEN_PATH.unlink()
    settings.set("Cloud", "last_cloud_backup", "")
    settings.save()
