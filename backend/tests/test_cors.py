from parcel_resolver.api.cors import get_allowed_origins


def test_defaults_to_local_dev_server(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)

    assert get_allowed_origins() == ["http://localhost:3000"]


def test_parses_comma_separated_origins(monkeypatch):
    monkeypatch.setenv(
        "CORS_ORIGINS", "https://app.example.com,https://staging.example.com"
    )

    assert get_allowed_origins() == [
        "https://app.example.com",
        "https://staging.example.com",
    ]


def test_trims_whitespace_and_drops_empty_entries(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", " https://app.example.com , , ")

    assert get_allowed_origins() == ["https://app.example.com"]
