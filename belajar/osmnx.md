---

## 🔬 Bedah Konsep: OSMnx

---

### Akar Pertanyaan — Masalah Apa yang Memanggilnya Lahir?

Ada dua dunia yang secara historis tidak bisa berbicara satu sama lain.

**Dunia pertama: OpenStreetMap (OSM).** Ia adalah database geografis kolaboratif terbesar di dunia — semacam Wikipedia untuk peta. Setiap jalan, gedung, sungai, taman di seluruh bumi tersimpan di sana dalam format XML. Tapi OSM dirancang untuk *penyimpanan dan rendering peta*, bukan untuk analisis matematika.

**Dunia kedua: Teori Graf dan Network Science.** Matematikawan dan ilmuwan komputer sudah memiliki alat yang luar biasa untuk menganalisis jaringan — shortest path, centrality, clustering, flow. Tapi alat-alat ini membutuhkan input berupa **graf**: kumpulan node dan edge yang terdefinisi rapi.

Pertanyaan yang melahirkan OSMnx: ***"Bagaimana kita mentransformasi jaringan jalan nyata dari OSM menjadi objek matematika berupa graf, sehingga seluruh kekuatan network science bisa diarahkan ke pertanyaan-pertanyaan urban?"***

Seperti: *Seberapa walkable Kota Yogyakarta? Jalan mana yang paling kritis secara topologis? Berapa lama rute terpendek dari Malioboro ke UGM?*

---

### Konstruksi Logis — Dari Model Data OSM ke Graf

**Langkah 1: Pahami model data mentah OSM.**

OSM menyimpan dunia dalam tiga primitif:
- **Node** — titik tunggal (koordinat). Bisa berupa tiang lampu, titik di tengah jalan, perempatan.
- **Way** — barisan node yang berurutan. Sebuah jalan adalah *way* dengan tag `highway=*`. Sebuah bangunan adalah *way* tertutup dengan tag `building=*`.
- **Relation** — kumpulan way/node yang membentuk entitas lebih besar (rute bus, batas wilayah administratif).

Jadi jalan Malioboro di OSM bukanlah satu objek tunggal — ia adalah *way* yang terdiri dari puluhan node yang berjejer membentuk geometri jalan tersebut.

**Langkah 2: Masalah transformasi.**

Dari barisan node ini, kamu tidak bisa langsung membuat graf. Mengapa? Karena tidak semua node adalah *intersection* (persimpangan sejati). Sebagian besar node hanyalah **shape points** — titik yang ada semata-mata untuk membentuk lengkungan geometri jalan. Mereka bukan persimpangan, dan jika semua node dijadikan node graf, kamu akan punya graf dengan jutaan node yang tidak berguna.

OSMnx melakukan satu transformasi kritis: ia mengidentifikasi **hanya node yang merupakan persimpangan atau ujung jalan buntu** sebagai node dalam graf. Node-node shape yang ada di antaranya *dilipat* menjadi atribut geometri dari edge.

```
Way OSM (barisan node mentah):
A → b → c → d → E → f → g → H

Dimana huruf kapital = persimpangan, huruf kecil = shape point

Graf yang dihasilkan OSMnx:
A ——————————— E ——————————— H
  (geometri b,c,d    (geometri f,g
   tersimpan di edge)  tersimpan di edge)
```

**Langkah 3: Mengapa Directed Multigraph?**

Graf yang dibangun OSMnx bukan graf sederhana — ia adalah `MultiDiGraph` (directed multigraph). Ada dua alasan yang masing-masing bisa diderivasi dari realitas fisik:

- **Directed** karena jalan satu arah (*one-way streets*) ada. Jika A→B ada tapi B→A tidak, graf harus merepresentasikan asimetri ini. Graf undirected akan kehilangan informasi krusial ini.
- **Multi** karena antara dua node bisa ada lebih dari satu edge. Bayangkan dua jalan paralel yang menghubungkan persimpangan yang sama. Atau, jalan dua arah direpresentasikan sebagai dua edge directed (A→B dan B→A) antara node yang sama.

**Langkah 4: Atribut Edge yang Membuat Graf Menjadi Bermakna.**

Setiap edge bukan hanya penghubung abstrak — ia membawa metadata dari OSM: `length` (meter), `name`, `highway` (tipe jalan), `maxspeed`, `oneway`, dan `geometry` (objek Shapely LineString yang merepresentasikan kurva jalan sesungguhnya).

---

### Implementasi — Membangun dari Bawah

```python
import osmnx as ox
import networkx as nx

# ── 1. Download graf jaringan jalan ──────────────────────────────────────────
# OSMnx memanggil Overpass API (query engine OSM) di balik layar
# network_type bisa: 'drive', 'walk', 'bike', 'all'
G = ox.graph_from_place("Yogyakarta, Indonesia", network_type="drive")

# G adalah objek networkx.MultiDiGraph
print(type(G))
print(f"Jumlah node (persimpangan): {G.number_of_nodes()}")
print(f"Jumlah edge (segmen jalan): {G.number_of_edges()}")
```

```python
# ── 2. Inspeksi struktur graf secara langsung ─────────────────────────────────
# Node adalah dict dengan atribut spasial
node_id = list(G.nodes)[0]
print(G.nodes[node_id])
# → {'y': -7.7828, 'x': 110.3649, 'street_count': 3}

# Edge adalah dict dengan atribut jalan
u, v, key = list(G.edges(keys=True))[0]
print(G.edges[u, v, key])
# → {'osmid': ..., 'name': '...', 'highway': 'residential',
#    'length': 87.3, 'geometry': <LINESTRING ...>}
```

```python
# ── 3. Shortest Path — algoritma Dijkstra di atas graf riil ──────────────────
# Temukan node terdekat dari dua koordinat
tugu = (110.3649, -7.7828)   # (lng, lat)
ugm  = (110.3761, -7.7703)

node_asal  = ox.nearest_nodes(G, tugu[0], tugu[1])
node_tujuan = ox.nearest_nodes(G, ugm[0],  ugm[1])

# nx.shortest_path menggunakan weight='length' (meter)
rute = nx.shortest_path(G, node_asal, node_tujuan, weight="length")

# Hitung total jarak
jarak_total = nx.shortest_path_length(G, node_asal, node_tujuan, weight="length")
print(f"Jarak terpendek: {jarak_total:.0f} meter")
```

```python
# ── 4. Proyeksi ke CRS metrik (penting sebelum hitung luas/jarak akurat) ─────
# Ingat dari GeoJSON: koordinat WGS84 tidak bisa langsung dihitung dalam meter
G_projected = ox.project_graph(G)
# OSMnx otomatis memilih UTM zone yang sesuai dengan lokasi

# Sekarang atribut 'length' sudah dalam meter yang akurat
```

```python
# ── 5. Analisis Jaringan — di sinilah kekuatan sesungguhnya ──────────────────
# Basic stats: density, average street length, intersection count
stats = ox.basic_stats(G)
print(f"Rata-rata panjang edge: {stats['edge_length_avg']:.1f} m")
print(f"Intersection density: {stats['intersection_density_km']:.1f} per km²")

# Betweenness centrality: node mana yang paling 'kritis' topologis?
# (node yang paling sering dilalui oleh semua shortest path)
centrality = nx.betweenness_centrality(G, weight="length", normalized=True)
node_paling_kritis = max(centrality, key=centrality.get)
print(f"Node paling kritis: {node_paling_kritis}, skor: {centrality[node_paling_kritis]:.4f}")
```

```python
# ── 6. Visualisasi ───────────────────────────────────────────────────────────
# Plot graf dasar
fig, ax = ox.plot_graph(G, figsize=(12, 12), node_size=5)

# Plot rute di atas graf
fig, ax = ox.plot_graph_route(G, rute, route_linewidth=4, route_color="red")
```

---

### Irisan Domain — Graf Jalan sebagai Sistem Fisika

Ada isomorfisme yang dalam antara jaringan jalan dan beberapa sistem dalam fisika:

**Betweenness Centrality ↔ Arus Listrik.** Dalam rangkaian listrik, arus mengalir melalui jalur dengan resistansi terendah. Dalam jaringan jalan, "arus" lalu lintas mengalir melalui rute terpendek. Node dengan betweenness centrality tinggi adalah analog dengan *bottleneck resistor* — ia yang paling sering "dilalui arus", dan jika ia dihilangkan (jembatan putus, jalan ditutup), seluruh jaringan terganggu.

**Graf Jalan ↔ Lattice dalam Fisika Statistik.** Cara node tersambung satu sama lain (topologi graf) menentukan sifat *difusi* di atasnya. Random walk di graf jalan adalah model matematis untuk pergerakan pejalan kaki. Pertanyaan "seberapa mudah orang menyebar ke seluruh kota?" adalah pertanyaan tentang *mixing time* dari Markov chain di atas graf tersebut.

Ini bukan analogi superfisial — persamaan differensialnya identik secara matematis.

---

### Batas dan Anomali — Di Mana OSMnx Runtuh?

**1. Kualitas data OSM adalah batas paling nyata.** OSMnx menghasilkan graf sebaik data OSM-nya. Di Yogyakarta, data OSM relatif lengkap. Di daerah rural yang belum banyak dipetakan, grafnya akan penuh lubang. Kesalahan OSMnx seringkali bukan bug library — melainkan cerminan dari ketidaklengkapan data sumbernya.

**2. Simplifikasi topologi persimpangan kompleks.** Bundaran besar, interchange tol, atau simpang susun tidak direpresentasikan dengan sempurna. OSMnx punya fungsi `ox.consolidate_intersections()` untuk memperbaiki ini, tapi ia butuh pemahaman tentang toleransi jarak yang tepat.

**3. Travel time butuh estimasi.** OSMnx tidak tahu kecepatan aktual kendaraan. Ia menggunakan `maxspeed` dari OSM (yang sering tidak diisi) atau heuristik berdasarkan tipe jalan (`highway=residential` → 30 km/h, `highway=primary` → 50 km/h, dll.). Fungsi `ox.add_edge_speeds()` dan `ox.add_edge_travel_times()` menghandle ini, tapi akurasinya terbatas.

**4. Memori untuk kota besar.** Graf seluruh kota Jakarta dengan network_type='all' bisa menghabiskan beberapa GB RAM. Untuk analisis skala besar, kamu harus bekerja per-district atau menggunakan pendekatan streaming.

---

### Koneksi ke GeoJSON

OSMnx dan GeoJSON bukan dua dunia terpisah — keduanya adalah representasi berbeda dari data yang sama:

```python
# Graf OSMnx → GeoDataFrame → GeoJSON
import geopandas as gpd

# Konversi edge graph ke GeoDataFrame (tiap edge jadi satu baris dengan geometri)
nodes, edges = ox.graph_to_gdfs(G)

# edges adalah GeoDataFrame — kamu bisa export ke GeoJSON
edges.to_file("jaringan_jalan_jogja.geojson", driver="GeoJSON")

# Sebaliknya: GeoJSON polygon → gunakan sebagai batas area download
import json
with open("batas_wilayah.geojson") as f:
    polygon = json.load(f)

from shapely.geometry import shape
batas = shape(polygon["features"][0]["geometry"])
G_dari_polygon = ox.graph_from_polygon(batas, network_type="walk")
```

OSMnx memberikan topologi dan kemampuan analisis jaringan. GeoJSON memberikan format pertukaran universal. Shapely menangani geometri. Ketiganya adalah lapisan berbeda dari satu ekosistem yang koheren.

---

### Pertanyaan Generatif

Kamu punya dua titik di Yogyakarta: Stasiun Tugu dan Candi Prambanan. Rute terpendek berdasarkan `length` (meter) dan rute tercepat berdasarkan `travel_time` (detik) hampir pasti **berbeda**.

Tanpa menjalankan kode — dari mental model graf yang baru kamu bangun — **mengapa keduanya bisa berbeda, dan kondisi topologi jaringan jalan seperti apa yang akan membuat perbedaannya paling ekstrem?** Bayangkan di graf seperti apa rute "paling pendek secara jarak" justru menjadi "paling lambat secara waktu."