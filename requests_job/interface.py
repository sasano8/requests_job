class IParser:
    @classmethod
    def parse_file(cls, path: str, loader=None):
        raise NotImplementedError()

    @classmethod
    def parse_str(cls, content: str, loader=None):
        raise NotImplementedError()

    @classmethod
    def dump(cls, data, Dumper=None, **kwargs):
        raise NotImplementedError()


class ISandbox:
    pass


class IResolver:
    pass


class IClient:
    pass


class IRequest:
    pass
