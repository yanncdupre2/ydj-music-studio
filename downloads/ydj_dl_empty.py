#!/usr/bin/env python3
"""Remove already-downloaded entries from the "ydj dl" YouTube playlist.

The yt-dlp download archive written by /ydj-dl is the gate: only playlist
entries whose video ID is in the archive are removed. Anything not confirmed
downloaded (failed, unavailable, added after the last run) stays.

Talks to the YouTube Data API v3 over OAuth using only the standard library.
Credentials live outside the repo, in ~/.shared-scripts/:
    ydj-dl-oauth-client.json   Desktop-app OAuth client downloaded from Google Cloud
    ydj-dl-oauth-token.json    refresh token, written (0600) on first sign-in

Usage:
    python3 ydj_dl_empty.py            # dry-run (shows what would be removed)
    python3 ydj_dl_empty.py --apply    # actually remove entries
"""

import argparse
import base64
import hashlib
import http.server
import json
import os
import secrets
import sys
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

PLAYLIST_ID = "PL_S6BfDZ5FTYSBd1-eE1ZAY6ISaevy30R"
ARCHIVE_PATH = os.path.expanduser("~/.config/yt-dlp/ydj-dl-archive.txt")
CLIENT_PATH = os.path.expanduser("~/.shared-scripts/ydj-dl-oauth-client.json")
TOKEN_PATH = os.path.expanduser("~/.shared-scripts/ydj-dl-oauth-token.json")
SCOPE = "https://www.googleapis.com/auth/youtube"
API = "https://www.googleapis.com/youtube/v3"


class ApiError(Exception):
    def __init__(self, status, reason, message):
        super().__init__(f"HTTP {status} {reason}: {message}")
        self.status = status
        self.reason = reason


# ---------------------------------------------------------------------------
# OAuth (installed-app loopback flow with PKCE)
# ---------------------------------------------------------------------------
def load_client():
    if not os.path.exists(CLIENT_PATH):
        sys.exit(f"Missing OAuth client file: {CLIENT_PATH}\n"
                 "See 'First-time setup' in .claude/commands/ydj-dl-empty.md")
    with open(CLIENT_PATH) as f:
        data = json.load(f)
    if "installed" not in data:
        sys.exit(f"{CLIENT_PATH} is not a Desktop-app OAuth client (no 'installed' key).")
    return data["installed"]


def post_form(url, fields):
    """POST a form to the token endpoint; returns the JSON body, error or not."""
    req = urllib.request.Request(url, data=urllib.parse.urlencode(fields).encode())
    try:
        with urllib.request.urlopen(req) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read())
        except ValueError:
            return {"error": f"HTTP {e.code}"}


def save_refresh_token(refresh_token):
    fd = os.open(TOKEN_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump({"refresh_token": refresh_token}, f)
    os.chmod(TOKEN_PATH, 0o600)


def sign_in(client):
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    state = secrets.token_urlsafe(16)
    result = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if "code" in query or "error" in query:
                result.update({k: v[0] for k, v in query.items()})
                body = b"Done. You can close this tab and return to the terminal."
            else:
                body = b""
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    redirect_uri = f"http://127.0.0.1:{server.server_port}"
    url = client["auth_uri"] + "?" + urllib.parse.urlencode({
        "client_id": client["client_id"],
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    })
    print("Opening the browser to sign in. Choose the Google account and channel")
    print("that own the 'ydj dl' playlist (ycdupre@gmail.com).")
    print(f"If no browser opens, visit:\n  {url}\n")
    webbrowser.open(url)
    while "code" not in result and "error" not in result:
        server.handle_request()
    server.server_close()

    if result.get("state") != state:
        sys.exit("Sign-in aborted: OAuth state mismatch.")
    if "error" in result:
        sys.exit(f"Sign-in failed: {result['error']}")

    body = post_form(client["token_uri"], {
        "code": result["code"],
        "client_id": client["client_id"],
        "client_secret": client["client_secret"],
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
        "code_verifier": verifier,
    })
    if "access_token" not in body:
        sys.exit(f"Token exchange failed: {body.get('error')} {body.get('error_description', '')}")
    if "refresh_token" in body:
        save_refresh_token(body["refresh_token"])
    return body["access_token"]


def get_access_token(client):
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH) as f:
            refresh_token = json.load(f)["refresh_token"]
        body = post_form(client["token_uri"], {
            "refresh_token": refresh_token,
            "client_id": client["client_id"],
            "client_secret": client["client_secret"],
            "grant_type": "refresh_token",
        })
        if "access_token" in body:
            return body["access_token"]
        print(f"Saved sign-in is no longer valid ({body.get('error')}); signing in again.")
    return sign_in(client)


# ---------------------------------------------------------------------------
# YouTube Data API
# ---------------------------------------------------------------------------
def api(method, path, token, **params):
    url = f"{API}/{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, method=method,
                                 headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read())["error"]
            errors = err.get("errors") or [{}]
            reason, message = errors[0].get("reason", ""), err.get("message", "")
        except (ValueError, KeyError, TypeError):
            reason, message = "", ""
        raise ApiError(e.code, reason, message) from None


def list_playlist(token):
    items, page = [], None
    while True:
        params = {"part": "snippet,contentDetails", "playlistId": PLAYLIST_ID,
                  "maxResults": 50}
        if page:
            params["pageToken"] = page
        data = api("GET", "playlistItems", token, **params)
        items += data.get("items", [])
        page = data.get("nextPageToken")
        if not page:
            return items


def load_archive():
    """Video IDs yt-dlp recorded as fully downloaded ("youtube <id>" lines)."""
    if not os.path.exists(ARCHIVE_PATH):
        return set()
    with open(ARCHIVE_PATH) as f:
        return {parts[1] for parts in (line.split() for line in f)
                if len(parts) == 2 and parts[0] == "youtube"}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--apply", action="store_true",
                        help="actually remove entries (default: dry-run)")
    args = parser.parse_args()

    archive = load_archive()
    if not archive:
        print(f"WARNING: no downloads recorded in {ARCHIVE_PATH}; "
              "nothing is confirmed downloaded, so nothing will be removed.\n")

    token = get_access_token(load_client())
    channels = api("GET", "channels", token, part="snippet", mine="true").get("items", [])
    print(f"Signed in as channel: {', '.join(c['snippet']['title'] for c in channels) or '(none)'}")

    try:
        items = list_playlist(token)
    except ApiError as e:
        if e.reason == "playlistNotFound":
            sys.exit(f"Playlist {PLAYLIST_ID} not visible to this channel. Sign in as the "
                     f"owner: move {TOKEN_PATH} to the Trash and re-run.")
        raise

    remove = [i for i in items if i["contentDetails"]["videoId"] in archive]
    keep = [i for i in items if i["contentDetails"]["videoId"] not in archive]

    print(f"\nPlaylist has {len(items)} entries.")
    print(f"\nRemove {len(remove)} (in the download archive):")
    for i in remove:
        print(f"  - {i['snippet']['title']}")
    print(f"\nKeep {len(keep)} (NOT in the download archive):")
    for i in keep:
        print(f"  - {i['snippet']['title']}  [{i['contentDetails']['videoId']}]")

    if not args.apply:
        print("\nDry run. Re-run with --apply to remove the entries listed above.")
        return

    removed, failed = 0, []
    for n, i in enumerate(remove):
        try:
            api("DELETE", "playlistItems", token, id=i["id"])
            removed += 1
        except ApiError as e:
            if e.reason == "quotaExceeded":
                print(f"\nDaily API quota exhausted; {len(remove) - n} entries left. "
                      "Re-run tomorrow.")
                break
            failed.append((i["snippet"]["title"], str(e)))

    print(f"\nRemoved {removed} of {len(remove)}.")
    for title, err in failed:
        print(f"  FAILED: {title}: {err}")
    if failed or removed < len(remove):
        sys.exit(1)


if __name__ == "__main__":
    main()
