# ADR-0009 — Gömülebilir React UI

**Durum:** Önerildi · **Faz:** PHASE-00 (iskelet PHASE-01, uygulama PHASE-08)

## Karar
- `packages/ui-react` → npm paketi `@aka/integration-ui`. Saf React bileşenleri; Next.js'e bağımlı değil
  (`next/*` import yasak), böylece hem App Router host'larında hem bağımsız admin'de çalışır.
- `apps/admin-web` (Next.js) aynı paketi kullanan ince bir kabuktur; iş mantığı içermez.
- Host entegrasyonu tek bir sağlayıcı ile: `<AkaIntegrationProvider adapters={{ auth, locale, theme, navigation, tenant }}>`.
  - `auth.getAccessToken()` → host'un token'ı; bileşen kendi login akışını başlatmaz.
  - `theme` → CSS custom property token'ları (`--aih-color-*`); host kendi token'larını geçirebilir.
  - `locale` → `tr` / `en`; metinler paket içindeki sözlüklerden.
  - `navigation` → host router'ına bağlanan `navigate(path)`.
- **iframe temel çözüm değildir** (MASTER_PROMPT §9).
- Stil: Tailwind ön eki `aih-` + CSS değişkenleri; host stilleriyle çakışmaz. Erişilebilirlik WCAG 2.2 AA hedefi.
- Storybook her ekran için senaryo içerir (PHASE-08/16).
