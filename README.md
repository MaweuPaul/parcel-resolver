# parcel-resolver

**Automated boundary-overlap detection for land parcels.**

`parcel-resolver` validates surveyed parcel boundaries and identifies parcels
that occupy the same area. It is intended to reduce manual review by producing
a focused list of potential boundary conflicts and their overlap areas.

## The problem

Land parcels are represented as polygons. Two neighboring parcels can overlap
because of survey errors, incorrect subdivision, duplicate registration,
encroachment, or a genuine boundary dispute.

This project does not decide ownership or resolve disputes. It detects geometry
that needs attention so a surveyor, land office, or legal team can review it.

## What is implemented

- Parcel validation using Shapely polygons
- Detection of invalid, self-intersecting parcel geometry
- Suspicious-area flags for parcels smaller than 1 or larger than 1,000,000
  square coordinate units
- Pairwise overlap detection with the exact intersection area
- Correct handling of adjacent parcels: sharing an edge is not treated as an
  overlap
- Candidate lookup with Shapely's `STRtree` spatial index
- Filtering of invalid parcels before overlap analysis
- GeoJSON Polygon coordinate extraction
- GeoJSON FeatureCollection parsing into parcel dictionaries keyed by
  `properties.parcelid`
- Data-driven overlap discovery that accepts any parcel dictionary
- Percentage-based overlap severity classification relative to the smaller
  parcel
- FastAPI `POST /resolve` endpoint for frontend integration
- Structured JSON overlap responses and HTTP 400 errors for malformed input
- Sample parcel fixtures and automated tests for validation, adjacency,
  overlap detection, indexed lookup, and API behavior

Coordinates are currently treated as planar `(x, y)` values. Areas are reported
in the square units of the input coordinate system.

## Current flow

```text
GeoJSON FeatureCollection
       |
       v
POST /resolve
       |
       v
Parcel dictionary
       |
       v
Cadastre validation
       |
       +-- invalid geometry --> skipped and reported
       |
       v
STRtree candidate search
       |
       v
Exact intersection check
       |
       v
Severity classification
       |
       v
(parcel A, parcel B, overlap area, percentage, severity)
```

The resolver accepts dictionaries shaped like
`{"P001": [(x, y), ...], ...}`. The GeoJSON parser creates this structure from
a FeatureCollection, while the test suite uses the same structure through its
sample parcel fixture.

## Project structure

```text
backend/
  parcel_resolver/
    api/
      resolve.py        # FastAPI POST /resolve endpoint
    cadastre/
      __init__.py       # parcel geometry and area validation
    io/
      geojson.py        # GeoJSON Polygon and FeatureCollection parsing
    resolver/
      overlap.py        # exact two-parcel overlap check
      index.py          # validation, spatial indexing, and overlap discovery
      severity.py       # percentage-based severity classification
  tests/
    fixtures/
      sample_parcels.py # representative sample polygons
    resolver/
      test_index.py
      test_overlap.py
      test_severity.py
    test_api.py
    test_cadastre.py
  requirements.txt
frontend/
  src/app/              # Next.js App Router frontend
  package.json
```

## Getting started

The backend requires Python 3.9 or later. From the repository root:

```bash
cd backend
python -m venv .venv
```

Activate the environment, then install the current runtime and test
dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the backend test suite:

```bash
python -m pytest
```

Run only the API tests:

```bash
python -m pytest tests/test_api.py -v
```

Install and run the Next.js frontend in a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend is available at `http://localhost:3000`.

## Usage

Check two parcel boundaries directly:

```python
from parcel_resolver.resolver.overlap import check_overlap

parcel_a = [(0, 0), (10, 0), (10, 10), (0, 10)]
parcel_b = [(8, 8), (18, 8), (18, 18), (8, 18)]

result = check_overlap(parcel_a, parcel_b)
# {"overlap": True, "overlap_area": 4.0}
```

Validate a parcel:

```python
from parcel_resolver.cadastre import validate_parcel

result = validate_parcel(parcel_a)
# {"is_valid": True, "area": 100.0, "flags": []}
```

Parse a GeoJSON FeatureCollection and run indexed overlap discovery:

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
                "coordinates": [
                    [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]
                ],
            },
        },
        {
            "type": "Feature",
            "properties": {"parcelid": "P002"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [[8, 8], [18, 8], [18, 18], [8, 18], [8, 8]]
                ],
            },
        },
    ],
}

parcels = parse_feature_collection(feature_collection)
overlaps = find_overlaps(parcels)
# list of (first_parcel_id, second_parcel_id, overlap_area) tuples
```

From the `backend` directory, run the temporary end-to-end example currently
included in `geojson.py`:

```bash
python -m parcel_resolver.io.geojson
```

## API

From the `backend` directory, start the development server:

```bash
python -m uvicorn parcel_resolver.api.resolve:app --reload
```

Interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

The backend exposes one endpoint:

```text
POST /resolve
```

Send a GeoJSON FeatureCollection as the JSON request body. A successful
response uses named fields that are easy for a frontend to consume:

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

Severity is based on how much of the smaller parcel is covered:

```text
overlap percentage = overlap area / smaller parcel area × 100
```

- No overlap: `none`
- Below 5%: `tolerance`
- 5% or above: `dispute`

For example, an overlap area of `4` between two parcels whose smaller area is
`100` covers 4% of that parcel and is classified as `tolerance`.

Malformed GeoJSON returns HTTP `400`:

```json
{
  "detail": "Invalid GeoJSON: 'features'"
}
```

## Status and roadmap

This is an early-stage prototype; there is no stable release yet.

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
- [ ] Configurable overlap severity thresholds
- [ ] Reading GeoJSON directly from files
- [ ] Shapefile input/output
- [ ] Persistent spatial storage
- [ ] Command-line batch processing
- [ ] Benchmarks on larger datasets
- [ ] Reports or a dashboard for flagged conflicts

## Limitations

- GeoJSON support currently accepts an in-memory dictionary; it does not yet
  read a `.geojson` file from disk.
- Only Polygon features and their outer coordinate rings are handled;
  MultiPolygon geometries and interior holes are not yet supported.
- GeoJSON features must store their parcel identifier in
  `properties.parcelid`.
- Input coordinates are assumed to use an appropriate projected coordinate
  system; geographic latitude/longitude needs projection before meaningful
  area calculations.
- Area thresholds are currently hardcoded.
- Validation reports self-intersection and suspicious area, but does not yet
  provide detailed repair guidance.
- Severity thresholds are currently hardcoded rather than configurable.
- The API does not yet configure cross-origin resource sharing (CORS) for a
  separately hosted browser frontend.

## License

Licensed under the [MIT License](LICENSE).
