# P1 — Single-channel and low-cost EEG: what it can and cannot measure

**Manuscript repository.** Source, analysis code, generated figures/tables and the JSON
files behind every number. Raw data are not included; download instructions are below.
Compiled manuscript: `main.pdf`.

**Links:** [OSF project](https://osf.io/8wxqj/) ·
[Zenodo DOI (reserved, activate before submission)](https://doi.org/10.5281/zenodo.23976432) ·
[GitHub](https://github.com/curiousbrutus/EEG-Benchmark)

---


**Status:** draft **v3.6** (2026-11-03) — full N=109 alpha arm; round-3 fixes applied; submission package ready.
**Owner:** Eyyüb Güven · **Branch:** paper production
**Target venue (verify before submission):** *Behavior Research Methods*.

## Ne iddia ediyoruz (tek paragraf)

Düşük maliyetli EEG cihazlarıyla yapılan "dikkat/rahatlama/duygu" iddiaları, kaydın o
iddiayı destekleyip desteklemediğini gösteren bilgiyle birlikte raporlanmıyor. Açık çok
kanallı kayıtları tek kanallı tüketici koşullarına indirgeyen **tekrarlanabilir bir
bozulma benchmark'ı** kuruyoruz ve hangi analizlerin ayakta kaldığını ölçüyoruz. Sonuçlar
koşullu: alfa reaktivitesi edinim zincirinden neredeyse hiç etkilenmiyor (**%99.99**,
site-eşleşmeli), ama **elektrot seçimi** EC alfa gücünün ~%42'sine mal oluyor; gürültü
etkiyi monoton olarak azaltıyor (0 dB'de referansın ~0.59'u). Duygu dekodlamada tam
montaj şansın üstünde (valence 0.69), tek elektrotta valence şansa düşüyor (0.52),
arousal zayıf kalıyor (0.56, düzeltme sonrası sınırda). Ayrıştırma, tam-montaj
avantajının bir kısmının beta bandında (muhtemelen EMG) olduğunu ve hiçbir tek sitein
valence'i kurtarmadığını gösteriyor. Katkı: yöntem + ayrıştırma + karar matrisi +
tekrarlanabilirlik; cihaz validasyonu değil.

## Analiz durumu (v3.2, N=109)

| Analiz | Sonuç | Yorum |
| :--- | :--- | :--- |
| Alfa — tam montaj | 0.91 [0.78, 1.04] | referans |
| Alfa — Fz tek kanal zinciri | 0.77 [0.65, 0.89] | naive kıyas (site karışık) |
| **Alfa — edinim zinciri, site-eşleşmeli** | **−0.0001 log → %99.99 korundu** [0.9996, 1.0001] | kanal/Hz/kuantizasyon/bant sorun değil |
| **Alfa — elektrot sitesi maliyeti** | Fz EC alfa / posterior **0.58** [0.52,0.63] | tek kanalın asıl maliyeti site seçimi |
| Gürültü 20/10/5/0 dB | 0.76 / 0.71 / 0.60 / 0.38; geometrik koruma 0.86/0.82/0.73/0.59 | monoton; BH-q < 0.001 |
| Blink 5/15/30/dk | 0.77 / 0.77 / 0.77 | artımlı etki −0.002 log; model kontrolü |
| **Duygu — tam montaj (N=18)** | valence **0.69** · arousal **0.68** · 4-sınıf 0.58 | şansın üstünde |
| **Duygu — tek kanal (Fz)** | valence **0.52** (şans) · arousal 0.56 (q≈0.05) · 4-sınıf 0.34 | valence şans |
| **Ayrıştırma (N=18)** | tek site Fz/Cz/Pz/Oz: valence 0.51–0.53, 4-sınıf 0.33–0.38 | hiçbiri montaja yaklaşmıyor |
| **Bant kontrolü (N=18)** | theta+alpha-only 0.60/0.46; beta-only 0.70/0.62 | montaj avantajı kısmen beta |
| **Emotiv 14ch (N=12)** | valence 0.67 · arousal 0.71 · 4-sınıf 0.56; eşleşmiş yüksek-donanım 0.73/0.66/0.61 | benzer ama **TOST eşdeğerliği yok** |
| Motor dekodlama | N=10: referans bile şans (0.54 [0.46,0.62]) | **geçersiz** |
| Short-lag stabilite (N=109) | 0.016 [−0.08, 0.11] | kısa pencere; güvenilirlik katsayısı değil |
| Blok ICC(2,1) (N=10) | 0.92 (CI yok) | kararlı bireysel fark |

Veri setleri: EEGBCI (PhysioNet; 109 denek) + Zenodo 14787743 (BrainVision + Emotiv;
CC BY 4.0). DEAP kullanılmadı (site kapalı); DREAMER restricted.
Ham çıktı: `results/*.json`; tablolar `tables/*.tex` (`scripts/28_make_tables.py`).

## Links
- OSF project (unregistered project page): https://osf.io/8wxqj/
- GitHub: https://github.com/curiousbrutus/EEG-Benchmark
- Zenodo DOI: 10.5281/zenodo.23976432 (reserved; activate before submission)

## Submission
`submission/` içinde cover letter, supplementary, source zip, checklist. Üçüncü hakem
turu raporları `reviews3/`'te; bulgularının tamamı v3.x'e işlendi (kalan: public DOI,
nihai proofread).

## Reproduce
```bash
python scripts/00_download_zenodo.py
python scripts/01_download.py --subjects 109 --runs 1 2
python scripts/run_all.py --subjects 109
```
