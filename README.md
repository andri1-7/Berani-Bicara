# BeraniBicara

An open-source AI conversation partner for practicing languages, one conversation at a time.

BeraniBicara bertujuan membantu pengguna berlatih speaking bahasa Inggris dengan respons suara, koreksi yang tidak berlebihan, dan penjelasan bahasa Indonesia. Bahasa lain menjadi pengembangan berikutnya.

## Status

**Implementasi awal, belum siap untuk percakapan AI live.** Fondasi evaluator Python dan kontrak offline sudah tersedia. Aplikasi menggunakan **Rust + Tauri 2 + TypeScript**, menggantikan proposal SwiftUI; lihat [migrasi arsitektur](docs/TAURI-MIGRATION.md). Belum ada model yang lolos benchmark proyek, biaya sesi nyata yang terukur, atau integrasi API berbayar. Nama model dalam plan adalah kandidat, bukan rekomendasi yang sudah tervalidasi.

## Pendekatan yang akan diuji

```text
Mikrofon Mac → Speech-to-text → AI tutor → Text-to-speech → Speaker Mac
```

Pipeline tersebut akan dibandingkan dengan native speech-to-speech jika akses dan anggaran disetujui. Pemilihan akhir didasarkan pada kualitas tutoring, pemahaman aksen, latency end-to-end, dan biaya nyata.

## Prinsip

- Bedakan koreksi grammar wajib dari alternatif gaya yang opsional.
- Jangan mengubah makna pengguna atau menganggap aksen sebagai kesalahan.
- Simpan transkrip asli terpisah dari koreksi; transkripsi mungkin salah.
- Jangan menyebut skor pronunciation valid tanpa evaluasi yang sesuai.
- Tidak menyimpan rekaman secara default.
- API key, rekaman pribadi, dan transkrip pengguna tidak masuk Git atau artifact CI.
- Tidak menjalankan model besar di VPS.

## Rencana dan kontribusi

Lihat [implementation and evaluation plan](docs/PLAN.md). Kontribusi melalui branch dan pull request. Jangan mengirim kredensial, rekaman orang lain tanpa izin, atau hasil benchmark sintetis yang diklaim sebagai pengukuran nyata.

Demo TypeScript dapat diuji dari `app/` dengan `npm ci`, `npm test`, dan `npm run build`. Demo memakai contoh tetap, **bukan mikrofon atau AI live**. Lihat `app/README.md` untuk batasan Tauri dan audio. Workflow offline hanya menguji Python/frontend tanpa API key; hasil build frontend bukan bukti build desktop Mac. Build Rust/Tauri, mikrofon, dan distribusi macOS masih memerlukan verifikasi terpisah. Jangan masukkan kredensial signing ke repository.

## Lisensi

Lisensi proyek belum ditetapkan; MIT adalah usulan yang menunggu persetujuan pemilik. Repository public tidak otomatis memberikan lisensi open-source. Dependency, model, dataset, dan layanan API mengikuti ketentuannya masing-masing.
