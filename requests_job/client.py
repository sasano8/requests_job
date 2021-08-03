from typing import Callable, Iterable

import httpx


class AsyncClientWrapper:
    events = {
        "build_request",
        "request",
        "response",
        "expect",
        "success",
        "error",
        "complete",
        "exception",
    }

    def __init__(self, **kwargs):
        # dryrun
        httpx.AsyncClient(**kwargs)
        self.kwargs = kwargs

    @staticmethod
    def _build_args(kwargs):
        request_args = {}
        send_args = {}

        for k, v in kwargs.items():
            if k in {"allow_redirects", "timeout", "stream", "auth"}:
                send_args[k] = v
            else:
                request_args[k] = v

        return request_args, send_args

    async def request(self, event_hooks={}, **kwargs):
        if self.client is None:
            raise RuntimeError("Client not created.use async with")
        event_hooks = self._build_event_hooks(event_hooks)

        request_args, send_args = self._build_args(kwargs)

        request = self.client.build_request(**request_args)
        request = self.on_build_request(request, event_hooks["build_request"])
        errors = self.on_request(request, event_hooks["request"])

        response = await self.client.send(request, **send_args)
        errors = self.on_response(response, event_hooks["response"])
        errors = self.on_expect(response, event_hooks["expect"])
        errors = await self.on_success(response, event_hooks["success"])
        errors = await self.on_error(response, event_hooks["error"])
        errors = await self.on_complete(response, event_hooks["complete"])
        errors = await self.on_exception(errors, event_hooks["exception"])
        return response

    async def __aenter__(self):
        self.client = httpx.AsyncClient(**self.kwargs)
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        client = self.client
        self.client = None
        return await client.__aexit__(exc_type, exc, tb)

    @classmethod
    def _build_event_hooks(cls, event_hooks: dict):
        base_event_hooks = {k: [] for k in cls.events}  # type: ignore
        event_hooks = event_hooks or {}
        base_event_hooks.update(event_hooks)
        return base_event_hooks

    def on_build_request(self, request, events: Iterable[Callable]):
        for func in events:
            request = func(request)
        return request

    def on_request(self, request, events: Iterable[Callable]):
        for func in events:
            func(request)

    def on_response(self, response, events: Iterable[Callable]):
        for func in events:
            func(response)

    def on_expect(self, response, events: Iterable[Callable]):
        for func in events:
            func(response)

    async def on_success(self, response, events: Iterable[Callable]):
        for func in events:
            await func(response)

    async def on_error(self, response, events: Iterable[Callable]):
        for func in events:
            await func(response)

    async def on_complete(self, response, events: Iterable[Callable]):
        for func in events:
            await func(response)

    async def on_exception(self, errors, events: Iterable[Callable]):
        """
        イベント実行時に想定外のエラーが発生した場合に実行される
        """
        if not errors:
            return

        for func in events:
            await func(errors)
