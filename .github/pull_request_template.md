## Özet
<!-- Ne değişti, neden? İlgili faz / ADR. -->

## Test
<!-- Çalıştırılan komutlar ve sonuçları. Yeni testler. -->

## Kalite kapısı (docs/standards/PYTHON_CODING_STANDARDS.md §10, hedef ≥ 8,5)
- [ ] `make check` yeşil (ruff, mypy --strict, import-linter, pytest + kapsam ≥ %85, pip-audit)
- [ ] Web değişikliği varsa `npm run typecheck && npm test && npm run build` yeşil
- [ ] Güvenlik: tenant filtresi, yetki kontrolü, SSRF/injection, secret ve PII sızıntısı kontrol edildi
- [ ] Yeni iş kuralı için pozitif, negatif ve sınır testleri eklendi
- [ ] Yeni bağımlılık yok ya da lisansı uygun, pinlendi ve `LICENSE_INVENTORY.md` güncellendi
- [ ] Migration varsa geri alınabilir ve mevcut veriyi korur
- [ ] Doküman / ADR / CHANGELOG güncellendi
