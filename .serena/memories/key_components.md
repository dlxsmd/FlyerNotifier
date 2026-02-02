# Key Components

## ShufooClient (src/shufoo/client.py)
- Fetches chirashi list from Shufoo! shop pages
- Extracts chirashi IDs from HTML link patterns and dataLayer JavaScript
- Probes tile URLs by date (HEAD requests on last 8 days) to find valid tile base URL
- Discovers tile grid (pages x tiles) via sequential HEAD requests
- Tile URL pattern: `https://ipqcache2.shufoo.net/c/{YYYY}/{MM}/{DD}/{chirashiId}/index/img/{page}_{zoom}_{tile}.jpg`

## ChirashiDownloader (src/shufoo/downloader.py)
- Downloads tile images for each chirashi page
- Auto-detects grid columns from tile width patterns
- Stitches tiles into full-page images using PIL
- Saves to data/images/{store_name}/
- Cleanup: removes images older than N days

## LineNotifier (src/notify/line_notifier.py)
- Uploads original + preview images to catbox.moe
- Sends text header + up to 4 ImageMessages per push_message request (LINE limit: 5 messages/request)
- Uses LINE Messaging API v3 (line-bot-sdk)

## image_uploader (src/utils/image_uploader.py)
- `upload_image()`: POST to catbox.moe/user/api.php -> returns HTTPS URL
- `create_preview()`: Resize to 240px width for LINE preview thumbnails

## AppConfig (src/config.py)
- Loads config.yaml with store list and LINE settings
- Validates required fields (stores, line)

## Models (src/models.py)
- `StoreConfig`: name, shop_id, enabled
- `Chirashi`: chirashi_id, store, title, image_urls, publish dates, local_image_paths
