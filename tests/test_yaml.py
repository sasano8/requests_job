def test_yaml_types():
    from datetime import date, datetime, timezone

    import yaml

    result = yaml.safe_load("date: 2000-01-01\ndatetime: 2000-01-01 00:00:00 +00:00")
    assert result["date"] == date(2000, 1, 1)
    assert result["datetime"] == datetime(
        2000, 1, 1, hour=0, minute=0, second=0, tzinfo=timezone.utc
    )
