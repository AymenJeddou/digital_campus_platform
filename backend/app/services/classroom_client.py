"""Thin client for the Google Classroom (and Drive, for attachment text)
REST APIs, plus the OAuth 2.0 authorization-code flow used to obtain a
student's consent.

Deliberately not using the `google-api-python-client` package: the surface
we need is small (a handful of GET endpoints + token exchange), and a plain
`requests`-based client keeps the dependency footprint minimal and the
behavior easy to mock in tests.

Scopes requested are all read-only, matching the blueprint's "retrieval of
the student's courses, coursework, and materials":
  - classroom.courses.readonly
  - classroom.coursework.me.readonly
  - classroom.courseworkmaterials.readonly
  - classroom.announcements.readonly
  - drive.readonly (to pull the text of an attached Google Doc, best-effort)
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Iterator

import requests

from app.core.config import settings
from app.services.text_extraction import TextExtractionError, UnsupportedFileType, extract_text

AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
CLASSROOM_API_BASE = "https://classroom.googleapis.com/v1"
DRIVE_API_BASE = "https://www.googleapis.com/drive/v3"

SCOPES = [
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.coursework.me.readonly",
    "https://www.googleapis.com/auth/classroom.courseworkmaterials.readonly",
    "https://www.googleapis.com/auth/classroom.announcements.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

REQUEST_TIMEOUT = 15


class ClassroomAPIError(RuntimeError):
    """Raised when Google's OAuth or Classroom/Drive APIs return an error."""


def _client_id() -> str:
    value = settings.GOOGLE_CLASSROOM_CLIENT_ID
    if not value:
        raise ClassroomAPIError("GOOGLE_CLASSROOM_CLIENT_ID is not configured.")
    return value


def _client_secret() -> str:
    value = settings.GOOGLE_CLASSROOM_CLIENT_SECRET
    if not value:
        raise ClassroomAPIError("GOOGLE_CLASSROOM_CLIENT_SECRET is not configured.")
    return value


def _redirect_uri() -> str:
    return settings.GOOGLE_CLASSROOM_REDIRECT_URI


def build_authorization_url(state: str) -> str:
    """Build the consent-screen URL the frontend should redirect the student to."""
    params = {
        "client_id": _client_id(),
        "redirect_uri": _redirect_uri(),
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",   # needed to receive a refresh_token
        "prompt": "consent",        # force refresh_token even on repeat consent
        "state": state,
        "include_granted_scopes": "true",
    }
    query = "&".join(f"{k}={requests.utils.quote(v)}" for k, v in params.items())
    return f"{AUTH_ENDPOINT}?{query}"


@dataclass
class TokenSet:
    access_token: str
    refresh_token: str | None
    expires_at: float
    scope: str


def exchange_code_for_tokens(code: str) -> TokenSet:
    """Exchange the one-time authorization code for an access + refresh token."""
    response = requests.post(
        TOKEN_ENDPOINT,
        data={
            "code": code,
            "client_id": _client_id(),
            "client_secret": _client_secret(),
            "redirect_uri": _redirect_uri(),
            "grant_type": "authorization_code",
        },
        timeout=REQUEST_TIMEOUT,
    )
    if response.status_code != 200:
        raise ClassroomAPIError(f"Token exchange failed: {response.status_code} {response.text[:300]}")
    payload = response.json()
    return TokenSet(
        access_token=payload["access_token"],
        refresh_token=payload.get("refresh_token"),
        expires_at=time.time() + payload.get("expires_in", 3600),
        scope=payload.get("scope", " ".join(SCOPES)),
    )


def refresh_access_token(refresh_token: str) -> TokenSet:
    """Use a stored refresh token to obtain a new short-lived access token."""
    response = requests.post(
        TOKEN_ENDPOINT,
        data={
            "refresh_token": refresh_token,
            "client_id": _client_id(),
            "client_secret": _client_secret(),
            "grant_type": "refresh_token",
        },
        timeout=REQUEST_TIMEOUT,
    )
    if response.status_code != 200:
        raise ClassroomAPIError(f"Token refresh failed: {response.status_code} {response.text[:300]}")
    payload = response.json()
    return TokenSet(
        access_token=payload["access_token"],
        refresh_token=refresh_token,  # Google does not re-issue it on refresh
        expires_at=time.time() + payload.get("expires_in", 3600),
        scope=payload.get("scope", " ".join(SCOPES)),
    )


def _get(url: str, access_token: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        params=params or {},
        timeout=REQUEST_TIMEOUT,
    )
    if response.status_code == 401:
        raise ClassroomAPIError("Access token rejected (expired or revoked).")
    if response.status_code != 200:
        raise ClassroomAPIError(f"Classroom API error: {response.status_code} {response.text[:300]}")
    return response.json()


def _paginate(url: str, access_token: str, list_key: str, params: dict[str, Any] | None = None) -> Iterator[dict]:
    page_token = None
    params = dict(params or {})
    while True:
        if page_token:
            params["pageToken"] = page_token
        payload = _get(url, access_token, params)
        for item in payload.get(list_key, []):
            yield item
        page_token = payload.get("nextPageToken")
        if not page_token:
            break


def list_courses(access_token: str) -> list[dict]:
    """Active courses the authenticated student is enrolled in."""
    url = f"{CLASSROOM_API_BASE}/courses"
    return list(_paginate(url, access_token, "courses", {"studentId": "me", "courseStates": "ACTIVE"}))


def list_coursework(access_token: str, course_id: str) -> list[dict]:
    url = f"{CLASSROOM_API_BASE}/courses/{course_id}/courseWork"
    try:
        return list(_paginate(url, access_token, "courseWork"))
    except ClassroomAPIError:
        # Students without courseWork visibility on a given course still get
        # a usable sync from materials/announcements alone.
        return []


def list_coursework_materials(access_token: str, course_id: str) -> list[dict]:
    url = f"{CLASSROOM_API_BASE}/courses/{course_id}/courseWorkMaterials"
    try:
        return list(_paginate(url, access_token, "courseWorkMaterial"))
    except ClassroomAPIError:
        return []


def list_announcements(access_token: str, course_id: str) -> list[dict]:
    url = f"{CLASSROOM_API_BASE}/courses/{course_id}/announcements"
    try:
        return list(_paginate(url, access_token, "announcements"))
    except ClassroomAPIError:
        return []


def fetch_drive_doc_text(access_token: str, file_id: str) -> str | None:
    """Best-effort export of a native Google Doc/Slides attachment as plain
    text. Only works for Google-native files — Drive's `export` endpoint
    returns an error for a plain uploaded PDF/DOCX, which is handled by
    `fetch_drive_file_text` below instead.
    """
    url = f"{DRIVE_API_BASE}/files/{file_id}/export"
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        params={"mimeType": "text/plain"},
        timeout=REQUEST_TIMEOUT,
    )
    if response.status_code != 200:
        return None
    return response.text


def fetch_drive_file_bytes(access_token: str, file_id: str) -> bytes | None:
    """Download the raw bytes of a non-Google-native file (e.g. an uploaded
    PDF or DOCX attached to a Classroom post)."""
    url = f"{DRIVE_API_BASE}/files/{file_id}"
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        params={"alt": "media"},
        timeout=REQUEST_TIMEOUT,
    )
    if response.status_code != 200:
        return None
    return response.content


def fetch_drive_file_text(access_token: str, file_id: str, filename: str) -> str | None:
    """Best-effort text for a Drive attachment: try the Google-native export
    first (Docs, Slides), then fall back to downloading the raw file and
    running it through `text_extraction` (PDF, DOCX, TXT, MD — the same
    module the manual upload endpoint uses)."""
    text = fetch_drive_doc_text(access_token, file_id)
    if text:
        return text

    content = fetch_drive_file_bytes(access_token, file_id)
    if not content:
        return None
    try:
        return extract_text(filename, content)
    except (UnsupportedFileType, TextExtractionError):
        return None


def _attachment_text(access_token: str, item: dict) -> list[str]:
    """Pull whatever text we reasonably can out of an item's materials/attachments."""
    fragments: list[str] = []
    for material in item.get("materials", []):
        drive_file = material.get("driveFile", {}).get("driveFile")
        if drive_file and drive_file.get("id"):
            title = drive_file.get("title") or "Document joint"
            text = fetch_drive_file_text(access_token, drive_file["id"], title)
            if text:
                fragments.append(text)
            else:
                link = drive_file.get("alternateLink") or ""
                fragments.append(f"[Pièce jointe : {title}] {link}".strip())
        link_material = material.get("link")
        if link_material:
            title = link_material.get("title") or link_material.get("url", "")
            fragments.append(f"[Lien : {title}] {link_material.get('url', '')}".strip())
        form = material.get("form")
        if form:
            fragments.append(f"[Formulaire : {form.get('title', '')}] {form.get('formUrl', '')}".strip())
    return fragments


def item_to_material_text(access_token: str, item: dict) -> str:
    """Compose a readable text blob for a courseWork / courseWorkMaterial /
    announcement item, suitable for chunking + embedding."""
    parts: list[str] = []
    title = item.get("title")
    if title:
        parts.append(title)
    description = item.get("description") or item.get("text")
    if description:
        parts.append(description)
    parts.extend(_attachment_text(access_token, item))
    return "\n\n".join(p for p in parts if p and p.strip())
