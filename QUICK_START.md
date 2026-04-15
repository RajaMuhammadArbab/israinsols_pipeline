# Israinsols Pipeline - 24/7 Automation Setup

✅ **Redis Installed**: Automatically downloaded and installed  
✅ **Celery Configured**: 5 Freelancer queries + alerts every 5 min  
✅ **Start Script**: `start_celery.py` ready to run  

## Quick Start

1. **Redis start karo** (already installed):
   ```bash
   # Redis already running - check with:
   redis-cli ping  # Should return PONG
   ```

2. **Celery start karo**:
   ```bash
   cd c:\Users\ccslaptophyd\OneDrive\Desktop\israinsols_pipeline
   python start_celery.py
   ```

Ab system automatically chalega! 🚀

## Kya Hota Hai Automatically?

- **Har 1 ghante**: Freelancer Python Django leads
- **Har 1.5 ghante**: Freelancer Web Scraping leads  
- **Har 1 ghante**: Freelancer React Developer leads
- **Har 2 ghante**: Freelancer Mobile App leads
- **Har 1.5 ghante**: Freelancer Shopify Developer leads
- **Har 5 minute**: Naye leads Telegram par alert

## 24/7 Chalane Ke Liye

### Windows pe (Recommended):
Ek baar `setup_windows_services.ps1` run karo — isse services automatically ban jayengi:
```powershell
Set-Location c:\Users\ccslaptophyd\OneDrive\Desktop\israinsols_pipeline
.\setup_windows_services.ps1
```

Ye script:
- Redis ko Windows service banati hai
- Celery worker service banati hai
- Celery beat service banati hai
- Sab services auto-start pe set kar deti hai

Agar NSSM installed nahi hai, toh pehle install karo: https://nssm.cc/download

### Manual Start:
Agar service setup abhi nahi karna, toh temporary start ke liye:
```bash
# Terminal 1: Redis start
"C:\Program Files\Redis\redis-server.exe" "C:\Program Files\Redis\redis.windows.conf"

# Terminal 2: Celery start  
python start_celery.py
```

## Troubleshooting

- **Redis not running**: `redis-cli ping` check karo
- **Celery errors**: Logs check karo
- **No alerts**: Telegram bot token verify karo

Ab Freelancer leads automatically aate rahenge! 🎉