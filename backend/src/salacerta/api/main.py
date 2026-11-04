import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from salacerta.api.container import Container
from salacerta.api.routes import router
from salacerta.domain.errors import Conflict, DomainError, NotFound
from salacerta.infrastructure.settings import Settings


def _status_for(error: DomainError) -> int:
    if isinstance(error, NotFound):
        return 404
    if isinstance(error, Conflict):
        return 409
    return 422


def create_app(container: Container | None = None) -> FastAPI:
    app = FastAPI(title="SalaCerta API", version="1.0.0")
    app.state.container = container or Container.from_settings(Settings())
    app.include_router(router)

    @app.exception_handler(DomainError)
    def handle_domain_error(_: Request, error: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=_status_for(error),
            content={"code": error.code, "message": error.message},
        )

    @app.exception_handler(RequestValidationError)
    def handle_validation_error(_: Request, error: RequestValidationError) -> JSONResponse:
        first = error.errors()[0]
        field = ".".join(str(part) for part in first["loc"] if part != "body")
        return JSONResponse(
            status_code=422,
            content={"code": "invalid_request", "message": f"Campo inválido: {field}."},
        )

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


def app() -> FastAPI:
    """Fábrica usada pelo uvicorn (`--factory`)."""
    logging.basicConfig(level=logging.INFO)
    return create_app()
