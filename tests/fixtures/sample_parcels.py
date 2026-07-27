"""
Hardcoded test parcels for exercising Cadastre and Resolver logic
before touching real survey data.

Each parcel is a plain list of (x, y) coordinate tuples describing
the boundary, in order. Coordinates here are arbitrary planar units,
not real-world coordinates.
"""

SAMPLE_PARCELS = {
    # A clean, valid square parcel.
    "P001": [(0, 0), (10, 0), (10, 10), (0, 10)],

    # A clean, valid square parcel adjacent to P001 (shares an edge, no overlap).
    "P002": [(10, 0), (20, 0), (20, 10), (10, 10)],

    # Deliberately overlaps P002 by a significant chunk.
    "P003": [(9, 9), (19, 9), (19, 19), (9, 19)],

    # A clean, valid square parcel adjacent to P001 (shares an edge, no overlap).
    "P004": [(0, 10), (10, 10), (10, 20), (0, 20)],

    # Deliberately self-intersecting ("bowtie") shape -- should fail validation.
    "P005": [(0, 0), (10, 10), (10, 0), (0, 10)],

    "P006": [(0, 0), (0.5, 0), (0.5, 0.5), (0, 0.5)]  # deliberately tiny -- area = 0.25
}