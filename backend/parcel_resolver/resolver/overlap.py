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
    
    TOLERANCE_THRESHOLD  = 5
    if overlap_area == 0:
        severity ="none"
    elif overlap_area < TOLERANCE_THRESHOLD:
        severity ="tolerance"
    else:
        severity ="dispute"
        
    return {
    "overlap": severity != "none",
    "overlap_area": overlap_area,
    "severity": severity
    }
    

   