# PlatformApp Acceptance Criteria
PlatformApp is accepted for the current release when:

- Platform Owner must log in before seeing tenants;
- first Platform Owner bootstrap is explicit and one-time;
- Platform Owner login does not require OTP/TOTP in the current release;
- tenant creation requires name, subdomain, and GSM number;
- tenant starts as `provisioning`;
- tenant becomes `active` only after required setup records commit;
- provisioning failure is visible and recoverable;
- starter template is applied exactly once;
- manual DNS readiness is trackable but not automated;
- PlatformApp cannot mutate tenant runtime orders, payments, sessions, preparation, or delivery as a normal flow.
