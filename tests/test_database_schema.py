from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex

import iotables.database.schema  # noqa: F401
from iotables.database.base import metadata

EXPECTED_FOUNDATION_TABLES = {
    "tenants",
    "tenant_operational_settings",
    "tenant_health",
    "tenant_lifecycle_events",
    "starter_template_applications",
    "tenant_provisioning_idempotency",
    "users",
    "credentials",
    "login_sessions",
    "platform_role_assignments",
    "totp_factors",
    "staff_profiles",
    "staff_role_assignments",
    "halls",
    "venue_tables",
    "stations",
    "menu_categories",
    "product_services",
    "product_variants",
    "availability_overrides",
    "modifier_groups",
    "modifier_options",
    "staff_station_assignments",
    "staff_hall_assignments",
    "table_display_firmware_packages",
    "table_display_credentials",
    "table_access_tokens",
    "table_sessions",
    "checks",
    "customer_ordering_sessions",
    "customer_carts",
    "customer_cart_items",
    "orders",
    "order_items",
    "preparation_items",
    "preparation_transitions",
    "delivery_states",
    "delivery_transitions",
    "delivery_bulk_idempotency",
    "order_submit_idempotency",
    "price_adjustments",
    "session_closures",
    "payments",
    "payment_idempotency",
    "payment_void_idempotency",
    "cashier_corrections",
    "cashier_correction_idempotency",
    "otp_challenges",
    "otp_attempts",
    "message_deliveries",
    "audit_events",
    "outbox_messages",
    "external_effect_attempts",
}


def constraint_names(table_name: str, constraint_type: type[object]) -> set[str]:
    table = metadata.tables[table_name]
    return {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, constraint_type)
    }


def compiled_index_sql(table_name: str, index_name: str) -> str:
    table = metadata.tables[table_name]
    index = next(index for index in table.indexes if index.name == index_name)
    return str(CreateIndex(index).compile(dialect=postgresql.dialect()))


def check_constraint_sql(table_name: str, constraint_name: str) -> str:
    table = metadata.tables[table_name]
    constraint = next(
        constraint
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint) and constraint.name == constraint_name
    )
    return str(constraint.sqltext)


def test_platform_access_foundation_tables_are_registered() -> None:
    assert set(metadata.tables) >= EXPECTED_FOUNDATION_TABLES


def test_tenant_registry_enforces_identity_and_lifecycle_guards() -> None:
    tenant_checks = constraint_names("tenants", CheckConstraint)

    assert {
        "ck_tenants__sector",
        "ck_tenants__status",
        "ck_tenants__capacity_positive",
        "ck_tenants__provisioning_error_status",
    } <= tenant_checks

    subdomain_index = compiled_index_sql("tenants", "uq_tenants__subdomain_lower")
    gsm_index = compiled_index_sql("tenants", "uq_tenants__gsm_number")

    assert "UNIQUE INDEX uq_tenants__subdomain_lower" in subdomain_index
    assert "lower(subdomain)" in subdomain_index
    assert "UNIQUE INDEX uq_tenants__gsm_number" in gsm_index
    assert "gsm_number" in gsm_index


def test_users_have_separate_platform_and_tenant_username_uniqueness() -> None:
    tenant_username_index = compiled_index_sql("users", "uq_users__tenant_username_lower")
    platform_username_index = compiled_index_sql("users", "uq_users__platform_username_lower")

    assert "UNIQUE INDEX uq_users__tenant_username_lower" in tenant_username_index
    assert "lower(username)" in tenant_username_index
    assert "tenant_id IS NOT NULL" in tenant_username_index

    assert "UNIQUE INDEX uq_users__platform_username_lower" in platform_username_index
    assert "tenant_id IS NULL" in platform_username_index


def test_staff_access_uses_composite_tenant_foreign_keys() -> None:
    staff_profile_fks = constraint_names("staff_profiles", ForeignKeyConstraint)
    staff_role_fks = constraint_names("staff_role_assignments", ForeignKeyConstraint)

    assert "fk_staff_profiles__tenant_users" in staff_profile_fks
    assert "fk_staff_role_assignments__tenant_users" in staff_role_fks


def test_one_time_starter_template_guard_is_durable() -> None:
    starter_uniques = constraint_names("starter_template_applications", UniqueConstraint)

    assert {
        "uq_starter_template_applications__tenant_id_id",
        "uq_starter_template_applications__tenant_template_version",
    } <= starter_uniques


def test_tenant_provisioning_idempotency_preserves_replay_results() -> None:
    idempotency_uniques = constraint_names("tenant_provisioning_idempotency", UniqueConstraint)
    idempotency_checks = constraint_names("tenant_provisioning_idempotency", CheckConstraint)
    idempotency_fks = constraint_names("tenant_provisioning_idempotency", ForeignKeyConstraint)

    assert "uq_tenant_provisioning_idempotency__actor_key" in idempotency_uniques
    assert {
        "ck_tenant_provisioning_idempotency__idempotency_key_required",
        "ck_tenant_provisioning_idempotency__request_hash_required",
        "ck_tenant_provisioning_idempotency__response_payload_object",
        "ck_tenant_provisioning_idempotency__status",
        "ck_tenant_provisioning_idempotency__completed_result",
    } <= idempotency_checks
    assert {
        "fk_tenant_provisioning_idempotency__users",
        "fk_tenant_provisioning_idempotency__tenants",
    } <= idempotency_fks


def test_active_role_grants_are_idempotency_safe() -> None:
    active_owner_index = compiled_index_sql(
        "platform_role_assignments",
        "uq_platform_role_assignments__active_platform_owner",
    )
    active_staff_role_index = compiled_index_sql(
        "staff_role_assignments",
        "uq_staff_role_assignments__tenant_user_role_active",
    )

    assert "role = 'platform_owner'" in active_owner_index
    assert "status = 'active'" in active_owner_index
    assert "UNIQUE INDEX uq_staff_role_assignments__tenant_user_role_active" in (
        active_staff_role_index
    )
    assert "status = 'active'" in active_staff_role_index


def test_tenant_setup_tables_enforce_names_and_ordering() -> None:
    hall_uniques = constraint_names("halls", UniqueConstraint)
    table_uniques = constraint_names("venue_tables", UniqueConstraint)
    hall_checks = constraint_names("halls", CheckConstraint)
    table_checks = constraint_names("venue_tables", CheckConstraint)

    assert {
        "uq_halls__tenant_display_order",
        "uq_halls__tenant_table_number_base",
    } <= hall_uniques
    assert {
        "uq_venue_tables__tenant_hall_display_order",
        "uq_venue_tables__tenant_table_number",
    } <= table_uniques
    assert "uq_stations__tenant_display_order" in constraint_names("stations", UniqueConstraint)
    assert "uq_menu_categories__tenant_display_order" in constraint_names(
        "menu_categories",
        UniqueConstraint,
    )
    assert "ck_halls__table_number_base_range" in hall_checks
    assert {
        "ck_venue_tables__mode",
        "ck_venue_tables__boundary_slots_virtual",
    } <= table_checks

    assert "lower(name)" in compiled_index_sql("halls", "uq_halls__tenant_name_lower")
    assert "lower(name)" in compiled_index_sql(
        "venue_tables",
        "uq_venue_tables__tenant_hall_name_lower",
    )
    assert "lower(name)" in compiled_index_sql("stations", "uq_stations__tenant_name_lower")
    assert "lower(name)" in compiled_index_sql(
        "menu_categories",
        "uq_menu_categories__tenant_name_lower",
    )


def test_tenant_setup_tables_have_composite_tenant_foreign_keys() -> None:
    assert "fk_venue_tables__tenant_halls" in constraint_names(
        "venue_tables",
        ForeignKeyConstraint,
    )
    assert "fk_product_services__tenant_menu_categories" in constraint_names(
        "product_services",
        ForeignKeyConstraint,
    )
    assert "fk_product_services__tenant_stations" in constraint_names(
        "product_services",
        ForeignKeyConstraint,
    )
    assert "fk_product_variants__tenant_product_services" in constraint_names(
        "product_variants",
        ForeignKeyConstraint,
    )
    assert "fk_availability_overrides__tenant_product_variants" in constraint_names(
        "availability_overrides",
        ForeignKeyConstraint,
    )


def test_menu_catalog_money_and_modifier_guards_are_database_enforced() -> None:
    variant_checks = constraint_names("product_variants", CheckConstraint)
    override_checks = constraint_names("availability_overrides", CheckConstraint)
    group_checks = constraint_names("modifier_groups", CheckConstraint)
    option_checks = constraint_names("modifier_options", CheckConstraint)

    assert "ck_product_variants__price_minor_non_negative" in variant_checks
    assert "ck_availability_overrides__state" in override_checks
    assert "ck_availability_overrides__valid_time_window" in override_checks
    assert "ck_modifier_groups__selection_bounds" in group_checks
    assert "ck_modifier_options__price_delta_non_negative" in option_checks

    assert str(metadata.tables["product_variants"].c.currency_code.server_default.arg) == "TRY"
    assert str(metadata.tables["modifier_options"].c.currency_code.server_default.arg) == "TRY"


def test_product_and_modifier_uniqueness_matches_tenant_scope() -> None:
    assert "lower(name)" in compiled_index_sql(
        "product_services",
        "uq_product_services__tenant_category_name_lower",
    )
    assert "lower(name)" in compiled_index_sql(
        "product_variants",
        "uq_product_variants__tenant_product_name_lower",
    )
    assert "is_default IS true" in compiled_index_sql(
        "product_variants",
        "uq_product_variants__tenant_product_default",
    )
    assert "lower(name)" in compiled_index_sql(
        "modifier_groups",
        "uq_modifier_groups__tenant_product_name_lower",
    )
    assert "lower(name)" in compiled_index_sql(
        "modifier_options",
        "uq_modifier_options__tenant_group_name_lower",
    )


def test_staff_station_and_hall_assignments_are_tenant_scoped_and_idempotent() -> None:
    assert "fk_staff_station_assignments__tenant_users" in constraint_names(
        "staff_station_assignments",
        ForeignKeyConstraint,
    )
    assert "fk_staff_station_assignments__tenant_stations" in constraint_names(
        "staff_station_assignments",
        ForeignKeyConstraint,
    )
    assert "fk_staff_hall_assignments__tenant_users" in constraint_names(
        "staff_hall_assignments",
        ForeignKeyConstraint,
    )
    assert "fk_staff_hall_assignments__tenant_halls" in constraint_names(
        "staff_hall_assignments",
        ForeignKeyConstraint,
    )

    station_assignment_index = compiled_index_sql(
        "staff_station_assignments",
        "uq_staff_station_assignments__tenant_user_station_active",
    )
    hall_assignment_index = compiled_index_sql(
        "staff_hall_assignments",
        "uq_staff_hall_assignments__tenant_user_hall_active",
    )

    assert "UNIQUE INDEX uq_staff_station_assignments__tenant_user_station_active" in (
        station_assignment_index
    )
    assert "status = 'active'" in station_assignment_index
    assert "UNIQUE INDEX uq_staff_hall_assignments__tenant_user_hall_active" in (
        hall_assignment_index
    )
    assert "status = 'active'" in hall_assignment_index


def test_table_display_firmware_packages_are_one_time_tenant_scoped_secrets() -> None:
    package_uniques = constraint_names("table_display_firmware_packages", UniqueConstraint)
    package_fks = constraint_names("table_display_firmware_packages", ForeignKeyConstraint)
    package_checks = constraint_names("table_display_firmware_packages", CheckConstraint)
    package_lookup_index = compiled_index_sql(
        "table_display_firmware_packages",
        "ix_table_display_firmware_packages__tenant_table_created",
    )

    assert "uq_table_display_firmware_packages__download_token_hash" in package_uniques
    assert "fk_table_display_firmware_packages__tenant_venue_tables" in package_fks
    assert "fk_table_display_firmware_packages__tenant_credentials" in package_fks
    assert "fk_table_display_firmware_packages__tenant_users" in package_fks
    assert "ck_table_display_firmware_packages__downloaded_before_expiry" in package_checks
    assert "CREATE INDEX ix_table_display_firmware_packages__tenant_table_created" in (
        package_lookup_index
    )


def test_table_display_credentials_have_single_active_binding_per_table() -> None:
    credential_uniques = constraint_names("table_display_credentials", UniqueConstraint)
    credential_fks = constraint_names("table_display_credentials", ForeignKeyConstraint)
    credential_checks = constraint_names("table_display_credentials", CheckConstraint)
    active_credential_index = compiled_index_sql(
        "table_display_credentials",
        "uq_table_display_credentials__tenant_table_active",
    )

    assert "uq_table_display_credentials__credential_hash" in credential_uniques
    assert "fk_table_display_credentials__tenant_venue_tables" in credential_fks
    assert {
        "ck_table_display_credentials__status",
        "ck_table_display_credentials__revocation_lifecycle",
    } <= credential_checks
    assert "UNIQUE INDEX uq_table_display_credentials__tenant_table_active" in (
        active_credential_index
    )
    assert "status = 'active'" in active_credential_index


def test_table_access_tokens_are_unique_atomic_presence_guards() -> None:
    token_uniques = constraint_names("table_access_tokens", UniqueConstraint)
    token_fks = constraint_names("table_access_tokens", ForeignKeyConstraint)
    token_checks = constraint_names("table_access_tokens", CheckConstraint)
    token_lookup_index = compiled_index_sql(
        "table_access_tokens",
        "ix_table_access_tokens__tenant_table_created",
    )

    assert "uq_table_access_tokens__token_hash" in token_uniques
    assert "fk_table_access_tokens__tenant_venue_tables" in token_fks
    assert "ck_table_access_tokens__consumed_before_expiry" in token_checks
    assert "CREATE INDEX ix_table_access_tokens__tenant_table_created" in token_lookup_index
    assert "now()" not in token_lookup_index.lower()


def test_table_sessions_and_checks_enforce_single_open_operational_session() -> None:
    session_checks = constraint_names("table_sessions", CheckConstraint)
    check_checks = constraint_names("checks", CheckConstraint)
    session_fks = constraint_names("table_sessions", ForeignKeyConstraint)
    check_fks = constraint_names("checks", ForeignKeyConstraint)
    open_session_index = compiled_index_sql(
        "table_sessions",
        "uq_table_sessions__tenant_table_open",
    )

    assert "fk_table_sessions__tenant_venue_tables" in session_fks
    assert "fk_checks__tenant_table_sessions" in check_fks
    assert "uq_checks__table_session_id" in constraint_names("checks", UniqueConstraint)
    assert {"ck_table_sessions__status", "ck_table_sessions__closed_at_lifecycle"} <= (
        session_checks
    )
    assert {"ck_checks__status", "ck_checks__closed_at_lifecycle"} <= check_checks
    assert "UNIQUE INDEX uq_table_sessions__tenant_table_open" in open_session_index
    assert "status = 'open'" in open_session_index


def test_customer_ordering_sessions_carts_and_items_are_replay_safe() -> None:
    session_uniques = constraint_names("customer_ordering_sessions", UniqueConstraint)
    session_checks = constraint_names("customer_ordering_sessions", CheckConstraint)
    cart_checks = constraint_names("customer_carts", CheckConstraint)
    item_uniques = constraint_names("customer_cart_items", UniqueConstraint)
    active_cart_index = compiled_index_sql(
        "customer_carts",
        "uq_customer_carts__tenant_customer_session_active",
    )

    assert "uq_customer_ordering_sessions__cookie_token_hash" in session_uniques
    assert "ck_customer_ordering_sessions__presence_within_session" in session_checks
    assert "ck_customer_carts__status" in cart_checks
    assert "UNIQUE INDEX uq_customer_carts__tenant_customer_session_active" in active_cart_index
    assert "status = 'active'" in active_cart_index
    assert "uq_customer_cart_items__tenant_cart_client_item" in item_uniques
    assert "ck_customer_cart_items__quantity_positive" in constraint_names(
        "customer_cart_items",
        CheckConstraint,
    )


def test_orders_and_order_submit_idempotency_preserve_customer_and_table_links() -> None:
    order_fks = constraint_names("orders", ForeignKeyConstraint)
    item_fks = constraint_names("order_items", ForeignKeyConstraint)
    submit_uniques = constraint_names("order_submit_idempotency", UniqueConstraint)
    submit_checks = constraint_names("order_submit_idempotency", CheckConstraint)

    assert "fk_orders__tenant_customer_ordering_sessions" in order_fks
    assert "fk_orders__tenant_table_sessions" in order_fks
    assert "fk_order_items__tenant_orders" in item_fks
    assert "fk_order_items__tenant_product_variants" in item_fks
    assert {
        "ck_orders__status",
        "ck_orders__order_channel",
    } <= constraint_names("orders", CheckConstraint)
    assert {
        "ck_order_items__quantity_positive",
        "ck_order_items__void_fields_complete",
    } <= constraint_names("order_items", CheckConstraint)
    assert "uq_order_items__tenant_id_id_station_id" in constraint_names(
        "order_items",
        UniqueConstraint,
    )
    assert "uq_order_submit_idempotency__tenant_session_key" in submit_uniques
    assert {
        "ck_order_submit_idempotency__status",
        "ck_order_submit_idempotency__completed_result",
    } <= submit_checks


def test_preparation_items_are_one_per_routed_order_item_and_station_consistent() -> None:
    preparation_fks = constraint_names("preparation_items", ForeignKeyConstraint)
    preparation_uniques = constraint_names("preparation_items", UniqueConstraint)
    preparation_checks = constraint_names("preparation_items", CheckConstraint)
    station_queue_index = compiled_index_sql(
        "preparation_items",
        "ix_preparation_items__tenant_station_status_updated",
    )

    assert "uq_preparation_items__tenant_order_item" in preparation_uniques
    assert "fk_preparation_items__tenant_order_items_station" in preparation_fks
    assert "fk_preparation_items__tenant_stations" in preparation_fks
    assert "fk_preparation_items__tenant_updated_users" in preparation_fks
    assert {
        "ck_preparation_items__status",
        "ck_preparation_items__cannot_prepare_reason_lifecycle",
        "ck_preparation_items__non_pending_actor_required",
    } <= preparation_checks
    assert "station_id" in station_queue_index
    assert "status" in station_queue_index


def test_preparation_transitions_allow_only_documented_state_flow() -> None:
    transition_fks = constraint_names("preparation_transitions", ForeignKeyConstraint)
    transition_checks = constraint_names("preparation_transitions", CheckConstraint)

    assert "fk_preparation_transitions__tenant_preparation_items" in transition_fks
    assert "fk_preparation_transitions__tenant_users" in transition_fks
    assert {
        "ck_preparation_transitions__from_status",
        "ck_preparation_transitions__to_status",
        "ck_preparation_transitions__valid_transition",
        "ck_preparation_transitions__cannot_prepare_reason_lifecycle",
        "ck_preparation_transitions__actor_required_after_initial",
    } <= transition_checks


def test_delivery_states_do_not_store_ready_and_are_one_per_order_item() -> None:
    delivery_fks = constraint_names("delivery_states", ForeignKeyConstraint)
    delivery_uniques = constraint_names("delivery_states", UniqueConstraint)
    delivery_checks = constraint_names("delivery_states", CheckConstraint)
    status_sql = check_constraint_sql("delivery_states", "ck_delivery_states__status")

    assert "uq_delivery_states__tenant_order_item" in delivery_uniques
    assert "uq_delivery_states__tenant_id_id_order_item_id" in delivery_uniques
    assert "fk_delivery_states__tenant_order_items" in delivery_fks
    assert "fk_delivery_states__tenant_updated_users" in delivery_fks
    assert "ck_delivery_states__status" in delivery_checks
    assert "picked_up" in status_sql
    assert "delivered" in status_sql
    assert "ready" not in status_sql


def test_delivery_transitions_and_bulk_idempotency_are_tenant_scoped() -> None:
    transition_fks = constraint_names("delivery_transitions", ForeignKeyConstraint)
    transition_checks = constraint_names("delivery_transitions", CheckConstraint)
    bulk_fks = constraint_names("delivery_bulk_idempotency", ForeignKeyConstraint)
    bulk_uniques = constraint_names("delivery_bulk_idempotency", UniqueConstraint)
    bulk_checks = constraint_names("delivery_bulk_idempotency", CheckConstraint)

    assert "fk_delivery_transitions__tenant_delivery_states" in transition_fks
    assert "fk_delivery_transitions__tenant_users" in transition_fks
    assert {
        "ck_delivery_transitions__from_status",
        "ck_delivery_transitions__to_status",
        "ck_delivery_transitions__valid_transition",
    } <= transition_checks
    assert "uq_delivery_bulk_idempotency__tenant_actor_key" in bulk_uniques
    assert "fk_delivery_bulk_idempotency__tenant_users" in bulk_fks
    assert "fk_delivery_bulk_idempotency__tenant_venue_tables" in bulk_fks
    assert {
        "ck_delivery_bulk_idempotency__status",
        "ck_delivery_bulk_idempotency__delivered_order_item_ids_array",
        "ck_delivery_bulk_idempotency__completed_result",
    } <= bulk_checks


def test_payments_and_corrections_have_financial_lifecycle_guards() -> None:
    payment_checks = constraint_names("payments", CheckConstraint)
    payment_idempotency_uniques = constraint_names("payment_idempotency", UniqueConstraint)
    payment_void_uniques = constraint_names("payment_void_idempotency", UniqueConstraint)
    correction_checks = constraint_names("cashier_corrections", CheckConstraint)
    correction_idempotency_uniques = constraint_names(
        "cashier_correction_idempotency",
        UniqueConstraint,
    )

    assert {
        "ck_payments__amount_positive",
        "ck_payments__method",
        "ck_payments__status",
        "ck_payments__void_lifecycle",
    } <= payment_checks
    assert "uq_payment_idempotency__tenant_check_key" in payment_idempotency_uniques
    assert "uq_payment_void_idempotency__tenant_payment_key" in payment_void_uniques
    assert {
        "ck_cashier_corrections__type",
        "ck_cashier_corrections__reason_required",
    } <= correction_checks
    assert "uq_cashier_correction_idempotency__tenant_check_key" in (correction_idempotency_uniques)


def test_settlement_support_records_are_tenant_scoped() -> None:
    assert "fk_price_adjustments__tenant_checks" in constraint_names(
        "price_adjustments",
        ForeignKeyConstraint,
    )
    assert "fk_price_adjustments__tenant_order_items" in constraint_names(
        "price_adjustments",
        ForeignKeyConstraint,
    )
    assert "fk_session_closures__tenant_table_sessions" in constraint_names(
        "session_closures",
        ForeignKeyConstraint,
    )
    assert "fk_session_closures__tenant_checks" in constraint_names(
        "session_closures",
        ForeignKeyConstraint,
    )
    assert "uq_session_closures__table_session_id" in constraint_names(
        "session_closures",
        UniqueConstraint,
    )
    assert "ck_price_adjustments__correction_reason" in constraint_names(
        "price_adjustments",
        CheckConstraint,
    )


def test_otp_challenges_are_tenant_scoped_and_non_recoverable() -> None:
    challenge_fks = constraint_names("otp_challenges", ForeignKeyConstraint)
    challenge_checks = constraint_names("otp_challenges", CheckConstraint)
    challenge_index = compiled_index_sql(
        "otp_challenges",
        "ix_otp_challenges__tenant_user_purpose_created",
    )

    assert "fk_otp_challenges__tenant_users" in challenge_fks
    assert "fk_otp_challenges__users" in challenge_fks
    assert {
        "ck_otp_challenges__purpose",
        "ck_otp_challenges__tenant_scope",
        "ck_otp_challenges__target_gsm_required",
        "ck_otp_challenges__code_hash_required",
        "ck_otp_challenges__verified_before_expiry",
    } <= challenge_checks
    assert "tenant_id" in challenge_index
    assert "user_id" in challenge_index
    assert "purpose" in challenge_index


def test_otp_attempts_preserve_monotonic_v1_attempt_limit() -> None:
    attempt_fks = constraint_names("otp_attempts", ForeignKeyConstraint)
    attempt_uniques = constraint_names("otp_attempts", UniqueConstraint)
    attempt_checks = constraint_names("otp_attempts", CheckConstraint)
    attempt_range_sql = check_constraint_sql("otp_attempts", "ck_otp_attempts__attempt_no_v1_range")

    assert "fk_otp_attempts__tenant_otp_challenges" in attempt_fks
    assert "fk_otp_attempts__otp_challenges" in attempt_fks
    assert "uq_otp_attempts__tenant_challenge_attempt_no" in attempt_uniques
    assert {
        "ck_otp_attempts__attempt_no_v1_range",
        "ck_otp_attempts__result",
    } <= attempt_checks
    assert "between 1 and 5" in attempt_range_sql


def test_message_deliveries_preserve_send_limit_and_redacted_failure_state() -> None:
    delivery_fks = constraint_names("message_deliveries", ForeignKeyConstraint)
    delivery_uniques = constraint_names("message_deliveries", UniqueConstraint)
    delivery_checks = constraint_names("message_deliveries", CheckConstraint)
    delivery_range_sql = check_constraint_sql(
        "message_deliveries",
        "ck_message_deliveries__delivery_no_v1_range",
    )

    assert "fk_message_deliveries__tenant_otp_challenges" in delivery_fks
    assert "fk_message_deliveries__otp_challenges" in delivery_fks
    assert "uq_message_deliveries__tenant_challenge_delivery_no" in delivery_uniques
    assert {
        "ck_message_deliveries__delivery_no_v1_range",
        "ck_message_deliveries__provider_required",
        "ck_message_deliveries__status",
        "ck_message_deliveries__status_lifecycle",
    } <= delivery_checks
    assert "between 1 and 3" in delivery_range_sql


def test_audit_events_are_append_only_structured_records() -> None:
    audit_checks = constraint_names("audit_events", CheckConstraint)
    audit_fks = constraint_names("audit_events", ForeignKeyConstraint)
    tenant_index = compiled_index_sql("audit_events", "ix_audit_events__tenant_created")
    target_index = compiled_index_sql("audit_events", "ix_audit_events__target")
    action_sql = check_constraint_sql("audit_events", "ck_audit_events__action")

    assert "fk_audit_events__tenants" in audit_fks
    assert "fk_audit_events__users" in audit_fks
    assert {
        "ck_audit_events__action",
        "ck_audit_events__target_type_required",
        "ck_audit_events__target_id_required",
        "ck_audit_events__reason_not_empty",
        "ck_audit_events__metadata_object",
    } <= audit_checks
    assert "payment.voided" in action_sql
    assert "cashier.correction_applied" in action_sql
    assert "tenant.profile_updated" in action_sql
    assert "venue_layout.changed" in action_sql
    assert "table.disabled" in action_sql
    assert "station.changed" in action_sql
    assert "station.disabled" in action_sql
    assert "menu_catalog.changed" in action_sql
    assert "availability.changed" in action_sql
    assert "CREATE INDEX ix_audit_events__tenant_created" in tenant_index
    assert "CREATE INDEX ix_audit_events__target" in target_index


def test_outbox_messages_have_idempotency_and_worker_claim_guards() -> None:
    outbox_uniques = constraint_names("outbox_messages", UniqueConstraint)
    outbox_checks = constraint_names("outbox_messages", CheckConstraint)
    claim_index = compiled_index_sql("outbox_messages", "ix_outbox_messages__status_next_attempt")
    aggregate_index = compiled_index_sql("outbox_messages", "ix_outbox_messages__aggregate")

    assert "uq_outbox_messages__effect_idempotency_ref" in outbox_uniques
    assert {
        "ck_outbox_messages__effect_type",
        "ck_outbox_messages__aggregate_type_required",
        "ck_outbox_messages__aggregate_id_required",
        "ck_outbox_messages__payload_ref_object",
        "ck_outbox_messages__idempotency_ref_required",
        "ck_outbox_messages__status",
        "ck_outbox_messages__claim_lifecycle",
        "ck_outbox_messages__claim_expiry_after_claim",
        "ck_outbox_messages__completed_lifecycle",
    } <= outbox_checks
    assert "WHERE status IN ('pending', 'failed', 'claimed')" in claim_index
    assert "CREATE INDEX ix_outbox_messages__aggregate" in aggregate_index


def test_external_effect_attempts_preserve_append_only_provider_attempts() -> None:
    attempt_uniques = constraint_names("external_effect_attempts", UniqueConstraint)
    attempt_checks = constraint_names("external_effect_attempts", CheckConstraint)
    attempt_fks = constraint_names("external_effect_attempts", ForeignKeyConstraint)
    attempt_index = compiled_index_sql(
        "external_effect_attempts",
        "ix_external_effect_attempts__message_started",
    )

    assert "fk_external_effect_attempts__outbox_messages" in attempt_fks
    assert "uq_external_effect_attempts__message_attempt_no" in attempt_uniques
    assert {
        "ck_external_effect_attempts__attempt_no_positive",
        "ck_external_effect_attempts__result",
        "ck_external_effect_attempts__result_lifecycle",
    } <= attempt_checks
    assert "CREATE INDEX ix_external_effect_attempts__message_started" in attempt_index
