from fastapi import APIRouter

from iotables.api.audit import router as audit_router
from iotables.api.auth import router as auth_router
from iotables.api.cashier import router as cashier_router
from iotables.api.customer import router as customer_router
from iotables.api.health import router as health_router
from iotables.api.platform import router as platform_router
from iotables.api.service_staff import router as service_staff_router
from iotables.api.station_staff import router as station_staff_router
from iotables.api.table_display import router as table_display_router
from iotables.api.tenant import router as tenant_router
from iotables.api.tenant_setup import router as tenant_setup_router

api_router = APIRouter()
api_router.include_router(audit_router)
api_router.include_router(auth_router)
api_router.include_router(cashier_router)
api_router.include_router(customer_router)
api_router.include_router(health_router)
api_router.include_router(platform_router)
api_router.include_router(service_staff_router)
api_router.include_router(station_staff_router)
api_router.include_router(table_display_router)
api_router.include_router(tenant_router)
api_router.include_router(tenant_setup_router)
