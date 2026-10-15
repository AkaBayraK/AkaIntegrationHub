# ADR-0004 — Migration aracı: Flyway Community

**Durum:** Önerildi · **Faz:** PHASE-00

## Bağlam
Migration geri alınabilir ya da forward-fix stratejisi belgelenmiş olmalı (AGENTS.md). Araç ürünle birlikte müşteri
ortamına dağıtılacak.

## Karar
- **Flyway Community (Apache-2.0)**, `flyway-core` + `flyway-database-postgresql`, sürüm Spring Boot BOM'undan.
- Dosya adı: `V{YYYYMMDDHHmm}__{aciklama}.sql`, konum `apps/api/src/main/resources/db/migration`.
- Strateji **forward-fix**: yayımlanmış migration değiştirilmez. Her PR'da geri dönüş notu migration başlığında
  `-- rollback:` yorumu olarak yazılır ve gerekirse yeni bir `V…__revert_…` migration'ı ile uygulanır.
- Production'da `spring.jpa.hibernate.ddl-auto=validate`; şema yalnızca Flyway ile değişir.
- Migration yalnızca API uygulaması tarafından çalıştırılır; worker `spring.flyway.enabled=false`.

## Alternatifler
- **Liquibase 5.x:** Maven Central POM'u `FSL-1.1-ALv2` (Functional Source License) beyan ediyor (2026-10-15 doğrulandı).
  Rakip ürün kısıtı içerdiği için ticari SaaS/self-hosted dağıtımda hukuk incelemesi gerektirir → reddedildi.
- Liquibase 4.x (Apache-2.0): bakım sonuna yaklaşan hat; seçilmedi.
