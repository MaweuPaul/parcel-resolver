from shapely.geometry import Polygon

def check_overlap (coords1 ,coords2) -> dict:
    """
    Checks if two parcels overlap.

    Args:
        coords1 (list[tuple[float, float]]): Coordinates of the first parcel.
        coords2 (list[tuple[float, float]]): Coordinates of the second parcel.

    Returns:
        dict: A dictionary indicating if the parcels overlap and the area of the overlap.
    """
    polygon1 =Polygon(coords1)
    polygon2 =Polygon(coords2)
    
    if not polygon1.intersects(polygon2):
        return {"overlap": False, "overlap_area": 0.0}
    
    overlap_area = polygon1.intersection(polygon2).area 
    
    if overlap_area > 0:
        return {"overlap": True, "overlap_area": overlap_area}
    else :
        return {"overlap": False, "overlap_area": 0.0}
   
   