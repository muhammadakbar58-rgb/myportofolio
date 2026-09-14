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