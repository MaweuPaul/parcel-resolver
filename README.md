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
for the geometry work. The frontend is a Next.js dashboard shell — a sidebar
of analysis tools, two of which ("Parcel overlap detection" and "Geometry
validation") are fully wired up to the API; the rest are placeholders for
tools that don't exist yet (see [Roadmap](#roadmap--to-be-done)).

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
anything still planned and otherwise just links to it. Geometry validation
went from `planned` to `available` without touching `sidebar.tsx` at all —
adding the next tool means adding a page under `app/tools/<name>` and
flipping one entry in that config, not restructuring navigation around it.
Measurement, projection, and format conversion are still `planned`.

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

Open `http://localhost:3000` and go to **Overlap** or **Validation** in the
sidebar. The
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
feature with no `parcelid` — raises a Python exception that `/resolve` and
`/validate` both turn into an HTTP 400 with the exception's own message,
e.g. `"Invalid GeoJSON: 'features'"`.

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
```

## Frontend

Two tools are wired up end to end, and both share the same interaction
pattern deliberately — paste a GeoJSON `FeatureCollection` directly, upload
a `.json`/`.geojson` file, or click **Load sample** for a ready-made example.
Invalid JSON is caught client-side before it's sent; a non-2xx response or
an unreachable API surfaces the server's own error message inline instead of
a stack trace.

- `frontend/src/app/tools/overlap/page.tsx` submits to `POST {API_URL}/resolve`
  and renders a table of overlapping pairs — parcel A, parcel B, overlap
  area, overlap percentage, and a color-coded severity badge (green for
  `none`, amber for `tolerance`, red for `dispute`).
- `frontend/src/app/tools/validation/page.tsx` submits to
  `POST {API_URL}/validate` and renders one row per parcel — parcel ID, a
  valid/invalid badge, area, and any flags joined together (or an em dash
  when there are none).

Every other entry in the sidebar (**Measurement**, **Projection**,
**Conversion**) is a `planned`-status placeholder wired through
`dashboard.json` — the link exists and shows a "Soon" badge, but there's no
page behind it yet.

## Repository Layout

```text
parcel-resolver/
├── backend/
│   ├── parcel_resolver/
│   │   ├── api/
│   │   │   └── resolve.py       # FastAPI app, CORS config, POST /resolve + /validate
│   │   ├── cadastre/
│   │   │   └── __init__.py      # parcel geometry + area validation
│   │   ├── io/
│   │   │   └── geojson.py       # GeoJSON Polygon + FeatureCollection parsing
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
│   │   └── test_cadastre.py
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── app/
    │   │   ├── page.tsx             # dashboard home (still default scaffold — see Roadmap)
    │   │   └── tools/
    │   │       ├── overlap/
    │   │       │   └── page.tsx     # overlap detection tool
    │   │       └── validation/
    │   │           └── page.tsx     # geometry validation tool
    │   ├── components/shell/
    │   │   ├── sidebar.tsx
    │   │   └── nav-link.tsx
    │   └── config/
    │       └── dashboard.json       # sidebar nav + tool status, drives the shell
    └── package.json
```

## A Note on How This Was Tested

The backend has an automated `pytest` suite covering cadastre validation
(valid parcels, self-intersecting geometry, suspicious tiny/huge areas),
overlap detection (overlapping, adjacent-but-not-overlapping, disjoint
pairs), spatial-index-driven discovery across the full sample fixture set,
percentage-based severity classification, and both `/resolve` and
`/validate`'s success and HTTP-400 paths. Run it with `python -m pytest`
from `backend/`.

Both frontend tools were verified end-to-end in a real browser against a
running backend, not just checked for compiling: the overlap tool's sample
`FeatureCollection` returns the expected pair (`P001`/`P002`, 4 square
units, 4.00%, `tolerance`); the validation tool's sample returns one valid
parcel and one flagged `self intersecting, suspicious area` parcel, both
rendered correctly with no console errors.

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
- [ ] Repair guidance for flagged geometry, not just a flag name
- [ ] Configurable CORS origins (currently hardcoded to `localhost:3000`)
- [ ] Configurable overlap and suspicious-area thresholds
- [ ] Reading GeoJSON directly from files, not just request bodies
- [ ] MultiPolygon and interior-hole (donut parcel) support
- [ ] Shapefile input/output
- [ ] Persistent spatial storage
- [ ] Command-line batch processing
- [ ] Benchmarks on larger datasets
- [ ] Measurement, projection, and format-conversion tools (currently
      placeholders in the sidebar)
- [ ] Real dashboard home page (currently the default `create-next-app`
      scaffold)

## License

Licensed under the [MIT License](LICENSE).
