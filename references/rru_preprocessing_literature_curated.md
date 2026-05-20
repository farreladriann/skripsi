# Kurasi Literatur Ketat — GPS/MPD Preprocessing untuk Skripsi RRU

Kurasi ini memperketat hasil pencarian OpenAlex agar hanya memuat paper yang benar-benar terkait GPS trajectory, map matching, low-sampling trajectory, mobile phone/MPD OD, stay point, probe/floating vehicle, traffic estimation, atau akurasi GPS/A-GPS.

## Paper utama hasil pencarian

### 1. Feature-based Map Matching for Low-Sampling-Rate GPS Trajectories
- **Tahun/sumber**: 2018 — ACM Transactions on Spatial Algorithms and Systems
- **Penulis**: Yifang Yin, Rajiv Ratn Shah, Guanfeng Wang, Roger Zimmermann
- **Sitasi OpenAlex**: 32
- **DOI**: https://doi.org/10.1145/3223049
- **Open PDF**: -
- **Keyword cocok**: map matching, gps traject, low-sampling, low sampling rate
- **Pemakaian untuk RRU**: Justifikasi bahwa GPS/MPD perlu map matching/filtering terhadap jaringan jalan; juga mendukung kehati-hatian pada data sparse/noisy.
- **Abstrak metadata**: With the increasing availability of GPS-equipped mobile devices, location-based services have become an integral part of everyday life. Among one of the initial steps of positioning data management, map matching aims to reduce the uncertainty in a trajectory by matching the GPS points to the road network on a digital map. Most existing work has focused on estimating the likelihood of a candidate route based on the GPS observations, while neglecting to model the probability of a route choice from the perspective of drivers. In this work, we prop…

### 2. A Trajectory Collaboration Based Map Matching Approach for Low-Sampling-Rate GPS Trajectories
- **Tahun/sumber**: 2020 — Sensors
- **Penulis**: Wentao Bian, Ge Cui, Xin Wang
- **Sitasi OpenAlex**: 18
- **DOI**: https://doi.org/10.3390/s20072057
- **Open PDF**: https://www.mdpi.com/1424-8220/20/7/2057/pdf?version=1586176275
- **Keyword cocok**: map matching, gps traject, low-sampling, low sampling rate
- **Pemakaian untuk RRU**: Justifikasi bahwa GPS/MPD perlu map matching/filtering terhadap jaringan jalan; juga mendukung kehati-hatian pada data sparse/noisy.
- **Abstrak metadata**: GPS (Global Positioning System) trajectories with low sampling rates are prevalent in many applications. However, current map matching methods do not perform well for low-sampling-rate GPS trajectories due to the large uncertainty between consecutive GPS points. In this paper, a collaborative map matching method (CMM) is proposed for low-sampling-rate GPS trajectories. CMM processes GPS trajectories in batches. First, it groups similar GPS trajectories into clusters and then supplements the missing information by resampling. A collaborative GPS…

### 3. A Hidden Markov Model-Based Map-Matching Approach for Low-Sampling-Rate GPS Trajectories
- **Tahun/sumber**: 2017 — ?
- **Penulis**: Yu-Ling Hsueh, Ho-Chian Chen, Weijie Huang
- **Sitasi OpenAlex**: 13
- **DOI**: https://doi.org/10.1109/sc2.2017.52
- **Open PDF**: -
- **Keyword cocok**: map matching, map-matching, gps traject, low-sampling
- **Pemakaian untuk RRU**: Justifikasi bahwa GPS/MPD perlu map matching/filtering terhadap jaringan jalan; juga mendukung kehati-hatian pada data sparse/noisy.
- **Abstrak metadata**: Map matching is the process of matching a series of recorded geographic coordinates (e.g., a GPS trajectory) to a road network. Due to GPS positioning errors and the sampling constraints, the GPS data collected by the GPS devices are not precise, and the location of a user cannot always be correctly shown on the map. Unfortunately, most current map-matching algorithms only consider the distance between the GPS points and the road segments, the topology of the road network, and the speed constraint of the road segment to determine the matching r…

### 4. Real-time urban traffic sensing with GPS equipped Probe Vehicles
- **Tahun/sumber**: 2012 — ?
- **Penulis**: Peng-Jui Tseng, Chia-Chen Hung, Tsung-Hsun Chang, Yu-Hsiang Chuang
- **Sitasi OpenAlex**: 10
- **DOI**: https://doi.org/10.1109/itst.2012.6425188
- **Open PDF**: -
- **Keyword cocok**: map matching, gps traject, probe vehicle, floating car
- **Pemakaian untuk RRU**: Konteks probe/floating vehicle: data sampel dapat menangkap pola, tetapi butuh kalibrasi untuk menjadi volume/arus aktual.
- **Abstrak metadata**: GPS-based Vehicle Probe (GVP) has become an important floating car source in Intelligent Transportation System (ITS) for its efficiency and accuracy. We develop a real time GVP traffic estimation system in Taiwan by collecting the GPS data of commercial fleet and taxi. After filtering out some improper data, the retained GPS data are processed by an incremental map matching method which maps the GPS trajectories to real road map concerning of latency and accuracy. Then, road speed information can be produced by Speed Estimation module. To suppl…

### 5. Map-matching for low-sampling-rate GPS trajectories
- **Tahun/sumber**: 2009 — ?
- **Penulis**: Yin Lou, Chengyang Zhang, Yu Zheng, Xing Xie, Wei Wang, Yan Huang
- **Sitasi OpenAlex**: 784
- **DOI**: https://doi.org/10.1145/1653771.1653820
- **Open PDF**: -
- **Keyword cocok**: map-matching, gps traject, low-sampling
- **Pemakaian untuk RRU**: Justifikasi bahwa GPS/MPD perlu map matching/filtering terhadap jaringan jalan; juga mendukung kehati-hatian pada data sparse/noisy.
- **Abstrak metadata**: Map-matching is the process of aligning a sequence of observed user positions with the road network on a digital map. It is a fundamental pre-processing step for many applications, such as moving object management, traffic flow analysis, and driving directions. In practice there exists huge amount of low-sampling-rate (e.g., one point every 2--5 minutes) GPS trajectories. Unfortunately, most current map-matching approaches only deal with high-sampling-rate (typically one point every 10--30s) GPS data, and become less effective for low-sampling-…

### 6. An Interactive-Voting Based Map Matching Algorithm
- **Tahun/sumber**: 2010 — ?
- **Penulis**: Jing Yuan, Yu Zheng, Chengyang Zhang, Xing Xie, Guangzhong Sun
- **Sitasi OpenAlex**: 315
- **DOI**: https://doi.org/10.1109/mdm.2010.14
- **Open PDF**: -
- **Keyword cocok**: map matching, gps traject, low-sampling
- **Pemakaian untuk RRU**: Justifikasi bahwa GPS/MPD perlu map matching/filtering terhadap jaringan jalan; juga mendukung kehati-hatian pada data sparse/noisy.
- **Abstrak metadata**: Matching a raw GPS trajectory to roads on a digital map is often referred to as the Map Matching problem. However, the occurrence of the low-sampling-rate trajectories (e.g. one point per 2 minutes) has brought lots of challenges to existing map matching algorithms. To address this problem, we propose an Interactive Voting-based Map Matching (IVMM) algorithm based on the following three insights: 1) The position context of a GPS point as well as the topological information of road networks, 2) the mutual influence between GPS points (i.e., the …

### 7. Reducing Uncertainty of Low-Sampling-Rate Trajectories
- **Tahun/sumber**: 2012 — ?
- **Penulis**: Kai Zheng, Yu Zheng, Xing Xie, Xiaofang Zhou
- **Sitasi OpenAlex**: 248
- **DOI**: https://doi.org/10.1109/icde.2012.42
- **Open PDF**: -
- **Keyword cocok**: map-matching, low-sampling, low sampling rate
- **Pemakaian untuk RRU**: Justifikasi bahwa frekuensi sampling rendah membatasi rekonstruksi lintasan dan klasifikasi belokan aktual.
- **Abstrak metadata**: The increasing availability of GPS-embedded mobile devices has given rise to a new spectrum of location-based services, which have accumulated a huge collection of location trajectories. In practice, a large portion of these trajectories are of low-sampling-rate. For instance, the time interval between consecutive GPS points of some trajectories can be several minutes or even hours. With such a low sampling rate, most details of their movement are lost, which makes them difficult to process effectively. In this work, we investigate how to reduc…

### 8. Online map-matching based on Hidden Markov model for real-time traffic sensing applications
- **Tahun/sumber**: 2012 — ?
- **Penulis**: Changzuo Goh, Justin Dauwels, Nikola Mitrović, Muhammad Tayyab Asif, Ali Oran, P Jaillet
- **Sitasi OpenAlex**: 221
- **DOI**: https://doi.org/10.1109/itsc.2012.6338627
- **Open PDF**: -
- **Keyword cocok**: map-matching, gps traject, probe vehicle
- **Pemakaian untuk RRU**: Justifikasi bahwa GPS/MPD perlu map matching/filtering terhadap jaringan jalan; juga mendukung kehati-hatian pada data sparse/noisy.
- **Abstrak metadata**: In many Intelligent Transportation System (ITS) applications that crowd-source data from probe vehicles, a crucial step is to accurately map the GPS trajectories to the road network in real time. This process, known as map-matching, often needs to account for noise and sparseness of the data because (1) highly precise GPS traces are rarely available, and (2) dense trajectories are costly for live transmission and storage. We propose an online map-matching algorithm based on the Hidden Markov Model (HMM) that is robust to noise and sparseness. W…

### 9. Map matching for low-sampling-rate GPS trajectories by exploring real-time moving directions
- **Tahun/sumber**: 2017 — Information Sciences
- **Penulis**: Yu-Ling Hsueh, Ho-Chian Chen
- **Sitasi OpenAlex**: 102
- **DOI**: https://doi.org/10.1016/j.ins.2017.12.031
- **Open PDF**: -
- **Keyword cocok**: map matching, gps traject, low-sampling
- **Pemakaian untuk RRU**: Justifikasi bahwa GPS/MPD perlu map matching/filtering terhadap jaringan jalan; juga mendukung kehati-hatian pada data sparse/noisy.
- **Abstrak metadata**: Tidak ada abstrak di metadata.

### 10. Enhanced Map-Matching Algorithm with a Hidden Markov Model for Mobile Phone Positioning
- **Tahun/sumber**: 2017 — ISPRS International Journal of Geo-Information
- **Penulis**: An Luo, Shenghua Chen, Bin Xv
- **Sitasi OpenAlex**: 47
- **DOI**: https://doi.org/10.3390/ijgi6110327
- **Open PDF**: https://www.mdpi.com/2220-9964/6/11/327/pdf?version=1511243425
- **Keyword cocok**: map-matching, mobile phone data, low sampling rate
- **Pemakaian untuk RRU**: Justifikasi bahwa GPS/MPD perlu map matching/filtering terhadap jaringan jalan; juga mendukung kehati-hatian pada data sparse/noisy.
- **Abstrak metadata**: Numerous map-matching techniques have been developed to improve positioning, using Global Positioning System (GPS) data and other sensors. However, most existing map-matching algorithms process GPS data with high sampling rates, to achieve a higher correct rate and strong universality. This paper introduces a novel map-matching algorithm based on a hidden Markov model (HMM) for GPS positioning and mobile phone positioning with a low sampling rate. The HMM is a statistical model well known for providing solutions to temporal recognition applicat…

### 11. Grab-Posisi
- **Tahun/sumber**: 2019 — ?
- **Penulis**: Xiaocheng Huang, Yifang Yin, Simon Lim, Guanfeng Wang, Bo Hu, Jagannadan Varadarajan, et al.
- **Sitasi OpenAlex**: 46
- **DOI**: https://doi.org/10.1145/3356995.3364536
- **Open PDF**: -
- **Keyword cocok**: map matching, gps traject, low sampling rate
- **Pemakaian untuk RRU**: Dukungan umum untuk preprocessing trajectory/mobility dari data GPS/MPD.
- **Abstrak metadata**: Real-world GPS trajectory datasets are essential for geographical applications such as map inference, map matching, traffic detection, etc. Currently only a handful of GPS trajectory datasets are publicly available and the quality of these datasets varies. Most of the existing datasets have limited geographical coverage (a focus on China or the USA), have low sampling rates and less contextual information of the GPS pings. This paper presents Grab-Posisi, the first GPS trajectory dataset of Southeast Asia from both developed countries (Singapor…

### 12. Calibrating Large Scale Vehicle Trajectory Data
- **Tahun/sumber**: 2012 — ?
- **Penulis**: Siyuan Liu, Ce Liu, Qiong Luo, Lionel M. Ni, Ramayya Krishnan
- **Sitasi OpenAlex**: 37
- **DOI**: https://doi.org/10.1109/mdm.2012.15
- **Open PDF**: -
- **Keyword cocok**: map matching, gps traject, low sampling rate
- **Pemakaian untuk RRU**: Dukungan umum untuk preprocessing trajectory/mobility dari data GPS/MPD.
- **Abstrak metadata**: An accurate and sufficient vehicle trajectory data set is the basis to many trajectory-based data mining tasks and applications. However, vehicle trajectories sampled by GPS devices are usually at a relatively low sampling rate and contain notable location errors. To address these two problems in GPS trajectory data, we propose WI-matching, the first vehicle trajectory calibration framework to take advantage of road networks topology and geometry information and trajectory historical information in large scale. WI-matching consists of a Weighti…

### 13. A novel algorithm of low sampling rate GPS trajectories on map-matching
- **Tahun/sumber**: 2017 — EURASIP Journal on Wireless Communications and Networking
- **Penulis**: Yankai Liu, Zhuo Li
- **Sitasi OpenAlex**: 17
- **DOI**: https://doi.org/10.1186/s13638-017-0814-6
- **Open PDF**: https://jwcn-eurasipjournals.springeropen.com/track/pdf/10.1186/s13638-017-0814-6
- **Keyword cocok**: map-matching, gps traject, low sampling rate
- **Pemakaian untuk RRU**: Justifikasi bahwa GPS/MPD perlu map matching/filtering terhadap jaringan jalan; juga mendukung kehati-hatian pada data sparse/noisy.
- **Abstrak metadata**: Map-matching is the process of matching the GPS locus to the road network on the digital map. However, due to the most existing map-matching algorithms that are based on high sampling rate, when the sampling interval is increased, the correct rate of the algorithm will be greatly reduced. Based on this, this paper proposed a new algorithm of map-matching for low sampling rate GPS trajectories. The algorithm gave full consideration to the road network of the geometric structure and topological structure and the mutual influence between adjacent …

### 14. A Big Data Demand Estimation Model for Urban Congested Networks
- **Tahun/sumber**: 2020 — Transport and Telecommunication Journal
- **Penulis**: Guido Cantelmo, Francesco Viti
- **Sitasi OpenAlex**: 8
- **DOI**: https://doi.org/10.2478/ttj-2020-0019
- **Open PDF**: https://sciendo.com/pdf/10.2478/ttj-2020-0019
- **Keyword cocok**: floating car, mobile phone data, origin-destination
- **Pemakaian untuk RRU**: Dukungan umum untuk preprocessing trajectory/mobility dari data GPS/MPD.
- **Abstrak metadata**: Abstract The origin-destination (OD) demand estimation problem is a classical problem in transport planning and management. Traditionally, this problem has been solved using traffic counts, speeds or travel times extracted from location-based sensor data. With the advent of new sensing technologies located on vehicles (GPS) and nomadic devices (mobile and smartphones), new opportunities have emerged to improve the estimation accuracy and reliability, and more importantly to better capture the dynamics of the daily mobility patterns. In this pap…

### 15. Erratum to: A novel algorithm of low sampling rate GPS trajectories on map-matching
- **Tahun/sumber**: 2017 — EURASIP Journal on Wireless Communications and Networking
- **Penulis**: Yankai Liu, Zhuo Li
- **Sitasi OpenAlex**: 4
- **DOI**: https://doi.org/10.1186/s13638-017-0933-0
- **Open PDF**: https://jwcn-eurasipjournals.springeropen.com/track/pdf/10.1186/s13638-017-0933-0
- **Keyword cocok**: map-matching, gps traject, low sampling rate
- **Pemakaian untuk RRU**: Justifikasi bahwa GPS/MPD perlu map matching/filtering terhadap jaringan jalan; juga mendukung kehati-hatian pada data sparse/noisy.
- **Abstrak metadata**: Since the publication of our article The first sentence of subsection 3.3 should read as follows: "In subsections 3.3 and 3.4, "Time Analysis" and "Result Matching", which are based on the methods proposed by Lou et al. (2009) [2], are utilized as the part of our design flow. These two steps are summarized as follows." In addition, the legend for Fig. 3 should read: "Influence factors of track point matching time speed information.

### 16. Optimization Big Data Real-time Analytics Using Mobile Phone Data in Origin Destination National Transportation (ATTN) Survey
- **Tahun/sumber**: 2019 — ?
- **Penulis**: Okkie Putriani, Sigit Priyanto
- **Sitasi OpenAlex**: 3
- **DOI**: https://doi.org/10.2991/apte-18.2019.39
- **Open PDF**: https://download.atlantis-press.com/article/125918755.pdf
- **Keyword cocok**: floating car, mobile phone data, origin destination
- **Pemakaian untuk RRU**: Justifikasi OD berbasis data mobile sebagai inferred/observed OD; cocok untuk framing OD zona, bukan asal-tujuan sebenarnya.
- **Abstrak metadata**: The ATTN 2018 data collection process is obtained from the data collection of the sample OD-matrix using cellular data, carried out with the aim of obtaining data on the Origin Destination Matrix (movement) of the mobile phone user movement for a given period to get the sample OD-matrix. Data signals from cellular networks can be a means of analysing transportation systems to help formulate transportation models to predict future users. FCD (floating car/cellular data) is based on the collection of localization data, speed, direction of travel …

### 17. An Accurate and Fast Global Map-Matching Approach for Low-Sampling-Rate GPS Trajectories
- **Tahun/sumber**: 2020 — 2020 7th International Forum on Electrical Engineering and Automation (IFEEA)
- **Penulis**: Mao Du, Lin Yang, Jingni Yuan
- **Sitasi OpenAlex**: 2
- **DOI**: https://doi.org/10.1109/ifeea51475.2020.00150
- **Open PDF**: -
- **Keyword cocok**: map-matching, gps traject, low-sampling
- **Pemakaian untuk RRU**: Justifikasi bahwa GPS/MPD perlu map matching/filtering terhadap jaringan jalan; juga mendukung kehati-hatian pada data sparse/noisy.
- **Abstrak metadata**: Current global matching algorithms for low-sampling rate data still face the challenges of large computational costs and significant declines in accuracy with increases in the sampling interval time. Therefore, this paper proposes a novel global map-matching algorithm based on the hidden Markov model to match the data accurately and quickly. First, we utilize the road accessibility instead of the gridding or confidence intervals to obtain the candidate information. Then, this algorithm synthetically considers the trajectory location at the prev…

### 18. Positional Accuracy of Assisted GPS Data from High-Sensitivity GPS-enabled Mobile Phones
- **Tahun/sumber**: 2011 — Journal of Navigation
- **Penulis**: Paul A. Zandbergen, Sean Barbeau
- **Sitasi OpenAlex**: 306
- **DOI**: https://doi.org/10.1017/s0373463311000051
- **Open PDF**: -
- **Keyword cocok**: positional accuracy, assisted gps
- **Pemakaian untuk RRU**: Justifikasi toleransi spasial/buffer karena akurasi GPS/A-GPS bervariasi di lingkungan urban.
- **Abstrak metadata**: Utilizing both Assisted GPS (A-GPS) techniques and new high-sensitivity embedded GPS hardware, mobile phones are now able to achieve positioning in harsh environments such as urban canyons and indoor locations where older embedded GPS chips could not. This paper presents an empirical analysis of the positional accuracy of location data gathered using a high-sensitivity GPS-enabled mobile phone. The performance of the mobile phone is compared to that of regular recreational grade GPS receivers. Availability of valid GPS position fixes on the mob…

### 19. Path and travel time inference from GPS probe vehicle data
- **Tahun/sumber**: 2009 — ?
- **Penulis**: Timothy Hunter, Ryan Herring, Pieter Abbeel, Alexandre M. Bayen
- **Sitasi OpenAlex**: 120
- **DOI**: -
- **Open PDF**: -
- **Keyword cocok**: gps probe, probe vehicle
- **Pemakaian untuk RRU**: Konteks probe/floating vehicle: data sampel dapat menangkap pola, tetapi butuh kalibrasi untuk menjadi volume/arus aktual.
- **Abstrak metadata**: We consider the problem of estimating real-time traffic conditions from sparse, noisy GPS probe vehicle data. We specifically address arterial roads, which are also known as the secondary road network (highways are considered the primary road network). We consider several estimation problems: historical traffic patterns, real-time traffic conditions, and forecasting future traffic conditions. We assume that the data available for these estimation problems is a small set of sparsely traced vehicle trajectories, which represents a small fraction …

### 20. MTrajRec
- **Tahun/sumber**: 2021 — ?
- **Penulis**: Huimin Ren, Sijie Ruan, Yanhua Li, Jie Bao, Chuishi Meng, Ruiyuan Li, et al.
- **Sitasi OpenAlex**: 87
- **DOI**: https://doi.org/10.1145/3447548.3467238
- **Open PDF**: -
- **Keyword cocok**: map matching, low sampling rate
- **Pemakaian untuk RRU**: Dukungan umum untuk preprocessing trajectory/mobility dari data GPS/MPD.
- **Abstrak metadata**: With the increasing adoption of GPS modules, there are a wide range of urban applications based on trajectory data analysis, such as vehicle navigation, travel time estimation, and driver behavior analysis. The effectiveness of urban applications relies greatly on the high sampling rates of trajectories precisely matched to the map. However, a large number of trajectories are collected under a low sampling rate in real-world practice, due to certain communication loss and energy constraints. To enhance the trajectory data and support the urban …

### 21. IF-Matching: Towards Accurate Map-Matching with Information Fusion
- **Tahun/sumber**: 2016 — IEEE Transactions on Knowledge and Data Engineering
- **Penulis**: Gang Hu, Jie Shao, Fenglin Liu, Wang Yuan, Heng Tao Shen
- **Sitasi OpenAlex**: 74
- **DOI**: https://doi.org/10.1109/tkde.2016.2617326
- **Open PDF**: -
- **Keyword cocok**: map-matching, gps traject
- **Pemakaian untuk RRU**: Justifikasi bahwa GPS/MPD perlu map matching/filtering terhadap jaringan jalan; juga mendukung kehati-hatian pada data sparse/noisy.
- **Abstrak metadata**: With the advance of various location-acquisition technologies, a myriad of GPS trajectories can be collected every day. However, the raw coordinate data captured by sensors often cannot reflect real positions due to many physical constraints and some rules of law. How to accurately match GPS trajectories to roads on a digital map is an important issue. The problem of map-matching is fundamental for many applications. Unfortunately, many existing methods still cannot meet stringent performance requirements in engineering. In particular, low/unst…

### 22. Convolutional LSTM based transportation mode learning from raw GPS trajectories
- **Tahun/sumber**: 2020 — IET Intelligent Transport Systems
- **Penulis**: Asif Nawaz, Huang Zhiqiu, Senzhang Wang, Yasir Hussain, Izhar Ahmed Khan, Zaheer Ullah Khan
- **Sitasi OpenAlex**: 52
- **DOI**: https://doi.org/10.1049/iet-its.2019.0017
- **Open PDF**: -
- **Keyword cocok**: gps traject, trajectory data mining
- **Pemakaian untuk RRU**: Dukungan umum untuk preprocessing trajectory/mobility dari data GPS/MPD.
- **Abstrak metadata**: With the advancement of location acquisition technologies, a large amount of raw global positioning system (GPS) trajectory data is produced by many moving devices. Learning transportation modes from the GPS trajectory data is an important problem in the domain of trajectory data mining. Traditional supervised learning‐based approaches rely heavily on data preprocessing and feature engineering, which require domain expertise and are time consuming. The authors propose a deep learning‐based convolutional long short term memory (LSTM) model for t…

### 23. Investigating the Mobile Phone Data to Estimate the Origin Destination Flow and Analysis; Case Study: Paris Region
- **Tahun/sumber**: 2015 — Transportation research procedia
- **Penulis**: Anahid Nabavi Larijani, Ana‐Maria Olteanu‐Raimond, Julien Perret, Mathieu Brédif, Cezary Ziemlicki
- **Sitasi OpenAlex**: 45
- **DOI**: https://doi.org/10.1016/j.trpro.2015.03.006
- **Open PDF**: -
- **Keyword cocok**: mobile phone data, origin destination
- **Pemakaian untuk RRU**: Justifikasi OD berbasis data mobile sebagai inferred/observed OD; cocok untuk framing OD zona, bukan asal-tujuan sebenarnya.
- **Abstrak metadata**: This paper is an output of a French national project called iSpace&Time aiming to provide a 4 dimensional platform of an urban dynamics. In order to express the urban traffic, we took an advantage of the mobile phone data to investigate the behavior of the origin destination flow within the Paris and its suburb aiming to explore the different mode of the transportation. Indeed the spatiotemporal heterogeneities of mobile phone data make the task of mode of transportation separation very challenging, sometimes even impossible. Thus, by exploring…

### 24. Probe vehicle lane identification for queue length estimation at intersections
- **Tahun/sumber**: 2017 — Journal of Intelligent Transportation Systems
- **Penulis**: Semuel Y. R. Rompis, Mecit Cetin, Filmon Habtemichael
- **Sitasi OpenAlex**: 32
- **DOI**: https://doi.org/10.1080/15472450.2017.1300887
- **Open PDF**: -
- **Keyword cocok**: gps probe, probe vehicle
- **Pemakaian untuk RRU**: Konteks probe/floating vehicle: data sampel dapat menangkap pola, tetapi butuh kalibrasi untuk menjadi volume/arus aktual.
- **Abstrak metadata**: Vehicles instrumented with Global Positioning Systems, also known as GPS probe vehicles, have become increasingly popular for collecting traffic flow data. Previous studies have explored the probe vehicle data for estimating speeds and travel time; however, there is very limited research on predicting queue dynamics from such data. In this research, a methodology was developed for identifying the lane position of the GPS-instrumented vehicles when they are standing in the queue at signalized intersections with multiple lanes, particularly in th…

### 25. Dynamic Origin-Destination Flow Prediction Using Spatial-Temporal Graph Convolution Network With Mobile Phone Data
- **Tahun/sumber**: 2021 — IEEE Intelligent Transportation Systems Magazine
- **Penulis**: Zhichen Liu, Zhiyuan Liu, Xiao Fu
- **Sitasi OpenAlex**: 20
- **DOI**: https://doi.org/10.1109/mits.2021.3082397
- **Open PDF**: -
- **Keyword cocok**: mobile phone data, origin-destination
- **Pemakaian untuk RRU**: Justifikasi OD berbasis data mobile sebagai inferred/observed OD; cocok untuk framing OD zona, bukan asal-tujuan sebenarnya.
- **Abstrak metadata**: Massive mobile phone data provide continuous and large-scale dynamic origin–destination (OD) flow information for multiple modes of transportation. In this study, we represent the dynamic OD flows obtained from mobile phone data as time-dependent graphs and propose two novel spatial-temporal graph convolutional network (STGCN)-based models to predict dynamic OD flows. Both models directly operate on the graph-structured OD flows, capture correlations among OD flows far apart in the Euclidean space, and fully explore the complex spatial-temporal…

### 26. Sample size analysis of GPS probe vehicles for urban traffic state estimation
- **Tahun/sumber**: 2011 — ?
- **Penulis**: Qiankun Zhao, Qing‐Jie Kong, Yingjie Xia, Yuncai Liu
- **Sitasi OpenAlex**: 18
- **DOI**: https://doi.org/10.1109/itsc.2011.6082829
- **Open PDF**: -
- **Keyword cocok**: gps probe, probe vehicle
- **Pemakaian untuk RRU**: Konteks probe/floating vehicle: data sampel dapat menangkap pola, tetapi butuh kalibrasi untuk menjadi volume/arus aktual.
- **Abstrak metadata**: Nowadays, probe vehicles equipped with Global Position System (GPS) are an effective way of collecting real-time traffic information. This paper first briefly introduces the Curve-Fitting Estimation Model (CFEM), which is one of the typical methods using GPS data to estimate the traffic flow state. After that, it is detailedly analyzed how many probe vehicles the CFEM requires in order to ensure enough estimated accuracy. Furthermore, a sample size algorithm is developed to calculate the minimum sample size of the CFEM. In the algorithm, the ro…

### 27. Traffic Flow Estimation using Probe Vehicle Data
- **Tahun/sumber**: 2020 — ?
- **Penulis**: Olga Gkountouna, Dieter Pfoser, Andreas Züfle
- **Sitasi OpenAlex**: 14
- **DOI**: https://doi.org/10.1109/dsaa49011.2020.00073
- **Open PDF**: -
- **Keyword cocok**: probe vehicle, traffic flow estimation
- **Pemakaian untuk RRU**: Konteks probe/floating vehicle: data sampel dapat menangkap pola, tetapi butuh kalibrasi untuk menjadi volume/arus aktual.
- **Abstrak metadata**: Traffic sensing has been revolutionized with the commoditization of GPS technology. Smartphone navigation applications ubiquitously track vehicles as samples of the overall traffic. This so-called Probe Vehicle Data (PVD) has replaced traditional road-side sensor technologies, such as induction loops and microwave sensors, given its relative low cost, good coverage, and reliability. However, while PVD allows us to assess speed and by extension the overall traffic condition in a road network, this sample-based approach does not provide us with t…

### 28. Deriving driver-centric travel information by mining delay patterns from single GPS trajectories
- **Tahun/sumber**: 2014 — ?
- **Penulis**: Richard Brunauer, Karl Rehrl
- **Sitasi OpenAlex**: 10
- **DOI**: https://doi.org/10.1145/2674918.2674922
- **Open PDF**: -
- **Keyword cocok**: gps traject, floating car
- **Pemakaian untuk RRU**: Dukungan umum untuk preprocessing trajectory/mobility dari data GPS/MPD.
- **Abstrak metadata**: Crowd-sourcing approaches for generating accurate real time travel information for road networks is promising but still challenging. For example, travel speeds, even if derived from highly sampled GPS trajectories, have limitations in their interpretability for more sophisticated travel information such as traffic-related delays or level of service (LOS) information. The proposed algorithm in this work analyzes the flow characteristics of individual vehicles by deriving and classifying delays into LOS relevant (e.g. queuing traffic) and LOS non…

### 29. Hidden Markov map matching through noise and sparseness
- **Tahun/sumber**: 2009 — ?
- **Penulis**: Paul Newson, John Krumm
- **Sitasi OpenAlex**: 995
- **DOI**: https://doi.org/10.1145/1653771.1653818
- **Open PDF**: -
- **Keyword cocok**: map matching
- **Pemakaian untuk RRU**: Justifikasi bahwa GPS/MPD perlu map matching/filtering terhadap jaringan jalan; juga mendukung kehati-hatian pada data sparse/noisy.
- **Abstrak metadata**: The problem of matching measured latitude/longitude points to roads is becoming increasingly important. This paper describes a novel, principled map matching algorithm that uses a Hidden Markov Model (HMM) to find the most likely road route represented by a time-stamped sequence of latitude/longitude pairs. The HMM elegantly accounts for measurement noise and the layout of the road network. We test our algorithm on ground truth data collected from a GPS receiver in a vehicle. Our test shows how the algorithm breaks down as the sampling rate of …

### 30. VTrack
- **Tahun/sumber**: 2009 — ?
- **Penulis**: Arvind Thiagarajan, Lenin Ravindranath, Katrina LaCurts, Samuel Madden, Hari Balakrishnan, Sivan Toledo, et al.
- **Sitasi OpenAlex**: 784
- **DOI**: https://doi.org/10.1145/1644038.1644048
- **Open PDF**: -
- **Keyword cocok**: map matching
- **Pemakaian untuk RRU**: Dukungan umum untuk preprocessing trajectory/mobility dari data GPS/MPD.
- **Abstrak metadata**: Traffic delays and congestion are a major source of inefficiency, wasted fuel, and commuter frustration. Measuring and localizing these delays, and routing users around them, is an important step towards reducing the time people spend stuck in traffic. As others have noted, the proliferation of commodity smartphones that can provide location estimates using a variety of sensors---GPS, WiFi, and/or cellular triangulation---opens up the attractive possibility of using position samples from drivers' phones to monitor traffic delays at a fine spati…

### 31. A survey of results on mobile phone datasets analysis
- **Tahun/sumber**: 2015 — EPJ Data Science
- **Penulis**: Vincent D. Blondel, Adeline Decuyper, Gautier Krings
- **Sitasi OpenAlex**: 646
- **DOI**: https://doi.org/10.1140/epjds/s13688-015-0046-0
- **Open PDF**: https://epjdatascience.springeropen.com/track/pdf/10.1140/epjds/s13688-015-0046-0
- **Keyword cocok**: mobile phone data
- **Pemakaian untuk RRU**: Dukungan umum untuk preprocessing trajectory/mobility dari data GPS/MPD.
- **Abstrak metadata**: In this paper, we review some advances made recently in the study of mobile phone datasets. This area of research has emerged a decade ago, with the increasing availability of large-scale anonymized datasets, and has grown into a stand-alone topic. We survey the contributions made so far on the social networks that can be constructed with such data, the study of personal mobility, geographical partitioning, urban planning, and help towards development as well as security and privacy issues.

### 32. Estimating Origin-Destination Flows Using Mobile Phone Location Data
- **Tahun/sumber**: 2011 — IEEE Pervasive Computing
- **Penulis**: Francesco Calabrese, Giusy Di Lorenzo, Liang Liu, Carlo Ratti
- **Sitasi OpenAlex**: 496
- **DOI**: https://doi.org/10.1109/mprv.2011.41
- **Open PDF**: https://dspace.mit.edu/bitstream/1721.1/101623/1/Ratti_Estimating%20origin.pdf
- **Keyword cocok**: origin-destination
- **Pemakaian untuk RRU**: Justifikasi OD berbasis data mobile sebagai inferred/observed OD; cocok untuk framing OD zona, bukan asal-tujuan sebenarnya.
- **Abstrak metadata**: Using an algorithm to analyze opportunistically collected mobile phone location data, the authors estimate weekday and weekend travel patterns of a large metropolitan area with high accuracy.

### 33. Travel time estimation for urban road networks using low frequency probe vehicle data
- **Tahun/sumber**: 2013 — Transportation Research Part B Methodological
- **Penulis**: Erik Jenelius, Haris N. Koutsopoulos
- **Sitasi OpenAlex**: 430
- **DOI**: https://doi.org/10.1016/j.trb.2013.03.008
- **Open PDF**: https://arxiv.org/pdf/1109.1966
- **Keyword cocok**: probe vehicle
- **Pemakaian untuk RRU**: Konteks probe/floating vehicle: data sampel dapat menangkap pola, tetapi butuh kalibrasi untuk menjadi volume/arus aktual.
- **Abstrak metadata**: Tidak ada abstrak di metadata.

### 34. A Survey of Traffic Prediction: from Spatio-Temporal Data to Intelligent Transportation
- **Tahun/sumber**: 2021 — Data Science and Engineering
- **Penulis**: Haitao Yuan, Guoliang Li
- **Sitasi OpenAlex**: 359
- **DOI**: https://doi.org/10.1007/s41019-020-00151-z
- **Open PDF**: https://link.springer.com/content/pdf/10.1007/s41019-020-00151-z.pdf
- **Keyword cocok**: map-matching
- **Pemakaian untuk RRU**: Dukungan umum untuk preprocessing trajectory/mobility dari data GPS/MPD.
- **Abstrak metadata**: Abstract Intelligent transportation (e.g., intelligent traffic light) makes our travel more convenient and efficient. With the development of mobile Internet and position technologies, it is reasonable to collect spatio-temporal data and then leverage these data to achieve the goal of intelligent transportation, and here, traffic prediction plays an important role. In this paper, we provide a comprehensive survey on traffic prediction, which is from the spatio-temporal data layer to the intelligent transportation application layer. At first, we…

### 35. Smartphone GPS accuracy study in an urban environment
- **Tahun/sumber**: 2019 — PLoS ONE
- **Penulis**: Krista Merry, Pete Bettinger
- **Sitasi OpenAlex**: 258
- **DOI**: https://doi.org/10.1371/journal.pone.0219890
- **Open PDF**: https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0219890&type=printable
- **Keyword cocok**: positional accuracy
- **Pemakaian untuk RRU**: Justifikasi toleransi spasial/buffer karena akurasi GPS/A-GPS bervariasi di lingkungan urban.
- **Abstrak metadata**: An iPhone 6 using the Avenza software for capturing horizontal positions was employed to understand relative positional accuracy in an urban environment, during two seasons of the year, two times of day, and two perceived WiFi usage periods. On average, time of year did not seem to influence the average error observed in horizontal positions when GPS-only (no WiFi) capability was enabled, nor when WiFi was enabled. Observations of average horizontal position error only seemed to improve with time of day (afternoon) during the leaf-off season. D…

## PDF lokal relevan yang sudah tersedia

- `references/Academic_Sandbox_Enabling_Access_and_Exploration_Mobile_Positioning_Data_for_Supporting_Mobility_Analytics.pdf` (601,665 bytes)
- `references/Efficient HMM Map Matching Method Using R-tree and Trajectory Seg.pdf` (2,780,277 bytes)
- `references/Extracting_Network_segments_from GPS.pdf` (5,967,950 bytes)
- `references/map-matching-ACM-GIS-camera-ready.pdf` (863,056 bytes)
- `references/Mobility_of_Indonesian_during_Early_Pandemic_Insights_from_Mobile_Positioning_Data.pdf` (689,824 bytes)
- `references/online/automated_vehicle_movement_classification_intersections_2021_arxiv.pdf` (583,966 bytes)
- `references/online/iqbal_2014_development_od_matrices_mobile_phone_call_data.pdf` (862,333 bytes)
- `references/online/li_2019_road_network_extraction_low_frequency_trajectories.pdf` (5,807,662 bytes)
- `references/online/real_time_vehicle_counts_probe_vehicle_data_2020_arxiv.pdf` (1,077,254 bytes)
- `references/online/saldivar_2023_data_driven_intersection_geometry_mapping.pdf` (6,685,747 bytes)
- `references/positional_accuracy_of_assisted_gps_data_from_high_3egafhsaqt_copy.pdf` (839,133 bytes)
- `references/TrajectoryDataMining-tist-yuzheng_published.pdf` (1,957,351 bytes)

## Prioritas rujukan untuk revisi skripsi RRU

- **Akurasi/ambang spasial**: Zandbergen & Barbeau 2011; Nurlita/Malioboro; smartphone GPS accuracy urban environment.
- **Map matching/noise/sparse GPS**: Quddus et al. 2007; Newson & Krumm 2009; Lou et al. 2009; online map-matching HMM; Efficient HMM + R-tree.
- **Trajectory mining dan low sampling**: Zheng 2015; Reducing uncertainty of low-sampling-rate trajectories; From GPS to Maps.
- **OD dari data mobile**: Alexander et al. 2015; Iqbal et al. 2014; mobile phone OD estimation papers.
- **Probe/floating vehicle**: gunakan hanya untuk mendukung “pola lalu lintas teramati”, bukan volume aktual tanpa ekspansi/kalibrasi.

## Keputusan metodologi yang didukung literatur

- Tetap pakai filter spasial konservatif terhadap jaringan RRU; 20 m dapat dijelaskan sebagai kompromi antara error GPS urban dan sensitivitas lokal.
- Hindari klaim rute/belokan aktual karena low-sampling Active MPD tidak cukup tanpa map matching+ground truth.
- OD zona pertama/terakhir teramati lebih robust daripada inferensi asal-tujuan rumah/catchment.
- Intensitas simpang dinyatakan sebagai MAID/ping teramati dan rerata harian, bukan traffic count aktual.