import pytest

from parcel_resolver.resolver.severity import classify_severity


@pytest.mark.parametrize(
    ("overlap_area", "expected_percentage", "expected_severity"),
    [
        (0.0, 0.0, "none"),
        (0.5, 0.5, "tolerance"),
        (4.99, 4.99, "tolerance"),
        (5.0, 5.0, "dispute"),
        (11.0, 11.0, "dispute"),
    ],
)
def test_classify_severity_thresholds(
    overlap_area,
    expected_percentage,
    expected_severity,
):
    result = classify_severity(overlap_area, 100.0, 200.0)

    assert result["overlap_percentage"] == expected_percentage
    assert result["severity"] == expected_severity


def test_classify_severity_uses_smaller_parcel_area():
    result = classify_severity(4.0, 100.0, 400.0)

    assert result == {
        "overlap_percentage": 4.0,
        "severity": "tolerance",
    }


def test_classify_severity_rejects_zero_area():
    with pytest.raises(ValueError, match="greater than zero"):
        classify_severity(1.0, 0.0, 100.0)
