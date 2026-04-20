# Sunmory Padel Club Attendance Dashboard

Aplikasi web Streamlit untuk tracking attendance, stamp loyalty, reward, leaderboard, dan dashboard player Sunmory Padel Club.

## Fitur

- Baca attendance dari Google Sheets tanpa service account via public CSV
- Service account tetap didukung sebagai opsi untuk private Google Sheet
- Data berasal dari Google Form
- Dedup attendance jika kombinasi `player + session_id` sama
- Unique player ID dari nama dan nomor HP
- KPI komunitas, leaderboard, recent activity, chart trend attendance
- Player dashboard dengan search nama atau nomor HP
- Reward milestone:
  - 3 stamp: free drink/snack
  - 5 stamp: diskon session
  - 10 stamp: free 1 session
  - 15 stamp: VIP / priority booking
- Admin insights untuk venue, attendance bulanan, repeat vs new player, dan player yang hampir mencapai reward
- Dummy data otomatis jika Google Sheets kosong atau belum bisa dibaca

## Struktur Project

```text
.
|-- app.py
|-- google_apps_script/
|   `-- Code.gs
|-- pages/
|   |-- admin_insights.py
|   |-- leaderboard.py
|   `-- player_dashboard.py
|-- utils/
|   |-- __init__.py
|   |-- app_data.py
|   |-- data_processing.py
|   |-- google_sheets.py
|   `-- ui.py
|-- .streamlit/
|   `-- secrets.toml.example
|-- requirements.txt
`-- README.md
```

## Struktur Google Sheets

Saran struktur dalam satu file Google Sheets:

- `Form_Responses`: raw data dari Google Form, jangan diedit manual
- `players_db`: database player hasil olahan, bisa dibuat nanti
- `referral_log`: log referral valid/invalid, bisa dibuat nanti
- `reward_log`: log reward yang sudah diclaim, bisa dibuat nanti

Untuk step awal, cukup pakai `Form_Responses` dari Google Form.

Field Google Form yang disarankan:

| Field form | Required | Catatan |
|---|---:|---|
| Name | Ya | Nama player |
| Phone | Ya | Nomor WhatsApp, penting untuk unique player dan referral |
| Venue | Ya | Dropdown venue |
| Date | Ya | Tanggal main |
| Session | Opsional | Pagi/sore/malam atau jam main |
| Referral Code | Opsional | Kode referral kalau ada |

App juga tetap mendukung format internal berikut:

| timestamp | player_name | phone | session_date | venue | session_id |
|---|---|---|---|---|---|
| 2026-04-18 07:00 | Alya Pratama | 081234567801 | 2026-04-18 | Senayan Padel | SPC-20260418-AM |

Catatan:

- `session_date` sebaiknya format `YYYY-MM-DD`
- Kalau `session_id` kosong, app otomatis membuatnya dari `Date + Venue + Session`
- Jika satu player mengisi form dua kali untuk `session_id` yang sama, app hanya menghitung satu attendance
- Referral tidak bisa divalidasi rapi tanpa `Phone`, karena nama player bisa typo atau sama dengan orang lain

## Olah Data ke Sheet Baru

Kalau form tetap cuma berisi `Name`, `Venue`, `Date`, dan `Referral Code`, gunakan Google Apps Script di folder `google_apps_script/Code.gs`.

Cara pasang:

1. Buka Google Sheets response.
2. Rename tab response menjadi `Form_Responses`.
3. Klik `Extensions > Apps Script`.
4. Paste isi `google_apps_script/Code.gs`.
5. Save.
6. Jalankan function `processAttendance` sekali dari Apps Script.
7. Beri permission ketika diminta.
8. Reload Google Sheets.
9. Menu baru `Sunmory > Process Attendance` akan muncul.

Script akan membuat tab:

- `players_db`: total attendance, stamp, last played, venue, reward eligibility
- `referral_log`: referral pertama valid, referral berikutnya dari nama yang sama invalid
- `reward_status`: status reward per player

Catatan penting: karena form tidak punya nomor HP, player dianggap sama berdasarkan nama yang sudah dinormalisasi. Misalnya `sandi bhirama` dan `Sandi  Bhirama` akan dianggap sama, tapi typo seperti `Sandi Birama` akan dianggap player berbeda.

## Setup Tanpa Service Account

Ada dua cara. Pilih salah satu.

### Opsi A: Share sheet ke anyone with the link

1. Buka Google Sheets attendance.
2. Klik `Share`.
3. Ubah General access menjadi `Anyone with the link`.
4. Pilih role `Viewer`.
5. Copy `GOOGLE_SHEET_ID` dari URL:

```text
https://docs.google.com/spreadsheets/d/GOOGLE_SHEET_ID/edit#gid=0
```

6. Copy angka `gid` dari URL. Biasanya `0`.
7. Buat file `.streamlit/secrets.toml` dari contoh `.streamlit/secrets.toml.example`.
8. Isi:

```toml
GOOGLE_SHEET_ID = "isi_google_sheet_id"
GOOGLE_SHEET_GID = "0"
```

### Opsi B: Publish to web sebagai CSV

1. Buka Google Sheets attendance.
2. Klik `File > Share > Publish to web`.
3. Pilih tab attendance.
4. Pilih format `Comma-separated values (.csv)`.
5. Klik `Publish`.
6. Copy URL CSV.
7. Isi `.streamlit/secrets.toml`:

```toml
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/xxx/pub?gid=0&single=true&output=csv"
```

Opsi B biasanya paling stabil untuk dashboard read-only.

## Setup Local

Install dependency:

```bash
pip install -r requirements.txt
```

Buat file secrets local:

```bash
mkdir .streamlit
copy .streamlit\secrets.toml.example .streamlit\secrets.toml
```

Isi `.streamlit/secrets.toml` dengan `GOOGLE_SHEET_ID` + `GOOGLE_SHEET_GID`, atau langsung `GOOGLE_SHEET_CSV_URL`.

Run app:

```bash
python -m streamlit run app.py
```

Jika Google Sheet belum bisa dibaca, aplikasi tetap jalan memakai dummy data.

## Setup Streamlit Community Cloud

1. Push project ini ke GitHub.
2. Buka Streamlit Community Cloud.
3. Create app dari repo GitHub.
4. Main file path: `app.py`.
5. Tambahkan secrets di menu App settings > Secrets.
6. Isi salah satu:

```toml
GOOGLE_SHEET_ID = "isi_google_sheet_id"
GOOGLE_SHEET_GID = "0"
```

Atau:

```toml
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/xxx/pub?gid=0&single=true&output=csv"
```

7. Deploy.

## Optional: Private Sheet dengan Service Account

Kalau nanti sheet mau tetap private, app masih mendukung service account. Isi `[gcp_service_account]` di `.streamlit/secrets.toml` sesuai JSON key Google Cloud, lalu share sheet ke email service account sebagai Viewer.

## Environment Variable Alternative

Selain `st.secrets`, app juga mendukung environment variable:

- `GOOGLE_SHEET_CSV_URL`
- `GOOGLE_SHEET_ID`
- `GOOGLE_SHEET_GID`
- `GOOGLE_SERVICE_ACCOUNT_JSON`, optional untuk private sheet

## Extend ke QR Check-in

Struktur saat ini sengaja dipisah:

- `utils/google_sheets.py` untuk data source
- `utils/data_processing.py` untuk logic attendance, reward, dan leaderboard
- `pages/` untuk UI

Untuk QR check-in ke depan, tambahkan kolom seperti `checkin_method`, `qr_token`, atau `checked_in_by`, lalu prosesnya bisa ditaruh sebagai function baru tanpa mengubah layout utama.
