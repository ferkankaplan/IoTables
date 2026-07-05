# UI Copy Style

This document defines shared current release UI copy rules for IoTables apps.

Source context:

- [accessibility-responsive.md](accessibility-responsive.md)
- [component-model.md](component-model.md)
- [wireframe-rules.md](wireframe-rules.md)
- [../../api/errors.md](../../api/errors.md)
- [../../security/threat-model.md](../../security/threat-model.md)
- [../platform/ui-states.md](../platform/ui-states.md)
- [../customer/ui-states.md](../customer/ui-states.md)
- [../tenant/ui-states.md](../tenant/ui-states.md)
- [../cashier/ui-states.md](../cashier/ui-states.md)
- [../station-staff/ui-states.md](../station-staff/ui-states.md)
- [../service-staff/ui-states.md](../service-staff/ui-states.md)

## Voice

| App Group | Voice |
| --- | --- |
| CustomerApp | Clear, calm, short, non-technical, service-oriented. |
| StationStaffApp / ServiceStaffApp | Direct, fast, action-oriented, operational. |
| CashierApp | Precise, accountable, state-aware. |
| TenantApp | Administrative, clear, reversible where possible. |
| PlatformApp | Sparse, diagnostic, platform-safe. |

Use Turkish product copy by default for UI text. Keep internal documentation in English unless a user-facing string is being specified.

## Universal Rules

- Use the user's visible object names: table, hall, station, product, order, payment, check/adisyon.
- Do not expose implementation terms to end users: token, hash, idempotency, credential, row lock, transaction, provider payload, cookie, session internals, database, stack trace.
- Match copy to the component's context: workspace labels stay short, panel titles identify the selected object, and destructive/dialog copy states the consequence.
- Use the same concept name across apps unless the app's user role needs a clearer label.
- Prefer short action verbs.
- Prefer concrete next steps over generic failure messages.
- Never imply an action succeeded until the backend accepted it.
- Do not blame the user for stale, expired, unavailable, or security-blocked states.
- Do not expose tenant, user, or account existence in security-sensitive failures.
- Destructive or audit-affecting actions must say what will happen and why a reason is required.

## CustomerApp Copy Rules

CustomerApp copy must protect trust without exposing security internals.

| Internal Condition | Customer Copy Pattern |
| --- | --- |
| QR expired | `Masanızdaki güncel QR kodu tekrar okutun.` |
| QR already consumed | `QR kod yenilendi. Masanızdaki yeni QR kodu okutun.` |
| Wrong-table QR | `Lütfen kendi masanızdaki QR kodu okutun.` |
| Fresh presence expired before submit | `Sipariş vermek için masanızdaki güncel QR kodu tekrar okutun. Sepetiniz korunur.` |
| Cart item unavailable | `Bu ürün şu anda sipariş edilemiyor.` |
| Variant/modifier invalid | `Seçiminizi gözden geçirin.` |
| Order accepted | `Siparişiniz alındı.` |
| Duplicate submit replay | `Siparişiniz zaten alındı.` |
| Table orders need fresh presence | `Masa siparişlerini görmek için güncel QR kodu okutun.` |
| Bill summary read-only | `Hesap özeti` |

Do not use:

- `token expired`;
- `session expired`;
- `idempotency conflict`;
- `hash mismatch`;
- `credential invalid`.

## Operational Staff Copy Rules

Station and service staff copy should be short enough for repeated use.

Preferred labels:

- `Hazırlamaya başla`
- `Hazır`
- `Hazırlanamıyor`
- `Teslim aldım`
- `Teslim edildi`
- `Toplu teslim et`
- `Sebep gerekli`
- `Bu ürün artık güncel değil`
- `Bu istasyon için yetkiniz yok`
- `Bu salon için yetkiniz yok`

Rules:

- Queue item text must prioritize table, product, quantity, note, and elapsed time.
- Error copy should tell staff whether to refresh, pick another item, or call a manager.
- Do not show cashier-only notes, payment state, or tenant setup details in station/service staff copy.

## CashierApp Copy Rules

Cashier copy must make financial state and audit impact explicit.

Preferred labels:

- `Ödeme al`
- `Kısmi ödeme`
- `Ödemeyi kaydet`
- `Ödemeyi iptal et`
- `Düzeltme ekle`
- `Oturumu kapat`
- `Kalan bakiye`
- `Ödenen`
- `Sebep`

Rules:

- Payment amount validation must be specific: `Tutar kalan bakiyeyi aşamaz.`
- Payment void and correction flows must say that a reason is required and the action is recorded.
- Close-session copy must make zero remaining balance clear.
- Closed sessions must not look actionable.

## TenantApp Copy Rules

Tenant admin copy should support configuration without pretending runtime state is editable here.

Preferred labels:

- `Salonlar`
- `Masalar`
- `Masa ayrıntısı`
- `Ekran kurulumu`
- `QR ekranını yetkilendir`
- `İstasyonlar`
- `Menü`
- `Personel`
- `Servis takibi`
- `Denetim kayıtları`

Rules:

- Tables are presented as part of hall management.
- Table detail copy should not imply a separate table management page.
- Immutable fields must say they cannot be changed after tenant creation.
- Setup actions that affect ordering, staff access, or customer visibility should use confirmation copy.

## PlatformApp Copy Rules

Platform copy should stay high-level and avoid tenant runtime exposure.

Preferred labels:

- `Tenant oluştur`
- `Tenant sağlığı`
- `Provisioning durumu`
- `DNS hazır`
- `Starter veri durumu`
- `Kurtarma gerekli`

Rules:

- Platform health copy must not expose tenant customer/order/payment detail.
- Tenant creation must clearly mark tenant name, subdomain, and GSM as required.
- DNS copy must reflect manual DNS responsibility.

## Error Copy Mapping

| API/Error Code | User-Facing Pattern |
| --- | --- |
| `unauthenticated` | `Oturum açmanız gerekiyor.` |
| `session_expired` | `Oturum süreniz doldu. Tekrar giriş yapın.` |
| `wrong_app_scope` | `Bu uygulamaya erişim yetkiniz yok.` |
| `not_authorized` | `Bu işlem için yetkiniz yok.` |
| `wrong_scope` | `Bu kayıt için yetkiniz yok.` |
| `csrf_failed` | `Güvenlik doğrulaması başarısız oldu. Sayfayı yenileyip tekrar deneyin.` |
| `fresh_presence_required` | CustomerApp: `Güncel QR kodu okutmanız gerekiyor.` |
| `token_expired` | CustomerApp: `Masanızdaki güncel QR kodu tekrar okutun.` |
| `token_consumed` | CustomerApp: `QR kod yenilendi. Yeni QR kodu okutun.` |
| `otp_expired` | `Doğrulama kodunun süresi doldu.` |
| `otp_invalid` | `Doğrulama kodu hatalı.` |
| `otp_locked` | `Çok fazla deneme yapıldı. Daha sonra tekrar deneyin.` |
| `rate_limit_exceeded` | `Çok sık deneme yapıldı. Biraz bekleyip tekrar deneyin.` |
| `idempotency_conflict` | `Bu işlem önceki denemeyle eşleşmiyor. Sayfayı yenileyip tekrar deneyin.` |
| `overpayment_not_allowed` | `Tutar kalan bakiyeyi aşamaz.` |
| `check_closed` | `Bu hesap kapatılmış.` |

App-specific copy may override these patterns only to be clearer for the current context, not to expose internal details.

## Confirmation Copy

Use confirmation only when the action is destructive, audit-affecting, hard to reverse, or easy to trigger accidentally.

Required confirmation flows:

- disable hall/table/station/product/category when allowed;
- revoke or rotate display credential;
- payment void;
- cashier correction;
- close session;
- disable user or revoke role/scope;
- tenant suspend/reactivate from PlatformApp.

Confirmation copy must include:

- object name;
- effect;
- whether a reason is required;
- safe recovery expectation when applicable.

## Empty State Copy

Empty states should explain the current state and expose the natural next action when the actor can act.

| Surface | Pattern |
| --- | --- |
| Platform tenant list | No tenant exists yet; show create tenant action. |
| Tenant hall list | No hall exists; show create hall action. |
| Tenant selected hall | No table exists in this hall; show create table action. |
| Station queue | No active item for this station. |
| Service queue | No ready item for your halls. |
| Cashier active sessions | No active table session. |
| Customer cart | Cart is empty; keep browsing menu. |
| Customer My Orders | No order from this browser yet. |
| Customer Table Orders | No active order for this table after QR verification. |

Do not use empty states to describe internal features, shortcuts, or implementation details.

## Copy Verification

Each app package must verify:

- copy maps to the shared component and wireframe responsibilities;
- customer copy has no internal security jargon;
- operational labels fit target controls on mobile/tablet/desktop;
- errors include next action where useful;
- destructive actions require reason copy when the backend requires reason;
- copy matches API/domain failure codes without redefining behavior;
- Turkish UI strings fit without clipping in expected containers.
