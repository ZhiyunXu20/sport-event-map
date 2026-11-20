# Sport Event Map 赛事分级地图

[English](README.md) · **简体中文**

一个按层级下钻的体育赛事地图：从等面积世界地图开始，一级一级进入到街道地图，每个点是一场比赛的起点，卡片显示赛事信息。纯静态网站，不需要后端，也不需要任何 API key。

**在线演示：** https://zhiyunxu20.github.io/sport-event-map/

在线演示用的是一小份知名赛事的示例数据（`examples/races.sample.json`）。我自己的参赛记录用同一套代码跑在我的个人网站上，那份数据不在这个仓库里。

## 特点

- **每一级都是等面积投影。** 世界用 Equal Earth，洲级大区用 Lambert 等面积方位投影，国家用 Albers 等面积圆锥投影。面积不会被拉伸，按颜色比较哪里比赛多才公平。
- **可以转动的世界地图。** 左右拖动转动中央经线，上下拖动平移，滚轮或双指按指针位置缩放；另有 0°、60°E、150°E 三个中心预设。
- **一套下钻规则走到底。** 世界、大区、国家、一级区域、街道地图、城市、区，最多七级；出现哪些层级由数据决定。
- **按赛事数量自适应。** 在街道地图上，某个地点超过 3 场就合并成带数字的圆圈，再点一层；3 场及以下直接显示点和卡片。
- **点在真实起点上。** 起点坐标来自 Strava 轨迹或手动标注；只有大致位置的赛事画成半透明虚线点。
- **贴合赛事的筛选。** 按运动类型筛选（铁三和铁二合并为"多项目"），也可以按特殊分组筛选：ITRA、UTMB、特殊届次，以及世界马拉松大满贯、SuperHalfs、IRONMAN、T100 等系列。地图颜色、地区列表和卡片同步更新。
- **卡片用图标链接。** 一个图标链到赛事官网，每个 Strava 活动一个橙色图标；多项目比赛每个有记录的分段（游泳、骑行、跑步）各一个图标。
- **中英双语**，页面上一键切换；支持浅色和深色主题。
- **每个视图都有独立网址**，例如 `#/EU/GB/GB-ENG/GB-LIV`，可以直接分享，也能用浏览器前进后退。

## 下钻逻辑

只有三条规则：

1. **颜色统计到下两级。** 世界地图上，每个国家按它各个一级区域的赛事数着色，一眼能看到国家内部哪里比赛多。
2. **点击只进入下一级。** 不会误点跳过层级。
3. **赛事多的地方多一级。** 街道地图上超过 3 场的地点变成数字圆圈。

| 层级 | 地图 | 颜色表示 | 点击进入 |
|---|---|---|---|
| 世界 | D3，Equal Earth，可旋转缩放 | 一级区域 | 大区或国家 |
| 大区 | D3，Lambert 等面积，可缩放 | 一级区域 | 国家 |
| 国家 | D3，Albers 等面积，可缩放 | 二级区域 | 一级区域 |
| 街道：一级区域 | Leaflet + OpenStreetMap | 点和数字圆圈 | 城市 |
| 街道：城市 | Leaflet，带区界 | 点和数字圆圈 | 区 |
| 街道：区 | Leaflet | 点 | 赛事卡片 |

细节：

- **大区按需出现。** 只有当某个大区（例如欧洲）有 2 个以上国家有赛事时，才插入这一级；否则世界地图直接进入国家。
- **空层级自动跳过。** 只有一个一级区域的国家直接打开街道地图。
- **太小点不到的区域**会加上虚线圈和名字，缩放时保持屏幕大小不变。
- **地图下方有地区列表**，列出当前层级能进入的所有区域和场数，小区域也一定点得到。

## 本地运行

页面用 `fetch` 读取数据，需要通过 HTTP 打开：

```sh
git clone https://github.com/ZhiyunXu20/sport-event-map.git
cd sport-event-map
python3 -m http.server 8000
# 浏览器打开 http://localhost:8000
```

## 换成自己的数据

把自己的赛事放在 `data/races.json`。页面会优先读取它，没有时退回示例数据。`data/` 已写进 `.gitignore`，自己的数据不会被提交。每场比赛的格式如下（必填的只有 `id`、`date`、`name`、`lat`、`lng` 和 `geo.path`）：

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

- `geo.path` 从国家往下列出区域代码：`[国家, 一级区域, 二级区域]`，可选第四级为区。要和 `assets/geo/` 边界文件里的要素 id 对应。大区由地图自动加上。
- `loc_precision`：精确起点用 `strava_start`、`strava_leg` 或 `manual_start`，大致位置用 `venue` 或 `city`。
- `links.strava_legs` 可选，多项目比赛用，格式是 `{ "url": ..., "leg": "swim" | "bike" | "run" | null }` 的列表。
- 界面文字和标签名称在 `assets/i18n.json`，格式为 `{ "en": {...}, "zh-Hans": {...} }`。

## 完整数据不公开

我的完整赛事表（含备注、隐藏的比赛和私人字段）放在私有仓库里。发布前，`tools/publish_filter.py` 按规则文件筛选，只输出可以展示的比赛和字段，同时生成一份报告，列出每一场被隐藏的比赛和原因。

```sh
python3 -I tools/publish_filter.py races_full.json publish_rules.json data/races.json
```

规则可以按 id、日期区间、运动类型、标签、国家隐藏，也可以用表里的 `public` 列。格式见 `tools/publish_rules.example.json`。真正的规则文件和完整表已写进 `.gitignore`。

## 使用的开源资源

| 资源 | 用途 | 协议或条款 |
|---|---|---|
| [D3](https://d3js.org/) 7.9.0 | 投影、缩放、矢量地图 | ISC |
| [topojson-client](https://github.com/topojson/topojson-client) 3.1.0 | 读取、合并边界 | ISC |
| [Leaflet](https://leafletjs.com/) 1.9.4 | 街道地图、打点 | BSD-2-Clause |
| [mapshaper](https://github.com/mbloch/mapshaper) | 简化边界（只在构建时使用） | MPL-2.0 |
| [OpenStreetMap](https://www.openstreetmap.org/copyright) 瓦片 | 街道底图 | [瓦片使用政策](https://operations.osmfoundation.org/policies/tiles/)，地图上已显示署名 |
| [Strava](https://www.strava.com/) | 我自己比赛的起点坐标、用时和活动链接 | [Strava 品牌指南](https://developers.strava.com/guidelines/) |

代码库通过 jsDelivr 和 unpkg 加载，没有复制进本仓库。

### 边界数据

| `assets/geo/` 里的文件 | 来源 | 条款 |
|---|---|---|
| `world.json`、`units-BE/DE/DK/GB/HK/MT/NL.json` | [Natural Earth](https://www.naturalearthdata.com/) | 公有领域 |
| `units-CN.json`、`districts-CN.json` | [GeoMapData_CN](https://github.com/lyhmyd1211/GeoMapData_CN)（阿里云 DataV / 高德数据） | 仅供学习和展示，商用前需替换 |
| `units-TW.json` | Natural Earth，其中一个单元来自 [geoBoundaries](https://www.geoboundaries.org/) | 该单元 © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright)，[ODbL 1.0](https://opendatacommons.org/licenses/odbl/) |

所有边界文件都用 mapshaper 简化过。赛事、系列和主办方名称（ITRA、UTMB、IRONMAN、T100 等）只作为文字描述使用，没有使用任何 logo。

## 后续计划

- 把层级配置和文案从 `race-map.js` 移到配置文件，换数据不用改代码。
- 按日期、距离筛选，加时间轴。
- 更好的键盘和读屏支持，手机上更大的点击区域。
- 赛事多时，一级区域以下也可以用颜色着色。
- 赛事与届次分开，同一场比赛多年参加合并显示。
- 有 GPS 轨迹的比赛画出路线。
- 用 GitHub Actions 自动拉取私有数据、筛选并发布。
- 层级切换时的过渡动画。

## 许可

代码：[MIT](LICENSE)。边界文件按上表各自的条款。示例赛事都是公开赛事，位置为大致场地，不代表任何人的成绩。
