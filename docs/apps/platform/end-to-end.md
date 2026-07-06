# PlatformApp End-to-End Role

This document extracts the parts of the shared current release end-to-end flow where this app participates.

See the full shared flow: [../_shared/canonical-end-to-end.md](../_shared/canonical-end-to-end.md).

### 1. Platform Owner Creates Tenant
1. Platform Owner logs into PlatformApp.
2. Platform Owner creates a tenant with required identity:
   - tenant name,
   - tenant subdomain,
   - tenant GSM number.
3. PlatformApp verifies tenant-creation OTP sent to the platform-owned tenant identity GSM.
4. PlatformApp submits the OTP-proven create-tenant command to Provisioning.
5. Provisioning registers the tenant in `provisioning` state.
6. Provisioning creates the first tenant admin through Access:
   - username: tenant subdomain,
   - temporary password: `admin`,
   - first password setup required before normal app access.
7. Provisioning applies the selected sector starter template exactly once.
8. Governance records starter template completion.
9. Provisioning moves tenant to `active` after required setup records commit.
10. Tenant host availability relies on the environment wildcard DNS namespace configured during deployment.

Acceptance criteria:

- Tenant name and subdomain cannot be changed after creation.
- Tenant GSM is unique, editable only by PlatformApp, and audited.
- Starter data does not rerun after restart, deployment, migration, release upgrade, or tenant edit.
- Failed provisioning leaves a recoverable `provisioning_failed` state instead of partial silent success.
- PlatformApp does not track tenant-level DNS state; wildcard DNS failures are deployment/ops faults.
