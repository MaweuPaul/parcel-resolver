# parcel-resolver

**Automated boundary-overlap detection for land parcels.**

`parcel-resolver` validates surveyed parcel boundaries and identifies parcels
that occupy the same area. It reduces manual review to a focused list of
potential boundary conflicts, their overlap areas, and how severe each one
is, so a surveyor, land office, or legal team knows what actually needs a
human look.

> This project does not decide ownership or resolve disputes. It detects
> geometry that needs attention. Nothing here writes to a registry, modifies
> a survey, or makes a legal determination.

## Table of Contents

- [What Is This?](#what-is-this)
- [Why It's Built This Way](#why-its-built-this-way)
- [Running It](#running-it)
- [How Data Gets In: GeoJSON, No Persistence](#how-data-gets-in-geojson-no-persistence)
- [The Resolver Pipeline](#the-resolver-pipeline)
- [API](#api)
- [Frontend](#frontend)
- [Repository Layout](#repository-layout)
- [A Note on How This Was Tested](#a-note-on-how-this-was-tested)
- [Known Limitations & Rough Edges](#known-limitations--rough-edges)
- [Contributing](#contributing)
- [Roadmap / To Be Done](#roadmap--to-be-done)
- [License](#license)

## What Is This?

Two neighboring land parcels can end up overlapping on paper for a lot of
mundane reasons: survey error, an incorrect subdivision, duplicate
registration, encroachment, or a genuine boundary dispute. Finding those
cases by eye across a batch of parcels doesn't scale. `parcel-resolver` takes
a set of parcel boundaries, validates each one as real, non-self-intersecting
geometry, checks every pair that's actually near each other, and reports the
ones that share area, along with what fraction of the smaller parcel that
overlap represents.

The backend is a FastAPI service built on [Shapely](https://shapely.readthedocs.io/)
for the geometry work, [pyproj](https://pyproj4.github.io/pyproj/) for
coordinate reprojection, and [pyshp](https://github.com/GeospatialPython/pyshp)
for Shapefile output. The frontend is a Next.js dashboard shell — every tool
in the sidebar ("Parcel overlap detection", "Geometry validation", "Area
and distance", "Coordinate projection", and "Format conversion") is fully
wired up to the API (see [Roadmap](#roadmap--to-be-done) for what's still
missing within each one).

## Why It's Built This Way

A few choices here aren't obvious from just reading the code, so it's worth
writing down the reasoning:

**Validate before resolving, always.** `find_overlaps` runs every parcel
through `cadastre.validate_parcel` before it's allowed anywhere near the
spatial index or an intersection check. A self-intersecting ("bowtie")
polygon doesn't have a well-defined area or a meaningful intersection, so
instead of letting Shapely raise deep inside the pairwise loop, invalid
parcels are filtered out up front and reported (currently to stdout) as
skipped. The resolver should never run against geometry it can't trust.

**A spatial index first, an exact check second.** Checking every parcel
against every other parcel is O(n²) and gets slow fast once there are more
than a few hundred parcels. `find_overlaps` builds a Shapely `STRtree` once
over all valid polygons, and for each parcel only asks the tree for nearby
*candidates* — the expensive exact intersection check
(`Polygon.intersection(...).area`) only runs on pairs the index actually
flagged as close, with a `j > i` guard so no pair is checked twice and a
parcel never gets checked against itself.

**Touching is not overlapping.** Two legitimately adjacent parcels share an
edge, and `Polygon.intersects()` alone would call that an intersection.
What actually gets measured is `Polygon.intersection(...).area` — a shared
edge has zero area, so adjacency is never mistaken for a conflict. This is
worth stating explicitly because it's the difference between a usable tool
and one that floods every neighboring pair with false positives.

**Severity is relative, not absolute — and it lives in exactly one place.**
`resolver/severity.py` classifies an overlap by what percentage of the
*smaller* parcel's area it covers, not by raw square units. A 4-square-unit
overlap is nothing on a large rural tract and a real problem on a small
urban lot, so a fixed area threshold can't tell those apart — a percentage
of the smaller parcel can. `resolver/overlap.py`'s `check_overlap()` used to
carry its own, older absolute-area `TOLERANCE_THRESHOLD` and return its own
`severity` key from before percentage-based severity existed; that
duplicate logic has been removed, so `check_overlap()` now only reports
*whether* two parcels overlap and by how much area — severity is computed
exactly once, in `severity.py`, from each parcel's real area. There's no
second definition left to disagree with the first.

**Plain coordinate dictionaries at the core, GeoJSON only at the edges.**
`find_overlaps` and `check_overlap` don't know what GeoJSON is — they work on
`{parcel_id: [(x, y), ...]}` dictionaries. `io/geojson.py` is the only module
that understands FeatureCollections, Features, and where a parcel ID lives
(`properties.parcelid`). That keeps the resolver and cadastre logic testable
against plain Python fixtures (`tests/fixtures/sample_parcels.py`) instead of
hand-built GeoJSON in every test, and means a second input format (a
Shapefile, say) would only need its own parser producing the same
dictionary shape — not changes to the resolver itself.

**FastAPI is a thin adapter, not where the logic lives.** `/resolve` does
exactly four things: parse the request body as GeoJSON, call `find_overlaps`,
attach a severity to each result pair, and turn parse errors into an HTTP
400. Every function it calls is importable and runs fine outside a server —
see the [Usage](#api) examples below and the `if __name__ == "__main__":`
block at the bottom of `geojson.py`.

**A dashboard shell built for more than one tool.** The sidebar's navigation
config (`frontend/src/config/dashboard.json`) lists every analysis tool with
a status of `available` or `planned`; the shell renders a "Soon" badge for
anything still planned and otherwise just links to it. Every tool has now
gone from `planned` to `available` without touching `sidebar.tsx` at all —
adding the next one still means adding a page under `app/tools/<name>` and
flipping one entry in that config, not restructuring navigation around it.
The dashboard home page (`app/page.tsx`) reads the same config and renders
from it too, so a new tool shows up on both the sidebar and the homepage
from one edit.

**Tool counts are computed, not duplicated.** The homepage used to read
"Available tools" / "Planned tools" from static numbers hand-maintained in
`dashboard.json`'s `summaryCards` — numbers that had to be manually bumped
in five separate commits as tools shipped, and that quietly drifted from
the actual tool list any time someone forgot. Those two counts are now
derived by filtering `dashboard.json`'s own `toolGroups` by `status`, so
there's exactly one source of truth (the per-tool `status` field) instead
of two that can disagree — the same category of fix as the severity
duplication described above.

**"Analyses completed" is an honest number, not a fake one.** A metric like
this normally implies server-side tracking this project doesn't have (see
[How Data Gets In](#how-data-gets-in-geojson-no-persistence) — nothing is
persisted). Rather than hardcode a permanent `0` or invent a count that
isn't real, `lib/analytics.ts` tracks successful tool runs in
`localStorage`, scoped to one browser, via `useSyncExternalStore` (not a
`useEffect` + `setState` — the newer `react-hooks/set-state-in-effect`
ESLint rule flags that pattern, and `useSyncExternalStore` is what React
actually recommends for reading state owned by something outside React,
which `localStorage` is). The homepage says exactly what this number is
and isn't, right under the summary cards, rather than let it be mistaken
for real usage analytics.

**The theme is deliberately light-only, so the CSS says that explicitly.**
`create-next-app`'s default `globals.css` ships a `prefers-color-scheme:
dark` media query that repaints `body` near-black for anyone with a
dark-mode OS or browser setting — harmless on the original placeholder
page, but it fought every hardcoded light color in this dashboard (the
`#F6F6F1` background, the white cards) once real content replaced it,
producing a broken half-dark page for a meaningful share of visitors.
`globals.css` now imports Tailwind and nothing else; `layout.tsx`'s own
`bg-[#F6F6F1] text-[#17211F]` on `<body>` is the only background rule left,
so there's nothing for an OS setting to override.

**Reprojection always pins coordinate order, because the alternative is a
silent bug.** `projection.reproject_coordinates` calls
`Transformer.from_crs(..., always_xy=True)`. Without `always_xy`, pyproj
honors each CRS's own defined axis order — and EPSG:4326 (WGS84) is
officially defined as (latitude, longitude), not (longitude, latitude).
Every GeoJSON coordinate in this codebase, and in GeoJSON generally, is
`[x, y]` i.e. `[longitude, latitude]`. Skipping `always_xy` wouldn't error;
it would just silently transpose every WGS84 coordinate and produce
plausible-looking, wrong output. This is a well-known pyproj gotcha and
worth naming explicitly rather than leaving future-you to rediscover it.

**Shapefile output reorients rings, not just copies coordinates.** The
ESRI Shapefile spec requires outer polygon rings to be wound clockwise;
this codebase's own parcel fixtures (and most hand-written GeoJSON) are
wound counter-clockwise. `conversion.parcels_to_shapefile_zip` runs every
ring through Shapely's `orient(..., sign=-1.0)` before handing it to
`pyshp`. Skipping that step wouldn't raise an error either — `pyshp` writes
whatever ring order it's given — but GIS software that honors winding
(ArcGIS in particular) would silently read the "outer" ring as a hole and
render an empty parcel. Same category of bug as the projection axis-order
issue above: technically valid-looking output that's wrong.

## Running It

Backend (Python 3.9+):

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment, then:

```bash
python -m pip install -r requirements.txt
python -m uvicorn parcel_resolver.api.resolve:app --reload
```

Interactive API docs land at `http://127.0.0.1:8000/docs`.

Frontend (in a separate terminal):

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` and pick any tool from the sidebar. The
backend allows cross-origin requests from `http://localhost:3000` only (see
[Known Limitations](#known-limitations--rough-edges)); if the API is hosted
somewhere else, point the frontend at it with:

```bash
NEXT_PUBLIC_API_URL=https://your-api-host npm run dev
```

It defaults to `http://localhost:8000` when unset.

Run the backend test suite from `backend/`:

```bash
python -m pytest
```

## How Data Gets In: GeoJSON, No Persistence

There's no database, no file storage, and no uploaded file that sticks
around. A request to `POST /resolve` carries a GeoJSON `FeatureCollection` in
the body; the resolver parses it, runs the pipeline below, and returns a
JSON result. Nothing is written anywhere, and nothing survives past the
response — send the same request twice and you'll get the same answer, not a
diff against something stored from last time.

Every feature in that collection needs:

- `geometry.type` of `"Polygon"` (MultiPolygon and interior holes aren't
  handled yet — see [Limitations](#known-limitations--rough-edges))
- `geometry.coordinates`, an outer ring of `[x, y]` pairs
- `properties.parcelid`, the identifier used everywhere downstream (in
  results, in skip messages, in the frontend table)

Anything short of that — a missing `features` key, a non-Polygon geometry, a
feature with no `parcelid` — raises a Python exception that every endpoint
(`/resolve`, `/validate`, `/measure`, `/project`, `/convert`) turns into an
HTTP 400 with the exception's own message, e.g.
`"Invalid GeoJSON: 'features'"`.

Coordinates are treated as planar `(x, y)` values throughout. There is no
coordinate-reference-system handling: geographic latitude/longitude needs to
be projected into a planar system before the areas this tool reports mean
anything.

## The Resolver Pipeline

```text
GeoJSON FeatureCollection
       |
       v
POST /resolve
       |
       v
Parcel dictionary  { "P001": [(x, y), ...], ... }
       |
       v
Cadastre validation
       |
       +-- invalid geometry --> skipped, logged, excluded from every later step
       |
       v
STRtree candidate search  (only nearby parcels get checked against each other)
       |
       v
Exact intersection check  (adjacency alone is not an overlap)
       |
       v
Severity classification  (overlap area ÷ smaller parcel's area)
       |
       v
(parcel A, parcel B, overlap area, overlap percentage, severity)
```

The same dictionary shape works whether it came from the GeoJSON parser or a
hand-built fixture — the resolver doesn't care which:

```python
from parcel_resolver.io.geojson import parse_feature_collection
from parcel_resolver.resolver.index import find_overlaps

feature_collection = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {"parcelid": "P001"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]],
            },
        },
        {
            "type": "Feature",
            "properties": {"parcelid": "P002"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[8, 8], [18, 8], [18, 18], [8, 18], [8, 8]]],
            },
        },
    ],
}

parcels = parse_feature_collection(feature_collection)
overlaps = find_overlaps(parcels)
# [("P001", "P002", 4.0)]
```

## API

Start the dev server (see [Running It](#running-it)), then:

```text
POST /resolve
```

Body: a GeoJSON `FeatureCollection`. Response uses named fields a frontend
can render directly:

```json
{
  "overlaps": [
    {
      "parcel_a": "P001",
      "parcel_b": "P002",
      "overlap_area": 4.0,
      "overlap_percentage": 4.0,
      "severity": "tolerance"
    }
  ]
}
```

Severity is the share of the smaller of the two parcels that the overlap
covers:

```text
overlap percentage = overlap area / smaller parcel area × 100
```

| Overlap percentage | Severity  |
| ------------------- | --------- |
| 0%                   | `none`    |
| below 5%             | `tolerance` |
| 5% or above          | `dispute` |

Malformed GeoJSON returns HTTP `400`:

```json
{
  "detail": "Invalid GeoJSON: 'features'"
}
```

```text
POST /validate
```

Body: a GeoJSON `FeatureCollection`, same shape as `/resolve`. Returns every
parcel's own validation result, independent of any other parcel — this is
`cadastre.validate_parcel` run once per feature, not a pairwise check:

```json
{
  "parcels": [
    {
      "parcel_id": "P001",
      "is_valid": true,
      "area": 100.0,
      "flags": []
    },
    {
      "parcel_id": "P005",
      "is_valid": false,
      "area": 0.0,
      "flags": ["self intersecting", "suspicious area"]
    }
  ]
}
```

A parcel can carry more than one flag at once (a self-intersecting polygon
often also reports a suspicious, near-zero area, as above). Malformed
GeoJSON returns the same HTTP `400` shape as `/resolve`.

```text
POST /measure
```

Body: a GeoJSON `FeatureCollection`, same shape as `/resolve` and
`/validate`. Returns each parcel's own area and perimeter — no comparison
between parcels, and no distance measurement between them yet (see
[Known Limitations](#known-limitations--rough-edges)):

```json
{
  "parcels": [
    {
      "parcel_id": "P001",
      "area": 100.0,
      "perimeter": 40.0
    }
  ]
}
```

```text
POST /project?source_crs=EPSG:4326&target_crs=EPSG:3857
```

Body: a GeoJSON `FeatureCollection`. Unlike the other endpoints, `/project`
also needs two query parameters — `source_crs` and `target_crs` — since a
reprojection isn't meaningful without knowing both ends. Any string
[pyproj](https://pyproj4.github.io/pyproj/) accepts works, most commonly an
EPSG code (`"EPSG:4326"`). Returns each parcel's coordinates reprojected
into `target_crs`:

```json
{
  "source_crs": "EPSG:4326",
  "target_crs": "EPSG:3857",
  "parcels": [
    {
      "parcel_id": "P001",
      "coordinates": [[-13627665.27, 4547675.35], ["..."]]
    }
  ]
}
```

An unrecognized CRS string returns HTTP `400`:

```json
{
  "detail": "Invalid CRS: Invalid projection: NOT_A_CRS: ..."
}
```

```text
POST /convert?crs=EPSG:4326
```

Body: a GeoJSON `FeatureCollection`. `crs` is optional — when given, it's
written into a `.prj` file so GIS software that reads the output knows what
the coordinates mean; `/convert` never reprojects (that's `/project`'s job).
Returns a `application/zip` binary response — not JSON — containing
`parcels.shp`, `parcels.shx`, `parcels.dbf`, and `parcels.prj` if a `crs`
was given, one `Feature` per shapefile record with its `parcelid` in a
`parcelid` field:

```text
Content-Type: application/zip
Content-Disposition: attachment; filename=parcels.zip
```

An unrecognized `crs` string returns the same `Invalid CRS: ...` HTTP `400`
shape as `/project`; malformed GeoJSON returns the same `Invalid GeoJSON:
...` shape as every other endpoint.

Direct function usage, without going through the API at all:

```python
from parcel_resolver.resolver.overlap import check_overlap
from parcel_resolver.cadastre import validate_parcel

parcel_a = [(0, 0), (10, 0), (10, 10), (0, 10)]
parcel_b = [(8, 8), (18, 8), (18, 18), (8, 18)]

check_overlap(parcel_a, parcel_b)
# {"overlap": True, "overlap_area": 4.0}
# severity isn't computed here -- see classify_severity below

validate_parcel(parcel_a)
# {"is_valid": True, "area": 100.0, "flags": []}

from parcel_resolver.measurement import measure_parcel

measure_parcel(parcel_a)
# {"area": 100.0, "perimeter": 40.0}

from parcel_resolver.projection import reproject_coordinates

reproject_coordinates([(-122.4194, 37.7749)], "EPSG:4326", "EPSG:3857")
# [(-13627665.27, 4547675.35)]

from parcel_resolver.conversion import parcels_to_shapefile_zip

archive_bytes = parcels_to_shapefile_zip({"P001": parcel_a})
# raw bytes of a .zip containing parcels.shp/.shx/.dbf
```

## Frontend

All five tools are wired up end to end, and all of them share the same
paste / upload / **Load sample** interaction pattern deliberately. Invalid
JSON is caught client-side before it's sent; a non-2xx response or an
unreachable API surfaces the server's own error message inline instead of
a stack trace.

- `frontend/src/app/tools/overlap/page.tsx` submits to `POST {API_URL}/resolve`
  and renders a table of overlapping pairs — parcel A, parcel B, overlap
  area, overlap percentage, and a color-coded severity badge (green for
  `none`, amber for `tolerance`, red for `dispute`).
- `frontend/src/app/tools/validation/page.tsx` submits to
  `POST {API_URL}/validate` and renders one row per parcel — parcel ID, a
  valid/invalid badge, area, and any flags joined together (or an em dash
  when there are none).
- `frontend/src/app/tools/measurement/page.tsx` submits to
  `POST {API_URL}/measure` and renders one row per parcel — parcel ID, area,
  and perimeter.
- `frontend/src/app/tools/projection/page.tsx` adds a source/target CRS
  field pair (autocompleted against a handful of common EPSG codes via an
  HTML `<datalist>`, but free text is accepted — any string pyproj
  understands works) on top of the usual GeoJSON input, submits to
  `POST {API_URL}/project?source_crs=...&target_crs=...`, and renders each
  parcel's reprojected coordinate ring as raw JSON in a scrollable
  monospace block, since a table doesn't suit an arbitrary-length list of
  coordinate pairs the way it suits one value per parcel.
- `frontend/src/app/tools/conversion/page.tsx` adds an optional CRS field
  (for the output `.prj`), submits to `POST {API_URL}/convert`, and — since
  this is the one endpoint that doesn't return JSON — reads the response as
  a `Blob`, builds an object URL, and clicks a synthetic `<a download>` to
  save `parcels.zip`, rather than rendering a results table.

`app/page.tsx`, the dashboard home page, isn't a tool itself — it renders
three summary cards (available tools, planned tools, and analyses
completed, all computed rather than hand-maintained; see
[Why It's Built This Way](#why-its-built-this-way)) and a card per tool
grouped exactly the way the sidebar groups them, sourced from the same
`dashboard.json`. Each of the five tool pages calls
`recordAnalysisCompleted()` from `lib/analytics.ts` right after a
successful response, so the homepage's count updates the next time it's
visited — including via client-side navigation, without a full reload.

## Repository Layout

```text
parcel-resolver/
├── backend/
│   ├── parcel_resolver/
│   │   ├── api/
│   │   │   └── resolve.py       # FastAPI app, CORS config, all five POST endpoints
│   │   ├── cadastre/
│   │   │   └── __init__.py      # parcel geometry + area validation
│   │   ├── conversion/
│   │   │   └── __init__.py      # GeoJSON -> zipped Shapefile
│   │   ├── io/
│   │   │   └── geojson.py       # GeoJSON Polygon + FeatureCollection parsing
│   │   ├── measurement/
│   │   │   └── __init__.py      # per-parcel area + perimeter
│   │   ├── projection/
│   │   │   └── __init__.py      # coordinate reference system reprojection
│   │   └── resolver/
│   │       ├── overlap.py       # exact two-parcel overlap check
│   │       ├── index.py         # validation + spatial index + overlap discovery
│   │       └── severity.py      # percentage-based severity classification
│   ├── tests/
│   │   ├── fixtures/
│   │   │   └── sample_parcels.py
│   │   ├── resolver/
│   │   │   ├── test_index.py
│   │   │   ├── test_overlap.py
│   │   │   └── test_severity.py
│   │   ├── test_api.py
│   │   ├── test_cadastre.py
│   │   ├── test_conversion.py
│   │   ├── test_measurement.py
│   │   └── test_projection.py
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── app/
    │   │   ├── page.tsx             # dashboard home: summary cards + tool grid, both computed from dashboard.json
    │   │   └── tools/
    │   │       ├── overlap/
    │   │       │   └── page.tsx     # overlap detection tool
    │   │       ├── validation/
    │   │       │   └── page.tsx     # geometry validation tool
    │   │       ├── measurement/
    │   │       │   └── page.tsx     # area + perimeter tool
    │   │       ├── projection/
    │   │       │   └── page.tsx     # CRS reprojection tool
    │   │       └── conversion/
    │   │           └── page.tsx     # GeoJSON -> Shapefile download
    │   ├── components/shell/
    │   │   ├── sidebar.tsx
    │   │   └── nav-link.tsx
    │   ├── config/
    │   │   └── dashboard.json       # tool list + status; drives the sidebar and the homepage
    │   └── lib/
    │       └── analytics.ts         # localStorage-backed "analyses completed" counter
    └── package.json
```

## A Note on How This Was Tested

The backend has an automated `pytest` suite covering cadastre validation
(valid parcels, self-intersecting geometry, suspicious tiny/huge areas),
overlap detection (overlapping, adjacent-but-not-overlapping, disjoint
pairs), spatial-index-driven discovery across the full sample fixture set,
percentage-based severity classification, area/perimeter measurement,
coordinate reprojection (an identity transform, a known WGS84 → Web
Mercator conversion checked against pyproj's own output, and a
shape-preservation sanity check), Shapefile packaging (archive contents,
optional `.prj`, and a round trip through `pyshp`'s own reader to confirm
geometry and the `parcelid` field survive intact), and all five endpoints'
success and HTTP-400 paths. Run it with `python -m pytest` from `backend/`.

All five frontend tools were verified end-to-end in a real browser against
a running backend, not just checked for compiling: the overlap tool's sample
`FeatureCollection` returns the expected pair (`P001`/`P002`, 4 square
units, 4.00%, `tolerance`); the validation tool's sample returns one valid
parcel and one flagged `self intersecting, suspicious area` parcel; the
measurement tool's sample returns `P001` at area `100`, perimeter `40`; the
projection tool's sample reprojects `P001` from `EPSG:4326` to `EPSG:3857`
with coordinates matching a direct API call byte-for-byte; the conversion
tool's sample triggers a real `parcels.zip` blob download confirmed against
the network log (`200 OK`, `application/zip`). Every tool's error path was
also checked — an invalid CRS string surfaces the backend's `Invalid CRS:
...` message inline on both the projection and conversion tools. All five
rendered correctly with no console errors, and the sidebar shows no
remaining "Soon" badges.

The dashboard home page was verified the same way: its tab title changed
from the default "Create Next App" to "GeoWorkspace", its summary cards
correctly read `5` available / `0` planned straight off `dashboard.json`,
and — the part that actually needed a real browser to check — running the
overlap tool's sample and then reloading the homepage moved "Analyses
completed" from `0` to `1`, confirming the `localStorage` counter survives
a full page reload rather than just an in-memory client-side transition.

## Known Limitations & Rough Edges

- CORS in `api/resolve.py` allows exactly one hardcoded origin,
  `http://localhost:3000`. There's no environment-driven configuration yet,
  so a frontend served from anywhere else needs a code change to reach the
  API.
- GeoJSON support only accepts Polygon features and their outer ring;
  MultiPolygon geometries and interior holes (donut-shaped parcels) aren't
  handled.
- The parcel identifier must live at `properties.parcelid`; there's no
  fallback field name.
- Coordinates are assumed to already be in a planar, projected system — no
  geographic (lat/lon) reprojection happens anywhere in this pipeline.
- Suspicious-area thresholds (`< 1` or `> 1,000,000` square units) and
  severity thresholds (5% dispute cutoff) are hardcoded, not configurable.
- Validation reports *that* a parcel is self-intersecting or has a
  suspicious area, but gives no guidance on how to fix the geometry.
- There's no persistence layer: results exist only for the lifetime of one
  request/response. Re-running an analysis means re-sending the same data.
- `/measure` reports each parcel's own area and perimeter only — there's no
  distance measurement *between* parcels yet, even though the sidebar's
  tool description ("Area and distance") implies it.
- `/project` reprojects coordinates only; it doesn't recompute area or
  perimeter in the target CRS, and it accepts whatever CRS string pyproj
  can resolve without validating that it's an appropriate choice for the
  input data (e.g. nothing stops reprojecting already-planar local survey
  coordinates as if they were WGS84 lat/lon).
- `/convert` only goes one direction (GeoJSON in, Shapefile out) and only
  supports one target format. Reading a Shapefile back into GeoJSON isn't
  implemented, and there's no CSV, KML, or GeoPackage output either.
- Every shapefile record carries exactly one attribute, `parcelid` — no
  other GeoJSON `properties` fields survive the conversion.
- "Analyses completed" on the dashboard home page is a per-browser
  `localStorage` count, not a real usage metric — it means nothing across
  devices or browsers, and resets if the user clears site data.

## Contributing

Contributions and bug fixes are welcome. If you're adding a new analysis
tool, follow the existing shape: a self-contained module under
`parcel_resolver/` with its own tests, a thin FastAPI route if it needs one,
and a page under `frontend/src/app/tools/<name>` wired through
`dashboard.json` rather than hand-added to the sidebar component. Please
don't send a result without the test (or reproducible example) that backs
it — see [A Note on How This Was Tested](#a-note-on-how-this-was-tested).

## Roadmap / To Be Done

- [x] Cadastre geometry validation
- [x] Pairwise overlap detection
- [x] Spatial-index candidate lookup
- [x] Invalid-parcel filtering
- [x] Automated tests with known parcel cases
- [x] In-memory GeoJSON FeatureCollection parsing
- [x] Resolver input decoupled from test fixtures
- [x] Frontend-facing overlap API
- [x] API success and error-response tests
- [x] Percentage-based severity classification
- [x] Overlap-detection dashboard UI (paste/upload/sample GeoJSON, results table)
- [x] Reconcile the duplicate absolute-area severity logic in `overlap.py`
- [x] Fix the `httpx2` → `httpx` typo in `requirements.txt`
- [x] Geometry validation API (`POST /validate`) and dashboard tool
- [x] Area/perimeter measurement API (`POST /measure`) and dashboard tool
- [x] Coordinate reprojection API (`POST /project`) and dashboard tool
- [x] GeoJSON-to-Shapefile conversion API (`POST /convert`) and dashboard tool
- [x] Real dashboard home page (computed summary cards + tool grid, sourced from `dashboard.json`)
- [ ] Distance measurement between parcels (measurement tool is area/perimeter-only today)
- [ ] Recompute area/perimeter after reprojection, not just coordinates
- [ ] Shapefile-to-GeoJSON conversion (the reverse direction; `/convert` is one-way today)
- [ ] Preserve arbitrary GeoJSON `properties` fields through conversion, not just `parcelid`
- [ ] Additional conversion targets (CSV, KML, GeoPackage)
- [ ] Repair guidance for flagged geometry, not just a flag name
- [ ] Configurable CORS origins (currently hardcoded to `localhost:3000`)
- [ ] Configurable overlap and suspicious-area thresholds
- [ ] Reading GeoJSON directly from files, not just request bodies
- [ ] MultiPolygon and interior-hole (donut parcel) support
- [ ] Persistent spatial storage
- [ ] Command-line batch processing
- [ ] Benchmarks on larger datasets

## License

Licensed under the [MIT License](LICENSE).
