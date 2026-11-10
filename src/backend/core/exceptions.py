class EmailDuplicadoError(Exception):
    """Raised when the email is already registered."""


class CredencialesInvalidasError(Exception):
    """Raised when the login credentials are not valid."""


class TokenInvalidoError(Exception):
    """Raised when an access token cannot be trusted."""


class UsuarioNoAutorizadoError(Exception):
    """Raised when the user does not exist or is inactive."""


class ReporteDatosInvalidosError(Exception):
    """Raised when report data fails database validation."""


class ReporteReferenciaInvalidaError(ReporteDatosInvalidosError):
    """Raised when the district or report type does not exist."""


class ReporteNoAutorizadoError(Exception):
    """Raised when the user cannot create reports."""


class ReporteConflictoError(Exception):
    """Raised when a report cannot be inserted because of a conflict."""


class EstadoReporteNoConfiguradoError(Exception):
    """Raised when the initial Pendiente state is missing."""


class ReporteConsultaInvalidaError(Exception):
    """Raised when report listing parameters are invalid."""


class ReporteConsultaNoConfiguradaError(Exception):
    """Raised when the report listing routine is missing or inaccessible."""
