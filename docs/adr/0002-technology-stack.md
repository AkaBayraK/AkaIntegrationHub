# ADR-0002 — Teknoloji yığını ve sürüm pinleri

**Durum:** Önerildi · **Faz:** PHASE-00 · **Doğrulama tarihi:** 2026-10-15

## Karar
Sürümler resmi kaynaklardan (Maven Central metadata, npm registry, Docker registry) okunmuştur. Otomatik "en yeni"
yükseltme yapılmaz; yükseltmeler ayrı PR ve lisans kapısı ile yapılır.

| Katman | Seçim | Sürüm | Lisans (SPDX) | Kaynak |
|---|---|---|---|---|
| Dil (backend) | Java (bytecode hedefi) | 21 (`--release 21`) | GPL-2.0-with-classpath-exception (JDK) | MASTER_PROMPT |
| Framework | Spring Boot | 4.1.1 | Apache-2.0 | Maven Central |
| DB migration | Flyway Community | Spring Boot BOM | Apache-2.0 | ADR-0004 |
| OpenAPI | springdoc-openapi | 3.x (Boot 4 hattı) | Apache-2.0 | PHASE-01'de pinlenir |
| Veritabanı | PostgreSQL | 17.6 | PostgreSQL | Docker Hub `postgres:17.6-alpine` |
| Cache | Valkey | 8.1.4 | BSD-3-Clause | Docker Hub `valkey/valkey:8.1.4-alpine` |
| Broker | RabbitMQ | 4.1.4 | MPL-2.0 | Docker Hub `rabbitmq:4.1.4-management-alpine` |
| Dev mail | Mailpit | v1.27.10 | MIT | Docker Hub `axllent/mailpit:v1.27.10` |
| Kimlik (opsiyonel) | Keycloak | 26.4.1 | Apache-2.0 | quay.io |
| Web | Next.js / React | 16.4.1 / 19.x | MIT | npm |
| Stil | Tailwind CSS | 4.x | MIT | npm |
| Docs | Docusaurus | 3.x | MIT | npm (PHASE-16; iskelet PHASE-01) |
| Test | JUnit 5, Testcontainers, Vitest | BOM / 2.x / 5.x | EPL-2.0 / MIT / MIT | |

## Notlar
- Yerel geliştirme makinesinde JDK 25 kuruludur; derleme `maven.compiler.release=21` ile Java 21 bytecode üretir.
  CI Temurin 21 kullanır. JDK 21 yerelde kurulursa birebir eşleşir.
- **Java 21 seçimi:** MASTER_PROMPT gereği. SDK'lar Java 21 müşterilerinde çalışmalı; API de aynı baseline'da tutulur.
- **RabbitMQ MPL-2.0:** dosya bazlı zayıf copyleft. Değiştirilmemiş resmi image'ı ayrı servis olarak çalıştırmak
  kapalı kaynak ürün kodunu etkilemez; image'ı yeniden dağıtırken NOTICE/kaynak bağlantısı verilmelidir. Hukuk teyidi önerilir.
- **EPL-2.0 (JUnit):** yalnızca test kapsamı, ürünle dağıtılmaz.

## Alternatifler
- Spring Boot 3.5.x: OSS desteği 2026 ortasında bitiyor; yeni ürün için 4.x hattı seçildi.
- Liquibase: 5.x sürümü FSL-1.1-ALv2 lisanslı (bkz. ADR-0004) → reddedildi.
