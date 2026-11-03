# Arayüz Tasarım Standartları — Zorunlu

Aka Integration Hub ticari bir üründür; müşteri ilk izlenimi ekrandan alır. Her yeni ekran ve değişiklik bu
kurallara uyar. Bileşenler `packages/ui-react`, renk ve ölçüler `packages/design-tokens` içindedir; aynı işi yapan
ikinci bir bileşen yazılmaz.

## 1. İlkeler

1. **Önce anlam, sonra süs.** Her ikon, renk ve rozet bir bilgi taşır (tür, durum, alan). Dekoratif öğe eklenmez.
2. **Tek bakışta durum.** Kullanıcı bir hesabın sağlıklı olup olmadığını, varsayılan olup olmadığını ve ne
   yapabileceğini ekranı kaydırmadan görür.
3. **Tutarlılık.** Aynı kavram her ekranda aynı ikon, aynı renk ve aynı sözcükle gösterilir (§4).
4. **Erişilebilirlik.** WCAG 2.2 AA: metin kontrastı ≥ 4.5:1, odak halkası görünür, her etkileşim klavyeyle
   yapılabilir, ikon tek başına anlam taşımaz (yanında metin ya da `aria-label` vardır).
5. **Açık ve koyu tema, masaüstü ve telefon** her ekranda kontrol edilir (§7).

## 2. Sayfa iskeleti

| Bölge | Bileşen | Kural |
|---|---|---|
| Üst çubuk | `AppShell` | Solda logo kapsülü, ortada sekmeli menü (aktif sekme koyu kapsül), sağda dil (bayraklı), bildirim, kullanıcı kartı. |
| Sol şerit | `AppShell` | Tema (güneş/ay), sayfa kısayolları, en altta çıkış. **Her ikonun üzerine gelince ya da klavyeyle odaklanınca adı görünür** (`data-tooltip`). Yeni sayfa eklenince `DEFAULT_NAV_ITEMS`'a ikonuyla eklenir. |
| Sayfa başlığı | `TypeMark` + `h1` + açıklama | Kırıntı (← Ana Sayfa / Tür), birincil eylem sağ üstte tek mavi düğme. |
| Liste + detay | `aih-split` | Solda seçilebilir liste (ikon, ad, alt bilgi, durum noktası), sağda detay. 900 px altında alt alta. |

## 3. Detay ekranı düzeni

Sırasıyla:

1. **`DetailHero`** — büyük tür/sağlayıcı ikonu, hesap adı, alt bilgi (sağlayıcı · sürüm · ortam), durum
   rozetleri (sağlık, varsayılan) ve sağda en fazla 3 eylem. Birincil eylem (ör. **Bağlantı testi**) mavi ve ikonlu,
   diğerleri çerçeveli ve ikonlu.
2. **`InfoTiles`** — her alan bir kutu: renkli ikon, BÜYÜK HARF küçük etiket, değer. Teknik değerler (host, port,
   veritabanı, ön ek) `mono` yazılır.
3. **Bölümler** — `SectionTitle` (ikon + başlık + sağda tarih/sonuç). Bağlantı testi sonucu `StepTimeline` ile,
   sunucu özeti `InfoTiles size="lg"` ile gösterilir.
4. **`ConsolePanel`** — sağlayıcının yönetim arayüzü adresi varsa: "Yeni sekmede aç" ve "Ekranda göster".
5. **Alt eylemler** — geri alınabilir ama dikkat isteyen işler (varsayılan yap, pasifleştir) çizgiyle ayrılmış
   altta durur; onay paneli ister.

## 4. İkon sözlüğü

İkonlar `components/Icon.tsx` içinde, 24×24, `currentColor`, 1.75 çizgi kalınlığında çizilmiştir. Harici ikon
kütüphanesi eklenmez; yeni ikon aynı stille bu dosyaya eklenir.

| Kavram | İkon | Kavram | İkon |
|---|---|---|---|
| Sunucu / host | `server` | Veritabanı | `database` |
| Güvenlik (TLS kapalı) | `shield` | TLS açık | `lock` |
| Kimlik / şifre / ACL | `key` | Anahtar ön eki | `tag` |
| Gönderen adresi | `at` | Son gönderim / gönder | `send` |
| Öncelik / varsayılan | `star` | Zaman aşımı | `timer` |
| Hız sınırı | `gauge` | Son test / süre | `clock` |
| Bağlantı testi başlat | `play` | Düzenle | `pencil` |
| Aktif/pasif | `power` | Bellek / sunucu özeti | `cpu` |
| Bağlı istemci | `users` | Yönetim arayüzü | `monitor` |

Bağlantı adımları: DNS `globe`, TCP/bağlantı `plug`, SMTP karşılama `message`, TLS `lock`, kimlik `key`,
veritabanı seçimi `database`, PING `activity`, sunucu bilgisi `info`. Adım ikonunun köşesinde ✓ (yeşil) ya da
✕ (kırmızı) işareti ve süresi bulunur; hata kodu adımın altında yazılır.

Entegrasyon türleri `type-email`, `type-cache`, `type-queue`, `type-sms`, `type-webhook`, `type-push`,
`type-whatsapp`, `type-storage`; her türün rengi `styles.css` içindeki `--aih-mark-color` ile tanımlıdır.

## 5. Renk ve durum

- Yalnız token kullanılır (`--aih-color-*`); bileşen içinde sabit renk yazılmaz (tür renkleri hariç, tek yerde).
- Durum renkleri: başarılı `success` (yeşil), hata `danger` (kırmızı), uyarı `warning` (amber), bilgi/varsayılan
  `accent` (mavi), pasif `neutral` (gri). Renk tek başına anlam taşımaz; yanında metin ya da ikon vardır.
- Ton: zemin %6–14 tint, ikon/metin tam renk. Dolu renkli büyük alan yalnız birincil düğme ve aktif sekmede.
- **Kutu kenarı = durum rengi.** Sağlığı olan her kart, liste öğesi ve detay paneli `healthClass(tone, ...)` ile
  çizilir: sağlıklı yeşil, hatalı kırmızı, test edilmemiş/lisansı bitmek üzere amber, pasif gri. Kenar rengi her
  zaman aynı kutudaki durum rozetiyle aynıdır.

## 6. Tipografi, boşluk, şekil

- Font sistem yığını (`--aih-font-family`), teknik değerler `--aih-font-mono`.
- Ölçek: sayfa başlığı 2rem/800, detay başlığı 1.375rem/700, bölüm 1rem/700, etiket 0.6875rem/700 büyük harf.
- Boşluk yalnız `--aih-space-*` (4'ün katları). Kart iç boşluğu 24 px, kutular arası 12–16 px, bölümler arası 24 px.
- Köşe: kart 16 px, kutu 10–12 px, düğme/kapsül tam yuvarlak. Gölge yalnız çok hafif (`0 1px 2px`).

## 7. Kontrol listesi (her ekran değişikliğinde)

- [ ] Açık ve koyu temada okunuyor; kontrast AA.
- [ ] 1440 px, 1024 px ve 375 px genişlikte taşma ya da kesik yok; üst menü tek satır (1100 px altında iki satır).
- [ ] Her alan ve adım ikonlu; sol şeritte ad ipucu çıkıyor.
- [ ] Klavyeyle tüm eylemlere ulaşılıyor, odak halkası görünüyor; ikon düğmelerinde `aria-label` var.
- [ ] Boş durum, yükleniyor ve hata durumları tasarlanmış (ne yapılacağını söyleyen metinle).
- [ ] Sır, token ve tam kişisel veri ekranda gösterilmiyor; Viewer rolünde host/kullanıcı maskeli.
- [ ] Testler (`npm test`) ve tip kontrolü (`npm run typecheck`) geçiyor.
