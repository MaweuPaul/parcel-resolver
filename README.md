# parcel-resolver

**Automated boundary overlap detection for land parcels.**

parcel-resolver takes a set of surveyed land parcel boundaries and automatically
flags which ones overlap with each other — so a human only has to review
the flagged cases instead of manually checking every parcel against its
neighbors.

---

## The problem

Land parcels are polygons. Sometimes two neighboring parcels' boundaries
overlap on paper , from survey errors, improper subdivision, duplicate
registration, or a genuine dispute over where the line actually is.
Today, this is usually only caught manually, often after it's already
escalated into a legal dispute.

This is a well-documented, recurring problem — not a hypothetical one:

- Improper subdivision without correct registration leading to multiple
  owners claiming overlapping plots (documented case: Kasarani).
- Survey/registry-map discrepancies where one parcel measures larger and
  its neighbor smaller than recorded, with a disputed strip between them.
- Boundaries shifting over time due to encroachment.

parcel-resolver doesn't resolve disputes — it finds and ranks them by severity,
and hands a clean, prioritized list to a human reviewer (surveyor, land
office, legal team).

## What it does

1. Take a list of parcels, each one just a polygon.
2. Validate each parcel's shape isn't broken (e.g. boundary lines that
   cross themselves — a data error, not a dispute).
3. Compare each parcel against its neighbors and check whether any two
   overlap — and if so, whether it's a tiny sliver (likely measurement
   noise) or a real chunk (likely a genuine conflict).
4. Output a list: which parcels overlap, and by how much.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  Cadastre   │────▶│   Resolver   │────▶│   Registry   │
│  (validate) │     │  (detect &   │     │  (store &    │
│             │     │   classify)  │     │   query)     │
└─────────────┘     └──────────────┘     └──────────────┘
```

- **Cadastre** — validates individual parcel geometry (closed rings, no
  self-intersection, sane area bounds) before anything downstream runs.
- **Resolver** — the detection core. Uses a spatial index to find
  candidate neighboring parcels, computes pairwise overlaps, and
  classifies each as none / survey-tolerance / significant dispute.
- **Registry** — persistence layer for parcel geometry, ownership/title
  reference, and flagged disputes, queryable spatially.

## Stack

- **Shapely** — geometry primitives and operations
- **GeoPandas** — tabular parcel data + spatial joins
- **Shapely STRtree** — spatial indexing for scalable pairwise checks
- **PostGIS + GeoAlchemy2** — persistent spatial storage
- **Fiona** — Shapefile I/O (common format for government land data)

## Status

Early development. Core validation and overlap-detection logic in
progress; no stable release yet.

## Roadmap

- [ ] Cadastre: geometry validation
- [ ] Resolver: pairwise overlap detection via spatial index
- [ ] Resolver: severity classification (tolerance vs. dispute)
- [ ] Registry: PostGIS schema + spatial queries
- [ ] Benchmark suite validating results against known test cases
- [ ] CLI for batch-processing a parcel dataset
- [ ] Basic reporting/dashboard for flagged disputes

## License

TBD
