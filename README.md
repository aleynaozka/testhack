# ISOV Bridge — Lovable + Python Demo Backend

Bu paket, Lovable ile hazırlanan frontend'in bağlanabileceği Git-uyumlu FastAPI backend'idir.
Test verisiyle anahtar olmadan çalışır; `GEMINI_API_KEY` eklenince problem analizi ve doğal
dille öğrenci arama katmanında Gemini kullanır. Nihai eşleştirme puanını her zaman kontrollü
Python motoru hesaplar.

## İçerik

- Üç sanayici profili: `entrepreneur`, `company_without_rd`, `rd_center`
- `.edu.tr` öğrenci/akademisyen kayıt kontrolü
- Supabase e-posta onaylı oturumu backend'de doğrulayan `/api/auth/me`
- Sanayici doğrulaması için değiştirilebilir `pending/verified/rejected` akışı
- AI destekli problem yapılandırma ve soru üretme
- Akademisyen ve öğrenci için açıklanabilir ağırlıklı eşleştirme
- Doğal dilde öğrenci arama asistanı
- AI yoksa çalışan yerel kural motoru
- 8 kurgusal akademisyen, 10 kurgusal öğrenci ve 6 sanayi problemi
- Lovable için hazır TypeScript API istemcisi
- Supabase profil tablosu ve `.edu.tr` veritabanı kontrolü

> `data/candidates.json` içindeki bütün kişiler test verisidir. Gerçek kişi gibi sunulmamalıdır.

## Klasör yapısı

```text
app/
  main.py                 FastAPI endpoint'leri
  schemas.py              İstek modelleri
  services/
    analyzer.py           Problem analizi ve sanayiciye göre sorular
    matching.py           Kontrollü eşleştirme puanı
    talent.py             Doğal dilde öğrenci arama
    auth.py               E-posta ve Supabase token doğrulaması
    ai.py                 Opsiyonel Gemini bağlantısı
data/
  candidates.json         Test akademisyen/öğrenciler
  problems.json           Test problemleri
lovable/api.ts            Lovable frontend bağlantısı
tests/test_core.py        Otomatik çekirdek testleri
supabase_profiles.sql     Supabase profil ve RLS kurulumu
```

## Yerelde çalıştırma

Python 3.11 veya 3.12 önerilir.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000 --env-file .env
```

Windows PowerShell aktivasyonu:

```powershell
.venv\Scripts\Activate.ps1
```

Tarayıcıdan:

- Swagger test ekranı: `http://localhost:8000/docs`
- Sağlık kontrolü: `http://localhost:8000/health`

`.env` dosyası otomatik yüklenmiyorsa değişkenleri dağıtım platformunun Secrets/Environment
bölümüne ekleyin. Üretimde önerilen yöntem de budur.

## Otomatik test

Ek test paketi gerektirmez:

```bash
python -m unittest discover -s tests -v
```

Testler; `.edu.tr` kuralını, farklı problemlerin farklı kişileri önermesini, takım
eşleştirmesini, doğal dilde öğrenci aramayı ve JSON test verilerini kontrol eder.

## Önemli endpoint'ler

| Endpoint | Görev |
| --- | --- |
| `GET /health` | Sunucu, Gemini ve Supabase yapılandırma durumu |
| `GET /api/demo/candidates` | Test adaylarını listeler |
| `GET /api/demo/problems` | Test problemlerini listeler |
| `POST /api/auth/validate-registration` | Rol ve `.edu.tr` kontrolü |
| `GET /api/auth/me` | Supabase Bearer token ve e-posta onayı kontrolü |
| `POST /api/auth/industry-verification` | Sanayici doğrulama başvurusunu kontrol eder |
| `POST /api/ai/analyze-problem` | Problemi yapılandırır ve takip soruları üretir |
| `POST /api/match` | Akademisyen veya öğrenci eşleştirir |
| `POST /api/match/team` | Akademisyen + öğrenci takım önerir |
| `POST /api/ai/talent-search` | Doğal dille öğrenci arar |
| `POST /api/assistant/message` | Mesajı problem analizi veya aday aramasına yönlendirir |

### Örnek eşleştirme isteği

```json
POST /api/match
{
  "problem_text": "Tekstil atık suyunda membran ve adsorpsiyonla renk giderimini artırmak istiyoruz.",
  "target_role": "academic",
  "industry_type": "company_without_rd",
  "top_k": 3,
  "ai_mode": "local",
  "confidentiality": "masked"
}
```

`ai_mode` seçenekleri:

- `local`: AI çağrısı yapmaz; tamamen deterministik çalışır.
- `auto`: Anahtar varsa Gemini, hata veya anahtar yoksa yerel motor.
- `gemini`: Gemini zorunludur; hata olursa 503 döner.

`confidentiality` seçenekleri:

- `open`: Metin AI'ya gönderilebilir.
- `masked`: Teknik sayılar ve ekipman adları maskelendikten sonra gönderilir.
- `strict`: Harici AI çağrısı yapılmaz; yerel motor çalışır.

## Gemini ekleme

Dağıtım platformuna şu gizli değişkenleri ekleyin:

```text
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-3.6-flash
```

API anahtarını Lovable'a, `VITE_` değişkenine veya GitHub'a koymayın. Anahtar yalnızca
Python backend'de bulunmalıdır.

## Supabase doğrulaması

1. Supabase SQL Editor'da `supabase_profiles.sql` dosyasını çalıştırın.
2. Supabase Auth içinde e-posta doğrulamasını açık tutun.
3. Backend ortam değişkenlerine `SUPABASE_URL` ve publishable/anon key ekleyin.
4. Lovable, girişten aldığı access token'ı `/api/auth/me` isteğine gönderir:

```http
Authorization: Bearer SUPABASE_ACCESS_TOKEN
```

Backend, Supabase Auth kullanıcısını sorgular ve `email_confirmed_at` yoksa erişimi reddeder.
`service_role` anahtarı frontend'e veya bu demo endpoint'ine gerekmez.

Sanayici doğrulaması henüz kesinleşmediği için kod şu yöntemleri destekleyecek şekilde ayrıldı:
Google OAuth, iş e-postası, manuel inceleme ve Ar-Ge merkezi belgesi. Gerçek doğrulama sağlayıcısı
seçildiğinde sadece bu servis değiştirilir.

## Lovable bağlantısı

1. `lovable/api.ts` dosyasını Lovable projenizde `src/lib/api.ts` içine alın.
2. Lovable ortam değişkenine yayınlanmış backend adresini ekleyin:

```text
VITE_API_URL=https://YOUR-BACKEND.example.com
```

3. Backend'deki `CORS_ORIGINS` değişkenine Lovable preview ve production adreslerini ekleyin:

```text
CORS_ORIGINS=https://preview.example.com,https://project.lovable.app
```

Canlı ortamda `CORS_ORIGINS=*` ve `allow_credentials=True` kombinasyonunu kullanmayın.

## GitHub'a gönderme

Bu klasörün içindeyken:

```bash
git init
git add .
git commit -m "ISOV Bridge demo backend"
git branch -M main
git remote add origin https://github.com/KULLANICI/REPO.git
git push -u origin main
```

`.env` dosyası `.gitignore` içindedir. API anahtarlarının commit edilmediğini GitHub'a
göndermeden önce mutlaka kontrol edin.

## GitHub'dan dağıtma

Replit, Render veya Railway üzerinde GitHub reposunu içe aktarın ve başlangıç komutunu girin:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Docker destekleyen bir platformda repodaki `Dockerfile` doğrudan kullanılabilir. Dağıtım
tamamlandıktan sonra `/health` ve `/docs` adreslerini açarak backend'i kontrol edin.

## Demo sırası

1. `/api/demo/problems` içinden bir problem seçin.
2. `/api/ai/analyze-problem` ile yapılandırın.
3. `/api/match` ile akademisyenleri puanlayın.
4. `/api/match/team` ile akademisyen + öğrenci takımı gösterin.
5. `/api/ai/talent-search` ile “İTÜ Makine 4. sınıf SolidWorks bilen stajyer bul” sorgusunu deneyin.
6. Aynı akışı Lovable arayüzündeki kartlara bağlayın.
