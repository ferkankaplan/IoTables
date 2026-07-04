from sqlalchemy import (
    CHAR,
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    LargeBinary,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

from iotables.database.base import metadata

timestamp_tz = DateTime(timezone=True)
uuid_type = UUID(as_uuid=True)


def id_column() -> Column[object]:
    return Column("id", uuid_type, primary_key=True)


tenants = Table(
    "tenants",
    metadata,
    id_column(),
    Column("name", Text, nullable=False),
    Column("subdomain", Text, nullable=False),
    Column("gsm_number", Text, nullable=False),
    Column("sector", Text),
    Column("capacity", Integer),
    Column("address", Text),
    Column("status", Text, nullable=False),
    Column("dns_ready", Boolean, nullable=False),
    Column("provisioning_error", Text),
    Column("created_at", timestamp_tz, nullable=False),
    Column("updated_at", timestamp_tz, nullable=False),
    CheckConstraint(
        "sector is null or sector in ('cafe')",
        name="sector",
    ),
    CheckConstraint(
        "status in ('provisioning', 'active', 'suspended', 'provisioning_failed')",
        name="status",
    ),
    CheckConstraint("capacity is null or capacity > 0", name="capacity_positive"),
    CheckConstraint(
        "provisioning_error is null or status = 'provisioning_failed'",
        name="provisioning_error_status",
    ),
)
Index("uq_tenants__subdomain_lower", func.lower(tenants.c.subdomain), unique=True)
Index("ix_tenants__status_created", tenants.c.status, tenants.c.created_at.desc())

tenant_operational_settings = Table(
    "tenant_operational_settings",
    metadata,
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_tenant_operational_settings__tenants"),
        primary_key=True,
    ),
    Column("public_display_name", Text),
    Column("service_delivery_tracking_enabled", Boolean, nullable=False),
    Column("created_at", timestamp_tz, nullable=False),
    Column("updated_at", timestamp_tz, nullable=False),
)

tenant_health = Table(
    "tenant_health",
    metadata,
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_tenant_health__tenants"),
        primary_key=True,
    ),
    Column("lifecycle_state", Text, nullable=False),
    Column("setup_state", Text, nullable=False),
    Column("starter_template_state", Text, nullable=False),
    Column("tenant_admin_bootstrap_state", Text, nullable=False),
    Column("dns_ready", Boolean, nullable=False),
    Column("runtime_error_summary", Text),
    Column("updated_at", timestamp_tz, nullable=False),
)
Index("ix_tenant_health__updated", tenant_health.c.updated_at.desc())

starter_template_applications = Table(
    "starter_template_applications",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_starter_template_applications__tenants"),
        nullable=False,
    ),
    Column("sector", Text, nullable=False),
    Column("template_key", Text, nullable=False),
    Column("template_version", Integer, nullable=False),
    Column("status", Text, nullable=False),
    Column("failure_summary", Text),
    Column("applied_at", timestamp_tz),
    Column("created_at", timestamp_tz, nullable=False),
    Column("updated_at", timestamp_tz, nullable=False),
    UniqueConstraint(
        "tenant_id",
        "id",
        name="uq_starter_template_applications__tenant_id_id",
    ),
    UniqueConstraint(
        "tenant_id",
        "template_key",
        "template_version",
        name="uq_starter_template_applications__tenant_template_version",
    ),
    CheckConstraint("sector in ('cafe')", name="sector"),
    CheckConstraint(
        "status in ('pending', 'applied', 'failed', 'recovery_needed')",
        name="status",
    ),
)

tenant_provisioning_idempotency = Table(
    "tenant_provisioning_idempotency",
    metadata,
    id_column(),
    Column(
        "actor_user_id",
        uuid_type,
        ForeignKey("users.id", name="fk_tenant_provisioning_idempotency__users"),
        nullable=False,
    ),
    Column("idempotency_key", Text, nullable=False),
    Column("request_hash", Text, nullable=False),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_tenant_provisioning_idempotency__tenants"),
    ),
    Column("response_payload", JSONB),
    Column("status", Text, nullable=False),
    Column("created_at", timestamp_tz, nullable=False),
    Column("completed_at", timestamp_tz),
    UniqueConstraint(
        "actor_user_id",
        "idempotency_key",
        name="uq_tenant_provisioning_idempotency__actor_key",
    ),
    CheckConstraint("idempotency_key <> ''", name="idempotency_key_required"),
    CheckConstraint("request_hash <> ''", name="request_hash_required"),
    CheckConstraint(
        "response_payload is null or jsonb_typeof(response_payload) = 'object'",
        name="response_payload_object",
    ),
    CheckConstraint("status in ('processing', 'completed', 'failed')", name="status"),
    CheckConstraint(
        "status <> 'completed' or "
        "(tenant_id is not null and completed_at is not null and response_payload is not null)",
        name="completed_result",
    ),
)
Index(
    "ix_tenant_provisioning_idempotency__tenant",
    tenant_provisioning_idempotency.c.tenant_id,
)

users = Table(
    "users",
    metadata,
    id_column(),
    Column("tenant_id", uuid_type, ForeignKey("tenants.id", name="fk_users__tenants")),
    Column("username", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("first_password_change_required", Boolean, nullable=False),
    Column("created_at", timestamp_tz, nullable=False),
    Column("updated_at", timestamp_tz, nullable=False),
    UniqueConstraint("tenant_id", "id", name="uq_users__tenant_id_id"),
    CheckConstraint("status in ('active', 'disabled')", name="status"),
)
Index(
    "uq_users__tenant_username_lower",
    users.c.tenant_id,
    func.lower(users.c.username),
    unique=True,
    postgresql_where=users.c.tenant_id.is_not(None),
)
Index(
    "uq_users__platform_username_lower",
    func.lower(users.c.username),
    unique=True,
    postgresql_where=users.c.tenant_id.is_(None),
)

credentials = Table(
    "credentials",
    metadata,
    Column(
        "user_id",
        uuid_type,
        ForeignKey("users.id", name="fk_credentials__users"),
        primary_key=True,
    ),
    Column("password_hash", Text, nullable=False),
    Column("bootstrap_credential", Boolean, nullable=False),
    Column("changed_at", timestamp_tz, nullable=False),
)

login_sessions = Table(
    "login_sessions",
    metadata,
    id_column(),
    Column("tenant_id", uuid_type, ForeignKey("tenants.id", name="fk_login_sessions__tenants")),
    Column(
        "user_id",
        uuid_type,
        ForeignKey("users.id", name="fk_login_sessions__users"),
        nullable=False,
    ),
    Column("app_scope", Text, nullable=False),
    Column("session_token_hash", Text, nullable=False),
    Column("issued_at", timestamp_tz, nullable=False),
    Column("expires_at", timestamp_tz, nullable=False),
    Column("revoked_at", timestamp_tz),
    UniqueConstraint("session_token_hash", name="uq_login_sessions__session_token_hash"),
    CheckConstraint(
        "app_scope in ('platform', 'tenant', 'cashier', 'station', 'service')",
        name="app_scope",
    ),
)

platform_role_assignments = Table(
    "platform_role_assignments",
    metadata,
    id_column(),
    Column(
        "user_id",
        uuid_type,
        ForeignKey("users.id", name="fk_platform_role_assignments__users"),
        nullable=False,
    ),
    Column("role", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("created_at", timestamp_tz, nullable=False),
    Column("updated_at", timestamp_tz, nullable=False),
    CheckConstraint("role in ('platform_owner')", name="role"),
    CheckConstraint("status in ('active', 'disabled')", name="status"),
)
Index(
    "uq_platform_role_assignments__active_platform_owner",
    platform_role_assignments.c.role,
    unique=True,
    postgresql_where=(
        (platform_role_assignments.c.role == "platform_owner")
        & (platform_role_assignments.c.status == "active")
    ),
)

totp_factors = Table(
    "totp_factors",
    metadata,
    Column(
        "user_id",
        uuid_type,
        ForeignKey("users.id", name="fk_totp_factors__users"),
        primary_key=True,
    ),
    Column("secret_ciphertext", LargeBinary, nullable=False),
    Column("enrolled_at", timestamp_tz, nullable=False),
    Column("enabled", Boolean, nullable=False),
)

staff_profiles = Table(
    "staff_profiles",
    metadata,
    Column("user_id", uuid_type, primary_key=True),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_staff_profiles__tenants"),
        nullable=False,
    ),
    Column("display_name", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("created_at", timestamp_tz, nullable=False),
    Column("updated_at", timestamp_tz, nullable=False),
    ForeignKeyConstraint(
        ["tenant_id", "user_id"],
        ["users.tenant_id", "users.id"],
        name="fk_staff_profiles__tenant_users",
    ),
    CheckConstraint("status in ('active', 'disabled')", name="status"),
)

staff_role_assignments = Table(
    "staff_role_assignments",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_staff_role_assignments__tenants"),
        nullable=False,
    ),
    Column("user_id", uuid_type, nullable=False),
    Column("role", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("created_at", timestamp_tz, nullable=False),
    Column("revoked_at", timestamp_tz),
    UniqueConstraint("tenant_id", "id", name="uq_staff_role_assignments__tenant_id_id"),
    ForeignKeyConstraint(
        ["tenant_id", "user_id"],
        ["users.tenant_id", "users.id"],
        name="fk_staff_role_assignments__tenant_users",
    ),
    CheckConstraint(
        "role in ('tenant_admin', 'cashier', 'station_staff', 'service_staff')",
        name="role",
    ),
    CheckConstraint("status in ('active', 'revoked')", name="status"),
)
Index(
    "uq_staff_role_assignments__tenant_user_role_active",
    staff_role_assignments.c.tenant_id,
    staff_role_assignments.c.user_id,
    staff_role_assignments.c.role,
    unique=True,
    postgresql_where=staff_role_assignments.c.status == "active",
)
Index(
    "ix_staff_role_assignments__tenant_user_active",
    staff_role_assignments.c.tenant_id,
    staff_role_assignments.c.user_id,
    postgresql_where=staff_role_assignments.c.status == "active",
)

tenant_lifecycle_events = Table(
    "tenant_lifecycle_events",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_tenant_lifecycle_events__tenants"),
        nullable=False,
    ),
    Column("previous_status", Text),
    Column("next_status", Text, nullable=False),
    Column(
        "actor_user_id",
        uuid_type,
        ForeignKey("users.id", name="fk_tenant_lifecycle_events__users"),
    ),
    Column("reason", Text, nullable=False),
    Column("created_at", timestamp_tz, nullable=False),
    UniqueConstraint("tenant_id", "id", name="uq_tenant_lifecycle_events__tenant_id_id"),
    CheckConstraint(
        "previous_status is null or previous_status in "
        "('provisioning', 'active', 'suspended', 'provisioning_failed')",
        name="previous_status",
    ),
    CheckConstraint(
        "next_status in ('provisioning', 'active', 'suspended', 'provisioning_failed')",
        name="next_status",
    ),
    CheckConstraint(
        "previous_status is null or previous_status is distinct from next_status",
        name="status_transition",
    ),
)
Index(
    "ix_tenant_lifecycle_events__tenant_created",
    tenant_lifecycle_events.c.tenant_id,
    tenant_lifecycle_events.c.created_at.desc(),
)

halls = Table(
    "halls",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_halls__tenants"),
        nullable=False,
    ),
    Column("name", Text, nullable=False),
    Column("display_order", Integer, nullable=False),
    Column("enabled", Boolean, nullable=False),
    Column("created_at", timestamp_tz, nullable=False),
    Column("updated_at", timestamp_tz, nullable=False),
    UniqueConstraint("tenant_id", "id", name="uq_halls__tenant_id_id"),
    UniqueConstraint("tenant_id", "display_order", name="uq_halls__tenant_display_order"),
)
Index("uq_halls__tenant_name_lower", halls.c.tenant_id, func.lower(halls.c.name), unique=True)

venue_tables = Table(
    "venue_tables",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_venue_tables__tenants"),
        nullable=False,
    ),
    Column("hall_id", uuid_type, nullable=False),
    Column("name", Text, nullable=False),
    Column("display_order", Integer, nullable=False),
    Column("enabled", Boolean, nullable=False),
    Column("created_at", timestamp_tz, nullable=False),
    Column("updated_at", timestamp_tz, nullable=False),
    UniqueConstraint("tenant_id", "id", name="uq_venue_tables__tenant_id_id"),
    UniqueConstraint(
        "tenant_id",
        "hall_id",
        "display_order",
        name="uq_venue_tables__tenant_hall_display_order",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "hall_id"],
        ["halls.tenant_id", "halls.id"],
        name="fk_venue_tables__tenant_halls",
    ),
)
Index(
    "uq_venue_tables__tenant_hall_name_lower",
    venue_tables.c.tenant_id,
    venue_tables.c.hall_id,
    func.lower(venue_tables.c.name),
    unique=True,
)
Index(
    "ix_venue_tables__tenant_hall_display",
    venue_tables.c.tenant_id,
    venue_tables.c.hall_id,
    venue_tables.c.display_order,
)

stations = Table(
    "stations",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_stations__tenants"),
        nullable=False,
    ),
    Column("name", Text, nullable=False),
    Column("display_order", Integer, nullable=False),
    Column("enabled", Boolean, nullable=False),
    Column("created_at", timestamp_tz, nullable=False),
    Column("updated_at", timestamp_tz, nullable=False),
    UniqueConstraint("tenant_id", "id", name="uq_stations__tenant_id_id"),
    UniqueConstraint("tenant_id", "display_order", name="uq_stations__tenant_display_order"),
)
Index(
    "uq_stations__tenant_name_lower", stations.c.tenant_id, func.lower(stations.c.name), unique=True
)

menu_categories = Table(
    "menu_categories",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_menu_categories__tenants"),
        nullable=False,
    ),
    Column("name", Text, nullable=False),
    Column("display_order", Integer, nullable=False),
    Column("enabled", Boolean, nullable=False),
    Column("created_at", timestamp_tz, nullable=False),
    Column("updated_at", timestamp_tz, nullable=False),
    UniqueConstraint("tenant_id", "id", name="uq_menu_categories__tenant_id_id"),
    UniqueConstraint(
        "tenant_id",
        "display_order",
        name="uq_menu_categories__tenant_display_order",
    ),
)
Index(
    "uq_menu_categories__tenant_name_lower",
    menu_categories.c.tenant_id,
    func.lower(menu_categories.c.name),
    unique=True,
)

product_services = Table(
    "product_services",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_product_services__tenants"),
        nullable=False,
    ),
    Column("category_id", uuid_type, nullable=False),
    Column("station_id", uuid_type, nullable=False),
    Column("name", Text, nullable=False),
    Column("description", Text),
    Column("image_ref", Text),
    Column("enabled", Boolean, nullable=False),
    Column("created_at", timestamp_tz, nullable=False),
    Column("updated_at", timestamp_tz, nullable=False),
    UniqueConstraint("tenant_id", "id", name="uq_product_services__tenant_id_id"),
    ForeignKeyConstraint(
        ["tenant_id", "category_id"],
        ["menu_categories.tenant_id", "menu_categories.id"],
        name="fk_product_services__tenant_menu_categories",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "station_id"],
        ["stations.tenant_id", "stations.id"],
        name="fk_product_services__tenant_stations",
    ),
)
Index(
    "uq_product_services__tenant_category_name_lower",
    product_services.c.tenant_id,
    product_services.c.category_id,
    func.lower(product_services.c.name),
    unique=True,
)
Index(
    "ix_product_services__tenant_category_enabled_name",
    product_services.c.tenant_id,
    product_services.c.category_id,
    product_services.c.enabled,
    product_services.c.name,
)
Index(
    "ix_product_services__tenant_enabled_category",
    product_services.c.tenant_id,
    product_services.c.enabled,
    product_services.c.category_id,
)
Index(
    "ix_product_services__tenant_station",
    product_services.c.tenant_id,
    product_services.c.station_id,
)

product_variants = Table(
    "product_variants",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_product_variants__tenants"),
        nullable=False,
    ),
    Column("product_service_id", uuid_type, nullable=False),
    Column("name", Text, nullable=False),
    Column("price_minor", BigInteger, nullable=False),
    Column("currency_code", CHAR(3), nullable=False, server_default="TRY"),
    Column("display_order", Integer, nullable=False),
    Column("is_default", Boolean, nullable=False),
    Column("enabled", Boolean, nullable=False),
    Column("created_at", timestamp_tz, nullable=False),
    Column("updated_at", timestamp_tz, nullable=False),
    UniqueConstraint("tenant_id", "id", name="uq_product_variants__tenant_id_id"),
    UniqueConstraint(
        "tenant_id",
        "product_service_id",
        "id",
        name="uq_product_variants__tenant_product_id",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "product_service_id"],
        ["product_services.tenant_id", "product_services.id"],
        name="fk_product_variants__tenant_product_services",
    ),
    CheckConstraint("price_minor >= 0", name="price_minor_non_negative"),
)
Index(
    "uq_product_variants__tenant_product_name_lower",
    product_variants.c.tenant_id,
    product_variants.c.product_service_id,
    func.lower(product_variants.c.name),
    unique=True,
)
Index(
    "uq_product_variants__tenant_product_default",
    product_variants.c.tenant_id,
    product_variants.c.product_service_id,
    unique=True,
    postgresql_where=product_variants.c.is_default.is_(True),
)
Index(
    "ix_product_variants__tenant_product_display",
    product_variants.c.tenant_id,
    product_variants.c.product_service_id,
    product_variants.c.display_order,
)
Index(
    "ix_product_variants__tenant_product_enabled",
    product_variants.c.tenant_id,
    product_variants.c.product_service_id,
    product_variants.c.enabled,
)

availability_overrides = Table(
    "availability_overrides",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_availability_overrides__tenants"),
        nullable=False,
    ),
    Column("product_service_id", uuid_type, nullable=False),
    Column("product_variant_id", uuid_type),
    Column("state", Text, nullable=False),
    Column("reason", Text),
    Column("starts_at", timestamp_tz),
    Column("expires_at", timestamp_tz),
    Column("created_by_user_id", uuid_type, nullable=False),
    Column("created_at", timestamp_tz, nullable=False),
    UniqueConstraint("tenant_id", "id", name="uq_availability_overrides__tenant_id_id"),
    ForeignKeyConstraint(
        ["tenant_id", "product_service_id"],
        ["product_services.tenant_id", "product_services.id"],
        name="fk_availability_overrides__tenant_product_services",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "product_service_id", "product_variant_id"],
        [
            "product_variants.tenant_id",
            "product_variants.product_service_id",
            "product_variants.id",
        ],
        name="fk_availability_overrides__tenant_product_variants",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "created_by_user_id"],
        ["users.tenant_id", "users.id"],
        name="fk_availability_overrides__tenant_users",
    ),
    CheckConstraint("state in ('available', 'unavailable')", name="state"),
    CheckConstraint(
        "expires_at is null or starts_at is null or expires_at > starts_at",
        name="valid_time_window",
    ),
)
Index(
    "ix_availability_overrides__tenant_product",
    availability_overrides.c.tenant_id,
    availability_overrides.c.product_service_id,
    availability_overrides.c.product_variant_id,
)

modifier_groups = Table(
    "modifier_groups",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_modifier_groups__tenants"),
        nullable=False,
    ),
    Column("product_service_id", uuid_type, nullable=False),
    Column("name", Text, nullable=False),
    Column("required", Boolean, nullable=False),
    Column("min_selections", Integer, nullable=False),
    Column("max_selections", Integer, nullable=False),
    Column("display_order", Integer, nullable=False),
    Column("created_at", timestamp_tz, nullable=False),
    Column("updated_at", timestamp_tz, nullable=False),
    UniqueConstraint("tenant_id", "id", name="uq_modifier_groups__tenant_id_id"),
    ForeignKeyConstraint(
        ["tenant_id", "product_service_id"],
        ["product_services.tenant_id", "product_services.id"],
        name="fk_modifier_groups__tenant_product_services",
    ),
    CheckConstraint(
        "min_selections >= 0 and max_selections >= min_selections",
        name="selection_bounds",
    ),
)
Index(
    "uq_modifier_groups__tenant_product_name_lower",
    modifier_groups.c.tenant_id,
    modifier_groups.c.product_service_id,
    func.lower(modifier_groups.c.name),
    unique=True,
)
Index(
    "ix_modifier_groups__tenant_product_display",
    modifier_groups.c.tenant_id,
    modifier_groups.c.product_service_id,
    modifier_groups.c.display_order,
)

modifier_options = Table(
    "modifier_options",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_modifier_options__tenants"),
        nullable=False,
    ),
    Column("modifier_group_id", uuid_type, nullable=False),
    Column("name", Text, nullable=False),
    Column("price_delta_minor", BigInteger, nullable=False),
    Column("currency_code", CHAR(3), nullable=False, server_default="TRY"),
    Column("available", Boolean, nullable=False),
    Column("display_order", Integer, nullable=False),
    Column("created_at", timestamp_tz, nullable=False),
    Column("updated_at", timestamp_tz, nullable=False),
    UniqueConstraint("tenant_id", "id", name="uq_modifier_options__tenant_id_id"),
    ForeignKeyConstraint(
        ["tenant_id", "modifier_group_id"],
        ["modifier_groups.tenant_id", "modifier_groups.id"],
        name="fk_modifier_options__tenant_modifier_groups",
    ),
    CheckConstraint("price_delta_minor >= 0", name="price_delta_non_negative"),
)
Index(
    "uq_modifier_options__tenant_group_name_lower",
    modifier_options.c.tenant_id,
    modifier_options.c.modifier_group_id,
    func.lower(modifier_options.c.name),
    unique=True,
)
Index(
    "ix_modifier_options__tenant_group_display",
    modifier_options.c.tenant_id,
    modifier_options.c.modifier_group_id,
    modifier_options.c.display_order,
)

staff_station_assignments = Table(
    "staff_station_assignments",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_staff_station_assignments__tenants"),
        nullable=False,
    ),
    Column("user_id", uuid_type, nullable=False),
    Column("station_id", uuid_type, nullable=False),
    Column("status", Text, nullable=False),
    Column("created_at", timestamp_tz, nullable=False),
    Column("revoked_at", timestamp_tz),
    UniqueConstraint("tenant_id", "id", name="uq_staff_station_assignments__tenant_id_id"),
    ForeignKeyConstraint(
        ["tenant_id", "user_id"],
        ["users.tenant_id", "users.id"],
        name="fk_staff_station_assignments__tenant_users",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "station_id"],
        ["stations.tenant_id", "stations.id"],
        name="fk_staff_station_assignments__tenant_stations",
    ),
    CheckConstraint("status in ('active', 'revoked')", name="status"),
)
Index(
    "uq_staff_station_assignments__tenant_user_station_active",
    staff_station_assignments.c.tenant_id,
    staff_station_assignments.c.user_id,
    staff_station_assignments.c.station_id,
    unique=True,
    postgresql_where=staff_station_assignments.c.status == "active",
)
Index(
    "ix_staff_station_assignments__tenant_user_active",
    staff_station_assignments.c.tenant_id,
    staff_station_assignments.c.user_id,
    postgresql_where=staff_station_assignments.c.status == "active",
)
Index(
    "ix_staff_station_assignments__tenant_station",
    staff_station_assignments.c.tenant_id,
    staff_station_assignments.c.station_id,
)

staff_hall_assignments = Table(
    "staff_hall_assignments",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_staff_hall_assignments__tenants"),
        nullable=False,
    ),
    Column("user_id", uuid_type, nullable=False),
    Column("hall_id", uuid_type, nullable=False),
    Column("status", Text, nullable=False),
    Column("created_at", timestamp_tz, nullable=False),
    Column("revoked_at", timestamp_tz),
    UniqueConstraint("tenant_id", "id", name="uq_staff_hall_assignments__tenant_id_id"),
    ForeignKeyConstraint(
        ["tenant_id", "user_id"],
        ["users.tenant_id", "users.id"],
        name="fk_staff_hall_assignments__tenant_users",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "hall_id"],
        ["halls.tenant_id", "halls.id"],
        name="fk_staff_hall_assignments__tenant_halls",
    ),
    CheckConstraint("status in ('active', 'revoked')", name="status"),
)
Index(
    "uq_staff_hall_assignments__tenant_user_hall_active",
    staff_hall_assignments.c.tenant_id,
    staff_hall_assignments.c.user_id,
    staff_hall_assignments.c.hall_id,
    unique=True,
    postgresql_where=staff_hall_assignments.c.status == "active",
)
Index(
    "ix_staff_hall_assignments__tenant_user_active",
    staff_hall_assignments.c.tenant_id,
    staff_hall_assignments.c.user_id,
    postgresql_where=staff_hall_assignments.c.status == "active",
)
Index(
    "ix_staff_hall_assignments__tenant_hall",
    staff_hall_assignments.c.tenant_id,
    staff_hall_assignments.c.hall_id,
)

table_display_claims = Table(
    "table_display_claims",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_table_display_claims__tenants"),
        nullable=False,
    ),
    Column("table_id", uuid_type, nullable=False),
    Column("claim_hash", Text, nullable=False),
    Column("created_by_user_id", uuid_type, nullable=False),
    Column("expires_at", timestamp_tz, nullable=False),
    Column("consumed_at", timestamp_tz),
    Column("created_at", timestamp_tz, nullable=False),
    UniqueConstraint("tenant_id", "id", name="uq_table_display_claims__tenant_id_id"),
    UniqueConstraint("claim_hash", name="uq_table_display_claims__claim_hash"),
    ForeignKeyConstraint(
        ["tenant_id", "table_id"],
        ["venue_tables.tenant_id", "venue_tables.id"],
        name="fk_table_display_claims__tenant_venue_tables",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "created_by_user_id"],
        ["users.tenant_id", "users.id"],
        name="fk_table_display_claims__tenant_users",
    ),
    CheckConstraint(
        "consumed_at is null or consumed_at <= expires_at",
        name="consumed_before_expiry",
    ),
)
Index(
    "ix_table_display_claims__tenant_table_created",
    table_display_claims.c.tenant_id,
    table_display_claims.c.table_id,
    table_display_claims.c.created_at.desc(),
)

table_display_credentials = Table(
    "table_display_credentials",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_table_display_credentials__tenants"),
        nullable=False,
    ),
    Column("table_id", uuid_type, nullable=False),
    Column("credential_hash", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("provisioned_at", timestamp_tz, nullable=False),
    Column("revoked_at", timestamp_tz),
    Column("last_seen_at", timestamp_tz),
    UniqueConstraint("tenant_id", "id", name="uq_table_display_credentials__tenant_id_id"),
    UniqueConstraint("credential_hash", name="uq_table_display_credentials__credential_hash"),
    ForeignKeyConstraint(
        ["tenant_id", "table_id"],
        ["venue_tables.tenant_id", "venue_tables.id"],
        name="fk_table_display_credentials__tenant_venue_tables",
    ),
    CheckConstraint("status in ('active', 'revoked')", name="status"),
    CheckConstraint(
        "(status = 'active' and revoked_at is null) "
        "or (status = 'revoked' and revoked_at is not null)",
        name="revocation_lifecycle",
    ),
)
Index(
    "uq_table_display_credentials__tenant_table_active",
    table_display_credentials.c.tenant_id,
    table_display_credentials.c.table_id,
    unique=True,
    postgresql_where=table_display_credentials.c.status == "active",
)
Index(
    "ix_table_display_credentials__tenant_table",
    table_display_credentials.c.tenant_id,
    table_display_credentials.c.table_id,
)

table_access_tokens = Table(
    "table_access_tokens",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_table_access_tokens__tenants"),
        nullable=False,
    ),
    Column("table_id", uuid_type, nullable=False),
    Column("token_hash", Text, nullable=False),
    Column("expires_at", timestamp_tz, nullable=False),
    Column("consumed_at", timestamp_tz),
    Column("created_at", timestamp_tz, nullable=False),
    UniqueConstraint("tenant_id", "id", name="uq_table_access_tokens__tenant_id_id"),
    UniqueConstraint("token_hash", name="uq_table_access_tokens__token_hash"),
    ForeignKeyConstraint(
        ["tenant_id", "table_id"],
        ["venue_tables.tenant_id", "venue_tables.id"],
        name="fk_table_access_tokens__tenant_venue_tables",
    ),
    CheckConstraint(
        "consumed_at is null or consumed_at <= expires_at",
        name="consumed_before_expiry",
    ),
)
Index(
    "ix_table_access_tokens__tenant_table_created",
    table_access_tokens.c.tenant_id,
    table_access_tokens.c.table_id,
    table_access_tokens.c.created_at.desc(),
)

table_sessions = Table(
    "table_sessions",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_table_sessions__tenants"),
        nullable=False,
    ),
    Column("table_id", uuid_type, nullable=False),
    Column("status", Text, nullable=False),
    Column("opened_at", timestamp_tz, nullable=False),
    Column("closed_at", timestamp_tz),
    Column("created_at", timestamp_tz, nullable=False),
    Column("updated_at", timestamp_tz, nullable=False),
    UniqueConstraint("tenant_id", "id", name="uq_table_sessions__tenant_id_id"),
    ForeignKeyConstraint(
        ["tenant_id", "table_id"],
        ["venue_tables.tenant_id", "venue_tables.id"],
        name="fk_table_sessions__tenant_venue_tables",
    ),
    CheckConstraint("status in ('open', 'closed')", name="status"),
    CheckConstraint(
        "(status = 'open' and closed_at is null) or (status = 'closed' and closed_at is not null)",
        name="closed_at_lifecycle",
    ),
)
Index(
    "uq_table_sessions__tenant_table_open",
    table_sessions.c.tenant_id,
    table_sessions.c.table_id,
    unique=True,
    postgresql_where=table_sessions.c.status == "open",
)
Index(
    "ix_table_sessions__tenant_status_opened",
    table_sessions.c.tenant_id,
    table_sessions.c.status,
    table_sessions.c.opened_at.desc(),
)

checks = Table(
    "checks",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_checks__tenants"),
        nullable=False,
    ),
    Column("table_session_id", uuid_type, nullable=False),
    Column("status", Text, nullable=False),
    Column("opened_at", timestamp_tz, nullable=False),
    Column("closed_at", timestamp_tz),
    UniqueConstraint("tenant_id", "id", name="uq_checks__tenant_id_id"),
    UniqueConstraint("table_session_id", name="uq_checks__table_session_id"),
    ForeignKeyConstraint(
        ["tenant_id", "table_session_id"],
        ["table_sessions.tenant_id", "table_sessions.id"],
        name="fk_checks__tenant_table_sessions",
    ),
    CheckConstraint("status in ('open', 'closed')", name="status"),
    CheckConstraint(
        "(status = 'open' and closed_at is null) or (status = 'closed' and closed_at is not null)",
        name="closed_at_lifecycle",
    ),
)

customer_ordering_sessions = Table(
    "customer_ordering_sessions",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_customer_ordering_sessions__tenants"),
        nullable=False,
    ),
    Column("table_id", uuid_type, nullable=False),
    Column("table_session_id", uuid_type),
    Column("cookie_token_hash", Text, nullable=False),
    Column("presence_valid_until", timestamp_tz, nullable=False),
    Column("expires_at", timestamp_tz, nullable=False),
    Column("last_seen_at", timestamp_tz, nullable=False),
    Column("created_at", timestamp_tz, nullable=False),
    Column("updated_at", timestamp_tz, nullable=False),
    UniqueConstraint("tenant_id", "id", name="uq_customer_ordering_sessions__tenant_id_id"),
    UniqueConstraint(
        "cookie_token_hash",
        name="uq_customer_ordering_sessions__cookie_token_hash",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "table_id"],
        ["venue_tables.tenant_id", "venue_tables.id"],
        name="fk_customer_ordering_sessions__tenant_venue_tables",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "table_session_id"],
        ["table_sessions.tenant_id", "table_sessions.id"],
        name="fk_customer_ordering_sessions__tenant_table_sessions",
    ),
    CheckConstraint("presence_valid_until <= expires_at", name="presence_within_session"),
)
Index(
    "ix_customer_ordering_sessions__tenant_table_last_seen",
    customer_ordering_sessions.c.tenant_id,
    customer_ordering_sessions.c.table_id,
    customer_ordering_sessions.c.last_seen_at.desc(),
)

customer_carts = Table(
    "customer_carts",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_customer_carts__tenants"),
        nullable=False,
    ),
    Column("customer_ordering_session_id", uuid_type, nullable=False),
    Column("status", Text, nullable=False),
    Column("created_at", timestamp_tz, nullable=False),
    Column("updated_at", timestamp_tz, nullable=False),
    UniqueConstraint("tenant_id", "id", name="uq_customer_carts__tenant_id_id"),
    ForeignKeyConstraint(
        ["tenant_id", "customer_ordering_session_id"],
        ["customer_ordering_sessions.tenant_id", "customer_ordering_sessions.id"],
        name="fk_customer_carts__tenant_customer_ordering_sessions",
    ),
    CheckConstraint("status in ('active', 'submitted', 'abandoned')", name="status"),
)
Index(
    "uq_customer_carts__tenant_customer_session_active",
    customer_carts.c.tenant_id,
    customer_carts.c.customer_ordering_session_id,
    unique=True,
    postgresql_where=customer_carts.c.status == "active",
)

customer_cart_items = Table(
    "customer_cart_items",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_customer_cart_items__tenants"),
        nullable=False,
    ),
    Column("cart_id", uuid_type, nullable=False),
    Column("client_cart_item_id", Text, nullable=False),
    Column("product_service_id", uuid_type, nullable=False),
    Column("product_variant_id", uuid_type, nullable=False),
    Column("quantity", Integer, nullable=False),
    Column("selected_modifiers", JSONB, nullable=False),
    Column("note", Text),
    Column("estimated_price_minor", BigInteger, nullable=False),
    Column("created_at", timestamp_tz, nullable=False),
    Column("updated_at", timestamp_tz, nullable=False),
    UniqueConstraint("tenant_id", "id", name="uq_customer_cart_items__tenant_id_id"),
    UniqueConstraint(
        "tenant_id",
        "cart_id",
        "client_cart_item_id",
        name="uq_customer_cart_items__tenant_cart_client_item",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "cart_id"],
        ["customer_carts.tenant_id", "customer_carts.id"],
        name="fk_customer_cart_items__tenant_customer_carts",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "product_service_id"],
        ["product_services.tenant_id", "product_services.id"],
        name="fk_customer_cart_items__tenant_product_services",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "product_service_id", "product_variant_id"],
        [
            "product_variants.tenant_id",
            "product_variants.product_service_id",
            "product_variants.id",
        ],
        name="fk_customer_cart_items__tenant_product_variants",
    ),
    CheckConstraint("quantity > 0", name="quantity_positive"),
)
Index(
    "ix_customer_cart_items__tenant_cart",
    customer_cart_items.c.tenant_id,
    customer_cart_items.c.cart_id,
)

orders = Table(
    "orders",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_orders__tenants"),
        nullable=False,
    ),
    Column("customer_ordering_session_id", uuid_type, nullable=False),
    Column("table_session_id", uuid_type, nullable=False),
    Column("status", Text, nullable=False),
    Column("order_channel", Text, nullable=False),
    Column("submitted_at", timestamp_tz, nullable=False),
    Column("created_at", timestamp_tz, nullable=False),
    UniqueConstraint("tenant_id", "id", name="uq_orders__tenant_id_id"),
    ForeignKeyConstraint(
        ["tenant_id", "customer_ordering_session_id"],
        ["customer_ordering_sessions.tenant_id", "customer_ordering_sessions.id"],
        name="fk_orders__tenant_customer_ordering_sessions",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "table_session_id"],
        ["table_sessions.tenant_id", "table_sessions.id"],
        name="fk_orders__tenant_table_sessions",
    ),
    CheckConstraint("status in ('submitted')", name="status"),
    CheckConstraint("order_channel in ('dine_in_qr')", name="order_channel"),
)
Index(
    "ix_orders__tenant_customer_session_submitted",
    orders.c.tenant_id,
    orders.c.customer_ordering_session_id,
    orders.c.submitted_at.desc(),
)
Index(
    "ix_orders__tenant_table_session_submitted",
    orders.c.tenant_id,
    orders.c.table_session_id,
    orders.c.submitted_at.desc(),
)

order_items = Table(
    "order_items",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_order_items__tenants"),
        nullable=False,
    ),
    Column("order_id", uuid_type, nullable=False),
    Column("product_service_id", uuid_type, nullable=False),
    Column("product_variant_id", uuid_type, nullable=False),
    Column("station_id", uuid_type, nullable=False),
    Column("name_snapshot", Text, nullable=False),
    Column("variant_name_snapshot", Text, nullable=False),
    Column("unit_price_minor", BigInteger, nullable=False),
    Column("currency_code", CHAR(3), nullable=False, server_default="TRY"),
    Column("modifier_snapshot", JSONB, nullable=False),
    Column("quantity", Integer, nullable=False),
    Column("note", Text),
    Column("voided_at", timestamp_tz),
    Column("voided_by_user_id", uuid_type),
    Column("void_reason", Text),
    Column("created_at", timestamp_tz, nullable=False),
    UniqueConstraint("tenant_id", "id", name="uq_order_items__tenant_id_id"),
    UniqueConstraint(
        "tenant_id",
        "id",
        "station_id",
        name="uq_order_items__tenant_id_id_station_id",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "order_id"],
        ["orders.tenant_id", "orders.id"],
        name="fk_order_items__tenant_orders",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "product_service_id"],
        ["product_services.tenant_id", "product_services.id"],
        name="fk_order_items__tenant_product_services",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "product_service_id", "product_variant_id"],
        [
            "product_variants.tenant_id",
            "product_variants.product_service_id",
            "product_variants.id",
        ],
        name="fk_order_items__tenant_product_variants",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "station_id"],
        ["stations.tenant_id", "stations.id"],
        name="fk_order_items__tenant_stations",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "voided_by_user_id"],
        ["users.tenant_id", "users.id"],
        name="fk_order_items__tenant_void_users",
    ),
    CheckConstraint("quantity > 0", name="quantity_positive"),
    CheckConstraint("unit_price_minor >= 0", name="unit_price_non_negative"),
    CheckConstraint(
        "(voided_at is null and voided_by_user_id is null and void_reason is null) "
        "or (voided_at is not null and voided_by_user_id is not null "
        "and void_reason is not null and void_reason <> '')",
        name="void_fields_complete",
    ),
)
Index("ix_order_items__tenant_order", order_items.c.tenant_id, order_items.c.order_id)

preparation_items = Table(
    "preparation_items",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_preparation_items__tenants"),
        nullable=False,
    ),
    Column("order_item_id", uuid_type, nullable=False),
    Column("station_id", uuid_type, nullable=False),
    Column("status", Text, nullable=False),
    Column("cannot_prepare_reason", Text),
    Column("updated_by_user_id", uuid_type),
    Column("updated_at", timestamp_tz, nullable=False),
    Column("created_at", timestamp_tz, nullable=False),
    UniqueConstraint("tenant_id", "id", name="uq_preparation_items__tenant_id_id"),
    UniqueConstraint(
        "tenant_id",
        "order_item_id",
        name="uq_preparation_items__tenant_order_item",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "order_item_id", "station_id"],
        ["order_items.tenant_id", "order_items.id", "order_items.station_id"],
        name="fk_preparation_items__tenant_order_items_station",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "station_id"],
        ["stations.tenant_id", "stations.id"],
        name="fk_preparation_items__tenant_stations",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "updated_by_user_id"],
        ["users.tenant_id", "users.id"],
        name="fk_preparation_items__tenant_updated_users",
    ),
    CheckConstraint(
        "status in ('pending', 'preparing', 'ready', 'cannot_prepare')",
        name="status",
    ),
    CheckConstraint(
        "(status = 'cannot_prepare' and cannot_prepare_reason is not null "
        "and cannot_prepare_reason <> '') or "
        "(status <> 'cannot_prepare' and cannot_prepare_reason is null)",
        name="cannot_prepare_reason_lifecycle",
    ),
    CheckConstraint(
        "status = 'pending' or updated_by_user_id is not null",
        name="non_pending_actor_required",
    ),
)
Index(
    "ix_preparation_items__tenant_station_status_updated",
    preparation_items.c.tenant_id,
    preparation_items.c.station_id,
    preparation_items.c.status,
    preparation_items.c.updated_at.desc(),
)
Index(
    "ix_preparation_items__tenant_status_updated",
    preparation_items.c.tenant_id,
    preparation_items.c.status,
    preparation_items.c.updated_at.desc(),
)

preparation_transitions = Table(
    "preparation_transitions",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_preparation_transitions__tenants"),
        nullable=False,
    ),
    Column("preparation_item_id", uuid_type, nullable=False),
    Column("actor_user_id", uuid_type),
    Column("from_status", Text),
    Column("to_status", Text, nullable=False),
    Column("reason", Text),
    Column("created_at", timestamp_tz, nullable=False),
    UniqueConstraint("tenant_id", "id", name="uq_preparation_transitions__tenant_id_id"),
    ForeignKeyConstraint(
        ["tenant_id", "preparation_item_id"],
        ["preparation_items.tenant_id", "preparation_items.id"],
        name="fk_preparation_transitions__tenant_preparation_items",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "actor_user_id"],
        ["users.tenant_id", "users.id"],
        name="fk_preparation_transitions__tenant_users",
    ),
    CheckConstraint(
        "from_status is null or from_status in ('pending', 'preparing', 'ready', 'cannot_prepare')",
        name="from_status",
    ),
    CheckConstraint(
        "to_status in ('pending', 'preparing', 'ready', 'cannot_prepare')",
        name="to_status",
    ),
    CheckConstraint(
        "(from_status is null and to_status = 'pending') or "
        "(from_status = 'pending' and to_status in ('preparing', 'cannot_prepare')) or "
        "(from_status = 'preparing' and to_status in ('ready', 'cannot_prepare'))",
        name="valid_transition",
    ),
    CheckConstraint(
        "(to_status = 'cannot_prepare' and reason is not null and reason <> '') or "
        "(to_status <> 'cannot_prepare' and reason is null)",
        name="cannot_prepare_reason_lifecycle",
    ),
    CheckConstraint(
        "from_status is null or actor_user_id is not null",
        name="actor_required_after_initial",
    ),
)
Index(
    "ix_preparation_transitions__tenant_item_created",
    preparation_transitions.c.tenant_id,
    preparation_transitions.c.preparation_item_id,
    preparation_transitions.c.created_at.desc(),
)

delivery_states = Table(
    "delivery_states",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_delivery_states__tenants"),
        nullable=False,
    ),
    Column("order_item_id", uuid_type, nullable=False),
    Column("status", Text, nullable=False),
    Column("updated_by_user_id", uuid_type, nullable=False),
    Column("updated_at", timestamp_tz, nullable=False),
    Column("created_at", timestamp_tz, nullable=False),
    UniqueConstraint("tenant_id", "id", name="uq_delivery_states__tenant_id_id"),
    UniqueConstraint(
        "tenant_id",
        "id",
        "order_item_id",
        name="uq_delivery_states__tenant_id_id_order_item_id",
    ),
    UniqueConstraint(
        "tenant_id",
        "order_item_id",
        name="uq_delivery_states__tenant_order_item",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "order_item_id"],
        ["order_items.tenant_id", "order_items.id"],
        name="fk_delivery_states__tenant_order_items",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "updated_by_user_id"],
        ["users.tenant_id", "users.id"],
        name="fk_delivery_states__tenant_updated_users",
    ),
    CheckConstraint("status in ('picked_up', 'delivered')", name="status"),
)
Index(
    "ix_delivery_states__tenant_status_updated",
    delivery_states.c.tenant_id,
    delivery_states.c.status,
    delivery_states.c.updated_at.desc(),
)

delivery_transitions = Table(
    "delivery_transitions",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_delivery_transitions__tenants"),
        nullable=False,
    ),
    Column("delivery_state_id", uuid_type, nullable=False),
    Column("order_item_id", uuid_type, nullable=False),
    Column("actor_user_id", uuid_type, nullable=False),
    Column("from_status", Text),
    Column("to_status", Text, nullable=False),
    Column("created_at", timestamp_tz, nullable=False),
    UniqueConstraint("tenant_id", "id", name="uq_delivery_transitions__tenant_id_id"),
    ForeignKeyConstraint(
        ["tenant_id", "delivery_state_id", "order_item_id"],
        ["delivery_states.tenant_id", "delivery_states.id", "delivery_states.order_item_id"],
        name="fk_delivery_transitions__tenant_delivery_states",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "actor_user_id"],
        ["users.tenant_id", "users.id"],
        name="fk_delivery_transitions__tenant_users",
    ),
    CheckConstraint(
        "from_status is null or from_status = 'picked_up'",
        name="from_status",
    ),
    CheckConstraint("to_status in ('picked_up', 'delivered')", name="to_status"),
    CheckConstraint(
        "(from_status is null and to_status in ('picked_up', 'delivered')) or "
        "(from_status = 'picked_up' and to_status = 'delivered')",
        name="valid_transition",
    ),
)
Index(
    "ix_delivery_transitions__tenant_item_created",
    delivery_transitions.c.tenant_id,
    delivery_transitions.c.order_item_id,
    delivery_transitions.c.created_at.desc(),
)

delivery_bulk_idempotency = Table(
    "delivery_bulk_idempotency",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_delivery_bulk_idempotency__tenants"),
        nullable=False,
    ),
    Column("actor_user_id", uuid_type, nullable=False),
    Column("table_id", uuid_type, nullable=False),
    Column("idempotency_key", Text, nullable=False),
    Column("request_hash", Text, nullable=False),
    Column("delivered_order_item_ids", JSONB),
    Column("status", Text, nullable=False),
    Column("created_at", timestamp_tz, nullable=False),
    Column("completed_at", timestamp_tz),
    UniqueConstraint("tenant_id", "id", name="uq_delivery_bulk_idempotency__tenant_id_id"),
    UniqueConstraint(
        "tenant_id",
        "actor_user_id",
        "idempotency_key",
        name="uq_delivery_bulk_idempotency__tenant_actor_key",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "actor_user_id"],
        ["users.tenant_id", "users.id"],
        name="fk_delivery_bulk_idempotency__tenant_users",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "table_id"],
        ["venue_tables.tenant_id", "venue_tables.id"],
        name="fk_delivery_bulk_idempotency__tenant_venue_tables",
    ),
    CheckConstraint("status in ('processing', 'completed', 'failed')", name="status"),
    CheckConstraint(
        "delivered_order_item_ids is null or jsonb_typeof(delivered_order_item_ids) = 'array'",
        name="delivered_order_item_ids_array",
    ),
    CheckConstraint(
        "status <> 'completed' or "
        "(completed_at is not null and delivered_order_item_ids is not null)",
        name="completed_result",
    ),
)

order_submit_idempotency = Table(
    "order_submit_idempotency",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_order_submit_idempotency__tenants"),
        nullable=False,
    ),
    Column("customer_ordering_session_id", uuid_type, nullable=False),
    Column("idempotency_key", Text, nullable=False),
    Column("request_hash", Text, nullable=False),
    Column("order_id", uuid_type),
    Column("status", Text, nullable=False),
    Column("created_at", timestamp_tz, nullable=False),
    Column("completed_at", timestamp_tz),
    UniqueConstraint("tenant_id", "id", name="uq_order_submit_idempotency__tenant_id_id"),
    UniqueConstraint(
        "tenant_id",
        "customer_ordering_session_id",
        "idempotency_key",
        name="uq_order_submit_idempotency__tenant_session_key",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "customer_ordering_session_id"],
        ["customer_ordering_sessions.tenant_id", "customer_ordering_sessions.id"],
        name="fk_order_submit_idempotency__tenant_customer_ordering_sessions",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "order_id"],
        ["orders.tenant_id", "orders.id"],
        name="fk_order_submit_idempotency__tenant_orders",
    ),
    CheckConstraint("status in ('processing', 'completed', 'failed')", name="status"),
    CheckConstraint(
        "status <> 'completed' or (order_id is not null and completed_at is not null)",
        name="completed_result",
    ),
)

price_adjustments = Table(
    "price_adjustments",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_price_adjustments__tenants"),
        nullable=False,
    ),
    Column("check_id", uuid_type, nullable=False),
    Column("order_item_id", uuid_type),
    Column("type", Text, nullable=False),
    Column("amount_minor", BigInteger, nullable=False),
    Column("currency_code", CHAR(3), nullable=False, server_default="TRY"),
    Column("reason", Text),
    Column("created_by_user_id", uuid_type, nullable=False),
    Column("created_at", timestamp_tz, nullable=False),
    UniqueConstraint("tenant_id", "id", name="uq_price_adjustments__tenant_id_id"),
    ForeignKeyConstraint(
        ["tenant_id", "check_id"],
        ["checks.tenant_id", "checks.id"],
        name="fk_price_adjustments__tenant_checks",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "order_item_id"],
        ["order_items.tenant_id", "order_items.id"],
        name="fk_price_adjustments__tenant_order_items",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "created_by_user_id"],
        ["users.tenant_id", "users.id"],
        name="fk_price_adjustments__tenant_users",
    ),
    CheckConstraint(
        "type in ('tax', 'discount', 'service_charge', 'campaign', 'correction')",
        name="type",
    ),
    CheckConstraint(
        "type <> 'correction' or (reason is not null and reason <> '')",
        name="correction_reason",
    ),
)

session_closures = Table(
    "session_closures",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_session_closures__tenants"),
        nullable=False,
    ),
    Column("table_session_id", uuid_type, nullable=False),
    Column("check_id", uuid_type, nullable=False),
    Column("cashier_user_id", uuid_type, nullable=False),
    Column("reason", Text),
    Column("closed_at", timestamp_tz, nullable=False),
    UniqueConstraint("tenant_id", "id", name="uq_session_closures__tenant_id_id"),
    UniqueConstraint("table_session_id", name="uq_session_closures__table_session_id"),
    ForeignKeyConstraint(
        ["tenant_id", "table_session_id"],
        ["table_sessions.tenant_id", "table_sessions.id"],
        name="fk_session_closures__tenant_table_sessions",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "check_id"],
        ["checks.tenant_id", "checks.id"],
        name="fk_session_closures__tenant_checks",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "cashier_user_id"],
        ["users.tenant_id", "users.id"],
        name="fk_session_closures__tenant_users",
    ),
)

payments = Table(
    "payments",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_payments__tenants"),
        nullable=False,
    ),
    Column("check_id", uuid_type, nullable=False),
    Column("amount_minor", BigInteger, nullable=False),
    Column("currency_code", CHAR(3), nullable=False, server_default="TRY"),
    Column("method", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("cashier_user_id", uuid_type, nullable=False),
    Column("received_at", timestamp_tz, nullable=False),
    Column("voided_at", timestamp_tz),
    Column("voided_by_user_id", uuid_type),
    Column("void_reason", Text),
    Column("created_at", timestamp_tz, nullable=False),
    Column("updated_at", timestamp_tz, nullable=False),
    UniqueConstraint("tenant_id", "id", name="uq_payments__tenant_id_id"),
    ForeignKeyConstraint(
        ["tenant_id", "check_id"],
        ["checks.tenant_id", "checks.id"],
        name="fk_payments__tenant_checks",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "cashier_user_id"],
        ["users.tenant_id", "users.id"],
        name="fk_payments__tenant_cashier_users",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "voided_by_user_id"],
        ["users.tenant_id", "users.id"],
        name="fk_payments__tenant_void_users",
    ),
    CheckConstraint("amount_minor > 0", name="amount_positive"),
    CheckConstraint("method in ('cash', 'card', 'transfer')", name="method"),
    CheckConstraint("status in ('recorded', 'voided')", name="status"),
    CheckConstraint(
        "(status = 'recorded' and voided_at is null and voided_by_user_id is null "
        "and void_reason is null) or (status = 'voided' and voided_at is not null "
        "and voided_by_user_id is not null and void_reason is not null and void_reason <> '')",
        name="void_lifecycle",
    ),
)
Index(
    "ix_payments__tenant_check_received",
    payments.c.tenant_id,
    payments.c.check_id,
    payments.c.received_at.desc(),
)
Index("ix_payments__tenant_received", payments.c.tenant_id, payments.c.received_at.desc())

payment_idempotency = Table(
    "payment_idempotency",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_payment_idempotency__tenants"),
        nullable=False,
    ),
    Column("check_id", uuid_type, nullable=False),
    Column("idempotency_key", Text, nullable=False),
    Column("request_hash", Text, nullable=False),
    Column("payment_id", uuid_type),
    Column("status", Text, nullable=False),
    Column("created_at", timestamp_tz, nullable=False),
    Column("completed_at", timestamp_tz),
    UniqueConstraint("tenant_id", "id", name="uq_payment_idempotency__tenant_id_id"),
    UniqueConstraint(
        "tenant_id",
        "check_id",
        "idempotency_key",
        name="uq_payment_idempotency__tenant_check_key",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "check_id"],
        ["checks.tenant_id", "checks.id"],
        name="fk_payment_idempotency__tenant_checks",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "payment_id"],
        ["payments.tenant_id", "payments.id"],
        name="fk_payment_idempotency__tenant_payments",
    ),
    CheckConstraint("status in ('processing', 'completed', 'failed')", name="status"),
    CheckConstraint(
        "status <> 'completed' or (payment_id is not null and completed_at is not null)",
        name="completed_result",
    ),
)

payment_void_idempotency = Table(
    "payment_void_idempotency",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_payment_void_idempotency__tenants"),
        nullable=False,
    ),
    Column("payment_id", uuid_type, nullable=False),
    Column("idempotency_key", Text, nullable=False),
    Column("request_hash", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("created_at", timestamp_tz, nullable=False),
    Column("completed_at", timestamp_tz),
    UniqueConstraint("tenant_id", "id", name="uq_payment_void_idempotency__tenant_id_id"),
    UniqueConstraint(
        "tenant_id",
        "payment_id",
        "idempotency_key",
        name="uq_payment_void_idempotency__tenant_payment_key",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "payment_id"],
        ["payments.tenant_id", "payments.id"],
        name="fk_payment_void_idempotency__tenant_payments",
    ),
    CheckConstraint("status in ('processing', 'completed', 'failed')", name="status"),
    CheckConstraint(
        "status <> 'completed' or completed_at is not null",
        name="completed_result",
    ),
)

cashier_corrections = Table(
    "cashier_corrections",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_cashier_corrections__tenants"),
        nullable=False,
    ),
    Column("check_id", uuid_type, nullable=False),
    Column("type", Text, nullable=False),
    Column("target_type", Text, nullable=False),
    Column("target_id", uuid_type, nullable=False),
    Column("reason", Text, nullable=False),
    Column("created_by_user_id", uuid_type, nullable=False),
    Column("created_at", timestamp_tz, nullable=False),
    UniqueConstraint("tenant_id", "id", name="uq_cashier_corrections__tenant_id_id"),
    ForeignKeyConstraint(
        ["tenant_id", "check_id"],
        ["checks.tenant_id", "checks.id"],
        name="fk_cashier_corrections__tenant_checks",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "created_by_user_id"],
        ["users.tenant_id", "users.id"],
        name="fk_cashier_corrections__tenant_users",
    ),
    CheckConstraint("type in ('note', 'item_void', 'payment_void')", name="type"),
    CheckConstraint("reason <> ''", name="reason_required"),
)
Index(
    "ix_cashier_corrections__tenant_check_created",
    cashier_corrections.c.tenant_id,
    cashier_corrections.c.check_id,
    cashier_corrections.c.created_at.desc(),
)

cashier_correction_idempotency = Table(
    "cashier_correction_idempotency",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_cashier_correction_idempotency__tenants"),
        nullable=False,
    ),
    Column("check_id", uuid_type, nullable=False),
    Column("idempotency_key", Text, nullable=False),
    Column("request_hash", Text, nullable=False),
    Column("cashier_correction_id", uuid_type),
    Column("status", Text, nullable=False),
    Column("created_at", timestamp_tz, nullable=False),
    Column("completed_at", timestamp_tz),
    UniqueConstraint("tenant_id", "id", name="uq_cashier_correction_idempotency__tenant_id_id"),
    UniqueConstraint(
        "tenant_id",
        "check_id",
        "idempotency_key",
        name="uq_cashier_correction_idempotency__tenant_check_key",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "check_id"],
        ["checks.tenant_id", "checks.id"],
        name="fk_cashier_correction_idempotency__tenant_checks",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "cashier_correction_id"],
        ["cashier_corrections.tenant_id", "cashier_corrections.id"],
        name="fk_cashier_correction_idempotency__tenant_cashier_corrections",
    ),
    CheckConstraint("status in ('processing', 'completed', 'failed')", name="status"),
    CheckConstraint(
        "status <> 'completed' or (cashier_correction_id is not null and completed_at is not null)",
        name="completed_result",
    ),
)

otp_challenges = Table(
    "otp_challenges",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_otp_challenges__tenants"),
        nullable=False,
    ),
    Column("user_id", uuid_type, nullable=False),
    Column("purpose", Text, nullable=False),
    Column("target_gsm", Text, nullable=False),
    Column("code_hash", Text, nullable=False),
    Column("expires_at", timestamp_tz, nullable=False),
    Column("verified_at", timestamp_tz),
    Column("created_at", timestamp_tz, nullable=False),
    UniqueConstraint("tenant_id", "id", name="uq_otp_challenges__tenant_id_id"),
    ForeignKeyConstraint(
        ["tenant_id", "user_id"],
        ["users.tenant_id", "users.id"],
        name="fk_otp_challenges__tenant_users",
    ),
    CheckConstraint(
        "purpose in ('tenant_admin_first_password', 'cashier_first_password')",
        name="purpose",
    ),
    CheckConstraint("target_gsm <> ''", name="target_gsm_required"),
    CheckConstraint("code_hash <> ''", name="code_hash_required"),
    CheckConstraint(
        "verified_at is null or verified_at <= expires_at",
        name="verified_before_expiry",
    ),
)
Index(
    "ix_otp_challenges__tenant_user_purpose_created",
    otp_challenges.c.tenant_id,
    otp_challenges.c.user_id,
    otp_challenges.c.purpose,
    otp_challenges.c.created_at.desc(),
)

otp_attempts = Table(
    "otp_attempts",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_otp_attempts__tenants"),
        nullable=False,
    ),
    Column("otp_challenge_id", uuid_type, nullable=False),
    Column("attempt_no", Integer, nullable=False),
    Column("result", Text, nullable=False),
    Column("created_at", timestamp_tz, nullable=False),
    UniqueConstraint("tenant_id", "id", name="uq_otp_attempts__tenant_id_id"),
    UniqueConstraint(
        "tenant_id",
        "otp_challenge_id",
        "attempt_no",
        name="uq_otp_attempts__tenant_challenge_attempt_no",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "otp_challenge_id"],
        ["otp_challenges.tenant_id", "otp_challenges.id"],
        name="fk_otp_attempts__tenant_otp_challenges",
    ),
    CheckConstraint("attempt_no between 1 and 5", name="attempt_no_v1_range"),
    CheckConstraint(
        "result in ('success', 'failed', 'locked', 'expired')",
        name="result",
    ),
)
Index(
    "ix_otp_attempts__tenant_challenge_created",
    otp_attempts.c.tenant_id,
    otp_attempts.c.otp_challenge_id,
    otp_attempts.c.created_at.desc(),
)

message_deliveries = Table(
    "message_deliveries",
    metadata,
    id_column(),
    Column(
        "tenant_id",
        uuid_type,
        ForeignKey("tenants.id", name="fk_message_deliveries__tenants"),
        nullable=False,
    ),
    Column("otp_challenge_id", uuid_type, nullable=False),
    Column("delivery_no", Integer, nullable=False),
    Column("provider", Text, nullable=False),
    Column("provider_message_ref", Text),
    Column("status", Text, nullable=False),
    Column("error_summary", Text),
    Column("created_at", timestamp_tz, nullable=False),
    Column("completed_at", timestamp_tz),
    UniqueConstraint("tenant_id", "id", name="uq_message_deliveries__tenant_id_id"),
    UniqueConstraint(
        "tenant_id",
        "otp_challenge_id",
        "delivery_no",
        name="uq_message_deliveries__tenant_challenge_delivery_no",
    ),
    ForeignKeyConstraint(
        ["tenant_id", "otp_challenge_id"],
        ["otp_challenges.tenant_id", "otp_challenges.id"],
        name="fk_message_deliveries__tenant_otp_challenges",
    ),
    CheckConstraint("delivery_no between 1 and 3", name="delivery_no_v1_range"),
    CheckConstraint("provider <> ''", name="provider_required"),
    CheckConstraint("status in ('queued', 'sent', 'failed')", name="status"),
    CheckConstraint(
        "(status = 'queued' and completed_at is null and error_summary is null) or "
        "(status = 'sent' and completed_at is not null) or "
        "(status = 'failed' and completed_at is not null "
        "and error_summary is not null and error_summary <> '')",
        name="status_lifecycle",
    ),
)
Index(
    "ix_message_deliveries__tenant_challenge_created",
    message_deliveries.c.tenant_id,
    message_deliveries.c.otp_challenge_id,
    message_deliveries.c.created_at.desc(),
)

audit_events = Table(
    "audit_events",
    metadata,
    id_column(),
    Column("tenant_id", uuid_type, ForeignKey("tenants.id", name="fk_audit_events__tenants")),
    Column("actor_user_id", uuid_type, ForeignKey("users.id", name="fk_audit_events__users")),
    Column("action", Text, nullable=False),
    Column("target_type", Text, nullable=False),
    Column("target_id", Text, nullable=False),
    Column("reason", Text),
    Column("metadata", JSONB, nullable=False),
    Column("created_at", timestamp_tz, nullable=False),
    UniqueConstraint("tenant_id", "id", name="uq_audit_events__tenant_id_id"),
    CheckConstraint(
        "action in ("
        "'platform_owner.created', 'platform_owner.totp_enrolled', "
        "'tenant.created', 'tenant.provisioning_failed', 'tenant.activated', "
        "'tenant.suspended', 'tenant.gsm_changed', 'tenant.profile_updated', "
        "'tenant.dns_ready_changed', 'starter_template.applied', "
        "'user.created', 'user.disabled', 'password.changed', 'otp.verified', "
        "'venue_layout.changed', 'table.disabled', "
        "'station.changed', 'station.disabled', "
        "'menu_catalog.changed', 'availability.changed', "
        "'table_display.provisioned', 'table_display.revoked', 'order.submitted', "
        "'preparation.status_changed', 'delivery.status_changed', "
        "'payment.recorded', 'payment.voided', 'session.closed', "
        "'cashier.correction_applied')",
        name="action",
    ),
    CheckConstraint("target_type <> ''", name="target_type_required"),
    CheckConstraint("target_id <> ''", name="target_id_required"),
    CheckConstraint("reason is null or reason <> ''", name="reason_not_empty"),
    CheckConstraint("jsonb_typeof(metadata) = 'object'", name="metadata_object"),
)
Index(
    "ix_audit_events__tenant_created",
    audit_events.c.tenant_id,
    audit_events.c.created_at.desc(),
)
Index(
    "ix_audit_events__target",
    audit_events.c.target_type,
    audit_events.c.target_id,
    audit_events.c.created_at.desc(),
)
Index("ix_audit_events__action_created", audit_events.c.action, audit_events.c.created_at.desc())

outbox_messages = Table(
    "outbox_messages",
    metadata,
    id_column(),
    Column("tenant_id", uuid_type, ForeignKey("tenants.id", name="fk_outbox_messages__tenants")),
    Column("effect_type", Text, nullable=False),
    Column("aggregate_type", Text, nullable=False),
    Column("aggregate_id", Text, nullable=False),
    Column("payload_ref", JSONB, nullable=False),
    Column("idempotency_ref", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("next_attempt_at", timestamp_tz),
    Column("claimed_by", Text),
    Column("claimed_at", timestamp_tz),
    Column("claim_expires_at", timestamp_tz),
    Column("created_at", timestamp_tz, nullable=False),
    Column("completed_at", timestamp_tz),
    UniqueConstraint("tenant_id", "id", name="uq_outbox_messages__tenant_id_id"),
    UniqueConstraint(
        "effect_type",
        "idempotency_ref",
        name="uq_outbox_messages__effect_idempotency_ref",
    ),
    CheckConstraint(
        "effect_type in ('sms', 'printer', 'fiscal', 'payment_provider', "
        "'dns', 'notification', 'device')",
        name="effect_type",
    ),
    CheckConstraint("aggregate_type <> ''", name="aggregate_type_required"),
    CheckConstraint("aggregate_id <> ''", name="aggregate_id_required"),
    CheckConstraint("jsonb_typeof(payload_ref) = 'object'", name="payload_ref_object"),
    CheckConstraint("idempotency_ref <> ''", name="idempotency_ref_required"),
    CheckConstraint("status in ('pending', 'claimed', 'completed', 'failed')", name="status"),
    CheckConstraint(
        "(status = 'claimed' and claimed_by is not null and claimed_by <> '' "
        "and claimed_at is not null and claim_expires_at is not null "
        "and completed_at is null) or "
        "(status <> 'claimed' and claimed_by is null "
        "and claimed_at is null and claim_expires_at is null)",
        name="claim_lifecycle",
    ),
    CheckConstraint(
        "claim_expires_at is null or (claimed_at is not null and claim_expires_at > claimed_at)",
        name="claim_expiry_after_claim",
    ),
    CheckConstraint(
        "(status = 'completed' and completed_at is not null) or "
        "(status <> 'completed' and completed_at is null)",
        name="completed_lifecycle",
    ),
)
Index(
    "ix_outbox_messages__status_next_attempt",
    outbox_messages.c.status,
    outbox_messages.c.next_attempt_at,
    outbox_messages.c.claim_expires_at,
    outbox_messages.c.created_at,
    postgresql_where=outbox_messages.c.status.in_(["pending", "failed", "claimed"]),
)
Index(
    "ix_outbox_messages__aggregate",
    outbox_messages.c.aggregate_type,
    outbox_messages.c.aggregate_id,
)

external_effect_attempts = Table(
    "external_effect_attempts",
    metadata,
    id_column(),
    Column(
        "outbox_message_id",
        uuid_type,
        ForeignKey("outbox_messages.id", name="fk_external_effect_attempts__outbox_messages"),
        nullable=False,
    ),
    Column("attempt_no", Integer, nullable=False),
    Column("started_at", timestamp_tz, nullable=False),
    Column("completed_at", timestamp_tz),
    Column("result", Text, nullable=False),
    Column("result_summary", Text),
    UniqueConstraint(
        "outbox_message_id",
        "attempt_no",
        name="uq_external_effect_attempts__message_attempt_no",
    ),
    CheckConstraint("attempt_no > 0", name="attempt_no_positive"),
    CheckConstraint(
        "result in ('success', 'retryable_failure', 'permanent_failure', 'timeout')",
        name="result",
    ),
    CheckConstraint(
        "(result = 'success' and completed_at is not null) or "
        "(result <> 'success' and completed_at is not null "
        "and result_summary is not null and result_summary <> '')",
        name="result_lifecycle",
    ),
)
Index(
    "ix_external_effect_attempts__message_started",
    external_effect_attempts.c.outbox_message_id,
    external_effect_attempts.c.started_at.desc(),
)
