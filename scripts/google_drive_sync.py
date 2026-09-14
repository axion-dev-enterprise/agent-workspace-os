#!/usr/bin/env python3
"""
Google Drive Workspace Synchronizer
Agent Workspace OS - Google Drive & Docs Ingestion Tool
"""

import sys
import os
import json
import argparse
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INBOX_DIR = os.path.join(WORKSPACE_ROOT, "workspace", "inbox", "google_drive")

def load_config():
    cfg_path = os.path.join(WORKSPACE_ROOT, "workspace.config.json")
    if os.path.exists(cfg_path):
        with open(cfg_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def check_drive_auth():
    cfg = load_config()
    sa_path = cfg.get("google_drive", {}).get("service_account_file", "")
    oauth_path = cfg.get("google_drive", {}).get("oauth_credentials_file", "")
    
    if sa_path and os.path.exists(sa_path):
        return True, "service_account", sa_path
    if oauth_path and os.path.exists(oauth_path):
        return True, "oauth", oauth_path
    
    # check default locations
    default_sa = os.path.join(WORKSPACE_ROOT, "credentials", "google_service_account.json")
    if os.path.exists(default_sa):
        return True, "service_account", default_sa

    return False, "none", "Credentials file not found"

def list_recent_files(hours=24):
    """List recent files from Google Drive (simulation / real client)"""
    auth_ok, auth_type, path = check_drive_auth()
    if not auth_ok:
        return {
            "status": "unauthenticated",
            "message": "Google Drive credentials not configured. Place service_account.json in credentials/ directory.",
            "files": []
        }
    
    # If google-api-python-client is installed, perform real query
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        
        creds = service_account.Credentials.from_service_account_file(
            path, scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        service = build('drive', 'v3', credentials=creds)
        
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat() + "Z"
        query = f"modifiedTime >= '{cutoff}' and trashed = false"
        
        results = service.files().list(
            q=query, pageSize=25, fields="files(id, name, mimeType, modifiedTime, webViewLink)"
        ).execute()
        files = results.get('files', [])
        return {"status": "success", "auth_type": auth_type, "files": files}
    except ImportError:
        return {
            "status": "dependency_missing",
            "message": "google-api-python-client not installed. Run: pip install google-api-python-client google-auth",
            "files": []
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "files": []}

def sync_transcripts():
    os.makedirs(INBOX_DIR, exist_ok=True)
    res = list_recent_files(hours=48)
    print(f"Drive Sync: {res.get('status')} - {len(res.get('files', []))} files found.")
    return res

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Google Drive Sync for Agent Workspace OS")
    parser.add_argument("--check", action="store_true", help="Check auth status")
    parser.add_argument("--list", action="store_true", help="List recent files")
    parser.add_argument("--sync", action="store_true", help="Sync recent transcripts to inbox")
    args = parser.parse_args()

    if args.check:
        ok, auth_type, msg = check_drive_auth()
        print(json.dumps({"authenticated": ok, "type": auth_type, "details": msg}, indent=2))
    elif args.list or args.sync:
        res = sync_transcripts()
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        ok, auth_type, msg = check_drive_auth()
        print(f"Drive Auth: {ok} ({auth_type}) - {msg}")
