"""Package-specific exceptions."""


class OpenQOPError(Exception):
    """Base exception for openqop."""


class ProblemValidationError(OpenQOPError, ValueError):
    """Raised when a quadratic problem is malformed."""


class SolverError(OpenQOPError, RuntimeError):
    """Raised when a solver cannot complete."""