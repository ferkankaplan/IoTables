# CustomerApp Copy

CustomerApp copy is Turkish by default, short, calm, and non-technical. It must help the customer continue ordering without exposing security, session, token, database, or API internals.

Source context:

- [definition.md](definition.md)
- [scenarios.md](scenarios.md)
- [ui-states.md](ui-states.md)
- [visibility.md](visibility.md)
- [wireframes.md](wireframes.md)
- [../_shared/copy-style.md](../_shared/copy-style.md)
- [../../api/errors.md](../../api/errors.md)

## Voice

- Use direct customer language.
- Prefer one clear next step.
- Do not blame the customer for expired, stale, unavailable, or blocked states.
- Do not imply an order succeeded until backend acceptance is known.
- Do not mention `token`, `hash`, `credential`, `idempotency`, `session`, `cookie`, `database`, or `transaction`.

## Navigation and Surface Labels

| Surface | Label |
| --- | --- |
| Menu | `Menü` |
| Cart | `Sepet` |
| My Orders | `Siparişlerim` |
| Table Orders | `Masa Siparişleri` |
| Bill / Balance | `Hesap Özeti` |
| Product detail | Product name |
| QR retry | `QR kodu okut` |
| Order confirmation | `Siparişiniz alındı` |

## Primary Actions

| Action | Copy |
| --- | --- |
| Open cart | `Sepeti gör` |
| Add to cart | `Sepete ekle` |
| Update cart item | `Sepeti güncelle` |
| Remove item | `Ürünü çıkar` |
| Submit order | `Sipariş ver` |
| Return to menu | `Menüye dön` |
| View my orders | `Siparişlerimi gör` |
| View table orders | `Masa siparişlerini gör` |
| View bill | `Hesap özetini gör` |
| Scan again | `Güncel QR kodu okut` |

## QR and Presence States

| Internal Condition | Customer Copy |
| --- | --- |
| QR redemption loading | `Masanız doğrulanıyor...` |
| QR redeemed | `Menü hazır.` |
| QR expired | `Masanızdaki güncel QR kodu tekrar okutun.` |
| QR already consumed | `QR kod yenilendi. Masanızdaki yeni QR kodu okutun.` |
| Wrong-table QR | `Lütfen kendi masanızdaki QR kodu okutun.` |
| Fresh presence required for submit | `Sipariş vermek için masanızdaki güncel QR kodu tekrar okutun. Sepetiniz korunur.` |
| Fresh presence required for table orders | `Masa siparişlerini görmek için güncel QR kodu okutun.` |
| Fresh presence required for bill | `Hesap özetini görmek için güncel QR kodu okutun.` |
| Browser session lost | `Siparişe devam etmek için masanızdaki QR kodu tekrar okutun.` |
| Table unavailable | `Bu masa şu anda siparişe kapalı.` |
| Tenant unavailable | `Bu işletme şu anda sipariş alamıyor.` |

## Menu and Product States

| State | Customer Copy |
| --- | --- |
| Menu loading | `Menü yükleniyor...` |
| Empty menu | `Şu anda sipariş verilebilecek ürün yok.` |
| Category empty | `Bu kategoride sipariş verilebilecek ürün yok.` |
| Product unavailable | `Bu ürün şu anda sipariş edilemiyor.` |
| Variant unavailable | `Bu seçenek şu anda sipariş edilemiyor.` |
| Required variant missing | `Lütfen bir seçenek seçin.` |
| Required modifier missing | `Lütfen gerekli seçimleri tamamlayın.` |
| Invalid modifier combination | `Seçiminizi gözden geçirin.` |
| Quantity invalid | `Adedi gözden geçirin.` |
| Image missing fallback | `Görsel yok` |

## Cart States

| State | Customer Copy |
| --- | --- |
| Empty cart | `Sepetiniz boş.` |
| Editable cart | `Sepetiniz` |
| Stale item | `Bu ürün güncellendi. Devam etmek için sepeti gözden geçirin.` |
| Invalid item | `Bu üründeki seçimleri gözden geçirin.` |
| Unavailable item at submit | `Sepetinizde şu anda sipariş edilemeyen ürün var.` |
| Submit pending | `Siparişiniz gönderiliyor...` |
| Submit failed, cart kept | `Sipariş gönderilemedi. Sepetiniz korunur.` |
| Network failure after submit | `Bağlantı kesildi. Sipariş durumunu kontrol ediyoruz.` |
| Cart cleared after success | `Yeni sipariş için menüden seçim yapabilirsiniz.` |

## Order Confirmation and Status

| State | Customer Copy |
| --- | --- |
| Order accepted | `Siparişiniz alındı.` |
| Duplicate submit replay | `Siparişiniz zaten alındı.` |
| My Orders empty | `Bu cihazdan verilmiş sipariş yok.` |
| Table Orders empty | `Bu masada aktif sipariş yok.` |
| Status preparing | `Hazırlanıyor` |
| Status delivered | `Teslim edildi` |

Order time label:

```text
Sipariş saati
```

Item note label:

```text
Not
```

## Bill and Balance Copy

| Field | Copy |
| --- | --- |
| Bill title | `Hesap Özeti` |
| Total | `Toplam` |
| Paid | `Ödenen` |
| Remaining | `Kalan` |
| Order total | `Sipariş toplamı` |
| Last payment time | `Son ödeme zamanı` |
| Payment updated | `Hesap özeti güncellendi.` |

Bill copy must stay read-only. Do not show words such as `öde`, `ödeme yap`, `kapat`, `indirim iste`, `iptal et`, or `iade iste` as CustomerApp actions in v1.

## Error Copy Mapping

| API/Error Code | CustomerApp Copy |
| --- | --- |
| `fresh_presence_required` | `Güncel QR kodu okutmanız gerekiyor.` |
| `token_expired` | `Masanızdaki güncel QR kodu tekrar okutun.` |
| `token_consumed` | `QR kod yenilendi. Yeni QR kodu okutun.` |
| `wrong_table` | `Lütfen kendi masanızdaki QR kodu okutun.` |
| `tenant_unavailable` | `Bu işletme şu anda sipariş alamıyor.` |
| `table_unavailable` | `Bu masa şu anda siparişe kapalı.` |
| `session_expired` | `Siparişe devam etmek için masanızdaki QR kodu tekrar okutun.` |
| `empty_cart` | `Sipariş vermek için sepetinize ürün ekleyin.` |
| `item_not_orderable` | `Bu ürün şu anda sipariş edilemiyor.` |
| `variant_invalid` | `Seçiminizi gözden geçirin.` |
| `modifier_invalid` | `Seçiminizi gözden geçirin.` |
| `cart_changed_conflict` | `Sepetiniz güncellendi. Devam etmeden önce kontrol edin.` |
| `closed_table_session` | `Bu masa için önce güncel QR kodu okutmanız gerekiyor.` |
| `idempotency_conflict` | `Sipariş durumu kontrol edilemedi. Sayfayı yenileyip tekrar deneyin.` |
| `csrf_failed` | `Sayfayı yenileyip tekrar deneyin.` |
| `rate_limit_exceeded` | `Çok sık deneme yapıldı. Biraz bekleyip tekrar deneyin.` |

## Forbidden Customer Terms

Do not show these terms in CustomerApp UI:

- `token`
- `hash`
- `credential`
- `idempotency`
- `cookie`
- `session id`
- `table session id`
- `customer ordering session`
- `database`
- `transaction`
- `row lock`
- `stack trace`
- `station route`
- `payment mutation`

## Forbidden V1 Action Copy

These labels must not appear as CustomerApp actions in v1:

- `Ödeme yap`
- `Kartla öde`
- `Masayı kapat`
- `Siparişi iptal et`
- `Siparişi değiştir`
- `İndirim iste`
- `İade iste`
- `Fiş oluştur`
- `e-Adisyon oluştur`
- `Personel çağır` unless a future app scenario explicitly defines it.

## Copy Acceptance

CustomerApp copy is acceptable when:

- QR and session failures explain the next scan action without technical terms;
- submit failures state that the cart is preserved when it is preserved;
- order success appears only after backend acceptance or idempotent replay;
- bill text is read-only;
- no v1 out-of-scope action is visible.
