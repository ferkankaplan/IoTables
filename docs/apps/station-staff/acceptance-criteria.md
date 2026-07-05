# StationStaffApp Acceptance Criteria
StationStaffApp is accepted for the current release when:

- station staff must log in and change bootstrap password on first login;
- OTP is not required for station staff in the current release;
- one authorized station opens directly;
- multiple authorized stations require station selection;
- unauthorized stations are not visible or mutable;
- queue groups by preparation status and sorts oldest first;
- staff can move `pending -> preparing -> ready`;
- staff can move `pending/preparing -> cannot_prepare` with reason;
- duplicate or concurrent state changes are safe;
- customer preparation notes are visible when relevant;
- cashier-only notes and payment data are not visible.
