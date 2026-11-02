# Python Kodlama Standartları — Zorunlu

Kapsam: `apps/api`, `apps/worker`, `modules/common` ve bundan sonra eklenecek tüm Python kodu.
Genel kurallar için `docs/standards/CODING_STANDARDS.md`, güvenlik için `docs/standards/SECURITY_STANDARDS.md`,
performans için `docs/standards/PERFORMANCE_RULES.md` geçerlidir; bu belge onları Python'a uyarlar.

Dayanak: PEP 8 (stil), PEP 257 (docstring), PEP 484/604/695 (tipler), OWASP ASVS 4.0 ve OWASP API Security Top 10,
CWE Top 25. Kuralların çoğu araçla zorlanır; araçla zorlanamayanlar PR incelemesinde kontrol edilir.

## 1. Araç zinciri (tamamı ücretsiz ve açık kaynak)

| Araç | Amaç | Lisans | Nerede çalışır |
|---|---|---|---|
| ruff (lint + format) | PEP 8, isort, Bandit (`S`), pylint, karmaşıklık, hata yakalama, ölü kod | MIT | `make lint`, CI |
| mypy `--strict` + pydantic eklentisi | Statik tip kontrolü | MIT | `make lint`, CI |
| import-linter | Modül sınırları (common → app yasak, api ↔ worker bağımsız) | BSD-2-Clause | `make lint`, CI |
| pytest + pytest-asyncio + Testcontainers | Birim ve gerçek PostgreSQL/Valkey/RabbitMQ entegrasyon testleri | MIT / Apache-2.0 | `make test`, CI |
| pytest-cov (coverage.py) | Dal (branch) kapsamı, alt sınır **%85** | MIT / Apache-2.0 | `make test`, CI |
| pip-audit | Python bağımlılıklarında bilinen CVE taraması (PyPI/OSV) | Apache-2.0 | `make audit`, CI |
| Trivy | Dosya sistemi: bağımlılık CVE, gömülü secret, yanlış yapılandırma (Dockerfile/compose) | Apache-2.0 | CI |
| cyclonedx-bom | SBOM üretimi | Apache-2.0 | CI |

Lisans gerektiren ürün (Fortify, Checkmarx, Snyk ücretli, SonarQube Developer+ vb.) projeye bağımlılık olarak
**eklenmez**. Kurumun kendi Fortify/Sonar taraması varsa kod, aşağıdaki §6 eşlemesiyle o taramalardan da temiz
geçecek şekilde yazılır.

Tek komut: `make check` → lint + tip + modül sınırı + test/kapsam + bağımlılık taraması.

## 2. Biçim ve isimlendirme

- Biçimi `ruff format` belirler; elle hizalama yapılmaz. Satır uzunluğu **120**.
- Import sırası: stdlib → üçüncü taraf → proje (`aih_*`); göreli import (`from .x`) **yasak**; wildcard import yasak.
- Her modül `from __future__ import annotations` ile başlar.
- İsimler: modül/paket/fonksiyon/değişken `snake_case`, sınıf `PascalCase`, sabit `UPPER_SNAKE_CASE`,
  özel (modül içi) yardımcı `_onek`. Exception sınıfları `...Error` ile biter (`N818`).
- JSON alanları camelCase ise Python tarafı yine snake_case'dir; dönüşüm Pydantic `alias`/`alias_generator` ile yapılır.
- Boolean fonksiyon/özellik adı `is_`, `has_`, `can_`, `should_` ile başlar.

## 3. Tasarım kuralları

- Katmanlar: `routes.py` (HTTP, doğrulama, DTO) → `service.py` (iş kuralı, transaction) → model/DB.
  Route içinde iş kuralı, service içinde HTTP nesnesi (`Request`, `Response`) olmaz.
- Fonksiyon karmaşıklığı **≤ 10** (`C901`), dal sayısı ≤ 12, `return` sayısı ≤ 6, ifade sayısı ≤ 50.
  Aşılırsa fonksiyonu anlamlı alt adımlara böl (örnek: `providers/smtp/service.py` → `_validate_capability`,
  `_validate_transport_security`).
- Positional parametre **≤ 5** (`PLR0917`). Daha fazlası gerekiyorsa `*` sonrası keyword-only parametre ya da
  `@dataclass(frozen=True)` parametre nesnesi kullan. FastAPI handler'ları bağımlılık enjeksiyonu nedeniyle muaftır.
- Boolean parametre positional olamaz (`FBT001/002`); `*, enabled: bool` şeklinde yaz.
- Sihirli sayı yok (`PLR2004`): `HTTPStatus.*`, `SUBMISSION_PORT = 587` gibi isimli sabit kullan.
- Mutable default argüman yok (`B006`); `None` + içeride oluştur.
- Değişmez veri için `@dataclass(frozen=True)` ya da Pydantic model; dışarıdan gelen veri her zaman Pydantic
  şemasıyla (`extra="forbid"`) doğrulanır.
- Yorum yalnızca "neden"i açıklar; yorum satırına alınmış kod (`ERA001`) bırakılmaz. Public fonksiyonlarda kısa
  Türkçe docstring önerilir.

## 4. Tipler

- `mypy --strict` hatasız geçer. `Any` yalnızca dış sınır (JSON, üçüncü taraf) için, mümkünse hemen daraltılır.
- `# type: ignore` kodlu yazılır (`# type: ignore[attr-defined]`) ve gerekçesi PR'da açıklanır.
- `X | None` kullan (`Optional[X]` değil); koleksiyon tipleri `collections.abc` üzerinden.

## 5. Hata yönetimi ve loglama

- Hatalar `ApiError`/`DomainError` ile `AIH-<ALAN>-<NNN>` koduyla fırlatılır, merkezi handler RFC 9457
  `application/problem+json` döner. 5xx yanıtlarında iç ayrıntı (stack trace, SQL, sağlayıcı ham mesajı) dönmez.
- Çıplak `except:` ve sessiz yutma (`except Exception: pass`) **yasak** (`BLE001`, `S110`). Geniş yakalama yalnız
  sistem sınırında (readiness, yeniden bağlanma döngüsü) ve `# noqa: BLE001 - gerekçe` ile yapılır; hata türü loglanır.
- Yeniden fırlatırken zinciri koru: `raise XError(...) from exc` (`B904`).
- `assert` üretim kodunda **yasak** (`S101`; `python -O` ile silinir). Koşul kontrolü `if ... raise` ile yapılır.
- Log: yalnız `structlog`, olay adı sabit snake_case, değerler key/value (`_log.warning("rabbitmq_connect_failed",
  error=type(exc).__name__)`). f-string/`%` ile log mesajı kurulmaz (`G`). `print` yasak (`T201`; CLI hariç).
- Secret, token, şifre, tam e-posta/telefon loglanmaz; `aih_common.logging.redact_sensitive` anahtar adına göre
  maskeler, yine de hassas değer log çağrısına verilmez.

## 6. Güvenlik — Fortify / Trivy / OWASP eşlemesi

| Bulgu sınıfı (Fortify / CWE) | Kural | Zorlayan |
|---|---|---|
| SQL Injection (CWE-89) | SQLAlchemy ifadeleri ya da `text()` + bind parametresi; string birleştirme/f-string ile SQL yok | ruff `S608`, inceleme |
| Command Injection (CWE-78) | `subprocess` yalnız liste argümanla, `shell=True` yok; `os.system` yok | ruff `S602–S607` |
| Path Traversal (CWE-22) | Kullanıcı girdisinden dosya yolu üretilmez; gerekirse `Path.resolve()` + kök dizin kontrolü | ruff `PTH`, inceleme |
| SSRF (CWE-918) | Dış host'lar `NetworkPolicy` ile doğrulanır: özel/ayrılmış IP, metadata host'ları, izinsiz port reddedilir | `providers/smtp/network.py`, testler |
| Header/CRLF Injection (CWE-113/93) | Header'a giden alanlarda `\r\n\x00` reddedilir | `schemas._strip_single_line` |
| Hardcoded Password/Key (CWE-798) | Kodda ve testte gerçek secret yok; ayar `pydantic-settings` + ortam değişkeni, secret `SecretStore` | ruff `S105–S107`, Trivy secret |
| Weak Crypto / Insecure Random (CWE-327/330) | `md5`/`sha1` güvenlik amaçlı yok; token için `secrets`, şifreleme için `cryptography` | ruff `S303–S324`, `S311` |
| Insecure TLS (CWE-295) | `ssl.create_default_context()`, sertifika doğrulama kapatılmaz | ruff `S501`, `S323` |
| Unsafe Deserialization (CWE-502) | `pickle`, `marshal`, `yaml.load` yok; `json` / Pydantic | ruff `S301`, `S506` |
| XXE (CWE-611) | XML gerekirse `defusedxml` | ruff `S313–S320` |
| Log Forging / Privacy Violation (CWE-117/359) | structlog key/value + maskeleme; ham PII loglanmaz | ruff `G`, inceleme |
| Poor Error Handling (CWE-209/396) | §5 kuralları | ruff `BLE`, `S110`, `TRY` |
| Missing Timeout / DoS (CWE-400) | Her ağ çağrısında zaman aşımı; liste uçlarında `limit` üst sınırı ve cursor pagination | ruff `S113`, `ASYNC`, inceleme |
| Broken Access Control / IDOR (OWASP API1) | Her sorgu `tenant_id` ile filtrelenir; yetki `require(Permission.X)` ile route'ta | negatif testler |
| Vulnerable Components (OWASP A06) | Bağımlılıklar `uv.lock` ile sabit; CVE varsa merge edilmez | pip-audit, Trivy |
| Misconfiguration (OWASP A05) | Prod'da dev-mode kapalı, TLS zorunlu, Mailpit yalnız dev/test | settings doğrulayıcıları, Trivy config |

## 7. Performans ve async

- Async kodda bloklayan çağrı yok (`ASYNC`): `time.sleep`, senkron HTTP/DB, `open()` ile büyük dosya okuma yapılmaz.
- Döngü içinde DB sorgusu yok; toplu sorgu veya `IN (...)` kullan. Listeler sınırlı (`limit ≤ 200`) ve sayfalı.
- Transaction kısa tutulur; dış ağ çağrısı (SMTP, HTTP) transaction içinde yapılmaz.
- Gereksiz kopya/ara liste yok (`PERF`, `C4`); generator ve comprehension tercih edilir.

## 8. Test

- Her iş kuralı için pozitif, negatif ve sınır testi; güvenlik kuralları (SSRF, tenant izolasyonu, yetki) için
  mutlaka negatif test.
- Entegrasyon testleri gerçek servisle (Testcontainers) çalışır; DB mock'lanmaz.
- Toplam dal kapsamı **%85**'in altına düşen değişiklik CI'da kırılır; yeni kod kendi testleriyle gelir.
- Testlerde gerçek secret, gerçek e-posta adresi veya dış ağ çağrısı yok.

## 9. Bağımlılık ekleme

1. Önce mevcut bağımlılıklarla çözülebiliyor mu bak.
2. Lisansı `docs/licenses/LICENSE_POLICY.md`'ye uygun mu (MIT, BSD, Apache-2.0, PSF, MPL-2.0 serbest;
   GPL/AGPL/SSPL/BUSL/ticari **yasak**) kontrol et.
3. Tam sürümle pinle (`==`), `uv lock` çalıştır, `docs/licenses/LICENSE_INVENTORY.md`'ye satır ekle.
4. `make audit` temiz olmalı.

## 10. PR kalite kapısı (hedef ≥ 8,5 / 10)

PR açılmadan önce `make check` yeşil olmalıdır. İnceleme aşağıdaki ağırlıklarla puanlanır; **8,5 altı merge edilmez**.
Güvenlik veya doğrulukta 0 puan alan bir madde varsa toplam puandan bağımsız olarak PR reddedilir.

| Kriter | Ağırlık | Tam puan için |
|---|---|---|
| Doğruluk ve iş kuralı | 2,0 | Gereksinimi karşılar, kenar durumlar ele alınmış |
| Güvenlik | 2,0 | §6 ihlali yok, tenant izolasyonu ve yetki korunmuş, sızıntı yok |
| Test ve kapsam | 1,5 | Pozitif/negatif/sınır testleri var, kapsam ≥ %85 |
| Okunabilirlik ve tasarım | 1,5 | Katman kuralına uyar, karmaşıklık ≤ 10, isimler açık, tekrar yok |
| Hata yönetimi ve loglama | 1,0 | §5 kurallarına uyar |
| Performans | 1,0 | N+1, bloklayan çağrı, sınırsız liste yok |
| Dokümantasyon ve bakım | 1,0 | ADR/doküman/CHANGELOG güncel, migration geri alınabilir |

Kontrol listesi `.github/pull_request_template.md` içindedir.
