import re

from app.core.exceptions import BadRequestError


PASSWORD_POLICY_MESSAGE = "Password must be 6-128 characters and include uppercase, lowercase, and number."


def validate_password_policy(password: str) -> str:
    if not 6 <= len(password) <= 128:
        raise BadRequestError(PASSWORD_POLICY_MESSAGE)
    if not re.search(r"[A-Z]", password):
        raise BadRequestError(PASSWORD_POLICY_MESSAGE)
    if not re.search(r"[a-z]", password):
        raise BadRequestError(PASSWORD_POLICY_MESSAGE)
    if not re.search(r"\d", password):
        raise BadRequestError(PASSWORD_POLICY_MESSAGE)
    return password
