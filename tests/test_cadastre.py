from parcel_resolver.cadastre import validate_parcel
from tests.fixtures.sample_parcels import SAMPLE_PARCELS

def test_p001_has_no_flags():
    result = validate_parcel(SAMPLE_PARCELS["P001"])
    assert result["is_valid"] is True

def test_p002_has_no_flags():
    result = validate_parcel(SAMPLE_PARCELS["P002"])
    assert result["is_valid"] is True

def test_tiny_parcel_flagged_suspicious_area():
    result = validate_parcel(SAMPLE_PARCELS["P006"])
    assert "suspicious area" in result["flags"]
