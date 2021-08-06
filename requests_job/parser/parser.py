from ..schemas import Profile
from .loader import AppLoader
import yaml

__all__ = ["parse_file", "parse_str"]


def parse_file(path: str, extension: str = None, deserializer: str = None):
    return _parse_file(path=path, extension=extension, deserializer=deserializer)


def parse_str(content: str, extension: str = None, deserializer: str = None):
    return _parse_str(content, extension=extension, deserializer=deserializer)


def _parse_file(path: str, extension: str = None, deserializer: str = None):
    if not extension in {"yml", "json", "json5", "jsonc", "hjson", None}:
        raise ValueError(f"Invalid extension: {extension}")

    with open(path, "r") as f:
        content = f.read()

    return _parse_str(content, extension=extension, deserializer=deserializer)


def _parse_str(content: str, extension: str = None, deserializer: str = None):
    if not extension:
        pass
    elif extension == "yaml" or extension == "yml":
        return parse_yaml(content)
    elif extension == "json":
        return parse_json(content)
    else:
        raise ValueError(f"Invalid extension: {extension}")

    loaders = [parse_yaml, parse_json]

    errors = []

    undefined = object()
    config = undefined

    for loader in loaders:
        try:
            config = loader(content)
            break
        except Exception as e:
            errors.append(e)

    if config is undefined:
        raise RuntimeError(errors)

    return config


def parse_yaml(content: str):
    import yaml

    return yaml.safe_load(content)


def parse_json(content: str):
    import json

    return json.loads(content)
