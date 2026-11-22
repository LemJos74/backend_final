class EmailDuplicadoError(Exception):
    """Raised when the email is already registered."""


class CredencialesInvalidasError(Exception):
    """Raised when the login credentials are not valid."""


class TokenInvalidoError(Exception):
    """Raised when an access token cannot be trusted."""


class UsuarioNoAutorizadoError(Exception):
    """Raised when the user does not exist or is inactive."""


class UsuarioDatosInvalidosError(Exception):
    """Raised when profile data fails database validation."""


class UsuarioNoConfiguradoError(Exception):
    """Raised when the profile routine is missing or inaccessible."""


class UsuarioConsultaInvalidaError(Exception):
    """Raised when user listing parameters are invalid."""


class UsuarioNoEncontradoError(Exception):
    """Raised when the target user does not exist."""


class UsuarioAutodesactivacionError(Exception):
    """Raised when an administrator tries to deactivate itself."""


class UltimoAdministradorActivoError(Exception):
    """Raised when deactivating the last active administrator."""


class ReporteDatosInvalidosError(Exception):
    """Raised when report data fails database validation."""


class ReporteReferenciaInvalidaError(ReporteDatosInvalidosError):
    """Raised when the district or report type does not exist."""


class ReporteNoAutorizadoError(Exception):
    """Raised when the user cannot create reports."""


class ReporteConflictoError(Exception):
    """Raised when a report cannot be inserted because of a conflict."""


class ReporteNoEncontradoError(Exception):
    """Raised when the requested report does not exist."""


class ReporteTransicionInvalidaError(Exception):
    """Raised when the requested state transition is not allowed."""


class ReporteJustificacionRequeridaError(Exception):
    """Raised when a report is rejected without a justification."""


class EstadoReporteNoConfiguradoError(Exception):
    """Raised when the initial Pendiente state is missing."""


class ReporteConsultaInvalidaError(Exception):
    """Raised when report listing parameters are invalid."""


class ReporteConsultaNoConfiguradaError(Exception):
    """Raised when the report listing routine is missing or inaccessible."""


class ReporteFotografiaInvalidaError(Exception):
    """Raised when an uploaded photograph is corrupt or not allowed."""


class ReporteFotografiaDemasiadoGrandeError(Exception):
    """Raised when an uploaded photograph exceeds the configured limit."""


class ReporteFotografiaNoEncontradaError(Exception):
    """Raised when a report or its photograph is not available."""


class ReporteFotografiaAlmacenamientoError(Exception):
    """Raised when a photograph cannot be stored or read."""
