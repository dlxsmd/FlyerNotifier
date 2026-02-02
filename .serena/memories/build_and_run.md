# Build & Run Instructions

## Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run
```bash
source venv/bin/activate
python main.py
```

## Dependencies (requirements.txt)
- requests>=2.31.0
- PyYAML>=6.0.1
- Pillow>=10.0.0
- line-bot-sdk>=3.5.0

## Configuration
Edit `config.yaml` with:
- Store shopIds from Shufoo!
- LINE channel_access_token and user_id from LINE Developers Console

## Scheduling (macOS launchd)
```bash
cp scheduling/net.yuki.sale-notification.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/net.yuki.sale-notification.plist
```
Runs daily at 8:00 AM.

## No tests currently
Tests were removed during simplification (OCR/extraction modules deleted).
