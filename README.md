
Nama : Muhammad Akbar Rinaldy
NPM  : 2506586311
PBP  : E

### Tugas 1

1. saya menggunakan elemen semantik HTML5 contohnya <section> untuk membagi halaman menjadi beberapa bagian seperti profile dan eduction. Elemen <section> membantu saya dalam membuat static web karena struktur HTML menjadi lebih terorganisir dan setiap bagian memiliki tujuan yang jelas. Selain itu hal ini juga memudahkan saya dalam mengatur CSS, penggunaan elemen semantik juga membuat kode lebih mudah dibaca dan dipahami.

2. pertanyaan 1:
salah satu tantangan yang saya temukan adalah ketika menyesuaikan layout web dari layar lapton ke ukuran layar mobile. Di desktop, saya menggunakan CSS Grid dengan dua kolom(informasi profil di sebelah kiri dan foto di sebelah kanan). tapi di layar mobile dua kolom menjadi terlalu sempit sehingga saya memodifikasinnya agar  menjadi satu kolom.

pertanyaan 2:
Saya menentukan elemen yang harus diprioritaskan berdasarkan fungsi dan kepentingannya. Pada tampilan mobile, saya menempatkan nama dan informasi utama terlebih dahulu, kemudian foto dan detail lainnya. Saya juga menyesuaikan ukuran foto serta jarak antar elemen supaya tampilannya tetap nyaman dilihat dan tidak saling overlappping. Untuk mengeceknya, saya mencoba website pada beberapa ukuran layar dan melihat apakah teks, foto, navigasi, dan card masih terlihat dengan baik. Jika ada bagian yang terlalu besar atau posisinya kurang sesuai, saya memperbaikinya menggunakan CSS dan media query.

3. Karena website yang saya buat masih berupa static web, tentu ada beberapa keterbatasan dalam menyajikan informasi. Semua informasi masih ditulis langsung di dalam HTML, jadi kalau ada data yang ingin di ubah atau ditambahkan, saya harus mengedit kodenya secara manual.

Untuk pengembangan selanjutnya, saya ingin menambahkan section procejt ke dalam website saya. Di bagian tersebut, saya bisa menampilkan beberapa project yang pernah saya lakukan. Dan juga saya ingin membuatnya lebih interaktif, misalnya dengan fitur kategori atau filter agar pengunjung lebih mudah melihat project seperti apa yang mereka ingin lihat.

AI Disclosure : Dalam proses pembuatan website ini, saya menggunakan AI sebagai alat bantu untuk mencari ide, memahami HTML/CSS, dan memperbaiki beberapa masalah pada kode. Terutama dalam hal memahami syntax HTML dan CSS karena kedua bahasa ini baru bagi saya. Saya juga memberikan prompt yang spesifik dengan menjelaskan masalah dan hasil yang saya inginkan.

Saya juga tetap melakukan pengecekan dan perbaikan secara manual. Contohnya, setelah mengubah background dan warna header dengan bantuan AI karena saya tidak mengetahui kode warnyanya, ada teks yang kurang terlihat karena warnanya mirip dengan background. Lalu saya menyesuaikan warna teks secara manual agar lebih mudah dibaca. Jadi, AI saya gunakan sebagai alat bantu, sementara hasil akhirnya tetap saya periksa dan sesuaikan sendiri.

### Tugas 2
1. Saat user membuka halaman skills. request akan masuk ke urls.py proyek lalu diteruskan ke urls.py aplikasi main. Setelah URL yang sesuai ditemukan, django akan menjalankan view yang mengambil data dari model dan memasukkannya ke context. Data tersebut kemudian dikirim ke template untuk ditampilkan dalam bentuk HTML. Hasil akhirnya dikirim kembali ke browser dan ditampilkan kepada user.

2. Data baiknya disimpan di model supaya kita tidak perlu menulis data langsung di HTML. jadi jika ingin menambah atau mengubah data, kita cukup mengubah data di database tanpa harus mengubah template. Template hanya bertugas mengatur bagaimana data tersebut ditampilkan. alhasil cara ini membuat project lebih rapi dan lebih mudah dikembangkan ketika datanya semakin banyak.

3. makemigrations digunakan untuk mencatat perubahan yang kita buat pada model ke dalam file migration, sedangkan migrate digunakan untuk menerapkan perubahan tersebut ke database. Contohnya, saat saya menambahkan field image dan year pada model Experience, saya perlu menjalankan kedua perintah tersebut. Saya menjalankan python manage.py makemigrations terlebih dahulu, lalu python manage.py migrate agar perubahan model benar-benar diterapkan ke database.

AI disclosure: Saya menggunakan AI (chatgpt dan Codex) sebagai alat bantu selama proses pengerjaan tugas ini. AI membantu saya dalam memahami konsep MVT Django, memberikan saran struktur kode, serta membantu implementasi dan debugging beberapa bagian project. Saya tetap mengecek ulang dan menyesuaikan kode yang diberikan agar sesuai dengan kebutuhan dan ketentuan tugas. AI digunakan sebagai pendukung proses belajar dan pengembangan, bukan untuk menggantikan pemahaman saya terhadap kode yang dibuat.


### Tugas 3
1. ModelForm digunakan karena dapat membuat form secara otomatis berdasarkan model yang sudah kita buat di Django.jadi kita tidak perlu menulis setiap input HTML secara manual dan proses validasi serta penyimpanan data ke database juga menjadi lebih mudah. {% csrf_token %} digunakan untuk melindungi form dari serangan Cross-Site Request Forgery (CSRF) dengan memastikan bahwa request yang dikirim melalui form memang berasal dari halaman aplikasi kita.

2. JSON lebih banyak digunakan formatnya lebih sederhana dibandingkan XML. JSON juga memiliki struktur yang mirip dengan object pada js dan mudah diproses oleh berbagai bahasa pemrograman.XML membutuhkan banyak tag pembuka dan penutup, alasan- alasan tersebut adalah kenapa JSON banyak digunakan pada API dan komunikasi data pada aplikasi web modern.

3. Ketika user mengakses URL yang mengarah ke view JSON, Django akan menjalankan fungsi view tersebut dan mengambil data portofolio dari database melalui model. Data dari database masih berupa object/model Django, sehingga tidak bisa langsung dikirim sebagai JSON. Karena itu, dilakukan proses serialization, yaitu adalah mengubah object Django menjadi format data yang dapat direpresentasikan dan dikirim sebagai JSON. Setelah proses tersebut selesai, view mengembalikan data JSON melalui HTTP response sehingga data tersebut dapat digunakan oleh client atau bagian lain dari aplikasi.

AI disclosure : Dalam menerjakan tugas ini,saya menggunakan AI sebagai alat bantu untuk memahami konsep Django, khususnya penggunaan ModelForm, implementasi CRUD, serta proses serialization dan deserialization data JSON. AI juga saya gunakan untuk membantu memberikan saran dalam melakukan refactoring kode dan debugging ketika terdapat error. Seluruh kode yang dihasilkan tetap saya tinjau, sesuaikan dengan materi yang telah dipelajari, dan uji kembali untuk memastikan program dapat berjalan dengan baik.

### Tugas 4
AI disclosure : Saya menggunakan AI untuk membantu memahami tugas, meninjau ide implementasi Django, dan memperbaiki struktur kode. Seluruh saran yang diberikan AI telah saya tinjau ulang, disesuaikan, dan uji terlebih dahulu sebelum dimasukkan ke dalam program.

### Tugas 5

1. Debouncing adalah teknik untuk menunda eksekusi suatu fungsi sampai pengguna berhenti melakukan input selama kurung waktu tertentu, misalnya 300 ms. Teknik ini penting pada fitur pencarian yang menggunakan AJAX. kalau tidak menggunakan debouncing setiap karakter yang diketik pengguna dapat memicu request baru ke server. Hal ini dapat menyebabkan terlalu banyak request dalam waktu singkat dan membebani server. debouncingmembuat request hanya dikirim setelah pengguna berhenti mengetik dalam kurung waktu yang ditentukan, sehingga pencarian menjadi lebih efisien dan performa aplikasi menjadi lebih baik.

2. Penggunaan await pada fetch() berfungsi untuk menunggu proses asynchronous selesai sebelum program melanjutkan ke baris berikutnya. Hal ini penting karena fetch() mengembalikan sebuah promisew bukan langsung data hasil request. Dengan menggunakan await kita bisa memastikan bahwa response sudah diterima sebelum diproses lebih lanjut, misalnya menggunakan response.json(). Jika await tidak digunakan, variabel yang menyimpan hasil fetch() masih berupa Promise sehingga data belum bisa langsung digunakan. Sebagai alternatif, kita bisa menggunakan .then() untuk menangani Promise tersebut.

3. XSS atau Cross-Site Scripting adalah serangan ketika kode JavaScript berbahaya berhasil dimasukkan ke dalam halaman web dan dijalankan di browser pengguna. Data yang ditampilkan melalui AJAX atau JavaScript bisa lebih rentan terhadap serangan ini karena developer sering melakukan manipulasi DOM secara langsung, misalnya menggunakan innerHTML. Jika data dari pengguna dimasukkan tanpa sanitasi kode HTML atau JavaScript berbahaya bisa ikut dijalankan. Sementara itu, Django template secara default memiliki fitur auto-escaping yang mengubah karakter khusus seperti < dan > menjadi bentuk yang aman. Oleh karena itu, saat menampilkan data melalui JavaScript, lebih aman menggunakan textContent jika datanya hanya berupa teks biasa agar mengurangi risiko XSS.

AI disclosure: AI/Codex saya gunakan untuk membantu analisis struktur project, implementasi JavaScript, serta debugging/refactoring. Kode tetap selalu direview oleh saya sebagai developer sebelum dikumpulkan, hasil pemeriksaan otomatis tidak menggantikan review developer. Saya perlu melengkapi catatan review pribadi setelah benar-benar melakukannya.


### Tugas 6

1. REST adalah gaya arsitektur yang mengatur komunikasi client dan server melalui resource dan method HTTP. REST memiliki prinsip seperti stateless, client-server, dan cacheability. API yang menghasilkan JSON belum tentu RESTful, karena penggunaan method HTTP juga harus sesuai fungsinya. PUT digunakan untuk mengganti seluruh data resource, sedangkan PATCH hanya mengubah bagian tertentu. PUT bersifat idempotent, sementara PATCH bergantung pada operasinya. API tugas ini sudah mengikuti pola REST, tetapi masih menggunakan session authentication sehingga belum sepenuhnya stateless.

2. Serializer digunakan untuk mengubah data model menjadi JSON dan memvalidasi data yang masuk sebelum disimpan. ModelSerializer mempermudah proses ini karena dapat menggunakan aturan dari model secara langsung. Pada SkillSerializr, field ditentukan secara eksplisit, teks divalidasi, dan informasi star dihitung otomatis. Dibandingkan menggunakan JsonResponse manual, serializer membuat kode lebih rapi, validasi lebih konsisten, dan mengurangi risiko data sensitif ikut ditampilkan.

3. Autentikasi memastikan identitas pengguna, otorisasi menentukan apa yang boleh dilakukan pengguna tersebut. Dalam tugas ini semua orang bisa melihat data, editor dan superuser dapat mengedit, tapi hanya superuser yang boleh membuat atau menghapus data. Fitur star hanya tersedia untuk pengguna yang sudah login. Pembatasan ini harus diterapkan di server, bukan hanya dengan menyembunyikan tombol, karena pengguna tetap bisa mengirim request secara langsung.

4. CSRF digunakan untuk mencegah pihak lain melakukan perubahan data menggunakan sesi login pengguna tanpa izin. Karena API ini menggunakan session authentication, request seperti POST, PUT, PATCH, dan DELETE perlu menyertakan token CSRF. Token dikirim melalui header X-CSRFToken. Untuk mengujinya, digunakan apiClient dengan enforce_csrf_checks=True. Test memastikan request tanpa token ditolak dengan status 403 dan data tidak berubah, sedangkan request dengan token yang valid berhasil. force_authenticate tidak cukup untuk menguji CSRF karena melewati autentikasi normal.

AI disclosure: Saya menggunakan Codex sebagai alat bantu dalam mengerjakan Tugas 6, mulai dari memeriksa checklist dan meninjau kode yang sudah ada hingga melengkapi modal tambah/edit serta validasi pada bagian Skills. Codex juga membantu menyusun test untuk memeriksa hak akses pengguna, fitur star, dan perlindungan CSRF, serta membantu penyusunan dokumentasi dan draf jawaban reflektif. Kode dan penjelasan yang dihasilkan AI tetap saya tinjau, uji, dan pahami kembali sebelum dikumpulkan.

