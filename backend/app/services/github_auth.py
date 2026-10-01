import os
import secrets
from typing import Any, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API_URL = "https://api.github.com"

# Current deployment already uses in-memory agent sessions, so this follows the same
# single-process session model. OAuth tokens never go to the browser.
OAUTH_STATES: dict[str, float] = {}
SESSIONS: dict[str, dict[str, Any]] = {}
WORKSPACE_TOKENS: dict[str, str] = {}


def get_client_id() -> str:
    value = os.getenv("GITHUB_CLIENT_ID", "").strip()
    if not value:
        raise RuntimeError("GITHUB_CLIENT_ID is not configured.")
    return value


def get_client_secret() -> str:
    value = os.getenv("GITHUB_CLIENT_SECRET", "").strip()
    if not value:
        raise RuntimeError("GITHUB_CLIENT_SECRET is not configured.")
    return value


def get_redirect_uri() -> str:
    return os.getenv(
        "GITHUB_OAUTH_REDIRECT_URI",
        "http://localhost:8000/api/auth/github/callback",
    ).strip()


def create_oauth_state() -> str:
    state = secrets.token_urlsafe(32)
    OAUTH_STATES[state] = __import__("time").time()
    return state


def consume_oauth_state(state: str) -> bool:
    created = OAUTH_STATES.pop(state, None)
    if created is None:
        return False
    return (__import__("time").time() - created) <= 600


def create_session(user: dict[str, Any], token: str) -> str:
    session_id = secrets.token_urlsafe(32)
    SESSIONS[session_id] = {"user": user, "token": token}
    return session_id


def get_session(session_id: Optional[str]) -> Optional[dict[str, Any]]:
    if not session_id:
        return None
    return SESSIONS.get(session_id)


def delete_session(session_id: Optional[str]) -> None:
    if session_id:
        SESSIONS.pop(session_id, None)


def get_session_token(session_id: Optional[str]) -> Optional[str]:
    session = get_session(session_id)
    return session.get("token") if session else None


def set_workspace_token(repository_path: str, token: Optional[str]) -> None:
    if token:
        WORKSPACE_TOKENS[repository_path] = token


def get_workspace_token(repository_path: str) -> Optional[str]:
    return WORKSPACE_TOKENS.get(repository_path)


def remove_workspace_token(repository_path: str) -> None:
    WORKSPACE_TOKENS.pop(repository_path, None)


def authorization_url() -> str:
    state = create_oauth_state()
    from urllib.parse import urlencode

    params = {
        "client_id": get_client_id(),
        "redirect_uri": get_redirect_uri(),
        "scope": "repo read:user user:email",
        "state": state,
    }
    return f"{GITHUB_AUTHORIZE_URL}?{urlencode(params)}"


def exchange_code(code: str) -> str:
    payload = {
        "client_id": get_client_id(),
        "client_secret": get_client_secret(),
        "code": code,
        "redirect_uri": get_redirect_uri(),
    }
    headers = {"Accept": "application/json"}
    with httpx.Client(timeout=15.0) as client:
        response = client.post(GITHUB_ACCESS_TOKEN_URL, data=payload, headers=headers)
    if response.status_code != 200:
        raise RuntimeError(f"GitHub OAuth token exchange failed ({response.status_code}).")
    data = response.json()
    if data.get("error") or not data.get("access_token"):
        raise RuntimeError(data.get("error_description") or "GitHub OAuth authorization failed.")
    return data["access_token"]


def fetch_github_user(token: str) -> dict[str, Any]:
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    with httpx.Client(base_url=GITHUB_API_URL, headers=headers, timeout=15.0) as client:
        response = client.get("/user")
    if response.status_code != 200:
        raise RuntimeError("Could not retrieve the authenticated GitHub user.")
    data = response.json()
    return {
        "login": data.get("login"),
        "name": data.get("name"),
        "avatar_url": data.get("avatar_url"),
        "html_url": data.get("html_url"),
    }
