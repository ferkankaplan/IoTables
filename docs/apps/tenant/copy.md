# TenantApp Copy

TenantApp copy is Turkish by default, administrative, clear, and reversible where possible. It should help the Tenant Admin configure restaurant operations without implying live runtime control from the setup app.

Source context:

- [definition.md](definition.md)
- [scenarios.md](scenarios.md)
- [ui-states.md](ui-states.md)
- [visibility.md](visibility.md)
- [wireframes.md](wireframes.md)
- [../_shared/copy-style.md](../_shared/copy-style.md)
- [../../api/errors.md](../../api/errors.md)

## Voice

- Use operational object names consistently.
- Say when data is disabled for history instead of deleted.
- Say when a change affects customer visibility, staff access, or order routing.
- Never imply TenantApp can receive payments, close table sessions, prepare items, deliver items, or create customer orders.
- Never expose raw OTP, display credential, token, hash, stack trace, or provider payload.

## Navigation and Surface Labels

| Surface | Label |
| --- | --- |
| Public Tenant Page | `İşletme` |
| Tenant Login | `Admin girişi` |
| Admin Dashboard | `Kurulum` |
| Hall Management | `Salonlar` |
| Table Detail | `Masa ayrıntısı` |
| Station Management | `İstasyonlar` |
| Menu Management | `Menü` |
| Staff Management | `Personel` |
| Tenant Settings | `Ayarlar` |
| Tenant Audit | `Denetim kayıtları` |

## Primary Actions

| Action | Copy |
| --- | --- |
| Login | `Giriş yap` |
| Complete first password | `Şifreyi değiştir` |
| Send OTP | `Kod gönder` |
| Verify OTP | `Doğrula` |
| Create hall | `Salon ekle` |
| Create table | `Masa ekle` |
| Create station | `İstasyon ekle` |
| Create category | `Kategori ekle` |
| Create product/service | `Ürün ekle` |
| Create staff | `Personel ekle` |
| Save | `Kaydet` |
| Disable | `Devre dışı bırak` |
| Re-provision display | `Ekranı yeniden kur` |
| Create display claim | `Ekran kurulum kodu oluştur` |

## Public Page Copy

| State | Copy |
| --- | --- |
| Loading | `İşletme bilgileri yükleniyor...` |
| Tenant not found | `İşletme bulunamadı.` |
| Tenant unavailable | `Bu işletme şu anda erişilebilir değil.` |
| Public info fallback | `İşletme bilgileri` |

Public page copy must not mention setup checklist, staff users, orders, payments, table sessions, or platform internals.

## Login and OTP Copy

| State | Copy |
| --- | --- |
| Login loading | `Giriş durumu kontrol ediliyor...` |
| Invalid credentials | `Giriş bilgileri hatalı.` |
| First password change required | `Devam etmek için geçici şifreyi değiştirin.` |
| OTP required | `GSM numarasına gönderilen kodu girin.` |
| OTP expired | `Kodun süresi doldu. Yeni kod gönderin.` |
| OTP failed | `Kod hatalı.` |
| OTP locked | `Çok fazla deneme yapıldı. Daha sonra tekrar deneyin.` |
| Password rejected | `Şifre kurallarını karşılamıyor.` |

## Hall and Table Copy

| State / Field | Copy |
| --- | --- |
| Empty halls | `Henüz salon yok.` |
| Empty selected hall | `Bu salonda masa yok.` |
| Hall name | `Salon adı` |
| Table name | `Masa adı` |
| Display order | `Sıra` |
| Ordered grid helper | `V1 masa düzeni sıralı grid olarak yönetilir.` |
| Active session blocks table disable | `Bu masada aktif oturum var. Normal kapatma yapılamaz.` |
| Disable reason | `Sebep` |
| Table disabled | `Masa devre dışı.` |

Do not use copy that implies a separate primary `Masa Yönetimi` page.

## Table Display Provisioning Copy

| State | Copy |
| --- | --- |
| Not provisioned | `Bu masa ekranı kurulmamış.` |
| Claim created | `Kurulum kodu oluşturuldu.` |
| Claim one-time warning | `Bu kod bir kez gösterilir ve süresi dolunca geçersiz olur.` |
| Waiting for device | `Cihazın kurulum kodunu kullanması bekleniyor.` |
| Claim expired | `Kurulum kodunun süresi doldu.` |
| Claim consumed | `Masa ekranı kuruldu.` |
| Credential revoked | `Masa ekranı yetkisi iptal edildi.` |
| Re-provision warning | `Yeni kurulum eski ekran yetkisini iptal eder.` |

Do not show raw credential secrets after the one-time response is dismissed.

## Station Copy

| State / Field | Copy |
| --- | --- |
| Empty stations | `Henüz istasyon yok.` |
| Station name | `İstasyon adı` |
| Station disabled | `İstasyon devre dışı.` |
| Active queue blocks disable | `Bu istasyonda aktif işler var. Devre dışı bırakılamaz.` |
| Orderable products block disable | `Bu istasyona yönlenen siparişe açık ürünler var.` |

## Menu Copy

| State / Field | Copy |
| --- | --- |
| Empty categories | `Henüz kategori yok.` |
| Empty category products | `Bu kategoride ürün yok.` |
| Product name | `Ürün adı` |
| Product description | `Açıklama` |
| Variant | `Varyant / porsiyon` |
| Price | `Fiyat` |
| Modifier group | `Seçenek grubu` |
| Required modifier | `Zorunlu seçim` |
| Optional modifier | `Opsiyonel seçim` |
| Station assignment | `İstasyon` |
| Availability | `Müsaitlik` |
| Product unavailable | `Ürün geçici olarak siparişe kapalı.` |
| Product disabled | `Ürün devre dışı. Geçmiş kayıtlar korunur.` |
| Missing station | `Siparişe açmak için bir istasyon seçin.` |
| Disabled station route | `Seçilen istasyon devre dışı.` |
| Multiple station route | `V1'de her ürün tek istasyona atanır.` |
| Price snapshot helper | `Fiyat değişikliği eski siparişleri değiştirmez.` |

## Staff Copy

| State / Field | Copy |
| --- | --- |
| Empty staff | `Henüz personel yok.` |
| Username | `Kullanıcı adı` |
| Display name | `Görünen ad` |
| Role | `Rol` |
| Station scope | `İstasyon yetkisi` |
| Hall scope | `Salon yetkisi` |
| First password required | `İlk girişte şifre değiştirilecek.` |
| Cashier OTP helper | `Kasiyer ilk şifre kurulumu tenant GSM numarasıyla doğrulanır.` |
| Staff OTP not required | `İstasyon ve servis personeli için V1'de OTP gerekmez.` |
| Missing role/scope | `Bu rol için gerekli yetki alanı eksik.` |
| Disabled user | `Personel devre dışı.` |
| Permission changed | `Yetki değişti. Bir sonraki işlemde yeni yetki uygulanır.` |

## Settings Copy

| State / Field | Copy |
| --- | --- |
| Tenant name immutable | `Tenant adı değiştirilemez.` |
| Subdomain immutable | `Subdomain değiştirilemez.` |
| Public display name | `Görünen işletme adı` |
| GSM number | `GSM numarası` |
| Address | `Adres` |
| Capacity | `Kapasite` |
| Sector | `Sektör` |
| Sector helper | `Sektör değişirse starter veri tekrar çalışmaz.` |
| Service tracking | `Servis takibi` |
| Service tracking enabled | `Servis personeli teslim sürecini takip eder.` |
| Service tracking disabled | `Hazır durumundaki ürün müşteri için teslim edildi kabul edilir.` |
| GSM changed | `GSM güncellendi. Sonraki OTP akışlarında yeni numara kullanılır.` |
| Settings saved | `Ayarlar kaydedildi.` |

## Audit Copy

| State | Copy |
| --- | --- |
| Audit loading | `Denetim kayıtları yükleniyor...` |
| Audit empty | `Bu tenant için denetim kaydı yok.` |
| Audit filtered empty | `Bu filtrelere uygun kayıt yok.` |
| Audit access denied | `Denetim kayıtlarına erişim yetkiniz yok.` |

## Error Copy Mapping

| API/Error Code | TenantApp Copy |
| --- | --- |
| `unauthenticated` | `Oturum açmanız gerekiyor.` |
| `session_expired` | `Oturum süreniz doldu. Tekrar giriş yapın.` |
| `wrong_app_scope` | `Bu uygulamaya erişim yetkiniz yok.` |
| `not_authorized` | `Bu işlem için yetkiniz yok.` |
| `tenant_unavailable` | `Bu işletme şu anda erişilebilir değil.` |
| `validation_failed` | `Alanları kontrol edin.` |
| `immutable_identity` | `Tenant adı ve subdomain değiştirilemez.` |
| `duplicate_hall` | `Bu salon adı veya sırası zaten kullanılıyor.` |
| `duplicate_table` | `Bu masa adı veya sırası zaten kullanılıyor.` |
| `active_session_blocks_disable` | `Aktif oturum varken bu işlem yapılamaz.` |
| `duplicate_station` | `Bu istasyon adı veya sırası zaten kullanılıyor.` |
| `station_has_orderable_products` | `Bu istasyona yönlenen siparişe açık ürünler var.` |
| `station_has_active_queue` | `Bu istasyonda aktif işler var.` |
| `station_unavailable` | `Seçilen istasyon kullanılamıyor.` |
| `duplicate_category` | `Bu kategori adı veya sırası zaten kullanılıyor.` |
| `reason_required` | `Sebep gerekli.` |
| `claim_expired` | `Kurulum kodunun süresi doldu.` |
| `claim_consumed` | `Kurulum kodu daha önce kullanılmış.` |
| `otp_expired` | `Doğrulama kodunun süresi doldu.` |
| `otp_invalid` | `Doğrulama kodu hatalı.` |
| `otp_locked` | `Çok fazla deneme yapıldı. Daha sonra tekrar deneyin.` |
| `assignment_target_disabled` | `Seçilen yetki alanı devre dışı.` |
| `last_admin_not_allowed` | `Son admin yetkisi kaldırılamaz.` |
| `tenant_settings_missing` | `Tenant ayarları bulunamadı.` |

## Forbidden Claims

Do not show labels or copy that imply:

- TenantApp can create customer orders;
- TenantApp can receive payments or close table sessions;
- TenantApp can prepare or deliver items;
- tables have a standalone primary management page in v1;
- v1 supports floor-plan coordinates;
- starter data is recreated after edit/delete;
- sector change reruns starter data;
- raw display credentials can be viewed later;
- staff scope warnings are only frontend checks.

## Copy Acceptance

TenantApp copy is acceptable when:

- public page copy exposes only safe public fields;
- first login and OTP copy avoids raw security internals;
- table management copy keeps hall context;
- menu copy distinguishes disabled from unavailable;
- service tracking copy states customer/staff impact;
- destructive or audit-affecting actions explain reason/audit consequence;
- forbidden runtime controls and unsupported v1 claims are absent.
