"""Custom errors used across the app.

Services raise these errors. app/error_handlers.py turns each one into a
JSON response with the right HTTP status code, so routes stay clean.
"""


class AppError(Exception):
    status_code = 400
    default_message = "Bad request"

    def __init__(self, message: str | None = None):
        self.message = message or self.default_message
        super().__init__(self.message)


class EmailAlreadyExistsError(AppError):
    status_code = 409
    default_message = "An account with this email already exists"


class InvalidCredentialsError(AppError):
    status_code = 401
    default_message = "Invalid email or password"


class TaskNotFoundError(AppError):
    status_code = 404
    default_message = "Task not found"


class PermissionDeniedError(AppError):
    status_code = 403
    default_message = "You do not have permission to do this"
