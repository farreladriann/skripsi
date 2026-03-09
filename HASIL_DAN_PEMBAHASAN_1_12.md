# Hasil dan Pembahasan Analisis Spatiotemporal Mobilitas GPS DIY

## Gambaran Umum

Bab ini merangkum dua belas analisis spatiotemporal yang dilakukan pada data GPS mobilitas wilayah DIY untuk periode Oktober 2021 sampai Juni 2022. Seluruh analisis menggunakan data yang telah dikonversi ke format Parquet, dibersihkan, dan diurutkan, sehingga fokus pembahasan diarahkan pada pola mobilitas yang terbentuk, bukan lagi pada persoalan prapemrosesan data.

Secara umum, rangkaian analisis ini menunjukkan bahwa mobilitas di DIY memiliki tiga karakter utama. Pertama, pergerakan pengguna cenderung bersifat lokal dan berulang. Kedua, aktivitas mobilitas membentuk ritme waktu yang jelas, baik dalam skala harian maupun bulanan. Ketiga, struktur ruang aktivitas memperlihatkan kombinasi antara elemen yang stabil dan elemen yang dinamis.

## 1. Karakter Dasar Perpindahan

Analisis distribusi jarak lompatan pada Analisis 1 menunjukkan bahwa seluruh bulan menghasilkan nilai eksponen alpha di atas 2. Hal ini menempatkan pola perpindahan pada rezim **thin tailed**, sehingga perjalanan ekstrem jarak jauh tidak menjadi bentuk dominan mobilitas di DIY. Mayoritas pergerakan justru berada pada skala pendek hingga menengah.

Temuan ini konsisten dengan Analisis 8 yang memperlihatkan rata-rata median jarak perpindahan bulanan hanya **1,19 km**, sementara rata-rata median Radius of Gyration bulanan sebesar **1,34 km**. Dengan kata lain, baik dari sudut pandang perpindahan antartitik maupun ruang gerak individu, mobilitas tipikal pengguna lebih dekat ke pola aktivitas lokal daripada mobilitas jarak jauh.

Analisis 6 menguatkan temuan tersebut. Median Radius of Gyration keseluruhan sebesar **1,675 km** menunjukkan bahwa ruang aktivitas mayoritas pengguna cenderung kompak. Walaupun ada kelompok pengguna dengan ruang gerak lebih luas, kategori lokal tetap mendominasi banyak bulan. Secara substantif, ini menunjukkan bahwa dinamika mobilitas di DIY lebih banyak dibentuk oleh pengulangan aktivitas di sekitar beberapa titik penting daripada oleh eksplorasi wilayah yang sangat luas.

## 2. Ritme Temporal Mobilitas

Analisis 2 dan Analisis 7 sama-sama menunjukkan bahwa mobilitas GPS memiliki pola temporal yang kuat. Jam puncak paling umum berada pada **19:00 sampai 20:00 WIB**, menandakan bahwa aktivitas sore hingga malam memiliki peran besar dalam membentuk volume data GPS. Namun pola ini tidak sepenuhnya tetap, karena beberapa bulan menampilkan penyimpangan yang jelas, misalnya **Februari 2022** dengan puncak **23:00** dan **Maret 2022** dengan puncak **08:00**.

Dari perspektif mingguan, rasio weekday terhadap weekend mendekati 1, dengan rata-rata **0,92x**. Ini berarti mobilitas pada akhir pekan sedikit lebih tinggi daripada hari kerja, tetapi perbedaannya tidak ekstrem. Pola ini mengindikasikan bahwa struktur mobilitas DIY tidak sepenuhnya didominasi oleh commuting kerja formal, melainkan juga oleh aktivitas sosial, domestik, dan rekreasional yang tersebar di berbagai hari.

Analisis tren bulanan menunjukkan bahwa volume data sangat bervariasi antarbulan. **November 2021** menjadi bulan dengan total data tertinggi, sedangkan **April 2022** adalah bulan dengan data terendah. Variasi ini penting karena perubahan pola pada analisis lain harus selalu dibaca bersama konteks volume data dan banyaknya hari observasi. Oktober 2021 dan Juni 2022, misalnya, adalah bulan parsial sehingga interpretasinya perlu lebih hati-hati.

## 3. Struktur Hotspot dan Konsentrasi Aktivitas

Analisis 3 menunjukkan bahwa aktivitas GPS di DIY tidak tersebar merata, tetapi terkonsentrasi pada hotspot tertentu. Titik **(-7.805, 110.365)** muncul berulang kali sebagai lokasi terpadat pada sebagian besar bulan, yang menandakan adanya inti aktivitas spasial yang sangat dominan. Namun, ada pula bulan-bulan ketika pusat hotspot bergeser, seperti Desember 2021 dan Mei 2022. Ini menunjukkan bahwa struktur hotspot tidak benar-benar statis.

Analisis 12 kemudian memperdalam pembacaan tersebut. Dari **122 hotspot unik** yang muncul selama periode pengamatan, hanya **36** yang tergolong **persistent core**, yaitu hotspot yang tetap aktif minimal lima bulan. Temuan ini menunjukkan bahwa struktur ruang aktivitas memiliki dua lapisan. Lapisan pertama adalah hotspot inti yang stabil, sedangkan lapisan kedua adalah hotspot temporer yang muncul dan menghilang mengikuti dinamika bulanan.

Nilai Jaccard antarbulan yang bervariasi memperkuat hal itu. **Juni 2022** memiliki overlap hotspot tertinggi dengan bulan sebelumnya, menandakan kestabilan tinggi, sedangkan **Desember 2021** memiliki overlap terendah, menandakan adanya perubahan besar dalam susunan hotspot. Dengan demikian, hotspot di DIY perlu dipahami sebagai struktur yang sebagian konsisten dan sebagian adaptif terhadap konteks waktu.

## 4. Pola Origin-Destination dan Koridor Gerak

Analisis 4 memperlihatkan bahwa sebagian besar user-day memulai dan mengakhiri aktivitas pada zona yang sama. Proporsi pasangan origin-destination yang benar-benar berpindah zona hanya sekitar **7,9% sampai 15,3%**. Ini berarti mayoritas pergerakan harian bersifat intrazona atau kembali ke zona awal dalam hari yang sama.

Meskipun demikian, ketika perpindahan antarzona benar-benar terjadi, jaraknya cukup konsisten pada skala menengah, dengan rata-rata median sekitar **9 km**. Selain itu, rute seperti **7_4->6_4** dan **6_4->7_4** muncul berulang sebagai rute terpopuler di banyak bulan. Hal ini menunjukkan adanya koridor mobilitas utama yang berfungsi sebagai penghubung antarwilayah aktivitas inti.

Temuan ini penting untuk pembahasan skripsi karena memperlihatkan bahwa mobilitas DIY tidak sepenuhnya acak. Ada arus dominan yang berulang dan membentuk pola spasial yang terstruktur.

## 5. Mobilitas, Demografi, dan Home Anchor

Analisis 5 memperlihatkan bahwa ketika data GPS dikaitkan dengan PeopleGraph, median radius mobilitas pengguna yang matched cenderung rendah. Ini menunjukkan bahwa subset pengguna yang memiliki atribut demografis juga banyak bergerak dalam ruang lokal. Terdapat indikasi bahwa median radius pengguna laki-laki cenderung lebih tinggi daripada perempuan pada bulan-bulan dengan sampel cukup besar, walaupun hasil ini tetap perlu dibaca hati-hati karena komposisi sampelnya tidak seimbang.

Analisis 6 menambahkan dimensi yang lebih kuat melalui deteksi rumah berbasis kunjungan malam hari. Banyaknya rumah yang berhasil terdeteksi menunjukkan bahwa data malam cukup kaya untuk menjadi jangkar spasial. Kehadiran home anchor ini penting karena memberi dasar interpretasi bahwa pola mobilitas tidak sekadar kumpulan titik berpindah, tetapi terkait pada pusat aktivitas personal yang relatif tetap.

Dengan demikian, pembahasan mobilitas dapat diposisikan tidak hanya sebagai fenomena spasial agregat, tetapi juga sebagai ekspresi perilaku individu yang terikat pada rumah, area kerja, dan aktivitas rutin lain.

## 6. Regularitas dan Eksplorasi Ruang

Analisis 10 memperkenalkan pembacaan regularitas mobilitas melalui entropi spasial. Hasilnya menunjukkan bahwa median normalized entropy keseluruhan sebesar **0,456**, sedangkan median top-1 share mencapai **0,853**. Kombinasi ini menandakan bahwa mobilitas pengguna DIY pada umumnya tidak tersebar secara acak, tetapi terfokus kuat pada satu lokasi utama dan beberapa lokasi sekunder.

**Maret 2022** merupakan bulan paling rutin, dengan entropy nyaris nol dan top-1 share sempurna. Sebaliknya, **Desember 2021** menjadi bulan paling eksploratif. Temuan ini menunjukkan bahwa tingkat regularitas mobilitas berubah menurut waktu. Jadi, perilaku spasial pengguna tidak dapat direduksi menjadi satu pola tetap sepanjang periode observasi.

Dalam pembahasan skripsi, analisis ini sangat berharga karena menjembatani hasil-hasil sebelumnya. Jika Analisis 1, 6, dan 8 menunjukkan bahwa mobilitas cenderung lokal, maka Analisis 10 menjelaskan **mengapa** pola itu terjadi: karena banyak pengguna memang terus kembali ke lokasi inti yang sama.

## 7. Pergeseran Intrahari dan Denyut Kota

Analisis 11 memperlihatkan bahwa pusat aktivitas tidak diam di satu lokasi sepanjang hari. Daypart **Malam** menjadi fase yang paling dominan secara keseluruhan, tetapi pada beberapa bulan daypart dominan justru bergeser ke **Dini Hari**. Selain itu, jarak antar-centroid daypart menunjukkan bahwa aktivitas harian membentuk pergeseran spasial yang nyata.

Pergeseran terbesar muncul pada **Maret 2022**, ketika shift maksimum antar-daypart mencapai **1,70 km**. Ini berarti dalam satu hari, pusat aktivitas masyarakat dapat bergeser cukup jauh dari satu fase waktu ke fase waktu lain. Sebaliknya, **Desember 2021** menunjukkan pergeseran kecil, yang berarti pusat aktivitas intraharinya lebih rapat dan stabil.

Hasil ini memperlihatkan bahwa mobilitas di DIY mempunyai denyut intrahari yang terukur. Dari sudut pandang pembahasan, ini penting karena ruang aktivitas bukan hanya berubah antarbulan, tetapi juga berosilasi secara sistematis dalam satu hari.

## 8. Cakupan Spasial dan Evolusi Wilayah Aktivitas

Analisis 9 menunjukkan bahwa hampir separuh grid potensial di wilayah studi terisi data pada bulan-bulan normal. Coverage tertinggi terjadi pada **November 2021**, sedangkan coverage terendah terjadi pada **April 2022**. Walaupun demikian, centroid bulanan tetap berada pada kawasan yang relatif sama, sekitar **(-7.80, 110.37)**.

Temuan ini berarti perubahan mobilitas tidak selalu berarti perpindahan pusat aktivitas. Dalam banyak kasus, yang berubah adalah luas cakupan dan tingkat penyebaran di sekitar pusat yang relatif tetap. Dengan kata lain, DIY menunjukkan stabilitas pusat gravitasi mobilitas, tetapi mengalami ekspansi dan kontraksi ruang aktivitas dari waktu ke waktu.

Analisis ini melengkapi hotspot dan OD karena menunjukkan apakah perubahan mobilitas bersifat ekspansif, kontraktif, atau hanya redistributif di sekitar pusat yang sama.

## 9. Sintesis Temuan Utama

Jika dua belas analisis tersebut digabungkan, maka gambaran besar mobilitas GPS DIY dapat dirumuskan sebagai berikut.

Pertama, mobilitas masyarakat DIY cenderung **lokal dan rutin**. Ini terlihat dari distribusi jarak yang thin tailed, median perpindahan yang pendek, Radius of Gyration yang relatif kecil, serta entropy spasial yang moderat dengan dominasi kuat pada satu lokasi utama.

Kedua, mobilitas tersebut tetap memiliki **ritme temporal yang kuat**. Aktivitas cenderung memuncak pada sore hingga malam hari, tetapi beberapa bulan menunjukkan ritme yang berbeda. Selain itu, pusat aktivitas juga berpindah secara terukur sepanjang hari, membentuk denyut kota yang nyata.

Ketiga, struktur ruang mobilitas DIY memperlihatkan **kombinasi antara stabilitas dan dinamika**. Ada hotspot inti yang persisten, centroid bulanan yang relatif stabil, serta koridor OD yang berulang. Namun di saat yang sama, terdapat turnover hotspot, variasi coverage, dan perubahan regularitas mobilitas antarbulan.

Keempat, keterkaitan antara home anchor, atribut demografis, dan pola ruang menunjukkan bahwa mobilitas bukan hanya fenomena perpindahan teknis, tetapi juga fenomena perilaku sosial yang terikat pada rutinitas dan struktur wilayah.

## 10. Implikasi untuk Skripsi

Berdasarkan seluruh hasil tersebut, dapat dikatakan bahwa data GPS berskala besar memang layak digunakan untuk eksplorasi big data spatiotemporal. Data ini tidak hanya mampu memetakan di mana aktivitas berlangsung, tetapi juga kapan aktivitas memuncak, seberapa jauh pengguna bergerak, seberapa stabil pola ruangnya, dan bagaimana struktur hotspot berubah dari waktu ke waktu.

Dengan demikian, kontribusi utama kajian ini terletak pada kemampuannya mengungkap bahwa mobilitas di DIY adalah sistem yang:

- terpusat pada beberapa simpul utama,
- didominasi rutinitas lokal,
- memiliki denyut waktu yang kuat,
- namun tetap menyimpan dinamika spasial antarhari dan antarbulan.

Narasi ini dapat langsung dijadikan dasar untuk subbab hasil dan pembahasan pada skripsi, lalu diperkaya dengan visualisasi dari masing-masing folder analisis sesuai kebutuhan penulisan.
