# CashierApp Copy

CashierApp copy is Turkish by default, precise, auditable, and operational. It should support fast settlement work without implying broad financial override power.

Source context:

- [definition.md](definition.md)
- [scenarios.md](scenarios.md)
- [ui-states.md](ui-states.md)
- [visibility.md](visibility.md)
- [wireframes.md](wireframes.md)
- [../_shared/copy-style.md](../_shared/copy-style.md)
- [../../api/errors.md](../../api/errors.md)

## Voice

- Use short labels for cashier actions.
- Use `Adisyon` for the cashier-facing Check.
- Make remaining balance, required reason, and audit consequences explicit.
- Say when an action is blocked and why.
- Do not imply discounts, refunds, split checks, fiscal documents, or customer payment flows exist in the current release.

## Navigation and Surface Labels

| Surface | Label |
| --- | --- |
| Login | `Kasa girişi` |
| Cashier Workspace | `Kasa` |
| Table Board | `Masalar` |
| Session Detail | `Adisyon ayrıntısı` |
| Payment Drawer | `Ödeme al` |
| Correction Drawer | `Düzeltme kaydet` |
| Close Session Dialog | `Oturumu kapat` |
| Payment History | `Ödeme geçmişi` |

## Primary Actions

| Action | Copy |
| --- | --- |
| Login | `Giriş yap` |
| Change password | `Şifreyi değiştir` |
| Send OTP | `SMS kodu gönder` |
| Verify OTP | `Kodu doğrula` |
| Record payment | `Ödemeyi kaydet` |
| Add note correction | `Not ekle` |
| Void item | `Ürünü iptal et` |
| Void payment | `Ödemeyi iptal et` |
| Close session | `Oturumu kapat` |
| Refresh | `Yenile` |

## Login and OTP Copy

| State | Copy |
| --- | --- |
| Login loading | `Giriş durumu kontrol ediliyor...` |
| Invalid credentials | `Giriş bilgileri hatalı.` |
| First password required | `Devam etmek için geçici şifreyi değiştirin.` |
| OTP required | `Kasa kurulumu için SMS doğrulaması gerekli.` |
| OTP sent | `Doğrulama kodu tenant GSM numarasına gönderildi.` |
| OTP expired | `Kodun süresi doldu. Yeni kod isteyin.` |
| OTP locked | `Çok fazla deneme yapıldı. Daha sonra tekrar deneyin.` |
| No cashier role | `Kasa uygulamasına erişim yetkiniz yok.` |
| Tenant unavailable | `Bu işletme şu anda erişilebilir değil.` |

## Board and Session Copy

| State / Field | Copy |
| --- | --- |
| Board loading | `Masa durumu yükleniyor...` |
| Empty active sessions | `Aktif oturum yok.` |
| Available table | `Boş` |
| Active table | `Aktif` |
| Stale table | `Masa durumu değişti. Yenileniyor.` |
| Cannot prepare attention | `Hazırlanamayan ürün var` |
| Total | `Toplam` |
| Paid | `Ödenen` |
| Remaining | `Kalan` |
| Adisyon | `Adisyon` |
| Orders | `Siparişler` |
| Payments | `Ödemeler` |
| Corrections | `Düzeltmeler` |

## Payment Copy

| State / Field | Copy |
| --- | --- |
| Amount | `Tutar` |
| Method cash | `Nakit` |
| Method card | `Kart` |
| Method transfer | `Havale/EFT` |
| Optional note | `Kasa notu` |
| Empty amount | `Tutar girin.` |
| Invalid amount | `Tutar sıfırdan büyük olmalı.` |
| Over remaining | `Tutar kalan bakiyeyi aşamaz.` |
| Submitting payment | `Ödeme kaydediliyor...` |
| Payment recorded | `Ödeme kaydedildi.` |
| Duplicate payment | `Bu ödeme daha önce kaydedildi.` |
| Payment voided | `Ödeme iptal edildi.` |

## Close and Correction Copy

| State | Copy |
| --- | --- |
| Close disabled | `Kalan bakiye sıfır olmadan oturum kapatılamaz.` |
| Close confirm | `Adisyon kapatılacak. Bu işlemden sonra normal ödeme veya düzeltme yapılamaz.` |
| Closing | `Oturum kapatılıyor...` |
| Closed | `Oturum kapatıldı.` |
| Already closed | `Bu oturum zaten kapalı.` |
| Reason required | `Düzeltme nedeni zorunlu.` |
| Item void blocked | `Bu ürün artık kasa iptali için uygun değil.` |
| Payment void blocked | `Bu ödeme iptal edilemez.` |
| Any payment blocks item void | `Ödeme alınmış adisyonda ürün iptali yapılamaz.` |
| Correction saved | `Düzeltme kaydedildi.` |
| Stale session | `Adisyon durumu değişmiş. Güncel bilgileri kontrol edin.` |

## Payment History Copy

| State | Copy |
| --- | --- |
| History loading | `Ödemeler yükleniyor...` |
| Empty today | `Bugün ödeme kaydı yok.` |
| Current business day | `Bugünkü ödemeler` |
| Actor | `Kasa görevlisi` |
| Void reason | `İptal nedeni` |

## Error Copy Mapping

| API/Error Code | CashierApp Copy |
| --- | --- |
| `unauthenticated` | `Oturum açmanız gerekiyor.` |
| `session_expired` | `Oturum süreniz doldu. Tekrar giriş yapın.` |
| `wrong_app_scope` | `Bu uygulamaya erişim yetkiniz yok.` |
| `missing_role` | `Kasa rolünüz yok.` |
| `tenant_unavailable` | `Bu işletme şu anda erişilebilir değil.` |
| `invalid_credentials` | `Giriş bilgileri hatalı.` |
| `otp_required` | `SMS doğrulaması gerekli.` |
| `otp_invalid` | `Kod hatalı.` |
| `otp_expired` | `Kodun süresi doldu.` |
| `not_found_or_hidden` | `Kayıt bulunamadı veya erişiminiz yok.` |
| `overpayment_not_allowed` | `Ödeme kalan bakiyeyi aşamaz.` |
| `idempotency_conflict` | `Bu işlem önceki denemeyle eşleşmiyor. Güncel durumu yenileyin.` |
| `payment_void_not_allowed` | `Bu ödeme iptal edilemez.` |
| `correction_not_allowed` | `Bu düzeltme mevcut durumda yapılamaz.` |
| `reason_required` | `Neden alanı zorunlu.` |
| `remaining_balance_not_zero` | `Kalan bakiye sıfır değil.` |
| `check_closed` | `Adisyon kapalı.` |
| `invalid_state` | `Oturum durumu değişmiş. Güncel bilgileri kontrol edin.` |
| `csrf_failed` | `Güvenlik doğrulaması başarısız oldu. Sayfayı yenileyip tekrar deneyin.` |

## Forbidden Claims

Do not show labels or copy that imply:

- CashierApp can configure tenant setup;
- cashier can split checks, merge checks, move items, or split payment by item/person;
- cashier can apply manual discounts, service fees, campaign discounts, tax overrides, or price edits in the current release;
- customer can pay from CustomerApp in the current release;
- fiscal/e-Adisyon/ÖKC issuance exists in the current release;
- zero balance automatically closes the table session;
- frontend totals are final authority.

## Copy Acceptance

CashierApp copy is acceptable when:

- payment and close actions are clear and short;
- OTP copy states tenant GSM without exposing the full number;
- blocked correction reasons are explicit;
- stale/duplicate copy tells cashier to trust refreshed server state;
- out-of-scope payment, split, discount, provider, and fiscal language is absent.
