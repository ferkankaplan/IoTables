# PlatformApp Copy

PlatformApp copy is Turkish by default, sparse, diagnostic, and platform-safe. It should help the Platform Owner operate tenant lifecycle and setup state without exposing tenant runtime details or implying unsupported automation.

Source context:

- [definition.md](definition.md)
- [scenarios.md](scenarios.md)
- [ui-states.md](ui-states.md)
- [visibility.md](visibility.md)
- [wireframes.md](wireframes.md)
- [../_shared/copy-style.md](../_shared/copy-style.md)
- [../../api/errors.md](../../api/errors.md)

## Voice

- Use direct operational labels.
- Keep health and failure text high-level.
- Say when a step is manual.
- Say when an action is audited.
- Never imply DNS, fiscal, payment-provider, or tenant-runtime operations are automated in the current release.
- Never expose secrets, raw failure payloads, stack traces, or tenant runtime data.

## Navigation and Surface Labels

| Surface | Label |
| --- | --- |
| Login | `Platform girişi` |
| Dashboard | `Platform` |
| Tenant Workspace | `Tenantlar` |
| Tenant List | `Tenant sağlığı` |
| Create Tenant | `Tenant oluştur` |
| Tenant Detail | `Tenant ayrıntısı` |
| Tenant Settings | `Tenant ayarları` |
| Tenant Audit | `Tenant denetimi` |
| Provisioning | `Provisioning durumu` |
| Tenant host | `Tenant adresi` |
| Starter data | `Starter veri durumu` |

## Primary Actions

| Action | Copy |
| --- | --- |
| Login | `Giriş yap` |
| Logout | `Çıkış yap` |
| Create tenant | `Tenant oluştur` |
| Save profile | `Kaydet` |
| Suspend tenant | `Tenantı askıya al` |
| Reactivate tenant | `Tenantı tekrar aktif et` |
| Retry provisioning | `Provisioning tekrar dene` |
| View audit | `Denetimi gör` |

## Login and Access States

| State | Copy |
| --- | --- |
| Login loading | `Giriş durumu kontrol ediliyor...` |
| Bootstrap user missing | `Platform sahibi henüz oluşturulmamış. Bootstrap komutunu çalıştırın.` |
| First password change required | `Devam etmek için geçici şifreyi değiştirin.` |
| Invalid credentials | `Giriş bilgileri hatalı.` |
| Platform auth expired | `Oturum süreniz doldu. Tekrar giriş yapın.` |
| Wrong app scope | `Bu uygulamaya erişim yetkiniz yok.` |

## Tenant Creation Copy

| Field / State | Copy |
| --- | --- |
| Tenant name | `Tenant adı` |
| Tenant subdomain | `Tenant subdomaini` |
| Tenant GSM number | `Tenant GSM numarası` |
| Sector | `Sektör` |
| Capacity | `Kapasite` |
| Address | `Adres` |
| Required field missing | `Bu alan zorunlu.` |
| Duplicate subdomain | `Bu subdomain zaten kullanılıyor.` |
| Unsupported sector | `Bu sektör şu anda desteklenmiyor.` |
| Create pending | `Tenant oluşturuluyor...` |
| Create replay | `Bu tenant oluşturma isteği zaten işlendi.` |
| Create success | `Tenant oluşturuldu.` |
| Provisioning running | `Provisioning devam ediyor.` |
| Provisioning failed | `Provisioning başarısız oldu.` |
| Recovery needed | `Kurtarma gerekli.` |
| Tenant host available through wildcard namespace | `Tenant adresi wildcard DNS üzerinden yayınlanır.` |

Immutable field helper:

```text
Tenant adı ve subdomain oluşturulduktan sonra değiştirilemez.
```

Sector helper:

```text
Sektör, tenant oluşturulurken starter veriyi belirler. Sonradan değişirse starter veri tekrar çalışmaz.
```

V1 scope helper:

```text
V1 tek lokasyonlu, masadan QR sipariş akışını kapsar. Ödeme sağlayıcısı ve mali entegrasyon yoktur. Tenant adresleri ortamın wildcard DNS kaydı üzerinden yayınlanır.
```

## Tenant Status and Health Copy

| State | Copy |
| --- | --- |
| Active | `Aktif` |
| Provisioning | `Provisioning` |
| Provisioning failed | `Provisioning başarısız` |
| Suspended | `Askıda` |
| Starter applied | `Starter veri uygulandı` |
| Starter failed | `Starter veri başarısız` |
| Admin bootstrap pending | `Admin ilk giriş bekliyor` |
| Health unavailable | `Sağlık bilgisi alınamadı` |
| Partial health unavailable | `Bazı sağlık sinyalleri alınamadı` |
| Runtime summary unavailable | `Runtime özeti yok` |

Platform health copy must not mention customer names, order contents, payment amounts, cart contents, station queue details, or table-session details.

## Settings Copy

| State | Copy |
| --- | --- |
| GSM update warning | `GSM değişikliği denetim kaydına yazılır ve sonraki OTP akışlarında kullanılır.` |
| GSM format invalid | `GSM formatını kontrol edin.` |
| Same GSM submitted | `GSM değişmedi.` |
| Sector changed | `Sektör güncellendi. Starter veri tekrar çalıştırılmadı.` |
| Profile saved | `Tenant ayarları kaydedildi.` |
| Immutable identity edit blocked | `Tenant adı ve subdomain değiştirilemez.` |

## Lifecycle and Recovery Copy

| Action / State | Copy |
| --- | --- |
| Reason label | `Sebep` |
| Reason required | `Sebep gerekli.` |
| Suspend confirm title | `Tenant askıya alınsın mı?` |
| Suspend confirm body | `Tenant runtime uygulamaları normal trafiğe kapatılır. Bu işlem denetim kaydına yazılır.` |
| Reactivate confirm title | `Tenant tekrar aktif edilsin mi?` |
| Reactivate confirm body | `Tenant runtime uygulamaları tekrar erişilebilir olur. Bu işlem denetim kaydına yazılır.` |
| Retry provisioning title | `Provisioning tekrar denensin mi?` |
| Retry provisioning body | `Yalnızca tamamlanmamış veya güvenli tekrar denenebilir adımlar çalışır. Uygulanmış starter veri tekrar çalıştırılmaz.` |
| Stale tenant state | `Tenant durumu değişmiş. Devam etmeden önce yenileyin.` |
| Action pending | `İşlem uygulanıyor...` |
| Action success | `İşlem tamamlandı.` |

## Audit Copy

| State | Copy |
| --- | --- |
| Audit loading | `Denetim kayıtları yükleniyor...` |
| Audit empty | `Bu tenant için platform denetim kaydı yok.` |
| Audit filtered empty | `Bu filtrelere uygun kayıt yok.` |
| Audit access denied | `Denetim kayıtlarına erişim yetkiniz yok.` |

## Error Copy Mapping

| API/Error Code | PlatformApp Copy |
| --- | --- |
| `unauthenticated` | `Oturum açmanız gerekiyor.` |
| `session_expired` | `Oturum süreniz doldu. Tekrar giriş yapın.` |
| `wrong_app_scope` | `Bu uygulamaya erişim yetkiniz yok.` |
| `not_authorized` | `Bu işlem için yetkiniz yok.` |
| `not_found_or_hidden` | `Kayıt bulunamadı veya erişiminiz yok.` |
| `validation_failed` | `Alanları kontrol edin.` |
| `duplicate_subdomain` | `Bu subdomain zaten kullanılıyor.` |
| `unsupported_sector` | `Bu sektör şu anda desteklenmiyor.` |
| `provisioning_incomplete` | `Provisioning tamamlanmadı.` |
| `recovery_required` | `Kurtarma gerekli.` |
| `starter_already_applied` | `Starter veri daha önce uygulanmış.` |
| `invalid_lifecycle_transition` | `Bu durum geçişi yapılamaz.` |
| `reason_required` | `Sebep gerekli.` |
| `immutable_identity` | `Tenant adı ve subdomain değiştirilemez.` |
| `idempotency_conflict` | `Bu işlem önceki denemeyle eşleşmiyor. Sayfayı yenileyip tekrar deneyin.` |
| `csrf_failed` | `Güvenlik doğrulaması başarısız oldu. Sayfayı yenileyip tekrar deneyin.` |

## Forbidden Platform Terms and Claims

Do not show:

- raw OTP;
- raw SMS provider payload;
- password hash;
- credential secret;
- raw session token;
- stack trace;
- internal exception;
- database transaction detail;
- customer cart or order contents;
- payment card/provider secret;
- station queue internals.

Do not claim:

- DNS record is created automatically;
- DNS state can be changed per tenant;
- starter data can be re-run by changing sector;
- CustomerApp takes payments in the current release;
- PlatformApp is a cashier, station, service, or tenant runtime console;
- IoTables current release is a fiscal/POS-complete system.

## Copy Acceptance

PlatformApp copy is acceptable when:

- login and setup gates reveal no tenant data before authorization;
- tenant creation marks name, subdomain, and GSM as required;
- immutable identity and wildcard tenant host routing are clear;
- provisioning failure and recovery copy stays redacted and actionable;
- lifecycle actions mention reason/audit consequences;
- no tenant runtime mutation or unsupported automation is implied.
