from shapely.geometry import Polygon
from shapely.strtree import STRtree

from parcel_resolver.resolver.overlap import check_overlap
from parcel_resolver.cadastre  import validate_parcel


# Only keep parcels that pass Cadastre validation -- Resolver should
# never run against broken geometry (e.g. P005's self-intersecting shape).


def find_overlaps( parcels: dict):
 parcel_ids = []
 polygons = []
 overlaps=[] 

 for parcel_id, coords in parcels.items():
    validation = validate_parcel(coords)
    if validation["is_valid"]:
        parcel_ids.append(parcel_id)
        polygons.append(Polygon(coords))
    else:
        print(f"Skipping Parcel {parcel_id}: {validation['flags']}")

# Build the spatial index once, over all valid polygons.
 STRtree_index = STRtree(polygons)

  
 for i, polygon in enumerate(polygons):
     # Ask the tree which polygons are near this one -- only these
     # candidates get the real (expensive) overlap check below.
     candidate_indices = STRtree_index.query(polygon)
 
     for j in candidate_indices:
         if j > i:  # skip self-matches and mirrored duplicates
             result = check_overlap(
                 parcels[parcel_ids[i]],
                 parcels[parcel_ids[j]]
             )
             if result["overlap"]:
                 overlaps.append((parcel_ids[i], parcel_ids[j], result["overlap_area"]))
                 print(f"Parcel {parcel_ids[i]} may overlap with Parcel {parcel_ids[j]}")
 return overlaps