# Aka Integration Hub

**Connect · Notify · Automate** — BuildingFlow, TraceFlow, AkaAI ve bağımsız Java/.NET uygulamaları için multi-tenant,
SaaS veya self-hosted çalışan entegrasyon ve bildirim platformu.

> Durum: **PHASE-01 (Foundation & Branding)**. Faz planı: [PHASES.md](PHASES.md) · Durum: [docs/PHASE_STATUS.md](docs/PHASE_STATUS.md)

## Hızlı başlangıç
Gereksinimler: Docker, JDK 21+ (derleme `--release 21`), Maven 3.9+, Node 22+.

```bash
make up            # PostgreSQL, Valkey, RabbitMQ (.env yoksa .env.example'dan oluşturur)
make api           # API      → http://localhost:28080  (health: http://localhost:28081/actuator/health)
make worker        # Worker   → health: http://localhost:28091/actuator/health
npm install && npm run build && make web   # Admin    → http://localhost:28030
make up-mail       # + Mailpit (yalnız dev) → http://localhost:28025
make test          # backend testleri (Testcontainers, Docker gerekir)
```
Portlar BuildingFlow/TraceFlow ile çakışmaması için 2xxxx bloğundadır; `.env` ile değiştirilebilir.

## Yapı
| Yol | İçerik |
|---|---|
| `apps/api` | Spring Boot 4.1 API (Java 21), Flyway, health/readiness, problem details |
| `apps/worker` | Asenkron gönderim worker'ı (RabbitMQ) |
| `modules/common` | Ortak çekirdek (correlation id) |
| `apps/admin-web` | Next.js 16 bağımsız yönetim konsolu |
| `packages/ui-react` | `@aka/integration-ui` — host uygulamalara gömülebilir React bileşenleri |
| `packages/design-tokens` | Marka renkleri, aralıklar, light/dark CSS değişkenleri |
| `infra/docker` | Lokal Docker Compose |
| `docs` | ADR, lisans envanteri, tehdit modeli, rehberler, marka kılavuzu |

## Dokümantasyon
- Mimari kararlar: [docs/adr](docs/adr/README.md)
- Başlangıç rehberi: [TR](docs/guides/tr/getting-started.md) · [EN](docs/guides/en/getting-started.md)
- Marka kılavuzu: [docs/brand/BRAND_GUIDE.md](docs/brand/BRAND_GUIDE.md)
- Lisanslar: [docs/licenses/LICENSE_INVENTORY.md](docs/licenses/LICENSE_INVENTORY.md)
