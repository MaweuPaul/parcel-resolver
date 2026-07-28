def classify_severity(
    overlap_area: float,
    parcel_a_area: float,
    parcel_b_area: float,
) -> dict:
    """
    Classifies an overlap based on how much of the smaller parcel it covers.

    Args:
        overlap_area: Area shared by both parcels.
        parcel_a_area: Total area of the first parcel.
        parcel_b_area: Total area of the second parcel.

    Returns:
        A dictionary containing the overlap percentage and severity.
    """
    smaller_area = min(parcel_a_area, parcel_b_area)

    if smaller_area <= 0:
        raise ValueError("Parcel areas must be greater than zero")

    overlap_percentage = (overlap_area / smaller_area) * 100

    if overlap_percentage == 0:
        severity = "none"
    elif overlap_percentage < 5:
        severity = "tolerance"
    else:
        severity = "dispute"

    return {
        "overlap_percentage": overlap_percentage,
        "severity": severity,
    }
