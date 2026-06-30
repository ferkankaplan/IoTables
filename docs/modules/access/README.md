# Access Context

Access owns human identity, authentication, app authorization, staff assignments, and OTP/TOTP security flows.

CustomerOrderingSession is not a human identity and belongs to Ordering.

## Internal Modules

| Module | Purpose |
| --- | --- |
| [identity-access.md](identity-access.md) | Users, credentials, login sessions, first-login setup, platform owner TOTP |
| [staff-access.md](staff-access.md) | Staff profiles, roles, station assignment, hall assignment |
| [otp-messaging.md](otp-messaging.md) | OTP challenge lifecycle, verification, delivery attempts, SMS provider adapter |

## Primary Apps

- PlatformApp
- TenantApp
- CashierApp
- StationStaffApp
- ServiceStaffApp

## Boundary Rule

Access decides who the actor is and which app/scope they may use. Business transitions still belong to their domain modules.
