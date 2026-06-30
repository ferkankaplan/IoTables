# PlatformApp End-to-End Role

This document extracts the parts of the shared v1 end-to-end flow where this app participates.

See the full shared flow: [../_shared/master-end-to-end.md](../_shared/master-end-to-end.md).

### 1. Platform Owner Creates Tenant
1. Platform Owner logs into PlatformApp.
2. Platform Owner creates a tenant with required identity:
   - tenant name,
   - tenant subdomain,
   - tenant GSM number.
3. PlatformApp creates the tenant in `provisioning` state.
4. PlatformApp creates the first tenant admin:
   - username: tenant subdomain,
   - temporary password: `admin`,
   - first password setup requires OTP SMS to tenant GSM.
5. PlatformApp applies the selected sector starter template exactly once.
6. PlatformApp records starter template completion.
7. PlatformApp moves tenant to `active` after required setup records commit.
8. Platform Owner marks manual DNS readiness when DNS is configured outside the app.

Acceptance criteria:

- Tenant name and subdomain cannot be changed after creation.
- Tenant GSM is editable but audited.
- Starter data does not rerun after restart, deployment, migration, release upgrade, or tenant edit.
- Failed provisioning leaves a recoverable `provisioning_failed` state instead of partial silent success.
