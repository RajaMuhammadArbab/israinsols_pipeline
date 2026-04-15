from pathlib import Path
path = Path('config/settings.py')
text = path.read_text(encoding='utf-8')
idx = text.index('# Database - PostgreSQL / SQLite (fallback)')
print(text[idx-60:idx+140])
