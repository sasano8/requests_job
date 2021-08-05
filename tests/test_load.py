import pytest


def test_loadaaa():
    from requests_job import HttpxJob

    profile = HttpxJob.parse_file("tests/mock.yaml")
    profile.run()
