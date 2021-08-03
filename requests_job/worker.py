from functools import partial, wraps
from typing import Union

from asgi_lifespan import LifespanManager
from httpx import Response

from . import verifier
from .client import AsyncClientWrapper
from .schemas import Job, Profile
from .transport import ASGITransportLifespan


class Token:
    def __init__(self):
        self.is_cancelled = False


def run(config: Union[dict, Profile], token=None):
    token = token or Token()
    if isinstance(config, dict):
        profile = Profile(**config)
    elif isinstance(config, Profile):
        profile = config
    else:
        raise TypeError(f"{config.__class__} is not valid type.")

    for job in profile.jobs:
        execute_job(job, token)


def execute_job(job: Job, token):
    import asyncio

    asyncio.run(execute(job, token))


def manage_lifespan(func):
    @wraps(func)
    async def wrapper(job: Job, token):
        lifespan = None
        if job.transport:
            transport = job.transport.get_value()
            if isinstance(transport, ASGITransportLifespan):
                lifespan = transport

        if job.app:
            # transportを使用しない場合、サーバエラーはraiseされ、処理が失敗する
            lifespan = LifespanManager(job.app.value.attr)  # type: ignore

        if lifespan:
            # job.event_hooks.asgi_startup
            # httpxはstartup,shutdownイベントを発火しないので、発火させる
            async with LifespanManager(job.app.value.attr):
                await func(job, token)
            # job.event_hooks.asgi_shutdown
        else:
            await func(job, token)

    return wrapper


@manage_lifespan
async def execute(job: Job, token):
    client_args = job.build_client_args()
    event_hooks = client_args.pop("event_hooks", {})

    if job.app is not None:
        client_args["app"] = job.app.value.attr

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


def validate_expect(res: Response, checker):
    checker(res)
