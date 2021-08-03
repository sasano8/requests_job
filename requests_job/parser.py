from typing import Union

from pydantic import validate_arguments

from .schemas import Profile


def load_profile(path: str):
    with open(path, "r") as f:
        return loads(f)


def loads(json):
    return load_yaml(json)


def load_yaml(file):
    import yaml

    config = yaml.safe_load(file)
    return parse(config)


def load_json(file):
    import json

    config = json.loads(file)
    return parse(config)


@validate_arguments
def parse(profile: Union[dict, Profile]) -> Profile:
    if isinstance(profile, dict):
        profile = Profile(**profile)

    return profile
