import pytest

# from requests_job import Profile


# @pytest.fixture(scope="session")
# def success():
#     from requests_job import parser

#     return parser.load("tests/success.yaml")


# @pytest.fixture(scope="session")
# def example():
#     from requests_job import parser

#     return parser.load("tests/example.yaml")


# @pytest.fixture(scope="session")
# def mock():
#     from requests_job import parser

#     return parser.load("tests/mock.yaml")


# def test_load(success: Profile, example: Profile, mock: Profile):
#     assert isinstance(success, Profile)
#     assert isinstance(example, Profile)
#     assert isinstance(mock, Profile)


# def test_build_request(success: Profile):
#     results = []
#     for job in success.jobs:
#         results.append(job.get_requests())


# @pytest.mark.asyncio
# async def test_example(example: Profile):
#     task = example.jobs[0].tasks[0]
#     result = await task.request()
#     assert result.status_code == 200

#     task = example.jobs[0].tasks[1]
#     with pytest.raises(Exception):
#         result = await task.request()


def test_loadaaa():
    from requests_job.parser import load_profile
    from requests_job.worker import run

    profile = load_profile("tests/mock.yaml")
    assert profile

    run(profile)
