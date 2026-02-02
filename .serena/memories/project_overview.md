# FlyerNotifier - Project Overview

## Purpose
Shufoo! (Japanese digital flyer service) chirashi images are fetched, analyzed by AI for sale items, and recipe suggestions are sent to LINE every morning via scheduled launchd job.

## Architecture
Pipeline: Fetch chirashi list -> Download tile images -> Stitch tiles -> Upload to catbox.moe -> Send via LINE -> AI OCR analysis -> Recipe suggestion -> Send via LINE

## Directory Structure
```
FlyerNotifier/
├── main.py                     # Entry point: fetch -> download -> send -> analyze -> recipe pipeline
├── config.yaml                 # Store list + LINE credentials + AI provider config
├── config.yaml.example         # Config template (safe to commit)
├── requirements.txt            # requests, PyYAML, Pillow, line-bot-sdk, google-genai, openai
├── src/
│   ├── __init__.py
│   ├── models.py               # StoreConfig, Chirashi dataclasses
│   ├── config.py               # AppConfig: YAML loader (stores, line_config, ai_config)
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── base.py             # AIProvider ABC + AnalysisResult dataclass
│   │   ├── gemini_provider.py  # Google Gemini (google-genai SDK, file upload)
│   │   ├── deepseek_provider.py# DeepSeek (OpenAI-compatible API, base64 images)
│   │   └── factory.py          # create_ai_provider() factory function
│   ├── analysis/
│   │   ├── __init__.py
│   │   └── chirashi_analyzer.py# ChirashiAnalyzer: orchestrates AI provider calls
│   ├── shufoo/
│   │   ├── __init__.py
│   │   ├── client.py           # ShufooClient: chirashi discovery via tile probing
│   │   └── downloader.py       # ChirashiDownloader: tile download + PIL stitching
│   ├── notify/
│   │   ├── __init__.py
│   │   └── line_notifier.py    # LineNotifier: image upload + LINE push + recipe text
│   └── utils/
│       ├── __init__.py
│       ├── logging_config.py   # Logging setup
│       └── image_uploader.py   # catbox.moe upload + preview resize
├── data/images/                # Downloaded chirashi images (ephemeral)
├── logs/                       # Application logs
└── scheduling/
    ├── net.yuki.flyer-notifier.plist  # macOS launchd (daily 8:00 AM)
    └── install.sh
```

## Key Technologies
- Python 3.13
- requests: HTTP client for Shufoo! tile fetching and catbox.moe uploads
- Pillow (PIL): Tile stitching and preview image creation
- line-bot-sdk v3: LINE Messaging API v3 (push messages with ImageMessage + TextMessage)
- PyYAML: Configuration file parsing
- catbox.moe: Anonymous image hosting (LINE requires public HTTPS URLs)
- google-genai: Gemini API for multimodal image analysis
- openai: DeepSeek/OpenAI-compatible API for image analysis

## Data Flow
1. `ShufooClient.fetch_chirashi_list(store)` - Scrape Shufoo! shop page, extract chirashi IDs
2. `ChirashiDownloader.download(chirashi)` - Download + stitch tiles into full page images
3. `image_uploader.upload_image(path)` - Upload to catbox.moe, return HTTPS URL
4. `LineNotifier.send_chirashi(store, chirashi)` - Send text header + ImageMessage(s) via LINE
5. `ChirashiAnalyzer.analyze_images(paths)` - AI OCR: extract sale items + suggest recipes
6. `LineNotifier.send_recipe(store_name, text)` - Send recipe text via LINE (5000 char split)

## AI Provider Switching
- config.yaml `ai.provider`: "gemini" or "deepseek"
- Strategy pattern via AIProvider ABC
- Factory function `create_ai_provider(ai_config)` instantiates the right provider

## Configuration
- `config.yaml`: Store list + LINE credentials + AI provider settings (gitignored)
- `config.yaml.example`: Template without real keys (committed)
- Scheduling: macOS launchd plist, daily at 8:00 AM

## Git
- Branch: main (initial), feature/ocr-recipe-suggestion (AI feature)
