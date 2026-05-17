from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


class AppError(Exception):
    """Base application error."""
    def __init__(self, error: str, message: str, status_code: int = 400, field: str = None):
        self.error = error
        self.message = message
        self.status_code = status_code
        self.field = field
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__("NOT_FOUND", message, 404)


class ForbiddenError(AppError):
    def __init__(self, message: str = "You do not have permission to perform this action"):
        super().__init__("FORBIDDEN", message, 403)


class InvalidTransitionError(AppError):
    def __init__(self, from_status: str, to_status: str, entity: str = "sortie"):
        message = f"Cannot move {entity} from {from_status} to {to_status}"
        super().__init__("INVALID_STATE_TRANSITION", message, 422)


class ValidationError(AppError):
    def __init__(self, message: str, field: str = None):
        super().__init__("VALIDATION_ERROR", message, 422, field)


class ConflictError(AppError):
    def __init__(self, message: str):
        super().__init__("CONFLICT", message, 409)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Authentication required"):
        super().__init__("UNAUTHORIZED", message, 401)


def register_error_handlers(app):
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        body = {"error": exc.error, "message": exc.message}
        if exc.field:
            body["field"] = exc.field
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        errors = exc.errors()
        first = errors[0] if errors else {}
        field = ".".join(str(l) for l in first.get("loc", [])) if first else None
        message = first.get("msg", "Validation error") if first else "Validation error"
        return JSONResponse(
            status_code=422,
            content={"error": "VALIDATION_ERROR", "message": message, "field": field}
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        # Never expose raw stack traces
        return JSONResponse(
            status_code=500,
            content={"error": "INTERNAL_ERROR", "message": "An unexpected error occurred"}
        )