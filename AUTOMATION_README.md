# Israinsols Pipeline - 24/7 Automation Setup

Yeh guide batata hai kaise yeh system 24 ghante automatically chalay bina manually kuch karay.

## Requirements

1. **Redis Server** - Celery ke liye zaroori
2. **Python Virtual Environment** - Already setup
3. **Windows/Linux/Mac** - Koi bhi OS

## Step 1: Redis Install Karo

### Windows pe:
```bash
# Chocolatey use karo (agar installed hai)
choco install redis-64

# Ya manually download karo: https://redis.io/download
# Extract karo aur redis-server.exe run karo
```

### Linux/Mac pe:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install redis-server

# CentOS/RHEL
sudo yum install redis

# Mac
brew install redis
```

## Step 2: Redis Start Karo

```bash
# Windows
redis-server

# Linux/Mac
sudo systemctl start redis
# Ya manually: redis-server
```

## Step 3: Celery Start Karo

```bash
# Project directory mein jao
cd c:\Users\ccslaptophyd\OneDrive\Desktop\israinsols_pipeline

# Virtual environment activate karo
venv\Scripts\activate

# Celery start karo
python start_celery.py
```

Yeh command Celery worker aur beat scheduler dono start karega.

## Kya Hota Hai Automatically?

- **Har 1 ghante**: Freelancer Python Django leads scrape hote hain
- **Har 1.5 ghante**: Freelancer Web Scraping leads
- **Har 1 ghante**: Freelancer React Developer leads
- **Har 2 ghante**: Freelancer Mobile App leads
- **Har 1.5 ghante**: Freelancer Shopify Developer leads
- **Har 5 minute**: Naye leads Telegram par alert bhejte hain

Sab leads automatically database mein save hote hain aur duplicate skip hote hain.

## 24/7 Chalane Ke Liye

Local PC pe 24/7 chalane ke liye:

### Windows pe (Recommended):
1. **NSSM download karo**: https://nssm.cc/download
2. **Extract karo** aur command prompt admin mode mein open karo
3. **Service create karo**:
   ```bash
   nssm install IsrainsolsPipeline "c:\Users\ccslaptophyd\OneDrive\Desktop\israinsols_pipeline\venv\Scripts\python.exe"
   nssm set IsrainsolsPipeline AppParameters "c:\Users\ccslaptophyd\OneDrive\Desktop\israinsols_pipeline\start_celery.py"
   nssm set IsrainsolsPipeline AppDirectory "c:\Users\ccslaptophyd\OneDrive\Desktop\israinsols_pipeline"
   ```
4. **Service start karo**: `nssm start IsrainsolsPipeline`
5. **Check karo**: Services.msc mein "IsrainsolsPipeline" service hona chahiye

### Linux/Mac pe:
- **Systemd service** banao ya
- **Screen/Tmux** use karo

### Cloud Server pe deploy karo (Best for 24/7):
1. **Heroku/AWS/DigitalOcean** VPS rent karo
2. **Redis install karo**
3. **Code deploy karo**
4. **Celery service start karo**

## Monitoring

Logs check karne ke liye:
- Celery logs terminal mein show hote hain
- Django admin mein ScrapeLog model check karo

## Troubleshooting

- **Redis connection error**: Redis server start karo
- **Celery not starting**: Virtual env check karo
- **No alerts**: Telegram bot token check karo in settings.py

## Stop Karne Ke Liye

Celery stop karne ke liye terminal mein Ctrl+C press karo.