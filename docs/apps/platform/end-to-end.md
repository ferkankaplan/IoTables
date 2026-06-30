# PlatformApp End-to-End Role

This document extracts the parts of the shared v1 end-to-end flow where this app participates.

See the full shared flow: [../_shared/master-end-to-end.md](../_shared/master-end-to-end.md).

### 1. Platform Owner Creates Tenant
1. Platform Owner logs into PlatformApp.
2. Platform Owner creates a tenant with required identity:
   - tenant name,
   - tenant subdomain,
   - tenant GSM number.
3. PlatformApp submits the create-tenant command to Provisioning.
4. Provisioning registers the tenant in `provisioning` state.
5. Provisioning creates the first tenant admin through Access:
   - username: tenant subdomain,
   - temporary password: `admin`,
   - first password setup requires OTP SMS to tenant GSM.
6. Provisioning applies the selected sector starter template exactly once.
7. Governance records starter template completion.
8. Provisioning moves tenant to `active` after required setup records commit.
9. Platform Owner marks manual DNS readiness when DNS is configured outside the app.

Acceptance criteria:

- Tenant name and subdomain cannot be changed after creation.
- Tenant GSM is editable but audited.
- Starter data does not rerun after restart, deployment, migration, release upgrade, or tenant edit.
- Failed provisioning leaves a recoverable `provisioning_failed` state instead of partial silent success.
