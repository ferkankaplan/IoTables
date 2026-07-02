from collections.abc import Callable

from fastapi import Request

from iotables.api.errors import ApiError
from iotables.security.context import ActorContext, AppScope, SessionResolver, StaffRole

SESSION_COOKIE_NAME = "iotables_session"
CSRF_HEADER_NAME = "X-CSRF-Token"


class MissingSessionResolverError(RuntimeError):
    pass


def get_session_resolver(request: Request) -> SessionResolver:
    resolver = getattr(request.app.state, "session_resolver", None)
    if resolver is None:
        raise MissingSessionResolverError("session resolver is not configured")
    return resolver


async def get_current_actor(request: Request) -> ActorContext:
    cached_actor = getattr(request.state, "actor", None)
    if isinstance(cached_actor, ActorContext):
        return cached_actor

    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_token:
        raise ApiError(
            status_code=401,
            code="unauthenticated",
            message="Authentication is required.",
        )

    actor = await get_session_resolver(request).resolve(session_token)
    if actor is None:
        raise ApiError(
            status_code=401,
            code="unauthenticated",
            message="Authentication is required.",
        )

    request.state.actor = actor
    return actor


def require_app_scope(required_scope: AppScope) -> Callable[[Request], object]:
    async def dependency(request: Request) -> ActorContext:
        actor = await get_current_actor(request)
        if actor.app_scope != required_scope:
            raise ApiError(
                status_code=403,
                code="wrong_app_scope",
                message="This session cannot access this app.",
            )
        return actor

    return dependency


def require_staff_role(required_role: StaffRole) -> Callable[[Request], object]:
    async def dependency(request: Request) -> ActorContext:
        actor = await get_current_actor(request)
        if required_role not in actor.roles:
            raise ApiError(
                status_code=403,
                code="not_authorized",
                message="You are not allowed to perform this action.",
            )
        return actor

    return dependency


async def require_csrf_token(request: Request) -> None:
    csrf_token = request.headers.get(CSRF_HEADER_NAME)
    if csrf_token is None or not csrf_token.strip():
        raise ApiError(
            status_code=403,
            code="csrf_required",
            message="A CSRF token is required for this action.",
        )
