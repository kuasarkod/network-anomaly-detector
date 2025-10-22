# Deployment Guide

Bu doküman, Advanced Network Anomaly Detector projesini Docker Compose veya manuel kurulum ile çalıştırmak için gerekli adımları açıklar.

## 1. Ön Koşullar

- Docker ve Docker Compose 1.29+
- Python 3.11 (manuel kurulum için)
- Node.js 20+ (dashboard geliştirme için)
- MaxMind GeoIP/ASN veritabanı dosyaları (opsiyonel, zenginleştirme için)

## 2. Çevre Değişkenleri

`config/.env.example` dosyasını inceleyerek kopyalayın:

```bash
cp config/.env.example config/.env
```

Önemli alanlar:

- `API_HOST`, `API_PORT`: FastAPI servis adresi
- `CORS_ORIGINS`: Dashboard veya harici istemciler için izin verilen origin listesi (virgülle ayrılmış)
- `QUEUE_BACKEND`: `redis`, `kafka` veya `memory`
- `SLACK_WEBHOOK_URL`, `SMTP_*`: Uyarı kanalları için kimlik bilgileri
- `KAFKA_BOOTSTRAP_SERVERS`, `REDIS_HOST`: Queue sistemleri

## 3. Docker Compose ile Kurulum

Servisleri başlatmak için:

```bash
docker compose up --build
```

Oluşturulan servisler:

- **api**: FastAPI uygulaması (`http://localhost:8080`)
- **redis**: Redis Streams kuyruğu
- **postgres**: PostgreSQL depolama (gelecek sürümler için)
- **kafka**: Kafka broker (opsiyonel kullanım)
- **dashboard**: React tabanlı web arayüzü (`http://localhost:5173`)
- **prometheus**: Metrik toplayıcı (`http://localhost:9090`)
- **grafana**: Gözlem panosu (`http://localhost:3000`, varsayılan kullanıcı/parola `admin` / `admin`)

### Sağlık Kontrolleri

```bash
curl http://localhost:8080/health
curl http://localhost:8080/metrics
curl http://localhost:8080/anomalies
curl http://localhost:8080/events --header 'Accept: text/event-stream'
```

## 4. Manuel Kurulum

1. **Python bağımlılıkları**
   ```bash
   poetry install
   poetry run uvicorn anomaly_detector.api.main:app --reload
   ```

2. **Dashboard**
   ```bash
   cd web/dashboard
   npm install
   npm run dev -- --host
   ```

3. **Queue ve Veritabanları**
   - Redis: `docker run -p 6379:6379 redis:7`
   - Kafka: Bitnami docker imajı veya mevcut broker
   - PostgreSQL: `docker run -p 5432:5432 postgres:16`

## 5. MaxMind GeoIP/ASN Veritabanları

GeoIP veya ASN zenginleştirmesi için `.mmdb` dosyalarını `config/geoip/` altına yerleştirin ve aşağıdaki gibi yapılandırın:

```env
GEOIP_DB_PATH=/app/config/geoip/GeoLite2-City.mmdb
ASN_DB_PATH=/app/config/geoip/GeoLite2-ASN.mmdb
```

Bu değerler otomatik olarak `PipelineProcessor` tarafından okunur ve uygun enrichers zinciri oluşturulur.

## 6. Prometheus ve Grafana Entegrasyonu (Opsiyonel)

Prometheus için `docker/prometheus/prometheus.yml` örneğini kullanarak aşağıdaki scrape job'ı ekleyin:

```yaml
scrape_configs:
  - job_name: anomaly-detector
    scrape_interval: 10s
    static_configs:
      - targets: ["api:8080"]
```

Grafana tarafında Prometheus veri kaynağını ekleyerek `anomaly_detector_events_total` ve `anomaly_detector_last_score` metriklerini görselleştirebilirsiniz.

## 7. CLI Kullanımı

Olay dosyalarını içeri almak ve sonuçları görmek için:

```bash
poetry run python -m anomaly_detector.cli ingest data/events.json
poetry run python -m anomaly_detector.cli stats
```

Bu komutlar `InMemoryAnomalyRepository` üzerinden verileri saklar ve API tarafından görüntülenmesini sağlar.

---

Bu doküman, hızlı kurulum süreçlerine rehberlik etmek için hazırlanmıştır. Daha ileri mimari detaylar için `docs/` dizinindeki diğer belgeleri inceleyin.
