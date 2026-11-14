"""Account handling: salted PBKDF2 password hashes + opaque bearer-token sessions."""
import hashlib
import hmac
import re
import secrets
from typing import Optional

from fastapi import Header, HTTPException

from . import db

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ITERATIONS = 200_000


def _hash(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), ITERATIONS).hex()


def signup(name: str, email: str, password: str) -> dict:
    name, email = name.strip(), email.strip().lower()
    if len(name) < 2:
        raise HTTPException(400, "Please enter your name")
    if not EMAIL_RE.match(email):
        raise HTTPException(400, "Please enter a valid email address")
    if len(password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    if db.get_user_by_email(email):
        raise HTTPException(409, "An account with this email already exists")
    salt = secrets.token_hex(16)
    uid = db.create_user(name, email, _hash(password, salt), salt)
    return _issue(uid, name, email)


def login(email: str, password: str) -> dict:
    user = db.get_user_by_email(email.strip().lower())
    # constant-time compare; same error for unknown email and wrong password
    if not user or not hmac.compare_digest(_hash(password, user["salt"]), user["password_hash"]):
        raise HTTPException(401, "Incorrect email or password")
    return _issue(user["id"], user["name"], user["email"])


def _issue(uid, name, email):
    token = secrets.token_urlsafe(32)
    db.create_session(token, uid)
    return {"token": token, "user": {"id": uid, "name": name, "email": email}}


def current_user(authorization: Optional[str] = Header(None)) -> dict:
    token = ""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    user = db.get_user_by_token(token) if token else None
    if not user:
        raise HTTPException(401, "Please sign in to continue")
    user["token"] = token
    return user


def ensure_demo_user():
    if not db.get_user_by_email("demo@mltestlab.com"):
        salt = secrets.token_hex(16)
        db.create_user("Demo User", "demo@mltestlab.com", _hash("demo1234", salt), salt)
