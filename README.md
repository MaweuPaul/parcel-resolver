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
- Sample parcel fixtures and automated tests for validation, adjacency,
  overlap detection, and indexed lookup

Coordinates are currently treated as planar `(x, y)` values. Areas are reported
in the square units of the input coordinate system.

## Current flow

```text
Parcel coordinates
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
(parcel A, parcel B, overlap area)
```

The current indexed resolver uses the hardcoded parcels in
`tests/fixtures/sample_parcels.py` as its input dataset.

## Project structure

```text
parcel_resolver/
  cadastre/
    __init__.py       # parcel geometry and area validation
  resolver/
    overlap.py        # exact two-parcel overlap check
    index.py          # validation, spatial indexing, and overlap discovery
tests/
  fixtures/
    sample_parcels.py # representative sample polygons
  test_cadastre.py
  test_index.py
  test_resolver.py
```

## Getting started

Requires Python 3.9 or later.

```bash
python -m venv .venv
```

Activate the environment, then install the current runtime and test
dependencies:

```bash
python -m pip install shapely pytest
```

Run the test suite from the repository root:

```bash
python -m pytest
```

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

Run indexed overlap discovery against the current sample dataset:

```python
from parcel_resolver.resolver.index import find_overlaps

overlaps = find_overlaps()
# list of (first_parcel_id, second_parcel_id, overlap_area) tuples
```

## Status and roadmap

This is an early-stage prototype; there is no stable release yet.

- [x] Cadastre geometry validation
- [x] Pairwise overlap detection
- [x] Spatial-index candidate lookup
- [x] Invalid-parcel filtering
- [x] Automated tests with known parcel cases
- [ ] Configurable overlap severity thresholds
- [ ] Loading real parcel datasets instead of test fixtures
- [ ] GeoJSON and Shapefile input/output
- [ ] Persistent spatial storage
- [ ] Command-line batch processing
- [ ] Benchmarks on larger datasets
- [ ] Reports or a dashboard for flagged conflicts

## Limitations

- The indexed workflow is currently coupled to the sample test fixture.
- Input coordinates are assumed to use an appropriate projected coordinate
  system; geographic latitude/longitude needs projection before meaningful
  area calculations.
- Area thresholds are currently hardcoded.
- Validation reports self-intersection and suspicious area, but does not yet
  provide detailed repair guidance.
- Overlaps are not yet classified by severity.

## License

Licensed under the [MIT License](LICENSE).
