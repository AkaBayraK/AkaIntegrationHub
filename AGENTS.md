# AGENTS — AKA INTEGRATION HUB

## Çalışma protokolü
- Her iş başlangıcında MASTER_PROMPT.md ve PHASES.md oku.
- Kullanıcı hangi fazı istediyse sadece onu uygula. Önce planı ve etkilenecek dosyaları göster; kritik/geri döndürülemez değişiklikte onay iste.
- Her adımı Türkçe bildir: `[FAZ 04][ADIM 2/7][DEVAM] SMTP adapter kontratı oluşturuluyor`.
- Aşama sonunda: değişen dosyalar, çalıştırılan komutlar, test sonuçları, başarısız testler, açık riskler, sonraki faz, onay bekleniyor.
- Token kullanımını veya CLI limitlerini ancak ortam gerçekten sağlıyorsa göster; aksi halde `ölçülemiyor` yaz.
- Secrets .env.example'da yalnızca placeholder; gerçek sır asla commit edilmez.
- Yeni dependency eklemeden önce lisans, bakım, CVE ve dağıtım etkisini kaydet; SBOM üret.
- CI: lint, format, unit, integration, dependency scanning, license policy, SBOM, container scan.
- Test izolasyonu: tenant A'nın kaynaklarına tenant B erişemez; her API ve UI'da negatif test.
- Idempotency ve concurrency testleri zorunlu: bakiye, bildirim, callback, retry.
- Harici provider için mock/sandbox default; gerçek ücretli gönderim ancak açık onayla.
- Database migration geri alınabilir veya forward-fix stratejisi belgelenmiş olmalı.
- UI responsive, keyboard-accessible, TR/EN, dark/light; host tema tokenları kullanılabilir olmalı.
- Kullanıcının BuildingFlow/TraceFlow repo dosyalarını, entegrasyon fazı onayı olmadan değiştirme.

## Repo taslağı
apps/api, apps/worker, apps/admin-web, packages/ui-react, packages/ts-client, sdk/java, sdk/dotnet, modules/{identity,tenancy,providers,notifications,templates,credits,usage,billing,audit}, infra, docs/{adr,api,security,licenses}, tests.

## Done kriteri
İlgili fazın kabul kriterleri, testleri, dokümantasyonu, güvenlik kontrolleri ve lisans envanteri tamamlanmadan DONE yazma.


## Cache ve dokümantasyon kontrol listesi
- Valkey cache hiçbir zaman finansal defterin veya teslimat durumunun tek kayıt yeri değildir.
- Her cache anahtarı tenant/project scope taşır; cache başarısızlığında güvenli davranış test edilir.
- Her yeni endpoint için OpenAPI şeması, örnek istek/yanıt ve ilgili Java/.NET SDK kullanımı belgelenir.
- Her kullanıcı ekranı için TR/EN kullanım rehberi ve Storybook senaryosu hazırlanır.
- Lisans ve transitive dependency denetimi CI kapısıdır; lisans garantisi verilmez.

## Observability görevi
PHASE-10 çalışmasında `OBSERVABILITY_DESIGN.md` dosyasını oku. Her alt adımı Türkçe konsola yaz, tek alt adım uygula, test et ve onay bekle. Mevcut dosyaları izinsiz ezme.

## V4 OTel Collector
PHASE-10.2 sırasında `OTEL_COLLECTOR_DESIGN.md` belgesini oku; receiver/processor/exporter sinyal ayrımını doğrula. Var olan compose, environment ve auth ayarlarını ezme.

## Öncelikli kalite ve token protokolü (v2 ek)
- Önce `TOKEN_OPTIMIZATION.md`, `PHASE_EXECUTION_PROTOCOL.md` içindeki kısa yürütme kurallarını uygula; ilgili riskte `LICENSE_POLICY.md`, `SECURITY_STANDARDS.md`, `CODING_STANDARDS.md`, `PERFORMANCE_RULES.md` başlıklarına başvur.
- Fazların iş mantığını, mevcut kodu ve mevcut dosyaları koru; eski kurallarla çelişirse daha güvenli, dar kapsamlı ve açık onay gerektiren kural geçerlidir.
- `MASTER_PROMPT.md` ve `PHASES.md` dosyalarını her alt adımda yeniden okumak zorunda değilsin; yalnız ilgili bölümü oku.
- Yeni dependency eklemeden lisans kontrolü ve eşdeğer mevcut çözüm araştırması yap.
- Aynı işlev için mükerrer method, servis, component veya veri erişim katmanı oluşturma.
- Testleri hedefli çalıştır; tüm suite'i yalnız risk gerektirirse çalıştır.
- Türkçe, kısa, gerçek ilerleme ve test sonucu bildir; token sayısı uydurma.

