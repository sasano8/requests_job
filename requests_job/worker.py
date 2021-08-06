from . import parser, verifier
from .client import AsyncClientWrapper
from .schemas import Job, Profile


class Token:
    def __init__(self):
        self.is_cancelled = False


class HttpxJob:
    parser = parser
    __schema__ = Profile

    def __init__(self, profile):
        if not isinstance(profile, self.__schema__):
            raise TypeError(f"{profile} is not type: {self.__schema__}")

        self.profile = profile

    @classmethod
    def parse_file(cls, path: str):
        dic = cls.parser.parse_file(path=path)
        return cls.parse_dict(dic)

    @classmethod
    def parse_str(cls, content: str):
        dic = cls.parser.parse_str(content=content)
        return cls.parse_dict(dic)

    @classmethod
    def parse_dict(cls, profile: dict):
        if not isinstance(profile, dict):
            raise TypeError(f"{profile} is not dict")
        profile = cls.__schema__(**profile)
        return cls(profile)

    def run(self, token=None):
        token = token or Token()
        for job in self.profile.jobs:
            self.execute_job(job, token)

    @classmethod
    def execute_job(cls, job: Job, token):
        import asyncio

        asyncio.run(cls.execute(job, token))

    @classmethod
    async def execute(cls, job: Job, token):
        client_args = job.build_client_args()
        event_hooks = client_args.pop("event_hooks", {})

        async with AsyncClientWrapper(**client_args) as client:
            for task in job.tasks:
                if token.is_cancelled:
                    break

                request_args = task.build_request_args()
                event_hooks = request_args.pop("event_hooks", {"expect": []})

                checker = verifier.Verifier(task.expect or {})
                event_hooks["expect"].append(checker)
                result = await client.request(event_hooks, **request_args)
                print(result)
