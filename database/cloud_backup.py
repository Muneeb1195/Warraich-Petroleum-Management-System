from pathlib import Path
from datetime import datetime
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

from database.settings import settings
from utils.paths import config_dir, app_root

TOKEN_PATH = config_dir() / "cloud_token.json"
CLIENT_SECRETS_PATH = app_root() / "client_secrets.json"
BACKUP_FOLDER_NAME = "Warraich Petroleum Backups"


def get_auth_url():
    """Get Google OAuth URL. Returns (gauth, url)."""
    if not CLIENT_SECRETS_PATH.exists():
        raise FileNotFoundError(
            f"client_secrets.json not found.\n\n"
            f"1. Go to https://console.cloud.google.com/\n"
            f"2. Enable Google Drive API for your project\n"
            f"3. Create OAuth credentials (Desktop app type)\n"
            f"4. Download the JSON\n"
            f"5. Save it as:\n   {CLIENT_SECRETS_PATH}"
        )

    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    gauth = GoogleAuth()
    url = gauth.GetAuthUrl()
    return gauth, url


def authenticate(gauth, auth_code):
    """Complete authentication with authorization code from user."""
    gauth.Auth(auth_code)
    gauth.SaveCredentialsFile(str(TOKEN_PATH))
    return GoogleDrive(gauth)


def _get_drive():
    if not CLIENT_SECRETS_PATH.exists():
        raise FileNotFoundError(
            f"client_secrets.json not found.\n\n"
            f"1. Go to https://console.cloud.google.com/\n"
            f"2. Enable Google Drive API for your project\n"
            f"3. Create OAuth credentials (Desktop app type)\n"
            f"4. Download the JSON\n"
            f"5. Save it as:\n   {CLIENT_SECRETS_PATH}"
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
