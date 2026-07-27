from shapely.geometry import Polygon
from shapely.strtree import STRtree

from tests.fixtures.sample_parcels import SAMPLE_PARCELS
from parcel_resolver.resolver.overlap import check_overlap
from parcel_resolver.cadastre  import validate_parcel

# Only keep parcels that pass Cadastre validation -- Resolver should
# never run against broken geometry (e.g. P005's self-intersecting shape).
parcel_ids = []
polygons = []

for pid, coords in SAMPLE_PARCELS.items():
    validation = validate_parcel(coords)
    if validation["is_valid"]:
        parcel_ids.append(pid)
        polygons.append(Polygon(coords))
    else:
        print(f"Skipping Parcel {pid}: {validation['flags']}")

# Build the spatial index once, over all valid polygons.
STRtree_index = STRtree(polygons)


def find_overlaps():
 overlaps=[] 
  
 for i, polygon in enumerate(polygons):
     # Ask the tree which polygons are near this one -- only these
     # candidates get the real (expensive) overlap check below.
     candidate_indices = STRtree_index.query(polygon)
 
     for j in candidate_indices:
         if j > i:  # skip self-matches and mirrored duplicates
             result = check_overlap(
                 SAMPLE_PARCELS[parcel_ids[i]],
                 SAMPLE_PARCELS[parcel_ids[j]]
             )
             if result["overlap"]:
                 overlaps.append((parcel_ids[i], parcel_ids[j], result["overlap_area"]))
                 print(f"Parcel {parcel_ids[i]} may overlap with Parcel {parcel_ids[j]}")
 return overlaps