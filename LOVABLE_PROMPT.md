# Lovable'a verilecek entegrasyon talimatı

```text
Mevcut ISOV Bridge tasarımını koru ve Python FastAPI backend'e bağla.

Ortam değişkeni:
VITE_API_URL=https://BACKEND-ADRESI

src/lib/api.ts için paylaştığım lovable/api.ts dosyasını kullan.

Giriş ekranında üç rol olsun: öğrenci, akademisyen ve sanayici.
Öğrenci ve akademisyen formunda normal e-posta girilirse
/api/auth/validate-registration endpoint'ini çağır ve .edu.tr hatasını göster.
Supabase girişinden sonra access token ile /api/auth/me çağrısı yap.

Sanayici onboarding ekranında üç profil seçeneği göster:
- Girişimci: entrepreneur
- Ar-Ge merkezi olmayan işletme: company_without_rd
- Ar-Ge merkezi: rd_center

Problem ekranında problem metnini /api/ai/analyze-problem endpoint'ine gönder.
Dönen takip sorularını adım adım göster. Kullanıcı isterse AI yardımını atlayabilsin.

Eşleştir butonunda /api/match endpoint'ini çağır. Sonuç kartında toplam skor,
breakdown ve reasons alanlarını göster. Skoru tek başına göstermeyip nedenlerini de yaz.

“Takım öner” butonunda /api/match/team çağrısı yap ve bir akademisyen ile önerilen
öğrencileri aynı ekip kartında göster.

Sanayici paneline sabit bir AI asistan çubuğu ekle. Mesajı /api/assistant/message
endpoint'ine gönder. intent talent_search ise öğrenci kartları; problem_analysis ise
yapılandırılmış problem ve takip soruları göster.

Üç gizlilik seçeneği sun: open, masked, strict. strict seçildiğinde harici AI
kullanılmadığını kullanıcıya belirt.

Test verilerindeki profillerde “DEMO PROFİL” etiketi göster.
API hata verirse kullanıcıya anlaşılır Türkçe hata mesajı ve yeniden dene butonu göster.
```

