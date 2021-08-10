from .contexts import Context
from .schemas import Profile
from .yaml import Parser


class Resolver:
    PARSER = Parser
    CONTEXT = Context
    SANDBOX = lambda: {}

    def __init__(self, value: dict):
        self.value: dict = value

    @classmethod
    def from_file(cls, path: str):
        dic = cls.PARSER.parse_file(path)
        return cls.from_dict(dic)

    @classmethod
    def from_str(cls, content: str):
        dic = cls.PARSER.parse_str(content)
        return cls.from_dict(dic)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(data)

    def __iter__(self):
        data = self.value
        ctx = self.__class__.CONTEXT()
        env = ctx["env"]
        env.update(data.get("env", {}))

        sandbox = self.__class__.SANDBOX()
        jobs = self.value.get("jobs", [])
        profile = Profile(**self.value, jobs=[])

        for job in profile.jobs:
            yield job


# 解析する
# サンドボックスで解決する
# スキーマを検証する
