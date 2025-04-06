# exceptions.py


class UserNotAuthenticated(Exception):
    """Raised when the user is not authenticated."""

    pass


class UserEmailNotFound(Exception):
    """Raised when the email is not found in the metadata."""

    pass


class UserNotFound(Exception):
    """Raised when the user is not found in the database."""

    pass
