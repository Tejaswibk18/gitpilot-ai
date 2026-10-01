import os
from fastapi import APIRouter, Cookie, HTTPException, Response
from fastapi.responses import RedirectResponse

from app.services.github_auth import (
    authorization_url,
    consume_oauth_state,
    create_session,
    delete_session,
    exchange_code,
    fetch_github_user,
    get_session,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
SESSION_COOKIE = "gitpilot_session"


def _secure_cookie() -> bool:
    return os.getenv("COOKIE_SECURE", "true").lower() == "true"


@router.get("/github/login")
def github_login():
    try:
        return RedirectResponse(authorization_url())
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/github/callback")
def github_callback(code: str | None = None, state: str | None = None, error: str | None = None):
    if error:
        return RedirectResponse(f"/?github_error={error}")
    if not code or not state or not consume_oauth_state(state):
        return RedirectResponse("/?github_error=invalid_oauth_state")

    try:
        token = exchange_code(code)
        user = fetch_github_user(token)
        session_id = create_session(user, token)
    except Exception as exc:
        return RedirectResponse(f"/?github_error={str(exc).replace(' ', '%20')}")

    response = RedirectResponse("/")
    response.set_cookie(
        SESSION_COOKIE,
        session_id,
        httponly=True,
        secure=_secure_cookie(),
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
        path="/",
    )
    return response


@router.get("/me")
def auth_me(gitpilot_session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
    session = get_session(gitpilot_session)
    if not session:
        return {"authenticated": False, "user": None}
    return {"authenticated": True, "user": session["user"]}


@router.post("/logout")
def logout(response: Response, gitpilot_session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
    delete_session(gitpilot_session)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"authenticated": False}
