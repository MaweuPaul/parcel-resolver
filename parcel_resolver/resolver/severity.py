def classify_severity(
    overlap_area: float,
    parcel_a_area: float,
    parcel_b_area: float,
) -> dict:
    """
    Classifies an overlap by the percentage of the smaller parcel it covers.

    Less than 1% is low severity, 1% through 10% is medium severity, and
    greater than 10% is high severity.
    """
    smaller_area = min(parcel_a_area, parcel_b_area)

    if smaller_area <= 0:
        raise ValueError("Parcel areas must be greater than zero")

    overlap_percentage = (overlap_area / smaller_area) * 100

    if overlap_percentage < 1:
        severity = "low"
    elif overlap_percentage <= 10:
        severity = "medium"
    else:
        severity = "high"

    return {
        "severity": severity,
        "overlap_percentage": overlap_percentage,
    }
