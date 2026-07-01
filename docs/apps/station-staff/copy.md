# StationStaffApp Copy

StationStaffApp copy is Turkish by default, direct, fast, and operational. It should support repeated station work with clear action labels and no financial or tenant-setup language.

Source context:

- [definition.md](definition.md)
- [scenarios.md](scenarios.md)
- [ui-states.md](ui-states.md)
- [visibility.md](visibility.md)
- [wireframes.md](wireframes.md)
- [../_shared/copy-style.md](../_shared/copy-style.md)
- [../../api/errors.md](../../api/errors.md)

## Voice

- Use short action labels.
- Prioritize table, product, quantity, note, status, and elapsed time.
- Say whether staff should refresh, choose another item, or call cashier/manager.
- Do not use payment, refund, discount, cancellation, or settlement language.
- Do not expose cashier-only notes or payment state.

## Navigation and Surface Labels

| Surface | Label |
| --- | --- |
| Login | `İstasyon girişi` |
| Station Selector | `İstasyon seç` |
| Station Queue | `İstasyon kuyruğu` |
| Item Detail | `Ürün ayrıntısı` |
| Recent Items | `Son işler` |
| Workload | `Yoğunluk` |

## Primary Actions

| Action | Copy |
| --- | --- |
| Login | `Giriş yap` |
| Change password | `Şifreyi değiştir` |
| Select station | `İstasyona geç` |
| Start preparing | `Hazırlamaya başla` |
| Mark ready | `Hazır` |
| Cannot prepare | `Hazırlanamıyor` |
| Submit reason | `Kaydet` |
| Refresh | `Yenile` |

## Login and Station Access Copy

| State | Copy |
| --- | --- |
| Login loading | `Giriş durumu kontrol ediliyor...` |
| Invalid credentials | `Giriş bilgileri hatalı.` |
| First password required | `Devam etmek için geçici şifreyi değiştirin.` |
| No station role | `İstasyon uygulamasına erişim yetkiniz yok.` |
| No authorized stations | `Yetkili olduğunuz istasyon yok.` |
| Station disabled | `Bu istasyon şu anda kullanılamıyor.` |
| Tenant unavailable | `Bu işletme şu anda erişilebilir değil.` |

## Queue Copy

| State / Field | Copy |
| --- | --- |
| Queue loading | `Kuyruk yükleniyor...` |
| Empty queue | `Bu istasyonda aktif iş yok.` |
| Pending group | `Bekliyor` |
| Preparing group | `Hazırlanıyor` |
| Ready group | `Hazır` |
| Cannot prepare group | `Hazırlanamıyor` |
| Oldest pending age | `En eski bekleyen` |
| Average prep time | `Ortalama hazırlama` |
| Quantity | `Adet` |
| Note | `Not` |
| Ordered time | `Sipariş zamanı` |

## Item State and Error Copy

| State | Copy |
| --- | --- |
| Item loading | `Ürün bilgisi yükleniyor...` |
| Item not found | `Bu ürün artık kuyrukta yok.` |
| Item stale | `Ürün durumu değişmiş. Güncel durum yükleniyor.` |
| Unauthorized item | `Bu ürün için yetkiniz yok.` |
| Duplicate/stale action | `İşlem uygulanmadı. Güncel durum gösteriliyor.` |
| Network failure after action | `Bağlantı kesildi. Güncel durum kontrol ediliyor.` |
| Closed/completed item | `Bu ürün artık değiştirilemez.` |

## Cannot Prepare Copy

| State / Field | Copy |
| --- | --- |
| Dialog title | `Ürün hazırlanamadı` |
| Reason label | `Sebep` |
| Reason required | `Sebep gerekli.` |
| Helper | `Bu işlem ödeme, iptal veya indirim yapmaz. Kasiyer durumdan haberdar olur.` |
| Success | `Hazırlanamıyor olarak işaretlendi.` |

## Success Copy

| Action | Copy |
| --- | --- |
| Start preparing success | `Hazırlanıyor.` |
| Mark ready success | `Hazır olarak işaretlendi.` |
| Cannot prepare success | `Kasiyer dikkatine gönderildi.` |

## Error Copy Mapping

| API/Error Code | StationStaffApp Copy |
| --- | --- |
| `unauthenticated` | `Oturum açmanız gerekiyor.` |
| `session_expired` | `Oturum süreniz doldu. Tekrar giriş yapın.` |
| `wrong_app_scope` | `Bu uygulamaya erişim yetkiniz yok.` |
| `missing_role` | `İstasyon rolünüz yok.` |
| `outside_station_scope` | `Bu istasyon için yetkiniz yok.` |
| `station_unavailable` | `Bu istasyon şu anda kullanılamıyor.` |
| `invalid_preparation_transition` | `Ürün durumu değişmiş. Güncel durumu kontrol edin.` |
| `reason_required` | `Sebep gerekli.` |
| `not_found_or_hidden` | `Kayıt bulunamadı veya erişiminiz yok.` |
| `csrf_failed` | `Güvenlik doğrulaması başarısız oldu. Sayfayı yenileyip tekrar deneyin.` |

## Forbidden Claims

Do not show labels or copy that imply:

- payment, refund, discount, or session closure;
- customer delivery confirmation;
- tenant setup or menu editing;
- product station reassignment;
- cashier correction;
- frontend station selection is an authorization proof.

## Copy Acceptance

StationStaffApp copy is acceptable when:

- queue labels fit touch-first operational use;
- `cannot_prepare` is operational and not financial;
- stale/duplicate action copy tells staff current state is being refreshed;
- unauthorized station copy is direct and safe;
- cashier-only/payment/setup language is absent.
