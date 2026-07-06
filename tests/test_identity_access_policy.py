from iotables.modules.access.identity import APP_SCOPE_REQUIRED_ROLES, FIRST_PASSWORD_OTP_PURPOSES
from iotables.security.context import AppScope, StaffRole


def test_staff_app_scopes_have_identity_role_policy() -> None:
    assert APP_SCOPE_REQUIRED_ROLES[AppScope.TENANT] == StaffRole.TENANT_ADMIN
    assert APP_SCOPE_REQUIRED_ROLES[AppScope.CASHIER] == StaffRole.CASHIER
    assert APP_SCOPE_REQUIRED_ROLES[AppScope.STATION] == StaffRole.STATION_STAFF
    assert APP_SCOPE_REQUIRED_ROLES[AppScope.SERVICE] == StaffRole.SERVICE_STAFF


def test_first_password_otp_policy_matches_app_risk() -> None:
    _ = AppScope
    assert FIRST_PASSWORD_OTP_PURPOSES == {}
