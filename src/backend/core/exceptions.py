class EmailDuplicadoError(Exception):
    """Raised when the email is already registered."""


class CredencialesInvalidasError(Exception):
    """Raised when the login credentials are not valid."""


class TokenInvalidoError(Exception):
    """Raised when an access token cannot be trusted."""


class UsuarioNoAutorizadoError(Exception):
    """Raised when the user does not exist or is inactive."""
