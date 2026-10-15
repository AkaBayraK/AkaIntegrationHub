# Bağımlılık ve SBOM Politikası

Kaynak kural: kök dizindeki `LICENSE_POLICY.md`. Bu dosya CI'da nasıl uygulandığını tanımlar.

## İzin listesi (otomatik geçer)
Apache-2.0, MIT, BSD-2-Clause, BSD-3-Clause, ISC, PostgreSQL, 0BSD, Unicode-DFS-2016, CC0-1.0, Python-2.0 (yalnızca build).

## İnceleme gerektirir (CI uyarı verir, PR'da gerekçe istenir)
MPL-2.0, EPL-2.0, LGPL-2.1/3.0, CDDL-1.0/1.1, CC-BY-4.0, GPL-2.0-with-classpath-exception.

## Engelli (kullanıcı/hukuk onayı olmadan eklenemez)
GPL-*, AGPL-*, SSPL-*, BUSL-*, FSL-*, RSAL-*, Elastic-2.0, Commons Clause, lisansı belirsiz/`UNKNOWN`.

## CI
- Java: CycloneDX Maven plugin (Apache-2.0) → `target/bom.json`.
- Node: `npm sbom --sbom-format cyclonedx` (npm yerleşik).
- Container: image listesi `infra/docker/compose.yaml`'dan; tarama PHASE-14'te (Trivy, Apache-2.0 — sürüm doğrulanacak).
- SBOM'lar CI artefaktı olarak saklanır. Lisans kapısı script'i PHASE-02'de engelli listeye karşı fail eder;
  PHASE-01'de yalnızca raporlar.
