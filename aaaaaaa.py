import os
import re

import yaml

ENV_PATTERN = re.compile(r"\$\{(.*)\}")
ENV_TAG = "!env_var"

yaml.add_implicit_resolver(ENV_TAG, ENV_PATTERN, None, yaml.SafeLoader)


def env_var_constructor(loader, node):
    value = loader.construct_scalar(node)

    matched = ENV_PATTERN.match(value)
    if matched is None:
        return value
    proto = matched.group(1)

    default = None
    if len(proto.split(":")) > 1:
        env_key, default = proto.split(":")
    else:
        env_key = proto
    env_val = os.environ.get(env_key, default)

    try:
        env_val = float(env_val)
    except:
        pass

    return env_val


def myparse():
    yaml.add_constructor(ENV_TAG, env_var_constructor, yaml.SafeLoader)

    with open("test.yaml", "r") as f:
        config = yaml.safe_load(f)
    print(config)


myparse()
