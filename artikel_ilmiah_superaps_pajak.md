# Judul: Implementasi Sistem Pajak Pintar "SUPERAPS-PAJAK" Berbasis Optical Character Recognition (OCR) dan Web Scraping pada Dinas Kominfotik Provinsi Bengkulu

## Abstrak
Pengelolaan pajak kendaraan bermotor yang transparan dan cepat adalah tonggak penting dalam pelayanan publik pemerintah daerah. Artikel ini membahas pengembangan "SUPERAPS-PAJAK", sebuah sistem cerdas (smart system) terintegrasi berbasis microservices yang memanfaatkan Optical Character Recognition (OCR) dengan EasyOCR dan teknologi Web Scraping tingkat lanjut. Sistem dibangun secara modular dengan memisahkan antarmuka pengguna berbasis Laravel dan microservice pemrosesan berbasis FastAPI. Secara khusus, penelitian ini menyajikan alur prapemrosesan citra adaptif dan mekanisme koreksi karakter heuristik yang dioptimalkan untuk plat nomor kendaraan di Provinsi Bengkulu (kode plat "BD"). Pendekatan scraping menggunakan curl_cffi juga digunakan untuk melewati proteksi keamanan (Web Application Firewall) pada sistem repositori informasi pajak PUSAKO, mengekstraksi data relasional dan memetakannya secara mulus dengan proses OCR. Hasil pengujian menunjukkan rata-rata akurasi plat valid bisa mencapai 85-95% pada pencitraan terkontrol dengan jeda pemrosesan 2 sampai 5 detik pada perangkat eksekusi sentral komputasi (CPU processing).

Kata Kunci: OCR, EasyOCR, Web Scraping, Microservices, Pajak Kendaraan, Bengkulu. 

---

## 1. Introduction (Pendahuluan)

### 1.1 Latar Belakang
Pajak Kendaraan Bermotor (PKB) merupakan salah satu sumber utama Pendapatan Asli Daerah (PAD) yang krusial bagi pelumasan roda pembangunan infrastruktur dan pelayanan publik. Di era transformasi digital pemerintahan modern, optimalisasi penerimaan pajak menuntut adanya sistem administrasi yang efisien, transparan, cepat, dan serba otomatis. Di lingkungan Provinsi Bengkulu, inisiatif Dinas Komunikasi, Informatika, dan Statistik (DISKOMINFOTIK) dalam merancang ekosistem pemerintahan yang kohesif kerap berbenturan dengan hambatan operasional teknikal. Proses pengawasan dan identifikasi ketaatan pajak masyarakat di lapangan—seperti pada saat operasi penertiban gabungan—saat ini masih banyak yang mengandalkan pengecekan secara manual. Petugas di lapangan diwajibkan menginput nomor pelat satu per satu dengan mengetikkan kueri pada peranti mereka ke dalam basis data sistem informasi portal PUSAKO (Pusat Layanan Samsat). Rutinitas ini tidak hanya lambat dan memecah konsentrasi, namun juga memperlebar marjin *human-error* (kesalahan tik) yang berakibat pada kegagalan penemuan data wajib pajak.

### 1.2 Permasalahan
Tantangan utama dalam mewujudkan otomatisasi terpusat mencakup rintangan komputasi visual (Computer Vision) dan friksi integrasi inter-sistem. Permasalahan pertama adalah bagaimana meminimalisasi atau menyalurteruskan (*bypass*) inputan preskriptif manual tersebut ke dalam mekanisme pemindaian (scanning) yang sepenuhnya otomatis; dimana hanya berbekal tangkapan piksel dari kamera ponsel, sistem dapat mengekstrak string plat nomor yang sah di berbagai cuaca pencahayaan serta ragam modifikasi ketebalan *font* yang sering ditemui pada pelat kendaraan Indonesia. Permasalahan kedua bersinggungan dengan kapabilitas integrasi data sistem informasi lokal PUSAKO. Portal perpajakan PUSAKO diketahui tidak menyediakan *Application Programming Interface* (API) terbuka untuk pertukaran data B2B/B2G secara reguler. Selain itu, upaya menjembataninya dengan teknik ekstraksi data paksa (*spidering*/bot) selalu dimentahkan karena portal PUSAKO diproteksi secara ekstensif menggunakan gerbang rekayasa *Web Application Firewall* (WAF) mutakhir, sehingga skrip *request* HTTP standar selalu tertolak.

### 1.3 Tujuan dan Kontribusi Peneliti
Berangkat dari divergensi permasalahan tersebut, penelitian ini bertujuan untuk merancang, mengusulkan, dan mengimplementasi sebuah ekosistem piranti lunak inovatif multi-cabang yang dijuluki "SUPERAPS-PAJAK". Kontribusi ilmiah dan rekayasa perangkat lunak utama dari arsitektur ini memeluk penerapan landasan *microservices* asinkron. Beban interaksi antarmuka presentasional atau *Frontend/Backend logic* diarahkan murni pada ekosistem Laravel 10.x. Sementara itu, beban pemrosesan *Machine Learning* dan *fetching* jaringan yang berat didelegasikan murni ke layanan mandiri tersendiri (microservice) berbahan bakar FastAPI (Python 0.109.0). 

Penawaran dari microservice yang dirancang ini membawakan dua modul pintar, yakni: 
1. **Pipa OCR Tematik dan Heuristik**: Mengawinkan metode pra-pemrosesan citra lapis ganda, *engine deep learning* EasyOCR, dan aturan substitusi perbaikan otomatis (*Rule-Based Regex Correction*) yang dilatih khusus menyempurnakan kegagalan *engine* saat memprediksi prefiks kode wilayah lokal "BD" (Bengkulu) serta nomenkaltur wilayah Indonesia lainnya.
2. **Detasemen Anti-Scraping WAF**: Mengintegrasikan antarmuka modul *curl_cffi* dengan metodologi penyamaran lalu-lintas jaringan (*TLS fingerprinting impersonation*) agar *request* ekstraksi diakui secara valid selayaknya *browser* asli oleh *firewall* PUSAKO; menjamin ketersediaan aliran data perpajakan secepat kilat menjadi format *JavaScript Object Notation* (JSON) yang mudah diolah.

---

## 2. Method (Metode Penelitian)

### 2.1 Arsitektur Sistem (Microservices & Clean Architecture)
Metodologi perancangan perangkat lunak yang diusung menggunakan kerangka Clean Architecture di lingkungan Microservice. Layanan spesialis Machine Learning (ML Service) beroperasi sebagai pemroses berat asinkron terpisah sehingga backend klien (Laravel) tidak menerima beban bottleneck. Arsitektur ini terbagi menjadi 4 lapisan utama:
1. API Layer (app/api/): Menangani routing HTTP protocol dan membungkus permintaan (requests) dan respons (responses) JSON.
2. Service Layer (app/services/): Pusat logika bisnis komputasi (OCR processing dan data web scraping). Bagian ini berjalan independen (pure Python logic) dengan abstraksi dari HTTP spesifik framework.
3. Schema / Data Layer (app/schemas/): Melaksanakan pengetatan aturan validasi struktur data via librari Pydantic. Menjamin ketahanan dan serialisasi model.
4. Core Layer (app/core/): Memanajemen environment configuration dan Autentikasi Keamanan antar server secara injeksi dependensi menggunakan X-API-Key.

### 2.2 Pipeline Pre-Processing Citra
Untuk memaksimalkan EasyOCR dalam memetakan karakter piksel menjadi string, sebuah pipeline image preprocessing khusus dibangun memanfaatkan pustaka OpenCV dan Pillow:
1. Brightness Analysis: Evaluasi intensitas cahaya berbasis hitungan piksel gambar.
2. Adaptive Contrast Enhancement (1.5x): Meningkatkan penyesuaian kontras gambar yang mendapati underexposed.
3. Sharpness Enhancement (2.0x): Filter kernel diimplementasikan untuk meningkatkan tingkat detail ujung objek tipografi karakter dengan margin penguatan numerik ketajaman citra.
4. Denoising (Non-local Means Denoising): Penyaringan noise/grain (bintik acak) hasil performa kamera minim cahaya namun tetap menjaga edges (tepian huruf).
5. Grayscale Conversion: Reduksi latensi model dengan input dimensi saluran ganda ke saluran matriks keabuan.

### 2.3 Optmilisasi Mesin OCR dan Aturan Koreksi Heuristik
Pemrosesan Optical Character Recognition ditenagai oleh EasyOCR menggunakan infrastruktur tensor PyTorch. Diketahui ada variasi kesamaan vizual karakter abjad versus nomor, maka dari itu sebuah algoritma aturan berbasis konteks (Rule-based correction) tertanam pada service:
- Kontekstual Substitusi Angka di Segmen Numerik:
    - 0 ↔ 8 (Dikoreksi menjadi 8, jika bentuk geometri ambigu atau menjadi 0 tergantung probabilitas dan posisi seri kuota angka).
    - I ↔ 1 (Huruf I yang tak sengaja terkeluarkan engine di segmen angka otomatis dipulihkan menjadi "1").
    - O ↔ 0 (O dirubah menjadi nol dalam format empat angka pusat struktur plat).
- Penghapusan Noise Region: Koreksi kebisingan spasi dan pembatas tepi seperti string hasil OCR "IBD" yang otomatis dinaturalisasikan menjadi prefix plat yang sah "BD".
- Pattern Matching (Regular Expression): Menyaring keluaran yang valid, struktur nomor kepolisian kendaraan Indonesia diverifikasi wajib sepadan dengan format [1-2 Huruf Regional] [1-4 Angka Seri] [1-3 Huruf Suffix].

### 2.4 Metode Web Scraping dengan Detasemen WAF
Penarikan informasi sub-domisil situs portal pajak resmi milik daerah PUSAKO (https://pusako.bengkuluprov.go.id) dihadang oleh proteksi Web Application Firewall (WAF). Untuk melintasi pencekalan ini, web scraping dibangun tidak menggunakan modul konvensional, melainkan dengan curl_cffi yang mampu memalsukan proksimitas TLS/SSL Hello handshake menyerupai interaksi web peramban yang diakui. Data perpajakan ditarik menggunakan parser manipulasi letak elemen BeautifulSoup4, yang direkonstruksikan ke skema JSON.

---

## 3. Result and Discussion (Hasil dan Pembahasan)

### 3.1 Kinerja Pemindaian OCR
Dari berbagai macam percobaan (pengkondisian foto minimal resolusi 640x480 pixel), implementasi layanan berbasis Machine Learning ini mengungkit hasil rata-rata akurasi sekitar 85% hingga 95% pada set dataset plat wilayah yang jelas. Eksekusi pipeline inference menunjukkan performa pada tingkat komputasi waktu sekitar 2 sampai 5 detik di peranti keras bermode CPU-only. Ambang batas validasi (confidence threshold) model dikalibrasi pada skala 0.2. Konversi otomatis preprocessing sangat responsif memulihkan plat beraura redup dibandingkan membaca langsung native image.

### 3.2 Pengaruh Heuristik dan Algoritma Pengoreksi
Mekanisme pengoreksian (Character Correction) telah membawa perbaikan krusial pada "edge case" kegagalan ML di real-world data. Pembacaan plat bermasalah parah seperti deteksi string BD 6701 IJ yang asalnya BD 6781 IJ namun terhambat keretakan cat nomor 8, sukses diasosiasikan oleh validasi heuristik konteks. Penolakan dari prefix dan suffix tak dikenali ([missing prefix] atau BD ABC 123 - urutan letak yang keliru) memproteksi Web Scraper untuk tidak menyerang endpoint pencarian pajak dengan tag tidak bernilai sehingga mengurangi konsumsi memori dan traffic eksternal sia-sia.

### 3.3 Integritas Layanan API Integrasi PUSAKO
Restrukturisasi koneksi scraper dengan modul retries eksponensial (maksimal pengulangan 3-kali percobaan untuk rasio penolakan koneksi HTTP/403/500) berhasil memastikan persistensi. Pengujian fungsionalitas HTTP end-point pada URL /api/v1/predict (OCR murni) dan endpoint terintegrasi dengan scraper, membuktikan super app bekerja harmonis sebagai fasilitator end-to-end (satu proses serahan gambar mendapatkan respon tarif tunggakan pajak dalam format JSON murni). 

### 3.4 Fleksibilitas dan Modularitas Sistem
Dalam tinjauan Software Engineering, penerapan Clean Architecture di proyek SUPERAPS-PAJAK terbukti memitigasi kerutan dependensi (dependency spaghetti). Manajemen file tertata rapi dari root main.py menggunakan router spesifik, sampai injeksi verifikasi pada modul core/security.py diimplementasi mulus oleh FastAPI Dependency framework (Depends). Keandalan Singleton Pattern dimanfaatkan saat pengunggahan model easyocr.Reader sehingga alokalisasi memori tidak membludak di setiap siklus request asinkron yang melayaninya. Pengelompokan ini memfasilitasi integrasi DevOps dengan lancar termasuk skrip deployment batch (install.bat dan start.bat) dalam lingkungan server Windows. 

---

## 4. Conclusion (Kesimpulan)

### 4.1 Kesimpulan
Penelitian dan pengembangan inovasi "SUPERAPS-PAJAK" telah berhasil menyajikan instrumen administratif yang mapan bagi pengelolaan pajak kendaraan, khusus berfokus pada plat nomor "BD" (Bengkulu). Kombinasi model deep learning EasyOCR berpadu teknik pengolahan gambar (Tuning kontras dan Denoising ekstensif) ditambah sistem smart filtering pattern telah menciptakan daya handal OCR yang responsif dan sangat tinggi tingkat determinasinya. Microservice berbasis FastAPI memfasilitasi Web Scraping canggih menerobos resistansi jaringan WAF pada web PUSAKO untuk menarik tagihan pajak aktual, dikomplemen dengan manajemen endpoint API nan teramankan (Secure Token API Key). Secara holistik aplikasi ini meminimalkan peranan manual, mengalihkan tenaga manusia (verifikator) menjadi pengawas komputasifikasi presisi yang terotomatisasi secara instan.

### 4.2 Saran dan Pekerjaan ke Depan (Future Works)
Berdasarkan hasil yang diamati, penelitian pendatang atau kelanjutan implementasi pada lingkungan Production direkomendasikan untuk memperhatikan aspek berikut:
1. Peningkatan Infrastruktur Hardware: Mengkompail dan mengeksekusi inferensi AI menggunakan Backend GPU (CUDA) untuk mendongkrak optimasi latensi per permintaan dari level 2-5 detik menjadi eksekusi sub-sedetik (0.X detik) per gambar.
2. End-to-End Object Detection: Integrasi YOLOv8 di depan model OCR (sebagai pencari bounding box Region of Interest) agar dapat menyempurnakan crop plat spesifik bila plat difoto dari jarak relatif memanjang agar pembacaan plat tidak tercampur string komersil pada kendaraan.
3. Pengluasan Dataset: Menambahkan kamus pola dan algoritma model untuk lebih banyak tipe prefix region pulau Sumatera lainnya guna diversifikasi aplikasi untuk dipakai lintas dinas daerah (Smart Province Connectivity).

---

(Dokumen ini merupakan hasil rangkuman akademis sesuai implementasi riil repository superaps-pajak ML Microservice yang dirancang oleh DISKOMINFOTIK Bengkulu)
