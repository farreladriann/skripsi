---

## 🔬 Bedah Konsep: GeoJSON

---

### Akar Pertanyaan — Masalah Apa yang Memanggilnya Lahir?

Mulai dari tegangan fundamental ini: **dunia fisik bersifat kontinu dan spasial, sementara komputer hanya mengenal data diskrit dan tekstual.** Bagaimana kamu merepresentasikan "batas wilayah Yogyakarta" atau "rute jalan Malioboro" dalam format yang bisa dimengerti universally oleh semua sistem?

Sebelum GeoJSON lahir, ada kekacauan: Esri Shapefile (format biner proprietary), KML (XML Google Maps), WKT/WKB (teks matematika murni), TopoJSON, dan puluhan format lainnya. Masing-masing punya dialek sendiri. Interoperabilitasnya buruk.

Pertanyaan yang melahirkan GeoJSON: ***"Bisakah kita menggunakan JSON — yang sudah dipahami seluruh web — untuk mengkodekan geometri spasial, dengan vocabulary sekecil dan seuniversal mungkin?"***

---

### Konstruksi Logis — Dari Aksioma ke Atas

**Aksioma 1: Setiap lokasi di bumi bisa direpresentasikan sebagai pasangan angka.**

Sistem koordinat WGS84 (yang dipakai GPS) menetapkan bahwa setiap titik di bumi adalah `[longitude, latitude]`. Perhatikan urutannya: **longitude dulu, baru latitude** — ini bukan kebetulan. Ini mengikuti konvensi matematika `(x, y)` dimana x adalah sumbu horizontal (barat-timur) dan y adalah vertikal (selatan-utara). Banyak orang salah karena terbiasa membaca "lat, lng" dalam GPS.

```python
# Aksioma paling dasar: sebuah titik
titik_tugu_jogja = [110.3649, -7.7828]  # [longitude, latitude]
```

**Aksioma 2: Semua geometri kompleks adalah komposisi dari titik-titik.**

Dari satu titik, kita bisa membangun tiga primitif geometri:
- **LineString** — barisan titik yang berurutan (sungai, jalan, rute)
- **Polygon** — barisan titik yang *menutup dirinya sendiri* (wilayah, danau, bangunan)
- Keduanya bisa dijamakkan: **MultiPoint**, **MultiLineString**, **MultiPolygon**

Inilah seluruh *type system* GeoJSON — tidak ada lagi. Ini adalah **vocabulary minimum yang cukup** untuk merepresentasikan seluruh geografi dunia.

**Aksioma 3: Geometri tanpa atribut tidak berguna sebagai data.**

Sebuah polygon batas kota hanyalah kumpulan koordinat tanpa makna jika tidak ada yang mengatakan "ini adalah Kota Yogyakarta, populasi 422.732 jiwa, kode pos 55xxx." Solusinya: **Feature** — wrapper yang menikahkan *geometry* dengan *properties* (atribut sembarang dalam bentuk JSON object).

**Aksioma 4: Kumpulan Feature adalah dataset spasial lengkap.**

**FeatureCollection** adalah array of Features. Ini adalah unit terbesar dalam GeoJSON — sebuah dataset peta yang bisa langsung diplot.

```
Koordinat → Geometry → Feature → FeatureCollection
```

Inilah seluruh hierarki GeoJSON. Semua yang kamu temui di dunia nyata bisa ditempatkan di salah satu level ini.

---

### Wujud Strukturalnya di Python

```python
import json

# Level 1: Geometry murni (tanpa atribut)
geometry_titik = {
    "type": "Point",
    "coordinates": [110.3649, -7.7828]
}

geometry_jalan = {
    "type": "LineString",
    "coordinates": [
        [110.3649, -7.7828],
        [110.3690, -7.7800],
        [110.3720, -7.7750]
    ]
}

# Polygon: array of rings. Ring pertama = batas luar, ring berikutnya = lubang.
# Perhatikan: titik terakhir == titik pertama (ring harus menutup)
geometry_wilayah = {
    "type": "Polygon",
    "coordinates": [
        [   # Ring luar
            [110.36, -7.79],
            [110.37, -7.79],
            [110.37, -7.78],
            [110.36, -7.78],
            [110.36, -7.79]  # menutup kembali ke titik awal
        ]
        # Jika ada lubang (misal: danau di dalam wilayah), tambahkan ring kedua di sini
    ]
}

# Level 2: Feature = geometry + properties
feature_tugu = {
    "type": "Feature",
    "geometry": geometry_titik,
    "properties": {
        "nama": "Tugu Yogyakarta",
        "tahun_berdiri": 1755,
        "kategori": "monumen"
    }
}

# Level 3: FeatureCollection = dataset lengkap
dataset_wisata_jogja = {
    "type": "FeatureCollection",
    "features": [
        feature_tugu,
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [110.3641, -7.8014]
            },
            "properties": {
                "nama": "Kraton Yogyakarta",
                "kategori": "keraton"
            }
        }
    ]
}

# Serialisasi ke string JSON standar
geojson_string = json.dumps(dataset_wisata_jogja, indent=2)
print(geojson_string)
```

---

### Invariant yang Paling Penting

Perhatikan satu hal yang **tidak pernah hilang** di seluruh hierarki GeoJSON: field `"type"`. Setiap object — Geometry, Feature, maupun FeatureCollection — selalu punya `"type"` sebagai field pertamanya. Ini adalah **structural invariant** yang memungkinkan kode kamu untuk melakukan *polymorphic dispatch* — membaca sebuah GeoJSON tanpa tahu dulu isinya apa, lalu memutuskan cara memprosesnya berdasarkan `type`.

```python
def proses_geojson(obj):
    tipe = obj["type"]

    if tipe == "FeatureCollection":
        for feature in obj["features"]:
            proses_geojson(feature)  # rekursif ke level bawah

    elif tipe == "Feature":
        print(f"Nama: {obj['properties'].get('nama', 'Tanpa nama')}")
        proses_geojson(obj["geometry"])  # rekursif ke geometry

    elif tipe == "Point":
        lng, lat = obj["coordinates"]
        print(f"  → Koordinat: {lat}°LS, {lng}°BT")

    elif tipe == "Polygon":
        n_titik = len(obj["coordinates"][0])
        print(f"  → Polygon dengan {n_titik} titik batas")

proses_geojson(dataset_wisata_jogja)
```

Struktur rekursif ini bukan kebetulan — ia adalah konsekuensi langsung dari desain hierarkis GeoJSON. Kamu tidak perlu hafal API, cukup pahami hierarkinya.

---

### Library Python yang Memperluasnya

Ketika kamu menggunakan library seperti `shapely` atau `geopandas`, kamu sebenarnya membangun di atas fondasi yang sama — mereka hanya menambahkan operasi geometri (intersection, buffer, area) yang tidak ada di spec GeoJSON murni.

```python
from shapely.geometry import shape, mapping

# shape() mengubah dict GeoJSON → objek Shapely yang bisa dihitung
polygon = shape(geometry_wilayah)
print(f"Luas: {polygon.area}")  # dalam derajat² (bukan km², karena koordinat masih WGS84)

# mapping() mengubah kembali → dict GeoJSON
kembali_ke_geojson = mapping(polygon)
```

---

### Batas dan Anomali — Di Mana GeoJSON Runtuh?

Tiga batas penting yang justru memperdalam pemahaman:

**1. GeoJSON hanya mengenal WGS84 (lon/lat).** Ia tidak bisa natively menyimpan koordinat UTM atau proyeksi lain. Ini bukan kelemahan teknis — ini adalah *keputusan desain sadar* untuk menjaga vocabulary tetap minimal. Konsekuensinya: kalau kamu butuh menghitung jarak dalam meter, kamu harus memproyeksikan dulu ke CRS yang berbeda (misalnya EPSG:32749 untuk Jawa).

**2. Antimeridian Problem.** Jika kamu membuat polygon yang melewati garis bujur 180° (antara Rusia timur dan Alaska barat), GeoJSON standar akan "salah arah" — polygon-nya akan membentang melingkari seluruh bumi ke arah yang salah. RFC 7946 punya solusinya, tapi ia membutuhkan *winding order* yang benar (ring luar harus berlawanan jarum jam / counter-clockwise).

**3. Verbositas.** GeoJSON adalah teks murni. Sebuah dataset jalan seluruh Indonesia dalam GeoJSON bisa berukuran ratusan MB. Untuk kasus ini, format seperti **FlatGeobuf** atau **PMTiles** lebih tepat — keduanya menggunakan prinsip yang sama tapi dengan binary encoding.

---

### Irisan Domain — GeoJSON sebagai Struktur Pohon

Ada isomorfisme menarik antara GeoJSON dan **parse tree** dalam teori bahasa formal. FeatureCollection adalah root node, Features adalah internal nodes, dan Geometry (Point, LineString, Polygon) adalah leaf nodes. Struktur rekursif yang kamu tulis tadi bukan hanya kebetulan pythonic — ia mencerminkan grammar formal dari format ini. Siapapun yang memahami tree traversal dalam computer science, secara instinktif sudah tahu cara menafsirkan GeoJSON.

---

### Pertanyaan Generatif

Kamu punya dataset GeoJSON berisi 500 polygon kecamatan di seluruh Pulau Jawa, masing-masing dengan properties `{"nama_kecamatan": "...", "jumlah_penduduk": ...}`. Tanpa menggunakan library eksternal apapun — hanya Python built-in dan `json` — bagaimana kamu menulis fungsi yang **menemukan kecamatan dengan jumlah penduduk terbesar, dan mengembalikan koordinat centroid kasar-nya** (rata-rata semua titik dalam polygon-nya)?

Ini bukan soal sintaks. Ini soal apakah kamu bisa *navigasi hierarki* GeoJSON dan *mengekstrak informasi geometri* secara spontan dari mental model yang baru dibangun.