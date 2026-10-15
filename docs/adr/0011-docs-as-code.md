# ADR-0011 — Docs-as-code mimarisi

**Durum:** Önerildi · **Faz:** PHASE-00 (iskelet PHASE-01, portal PHASE-16) · **İlgili:** `DOCUMENTATION_PLAN.md`

## Karar
- Tüm dokümantasyon repoda Markdown/MDX olarak, kodla aynı PR'da güncellenir.
- Klasörler: `docs/adr`, `docs/api` (OpenAPI 3.1 kaynağı), `docs/security`, `docs/licenses`, `docs/guides/{tr,en}`,
  `docs/runbooks`, `docs/PHASE_STATUS.md`.
- Portal: `apps/docs` altında Docusaurus 3 (MIT), i18n `tr` (varsayılan) + `en`, sürümlü dokümanlar, Swagger UI
  (Apache-2.0) ile OpenAPI görüntüleme, Mermaid diyagramları. Portal PHASE-16'da kurulur; PHASE-01'de klasör iskeleti
  ve CI'da Markdown link kontrolü başlar.
- CI kapıları (aşamalı): Markdown link kontrolü (PHASE-01), OpenAPI lint (PHASE-02, Spectral MIT — sürüm doğrulanacak),
  SDK örnek derleme (PHASE-09), TR/EN eşlik kontrolü (PHASE-16).
- Her faz `docs/PHASE_STATUS.md`'ye kompakt özet ve changelog girişi ekler.
