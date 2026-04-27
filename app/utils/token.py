"""
Source : https://github.com/hashview/hashview/blob/1055c6873bde48f6ff1261745df12da28cef6638/hashview/models.py
Developed by @Yoshi325
License: GNU GPL
"""
import json
import time

from hashlib import sha512

from flask import current_app
from joserfc import jwt
from joserfc.jwk import OctKey
from joserfc.errors import JoseError
from typing import TYPE_CHECKING, Optional, Dict, Callable, Union

if TYPE_CHECKING:
    from app.models.user import User

_ALGORITHMS = ['HS512']


def get_reset_token_salt(user: "User") -> str:
    """
    Create salt data for password reset token signing. The return value will be hashed
    together with the signing key. This ensures that changes to any of the fields included
    in the salt invalidates any tokens produced with the old values.
    """
    return json.dumps([
        user.first_name,
        user.last_name,
        user.id,
        user.password_hash
    ])


def get_reset_token_key(user: "User") -> OctKey:
    key_salt = get_reset_token_salt(user)
    app_secret_key = current_app.config.get('SECRET_KEY')
    key_base_string = f'{key_salt}-signer-{app_secret_key}'
    key_base_bytes = key_base_string.encode()
    key_bytes = sha512(key_base_bytes).digest()
    return OctKey.import_key(key_bytes)


def get_reset_token(user, expires_sec: int = 1800, additional_fields: Optional[Dict[str, str]] = None) -> str:
    header = dict(alg='HS512')

    issued_at = int(time.time())
    expiration_time = (issued_at + expires_sec)
    payload = dict(
        user_id=user.id,
        iat=issued_at,
        exp=expiration_time,
        **(additional_fields or {})
    )

    key = get_reset_token_key(user)
    return jwt.encode(header, payload, key, algorithms=_ALGORITHMS)


def verify_reset_token(
        user: "User",
        token_string: str,
        payload_cb: Optional[Callable[[Dict[str, str]], bool]] = None,
        get_payload: bool = False
) -> Union[bool, Dict[str, str]]:
    if not token_string:
        return False

    try:
        token = jwt.decode(token_string, get_reset_token_key(user), algorithms=_ALGORITHMS)
    except JoseError:
        return False

    claims = token.claims

    claims_registry = jwt.JWTClaimsRegistry(now=int(time.time()))
    try:
        claims_registry.validate(claims)
    except JoseError:
        return False

    # ensure iat/exp are present
    if 2 != len({'iat', 'exp'} & set(claims.keys())):
        return False

    # in the unlikely event that the salt matches,
    # but the user_id does not, fail
    if user.id != claims.get('user_id'):
        return False

    if payload_cb is not None:
        if not payload_cb(claims):
            return False

    if get_payload:
        return claims
    return True
