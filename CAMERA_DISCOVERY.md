# Camera Discovery Process

## NV Roads API

### Endpoint (no API key required)
```
POST https://www.nvroads.com/List/GetData/Cameras
Content-Type: application/x-www-form-urlencoded

draw=1&start=0&length=100&columns[0][data]=Id&columns[0][name]=Id&columns[0][searchable]=true&order[0][column]=0&order[0][dir]=asc
```

Paginate with `start` parameter (0, 100, 200, ...). Total cameras: ~643.

### Response structure
Each camera object includes:
- `sourceId` — used as `id` in cameras.json
- `roadway` — camera name/location
- `images[0].videoUrl` — HLS stream URL (used as `stream` in cameras.json)
- `latLng.geography.wellKnownText` — coordinates as `POINT (lon lat)`

### Official API (requires key)
```
GET https://www.nvroads.com/api/v2/get/cameras?key=YOUR_KEY&format=json
```
Documented at https://www.nvroads.com/help/endpoint/cameras. We don't need this — the List endpoint above works without a key.

## Filtering by zip code

There is no zip code field in the API response. To find cameras in a given area:

1. Look up the approximate bounding box for the zip code (lat/lon ranges)
2. Fetch all cameras (paginate in batches of 100)
3. Parse coordinates from `latLng.geography.wellKnownText` (format: `POINT (lon lat)`)
4. Filter cameras whose coordinates fall within the bounding box

### Example: 89521 (South Reno)
Bounding box used: lat 39.30–39.55, lon -119.92 to -119.65

### One-liner to discover cameras in an area
```bash
curl -s -X POST "https://www.nvroads.com/List/GetData/Cameras" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "draw=1&start=0&length=100&columns[0][data]=Id&columns[0][name]=Id&columns[0][searchable]=true&order[0][column]=0&order[0][dir]=asc" \
  | python3 -c "
import json, sys, re
data = json.load(sys.stdin)
for cam in data['data']:
    wkt = cam.get('latLng',{}).get('geography',{}).get('wellKnownText','')
    m = re.search(r'POINT \(([^ ]+) ([^ ]+)\)', wkt)
    if not m: continue
    lon, lat = float(m.group(1)), float(m.group(2))
    # Adjust bounding box for your target area:
    if 39.30 <= lat <= 39.55 and -119.92 <= lon <= -119.65:
        name = cam.get('roadway','')
        sid = cam.get('sourceId','')
        vid = cam.get('images',[{}])[0].get('videoUrl','')
        print(f'{sid} | {name} | {lat},{lon} | {vid}')
"
```

## Gotchas

### Pagination is required
The API returns max 100 results per request regardless of the `length` parameter. You must paginate with `start=0`, `start=100`, `start=200`, etc. to fetch all ~643 cameras. The one-liner example above only fetches the first 100 — loop over pages to cover the full set.

### Duplicate cameras
Some cameras appear twice with different `sourceId` formats — once with a numeric ID (e.g. `9423`) and once with an alphanumeric hash (e.g. `5h5rp0ioolg`). These share the same stream URL. Use the numeric `sourceId` for consistency with our cameras.json.

### Stream URL port
Stream URLs returned by the API include `:443` in the hostname (e.g. `https://d2wse1.its.nv.gov:443/...`). This works fine as-is but is functionally equivalent to omitting the port since 443 is the default HTTPS port.

### Verifying streams
Spot-check stream URLs with `curl -s -o /dev/null -w '%{http_code}' <url>` — a 200 means the HLS playlist is live. A 404 or timeout means the camera may be offline or decommissioned.

## ID mapping note

The existing cameras.json uses IDs (e.g. "5008") that don't match the current API's `id` or `sourceId` fields. These appear to be from a previous version of the NV Roads API. The stream URLs do match, which is what matters. For new cameras, use the current API's `sourceId` as the `id` field.

## Bounding boxes for other areas

| Area | Lat range | Lon range |
|------|-----------|-----------|
| 89521 (South Reno) | 39.30–39.55 | -119.92 to -119.65 |
