# ServiceStaffApp Copy

ServiceStaffApp copy is Turkish by default, direct, fast, and operational. It should support physical service work without setup, station-preparation, payment, or cashier language.

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
- Prioritize table, station, item, quantity, note, ready age, and delivery status.
- Say clearly when service tracking is disabled.
- Do not imply `ready` means delivered while tracking is enabled.
- Do not expose payment, cashier correction, tenant setup, or station-preparation controls.

## Navigation and Surface Labels

| Surface | Label |
| --- | --- |
| Login | `Servis girişi` |
| Service Queue | `Servis kuyruğu` |
| Item Detail | `Teslim ayrıntısı` |
| Recent Deliveries | `Son teslimler` |
| Workload | `Yoğunluk` |

## Primary Actions

| Action | Copy |
| --- | --- |
| Login | `Giriş yap` |
| Change password | `Şifreyi değiştir` |
| Pick up | `Teslim aldım` |
| Deliver | `Teslim edildi` |
| Bulk deliver | `Toplu teslim et` |
| Clear selection | `Seçimi temizle` |
| Refresh | `Yenile` |

## Login and Access Copy

| State | Copy |
| --- | --- |
| Login loading | `Giriş durumu kontrol ediliyor...` |
| Invalid credentials | `Giriş bilgileri hatalı.` |
| First password required | `Devam etmek için geçici şifreyi değiştirin.` |
| No service role | `Servis uygulamasına erişim yetkiniz yok.` |
| No hall scope | `Yetkili olduğunuz salon yok.` |
| Tenant unavailable | `Bu işletme şu anda erişilebilir değil.` |

## Tracking Disabled Copy

| State | Copy |
| --- | --- |
| Tracking disabled title | `Servis takibi kapalı` |
| Tracking disabled body | `Bu tenant ayrı teslim takibi kullanmıyor. Hazır ürünler müşteri için teslim edildi kabul edilir.` |
| No queue | `Servis kuyruğu gösterilmez.` |

## Queue Copy

| State / Field | Copy |
| --- | --- |
| Queue loading | `Servis kuyruğu yükleniyor...` |
| Empty ready queue | `Yetkili salonlarda hazır ürün yok.` |
| Table group | `Masa` |
| Ready status | `Hazır` |
| Picked-up status | `Teslim alındı` |
| Delivered status | `Teslim edildi` |
| Source station | `İstasyon` |
| Ready age | `Hazır bekleme` |
| Oldest ready age | `En eski hazır` |
| Average delivery time | `Ortalama teslim` |
| Quantity | `Adet` |
| Note | `Not` |

## Item and Bulk State Copy

| State | Copy |
| --- | --- |
| Item loading | `Ürün bilgisi yükleniyor...` |
| Item not found | `Bu ürün artık servis kuyruğunda yok.` |
| Unauthorized hall | `Bu salon için yetkiniz yok.` |
| Item not ready | `Bu ürün henüz hazır değil.` |
| Already delivered | `Bu ürün teslim edilmiş.` |
| Stale item | `Ürün durumu değişmiş. Güncel durum yükleniyor.` |
| Network failure | `Bağlantı kesildi. Güncel durum kontrol ediliyor.` |
| Bulk selecting | `Aynı masadan ürünleri seçin.` |
| Mixed table selection | `Toplu teslim yalnızca aynı masadaki ürünler için yapılır.` |
| Bulk submitting | `Toplu teslim kaydediliyor...` |
| Bulk delivered | `Seçili ürünler teslim edildi.` |
| Bulk replay | `Bu toplu teslim işlemi zaten kaydedildi.` |

## Success Copy

| Action | Copy |
| --- | --- |
| Picked up | `Teslim alındı.` |
| Delivered | `Teslim edildi.` |
| Direct ready to delivered | `Ürün teslim edildi.` |

## Error Copy Mapping

| API/Error Code | ServiceStaffApp Copy |
| --- | --- |
| `unauthenticated` | `Oturum açmanız gerekiyor.` |
| `session_expired` | `Oturum süreniz doldu. Tekrar giriş yapın.` |
| `wrong_app_scope` | `Bu uygulamaya erişim yetkiniz yok.` |
| `missing_role` | `Servis rolünüz yok.` |
| `outside_hall_scope` | `Bu salon için yetkiniz yok.` |
| `service_tracking_disabled` | `Servis takibi kapalı.` |
| `not_ready_for_delivery` | `Bu ürün henüz hazır değil.` |
| `invalid_delivery_transition` | `Ürün durumu değişmiş. Güncel durumu kontrol edin.` |
| `bulk_mixed_table` | `Toplu teslim yalnızca aynı masa için yapılır.` |
| `bulk_item_invalid` | `Seçili ürünlerden biri artık teslim edilemez. Listeyi yenileyin.` |
| `idempotency_conflict` | `Bu toplu teslim önceki denemeyle eşleşmiyor. Listeyi yenileyin.` |
| `not_found_or_hidden` | `Kayıt bulunamadı veya erişiminiz yok.` |
| `csrf_failed` | `Güvenlik doğrulaması başarısız oldu. Sayfayı yenileyip tekrar deneyin.` |

## Forbidden Claims

Do not show labels or copy that imply:

- ServiceStaffApp can enable service tracking;
- `ready` means delivered while service tracking is enabled;
- service staff can receive payments, close sessions, refund, discount, or correct checks;
- service staff can start/ready/cannot-prepare station work;
- frontend hall/table selection is authorization proof.

## Copy Acceptance

ServiceStaffApp copy is acceptable when:

- disabled tracking is clear and non-actionable;
- queue/action labels fit touch-first service work;
- bulk delivery copy enforces same-table selection;
- stale/duplicate copy tells staff current state is refreshed;
- payment, cashier correction, tenant setup, and station-preparation language is absent.
