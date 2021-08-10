import pytest
import yaml


def test_yaml_types():
    from datetime import date, datetime, timezone

    import yaml

    result = yaml.safe_load("date: 2000-01-01\ndatetime: 2000-01-01 00:00:00 +00:00")
    assert result["date"] == date(2000, 1, 1)
    assert result["datetime"] == datetime(
        2000, 1, 1, hour=0, minute=0, second=0, tzinfo=timezone.utc
    )


def test_yaml_spec():
    result = yaml.dump({"root": tuple([1, 2])})
    content = "root: !!python/tuple\n- 1\n- 2\n"
    assert result == "root: !!python/tuple\n- 1\n- 2\n"

    # タグで独自型を読み込むのは脆弱性につながるため非推奨
    with pytest.raises(yaml.constructor.ConstructorError):
        yaml.safe_load(result)

    from yaml.loader import Loader

    result = yaml.load(content, Loader=Loader)
    result == {"root": tuple([1, 2])}


def test_parser():
    from requests_job import Parser
    from requests_job.sandbox import EvalStr

    content = "root: !!python/tuple\n- 1\n- 2\n"
    result = Parser.parse_str(content)
    assert result == {"root": tuple([1, 2])}

    content = "${PATH}"
    result = Parser.parse_str(content)
    assert result != "${PATH}"
    assert isinstance(result, EvalStr)
