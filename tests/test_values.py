import pytest

from requests_job.values import AttrInfo, AttrPath


def test_AttrPath():
    with pytest.raises(ValueError, match="empty"):
        AttrPath("")

    with pytest.raises(ValueError, match="invalid format"):
        AttrPath(1)

    with pytest.raises(ValueError, match="invalid format"):
        AttrPath("asyncio")

    with pytest.raises(ValueError, match="not exists"):
        AttrPath("asyncio:")

    assert isinstance(AttrPath("asyncio:run").value, AttrInfo)
