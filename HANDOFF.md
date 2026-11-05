# P1 handoff — 2026-11-05

## Durum
- Manuscript **v3.7**, 19 sayfa, derlenmiş: `main.pdf`.
- Alpha arm **N=109 tam örneklem**; affective arm N=18 BrainVision + N=12 Emotiv.
- 3 bağımsız hakem turu tamamlandı; düzeltmeler işlendi. **Son (4.) ön-gönderim
  kontrolü** `reviews4/` altında.
- GitHub repo (yalnız gerekli dosyalar, veri yok):
  https://github.com/curiousbrutus/EEG-Benchmark
- OSF proje sayfası (kayıtlı ön-kayıt değil): https://osf.io/8wxqj/
- Zenodo DOI: **10.5281/zenodo.23976432** — şu an **404** (rezerve; Zenodo'da
  "Publish" edilmeden çalışmaz). Yayına göndermeden önce aktive et ve makaledeki
  "reserved ... will be activated" cümlesini gerçek DOI linkiyle değiştir.

## Senin incelemen için önemli noktalar
1. **Abstract**: valence tek elektrotta şans; arousal 0.56 sınırda; 4-sınıf 0.34
   (şans 0.25'in üstü, montajın çok altı); beta/EMG caveat; motor arm geçersiz.
2. **Site seçimi**: Fz EC alfa, posterior ortalamanın ~%58'i (aritmetik; geometrik
   ~0.49). Bu, "tek kanalın asıl maliyeti" olarak yazıldı.
3. **0 dB**: retention 0.59 (referans), 0.68 (temiz zincir); "yarıya indiriyor" değil,
   "yaklaşık %40 azaltıyor" olarak oku.
4. **Emotiv**: eşleşmiş N=12'de yüksek-donanım 0.73/0.66/0.61; TOST geçmiyor;
   "eşdeğer" değil "bu örneklemde ayırt edilemedi" deniyor.
5. **Reliability**: r_SB=0.016 kısa pencere stabilitesi; ICC 0.92 blok düzeyi.
6. Yazarlık/afiliasyon, BRM article type ve güncel author guidelines senin kararın.

## Gönderim adımları
- [ ] Zenodo kaydını **Publish** et → DOI'yi doğrula (doi.org).
- [ ] `main.tex` data availability'de rezerve DOI cümlesini gerçek DOI ile değiştir.
- [ ] `bibtex main && latexmk -pdf ...` ile son derleme.
- [ ] BRM'ye yükle: `main.pdf`, `submission/P1_source.zip`, cover letter,
      supplementary, checklist.
- [ ] `SUBMISSION_LOG.md`'ye tarih/ID yaz.

## Follow-up (BrainLink Pro)
- Önce **raw 512 Hz export** testi: BrainJam raw/debug/CSV; yoksa BrainFlow/OpenViBE.
  Sadece 1 Hz eSense varsa P1 benchmark'ıyla doğrudan bağ kurulamaz; B2 planına geçilir.
- NKÜ etik başvurusu (bağımsız araştırmacı) + akademisyen işbirliği.
- OSF'te **kayıtlı** yeni bir ön-kayıt (bu proje değil, ayrı registration) aç.
- Protokol taslağı: N=12–15, 2 oturum, 2 dk EO / 2 dk EC / 2 dk müzik; raw + eSense;
  P1 pipeline + Fp1 simülasyonu karşılaştırması.

## Bilinen kalan limitasyonlar (makalede yazılı)
- Gerçek tek kanallı cihaz ölçülmedi (brainlink follow-up'ın konusu).
- Beta/EMG mekanizması test edilmedi.
- Plan kayıtlı değil (OSF proje sayfası, registration değil).
- IAPS etiketleri katılımcı rating'i değil; picture-level generalizasyon test edilmedi.

## Final pre-submission review (2026-11-05)
- **Domain review**: Major revision — fixed: same-dataset precedent engagement (Sánchez-Reolid 2022),
  Fz-vs-frontal site caveat, Hagemann reference/site literature, Ratti misattribution, 99.99%
  caveat, numeric typo.
- **Statistics review**: Major revision — fixed: 50% rule baselines (same-site chain vs clean
  chain), added blink/combined rows, `pre-registered` → `pre-specified`, stale N=30 values,
  valence "no significant evidence" wording, site-sweep BH, band-vs-quant contrast,
  PREREG updates, Emotiv alignment fields.
- **EIC quick check**: Minor revision — fixed: retention interval traced to
  `results/site_metrics.json`, dead DOI removed from manuscript/cover (assigned on acceptance),
  affective provenance sentence added, arousal family clarified.
- Two final reviewers (reproducibility, devil's advocate) failed at the tool level; their
  concerns were already covered by the completed domain/statistics/EIC checks and earlier rounds.

## Before upload
- [ ] **Zenodo**: publish the deposit and activate 10.5281/zenodo.23976432; then either add the
      live DOI or keep "assigned on acceptance" as currently written.
- [ ] Rebuild (`latexmk -pdf main.tex`), read the PDF, submit with `submission/P1_source.zip`.
- [ ] Optional: update the OSF project description to the final abstract.
