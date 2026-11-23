# Sport Event Map

**English** · [简体中文](README.zh-CN.md)

A hierarchical drill-down map of sport events. It starts from an equal-area world map and goes level by level down to a street map, where each point is a race start line and each card shows the race. It is a static site with no backend and no API keys.

**Live demo:** [https://zhiyunxu20.github.io/sport-event-map/](https://zhiyunxu20.github.io/projects/sport-event-map/)

The demo uses a small sample dataset of well-known races (`examples/races.sample.json`). My own race history runs on the same code on my personal site; that data is not in this repository.

## Features

- **Equal-area at every level.** The world uses Equal Earth, continent-scale regions use a Lambert azimuthal equal-area projection and countries use Albers equal-area conic. Areas keep their true size, so colour comparisons are fair.
- **A world map you can turn.** Drag sideways to move the central meridian, drag up and down to pan, and scroll or pinch to zoom at the pointer. There are presets for 0°, 60°E and 150°E.
- **One set of drill-down rules everywhere.** World, then macro-region, then country, then first-level area, then street map, then city, then district. Up to seven levels, and which levels appear depends on the data.
- **Adapts to how many races there are.** On a street map, a place with more than 3 races becomes a numbered circle that opens one more level. Places with 3 or fewer show their points and cards straight away.
- **Points at real start lines.** Start coordinates come from Strava GPS or are set by hand. Races that only have an approximate location are drawn as faded, dashed points.
- **Filters that match the sport.** Filter by sport (triathlon and duathlon are grouped as multisport) and by special groups: ITRA, UTMB, milestone editions, and race series such as the World Marathon Majors, SuperHalfs, IRONMAN and T100. The map colours, the place list and the cards all update together.
- **Cards with icon links.** One icon for the race website and one orange icon per Strava activity. A multisport race gets one icon for each recorded leg (swim, bike, run).
- **English and Simplified Chinese**, switchable on the page. Light and dark themes.
- **Every view has a URL**, such as `#/EU/GB/GB-ENG/GB-LIV`, so you can share it and use back and forward.

## How drill-down works

There are three rules:

1. **Colour counts two levels down.** On the world map, each country is shaded by the races in its first-level areas, so you can see where inside a country the races are.
2. **A click opens only the next level.** You never skip a level by accident.
3. **Busy places get one more level.** On a street map, a place with more than 3 races becomes a numbered circle.

| Level | Map | Colour shows | Click opens |
|---|---|---|---|
| World | D3, Equal Earth, rotate and zoom | first-level areas | macro-region or country |
| Macro-region | D3, Lambert equal-area, zoom | first-level areas | country |
| Country | D3, Albers equal-area, zoom | second-level areas | first-level area |
| Street: first level | Leaflet + OpenStreetMap | points and numbered circles | city |
| Street: city | Leaflet, with district outlines | points and numbered circles | district |
| Street: district | Leaflet | points | race card |

Some details:

- **Macro-regions appear only when needed.** A macro-region (for example Europe) is inserted only when 2 or more of its countries have races. Otherwise the world map goes straight to the country.
- **Empty levels are skipped.** A country with a single first-level area opens its street map directly.
- **Areas too small to click** get a dashed circle and a label that keep their screen size when you zoom.
- **A place list under the map** shows every area you can open at the current level, with its race count, so small areas are always reachable.

## Run it locally

The page loads its data with `fetch`, so serve the folder over HTTP:

```sh
git clone https://github.com/ZhiyunXu20/sport-event-map.git
cd sport-event-map
python3 -m http.server 8000
# open http://localhost:8000
```

## Use your own data

Put your races in `data/races.json`. The page loads it if it exists and falls back to the sample data otherwise. `data/` is in `.gitignore`, so your own data never gets committed. Each race looks like this (only `id`, `date`, `name`, `lat`, `lng` and `geo.path` are required):

```json
{
  "id": "20250921-001",
  "date": "2025-09-21",
  "country": "DE",
  "name": { "en": "Berlin Marathon", "zh": "柏林马拉松" },
  "city": { "en": "Berlin", "zh": "柏林" },
  "lat": 52.5163, "lng": 13.3777,
  "loc_precision": "strava_start",
  "geo": { "path": ["DE", "DE-BE", "DE-BE"] },
  "sport": "road", "category": "marathon",
  "distance_km": 42.195, "elev_m": 120,
  "status": "finished", "time": "3:30:00", "time_source": "official",
  "edition": 51, "tags": ["wmm"],
  "links": {
    "website": "https://www.bmw-berlin-marathon.com/",
    "strava": "https://www.strava.com/activities/...",
    "strava_legs": null
  }
}
```

- `geo.path` lists the area keys from the country down: `[country, first-level area, second-level area]`, with an optional fourth key for a district. They must match the feature ids in the boundary files in `assets/geo/`. Macro-regions are added by the map itself.
- `loc_precision` is `strava_start`, `strava_leg` or `manual_start` for an exact start line, or `venue` / `city` for an approximate one.
- `links.strava_legs` is an optional list of `{ "url": ..., "leg": "swim" | "bike" | "run" | null }` for multisport races.
- Interface text and tag names are in `assets/i18n.json`, as `{ "en": {...}, "zh-Hans": {...} }`.

## Keeping the full data private

My full race table (with notes, hidden races and private fields) stays in a private repository. Before publishing, `tools/publish_filter.py` applies a rules file and writes only the races and fields that should be shown, together with a report listing every hidden race and why.

```sh
python3 -I tools/publish_filter.py races_full.json publish_rules.json data/races.json
```

Rules can hide races by id, by date range, by sport, by tag or by country, or by a `public` column in the table. See `tools/publish_rules.example.json`. The real rules file and the full table are listed in `.gitignore`.

## Checks and CI

`tools/validate_races.py` checks a dataset before it is published: required fields, real dates, coordinates in range, known sports and categories, area keys that exist in the boundary files, and safe links. The data tools have unit tests (`pytest`). An Azure Pipelines build runs the validation and tests on every pull request, packages the site and can deploy it to Azure Static Web Apps. See [docs/azure-pipelines.md](docs/azure-pipelines.md).

```sh
python3 -I tools/validate_races.py data/races.json
```

## Built with

| Resource | Used for | Licence or terms |
|---|---|---|
| [D3](https://d3js.org/) 7.9.0 | projections, zoom, vector maps | ISC |
| [topojson-client](https://github.com/topojson/topojson-client) 3.1.0 | reading and merging boundaries | ISC |
| [Leaflet](https://leafletjs.com/) 1.9.4 | street maps, points | BSD-2-Clause |
| [mapshaper](https://github.com/mbloch/mapshaper) | simplifying boundaries (build time only) | MPL-2.0 |
| [OpenStreetMap](https://www.openstreetmap.org/copyright) tiles | street map background | [Tile usage policy](https://operations.osmfoundation.org/policies/tiles/), attribution shown on the map |
| [Strava](https://www.strava.com/) | start coordinates, times and activity links for my own races | [Strava brand guidelines](https://developers.strava.com/guidelines/) |

Libraries load from jsDelivr and unpkg. They are not copied into this repository.

### Boundary data

| Files in `assets/geo/` | Source | Terms |
|---|---|---|
| `world.json`, `units-BE/DE/DK/GB/HK/MT/NL.json` | [Natural Earth](https://www.naturalearthdata.com/) | Public domain |
| `units-CN.json`, `districts-CN.json` | [GeoMapData_CN](https://github.com/lyhmyd1211/GeoMapData_CN) (Aliyun DataV / Amap data) | For study and display only. Replace before any commercial use. |
| `units-TW.json` | Natural Earth, plus one unit from [geoBoundaries](https://www.geoboundaries.org/) | That unit is © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), [ODbL 1.0](https://opendatacommons.org/licenses/odbl/) |

All boundary files were simplified with mapshaper. Race, series and organiser names (ITRA, UTMB, IRONMAN, T100 and others) are used only as plain text to describe the races. No logos are used.

## Roadmap

- Move the level configuration and text out of `race-map.js` into a config file, so a new dataset needs no code changes.
- Date and distance filters, and a timeline.
- Better keyboard and screen-reader support, and larger touch targets on phones.
- Optional colour shading below the first level when there are many races.
- Separate races from editions, so the same race over several years shows as one entry.
- Route lines for races with GPS tracks.
- A GitHub Actions workflow that pulls the private table, runs the filter and publishes.
- Animated transitions between levels.

## Licence

Code: [MIT](LICENSE). Boundary files keep the terms listed above. The sample races are public events placed at approximate venues; they are not anyone's results.
