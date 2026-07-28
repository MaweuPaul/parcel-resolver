import pytest

from parcel_resolver.resolver.severity import classify_severity


@pytest.mark.parametrize(
    ("overlap_area", "expected_percentage", "expected_severity"),
    [
        (0.5, 0.5, "low"),
        (1.0, 1.0, "medium"),
        (10.0, 10.0, "medium"),
        (11.0, 11.0, "high"),
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
        "severity": "medium",
        "overlap_percentage": 4.0,
    }


def test_classify_severity_rejects_zero_area():
    with pytest.raises(ValueError, match="greater than zero"):
        classify_severity(1.0, 0.0, 100.0)
