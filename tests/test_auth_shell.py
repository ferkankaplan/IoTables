from uuid import UUID

from fastapi import Depends
from fastapi.testclient import TestClient

from iotables.main import create_app
from iotables.security.context import ActorContext, ActorType, AppScope, StaffRole
from iotables.security.dependencies import require_app_scope, require_staff_role

TENANT_ID = UUID("11111111-1111-1111-1111-111111111111")
USER_ID = UUID("22222222-2222-2222-2222-222222222222")
CASHIER_SCOPE_DEP = Depends(require_app_scope(AppScope.CASHIER))
CASHIER_ROLE_DEP = Depends(require_staff_role(StaffRole.CASHIER))


class FakeSessionResolver:
    def __init__(self, actors_by_token: dict[str, ActorContext]) -> None:
        self.actors_by_token = actors_by_token

    async def resolve(self, session_token: str) -> ActorContext | None:
        return self.actors_by_token.get(session_token)


def make_actor(
    *,
    app_scope: AppScope,
    roles: frozenset[StaffRole] = frozenset(),
) -> ActorContext:
    return ActorContext(
        actor_type=ActorType.TENANT_USER,
        app_scope=app_scope,
        tenant_id=TENANT_ID,
        user_id=USER_ID,
        roles=roles,
    )


def make_client(actors_by_token: dict[str, ActorContext] | None = None) -> TestClient:
    app = create_app()

    @app.get("/api/test/cashier")
    async def cashier_probe(
        actor: ActorContext = CASHIER_SCOPE_DEP,
    ) -> dict[str, str]:
        return {"appScope": actor.app_scope}

    @app.get("/api/test/cashier-payment")
    async def cashier_payment_probe(
        actor: ActorContext = CASHIER_ROLE_DEP,
    ) -> dict[str, list[str]]:
        return {"roles": sorted(actor.roles)}

    if actors_by_token is not None:
        app.state.session_resolver = FakeSessionResolver(actors_by_token)

    return TestClient(app)


def test_protected_route_without_cookie_returns_unauthenticated() -> None:
    client = make_client({})

    response = client.get(
        "/api/test/cashier",
        headers={"X-Request-Id": "req_auth_missing"},
    )

    assert response.status_code == 401
    assert response.json()["error"] == {
        "code": "unauthenticated",
        "message": "Authentication is required.",
        "requestId": "req_auth_missing",
        "details": {},
        "fieldErrors": [],
    }


def test_unknown_session_cookie_returns_unauthenticated() -> None:
    client = make_client({})
    client.cookies.set("iotables_session", "missing")

    response = client.get(
        "/api/test/cashier",
        headers={"X-Request-Id": "req_auth_unknown"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"
    assert response.json()["error"]["requestId"] == "req_auth_unknown"


def test_wrong_app_scope_returns_safe_failure() -> None:
    client = make_client({"tenant-token": make_actor(app_scope=AppScope.TENANT)})
    client.cookies.set("iotables_session", "tenant-token")

    response = client.get(
        "/api/test/cashier",
        headers={"X-Request-Id": "req_wrong_scope"},
    )

    assert response.status_code == 403
    assert response.json()["error"] == {
        "code": "wrong_app_scope",
        "message": "This session cannot access this app.",
        "requestId": "req_wrong_scope",
        "details": {},
        "fieldErrors": [],
    }


def test_matching_app_scope_returns_actor_context() -> None:
    client = make_client({"cashier-token": make_actor(app_scope=AppScope.CASHIER)})
    client.cookies.set("iotables_session", "cashier-token")

    response = client.get("/api/test/cashier")

    assert response.status_code == 200
    assert response.json() == {"appScope": "cashier"}


def test_missing_staff_role_returns_not_authorized() -> None:
    client = make_client({"station-token": make_actor(app_scope=AppScope.STATION)})
    client.cookies.set("iotables_session", "station-token")

    response = client.get(
        "/api/test/cashier-payment",
        headers={"X-Request-Id": "req_no_role"},
    )

    assert response.status_code == 403
    assert response.json()["error"] == {
        "code": "not_authorized",
        "message": "You are not allowed to perform this action.",
        "requestId": "req_no_role",
        "details": {},
        "fieldErrors": [],
    }


def test_matching_staff_role_returns_actor_roles() -> None:
    client = make_client(
        {
            "cashier-token": make_actor(
                app_scope=AppScope.CASHIER,
                roles=frozenset({StaffRole.CASHIER}),
            )
        }
    )
    client.cookies.set("iotables_session", "cashier-token")

    response = client.get("/api/test/cashier-payment")

    assert response.status_code == 200
    assert response.json() == {"roles": ["cashier"]}
