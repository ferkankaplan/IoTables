# ServiceStaffApp Acceptance Criteria
ServiceStaffApp is accepted for the current release when:

- service staff must log in and change bootstrap password on first login;
- OTP is not required for service staff in the current release;
- service delivery tracking is checked before showing the queue;
- disabled service tracking hides delivery controls;
- service staff sees only authorized halls;
- queue groups by table and sorts oldest ready item first;
- staff can mark `ready -> delivered`;
- staff may mark `ready -> picked_up -> delivered`;
- bulk delivery is allowed only for selected same-table items;
- single-item delivery transitions are duplicate-safe, bulk delivery is idempotent, and delivery transitions are audited;
- CustomerApp shows `Teslim edildi` only after delivered when service tracking is enabled.
