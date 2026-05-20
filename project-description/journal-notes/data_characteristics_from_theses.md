# Data Characteristics from Previous Theses (Same Dataset)

## Key findings from reading all 6 previous theses

### 1. Data Nature — Active MPD (Mobile Positioning Data)
- **Source:** GPS data from smartphone apps (active MPD), NOT cell tower triangulation (passive MPD)
- **Collection:** Via aggregator from apps requesting location permission (with user consent)
- **Columns:** maid (device ID), latitude, longitude, timestamp (unix epoch)
- **Coverage:** DIY (Daerah Istimewa Yogyakarta), October 2021 – June 2022
- **Accuracy:** GPS-level precision (meters), much better than passive MPD (100m–30km)

### 2. Critical Data Characteristic: ~85% Stationary Data
- **MOST IMPORTANT FINDING:** In Nurlita's thesis (Malioboro analysis), **84.4% of all GPS pings were from stationary users** (stay locations)
- Preprocessing: 2,195,131 → 342,123 (after stay removal) → 229,826 (after immobility filter + direction adjustment)
- This means: **only ~10-15% of raw GPS data represents actual movement**
- Our pipeline must handle this: the low-speed filter already addresses this somewhat, but the data is dominated by stationary pings

### 3. Stay Location Detection
- Nurlita used: stationary for ≥30 minutes within 200m radius → classified as stay
- After stay removal: 15.58% of data remained
- After eliminating points >20m from road: 15.52%
- After immobility filter (overlapping points post-map-matching): 10.46%

### 4. Low Sampling Rate
- This is **low-frequency GPS data** — users are not continuously tracked
- Rakhman et al. thesis specifically addresses "low-sampling-rate data" challenges
- Gap times between pings can be minutes to hours
- **Impact on our analysis:** Turning movement will be the hardest to detect accurately (confirmed as tertiary priority)
- Nurlita used 10-minute gap threshold for trajectory splitting (we proposed 30 min — may need to reconsider)

### 5. Map Matching Approaches Used by Seniors
- **Nurlita:** KDTree for initial matching → HMM + Viterbi for path reconstruction → time interpolation
- **Rakhman et al.:** KD-Tree nearest-neighbor → path reconstruction
- **HMM vs KD-Tree comparison:** HMM outperformed KD-Tree by ~20-30%, especially on sparse data
- BUT: HMM requires denser sequences; on very sparse data, both degrade

### 6. Vehicle vs Non-Vehicle Classification
- Intersection density thesis classified users by speed:
  - Non-vehicle: 0.36 km/h – 5 km/h (pedestrians, cyclists)
  - Vehicle: > 5 km/h
- Our low-speed filter (5 km/h threshold) aligns with this classification
- This is a known approach in the research group

### 7. Validation Approaches
- Nurlita validated speed patterns against Google Maps data: moderate correlation (r=0.52)
- Traffic flow validated against Dinas Perhubungan DIY data: weekday r=0.79, weekend r=0.44
- **Takeaway:** Our results should discuss validation limitations explicitly

### 8. Temporal Patterns Found by Seniors
- Weekdays: more predictable patterns, higher speeds
- Weekends: more variable, lower speeds
- Morning peak: 06:00–08:00, Evening peak: 15:00–18:00
- COVID-19 impact: data from late 2021 may show reduced mobility (PPKM period)

### 9. Implications for Our Pipeline
1. **Stay point removal is CRITICAL** — we already handle this via low-speed filter (removes MAIDs that never exceed 5 km/h), but we may need explicit stay detection
2. **Our 30-min gap threshold for trip segmentation needs justification** — Nurlita used 10 min, citing Zheng et al. We should test both
3. **Nearest-edge assignment is reasonable** — seniors used KDTree (geometric) as first step; HMM was for path reconstruction, not initial matching
4. **Our data is already heavily filtered** — from 8.9M pings → 625K (cleaned low-speed) means we've already removed most stationary data
5. **Turning movement accuracy will be limited** — explicitly acknowledged as tertiary

---

## External Literature Grounding (Beyond Lab Theses)

The lab theses above are valuable but focus on Malioboro Street (a one-way tourist corridor), not a multi-intersection ring road. Here are key external papers that directly support our methodology:

### Map Matching
- **Quddus et al. (2007)** — *"Current map-matching algorithms for transport applications"*, Transportation Research Part C. Classifies map-matching into 4 categories: geometric, topological, probabilistic, advanced. **Geometric (point-to-curve) is sufficient when the road network has low topological complexity** — which our fishbone structure has.
- **Newson & Krumm (2009)** — *"Hidden Markov Map Matching Through Noise and Sparseness"*, ACM SIGSPATIAL. The foundational HMM paper. Key finding: HMM works well at <30s sampling intervals, but **accuracy degrades significantly as sampling interval increases**. Our data has median gaps of minutes to hours → HMM would not add value over geometric matching on our simple network.
- **Yang & Gidofalvi (2018)** — *"Fast map matching"*, IJGIS. Integrates HMM with precomputation. Confirms that for complex urban grids, HMM is necessary, but **simpler networks benefit less from the transition probability modeling**.

### Trajectory Segmentation
- **Zheng (2015)** — *"Trajectory Data Mining: An Overview"*, ACM TIST. The definitive survey. Classifies segmentation into time-based, shape-based, and semantic-based. Notes that **threshold values are heuristic and application-specific**. Does NOT mandate a specific threshold — the 10-min vs 30-min choice depends on data characteristics.
- **Key insight:** Zheng's framework supports our approach of time-gap segmentation. The exact threshold (10 min) is justified by the low sampling rate of our data — longer gaps produce unreliable path inference.

### OD Matrix from Mobile Data
- **Alexander et al. (2015)** — *"Origin–destination trips by purpose and time of day inferred from mobile phone data"*, Transportation Research Part C. Validates that mobile-phone-derived OD matrices correlate well with survey data at aggregate spatial scales. **Key caveat: accuracy improves with spatial aggregation** — our intersection-level analysis (6 zones) is appropriate.
- **Calabrese et al. (2013)** — *"Understanding individual mobility patterns from urban sensing data"*, Transportation Research Part C. Demonstrates mobile phone traces as a reasonable proxy for individual mobility. Validated against odometer data. **Supports using MAID-level analysis for traffic characterization.**

### Home Location Estimation (Catchment)
- **Ahas et al. (2010)** — *"Using mobile positioning data to model locations meaningful to users"*, Journal of Urban Technology. Introduces the **anchor point model** — identifying home/work locations from temporal patterns of mobile activity. Uses nighttime activity for home identification, which is exactly our approach.
- **Validation:** Ahas et al. validated against population registry data at municipality level. Our grid-based approach (~550m resolution) is consistent with their methodology.

### Data Characteristics — Active MPD
- Active MPD (GPS-based, with user consent) is fundamentally different from passive MPD (CDR-based, cell tower). Our data has GPS-level accuracy (meters) but **very low temporal frequency** — this is consistent with the literature's characterization of smartphone GPS data collected passively by apps.
- The ~85% stationary data finding is consistent with Calabrese et al. (2013) who noted that mobile traces disproportionately capture stationary activities.
