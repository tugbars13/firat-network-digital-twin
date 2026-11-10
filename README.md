# Fırat Üniversitesi Kampüs Ağı Dijital İkizi

Fırat Üniversitesi kampüs bilgi işlem ağının 3D, etkileşimli dijital ikizi.
Sistem, simüle edilmiş ağ telemetrisini gerçek zamanlı izler, cihaz ve hat
durumunu kampüs haritası üzerinde görselleştirir ve arıza senaryolarının
etkisini önceden analiz eder.

## Kapsam
- Çekirdek, dağıtım ve erişim katmanlarından oluşan kampüs ağ topolojisi
- Simüle telemetri: hat doluluğu, gecikme, cihaz durumu, Wi-Fi istemci sayısı
- Cihaz detay görünümü
- Arıza simülasyonu ve etki analizi

## Teknolojiler
Python (FastAPI), MQTT (Mosquitto), PostgreSQL (TimescaleDB, PostGIS),
React, Three.js, Docker Compose

## Klasör yapısı
- `docs/` — proje belgeleri ve diyagramlar
- `backend/` — API ve analiz motoru
- `frontend/` — web arayüzü
- `simulator/` — telemetri simülatörü

## Proje bilgisi
Yazılım Mühendisliği Bitirme Projesi · Fırat Üniversitesi · 2026
Danışman: Resul DAŞ
