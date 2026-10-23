# JDK / Node.js güvenlik sabitlemesi (2026-10)

## JDK — CVE-2026-91403 (ele geçirilmiş eMudhra ara CA sertifikaları)
- Etkilenen: 27.0.1, 25.0.5, 21.0.13, 17.0.21, 11.0.33, 8u512 ve öncesi ([OpenJDK advisory 2026/10/21](https://openjdk.org/groups/vulnerability/advisories/2026-10-21)).
- Yamalı build, `lib/security/blocked.certs` içinde [`infra/security/emudhra-blocked.certs`](../../infra/security/emudhra-blocked.certs) dosyasındaki tüm SHA-256 parmak izlerini içerir.
- Doğrulanan durum (2026-10-23):

| Dağıtım | Sürüm | Durum |
|---|---|---|
| Homebrew `openjdk@21` | 21.0.13.0.2 | yamalı |
| Homebrew `openjdk@25` | 25.0.5.0.2 | yamalı |
| Homebrew `openjdk` | 27.0.1.0.2 | yamalı |
| Temurin | 21.0.13+9, 25.0.5+8 | **yamasız** (48 parmak izi eksik) |

- CI, Temurin 21.0.13'ü kullanır ve `infra/security/emudhra-blocked.certs` listesini JDK'nın blok listesiyle birleştirir; eksik parmak izi kalırsa iş başarısız olur.
- Blok listesi kaynağı: Azul, `https://docs.azul.com/assets/2026-10/emudhra-block-unix.certs`,
  SHA-256 `2596bb6dda83c66d96c5a252d7b2ae1f24cc1ae3f1890223b4f3591a8d52bf10`.
- Temurin yamalı build yayımladığında `java-version` yeni sürüme sabitlenir; birleştirme adımı ancak yeni build'in tüm parmak izlerini içerdiği doğrulandıktan sonra kaldırılır.

Yerel doğrulama:
```bash
comm -23 <(grep -E '^[0-9A-F]{64}$' infra/security/emudhra-blocked.certs | sort -u) \
         <(grep -E '^[0-9A-F]{64}$' "$JAVA_HOME/lib/security/blocked.certs" | sort -u) | wc -l   # 0 olmalı
```

## Node.js
- Yamalı sürümler: 22.23.4, 24.22.1, 26.12.1. 25.x, 23.x ve 20.x öncesi EOL.
- `.nvmrc` ve CI: 22.23.4. `package.json` `engines`: `^22.23.4 || ^24.22.1 || >=26.12.1`.
