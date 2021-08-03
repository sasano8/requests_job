from typing import Optional

import httpx
from asgi_lifespan import LifespanManager

unfefined = object()


class ASGITransportLifespan(httpx.ASGITransport):
    def __init__(
        self,
        app: str,
        raise_app_exceptions: bool = False,
        root_path: str = unfefined,  # type: ignore
        client=("127.0.0.1", 0),  # 一般的には0をbindするとOSが自動でポートを割り当てる
        startup_timeout: Optional[float] = 60 * 5,
        shutdown_timeout: Optional[float] = 60 * 10,
        **kwargs
    ):
        kwargs = dict(
            app=app,
            raise_app_exceptions=raise_app_exceptions,
            root_path=root_path,
            client=client,
            **kwargs
        )
        kwargs = {k: v for k, v in kwargs.items() if v is not unfefined}  # type: ignore
        self.kwargs = kwargs
        self.lifespan = None
        self.startup_timeout = startup_timeout
        self.shutdown_timeout = shutdown_timeout

    async def __aenter__(self):
        if self.lifespan:
            raise RuntimeError("app already running.")
        super().__init__(**self.kwargs)
        self.lifespan = LifespanManager(
            self.app,
            startup_timeout=self.startup_timeout,
            shutdown_timeout=self.shutdown_timeout,
        )  # type: ignore
        return await self.lifespan.__aenter__()

    async def __aexit__(self, exc_type, exc, tb):
        lifespan = self.lifespan
        self.lifespan = None
        return await lifespan.__aexit__(exc_type, exc, tb)

    async def handle_async_request(self, **kwargs):
        if self.lifespan is None:
            raise RuntimeError("app is not running.")
        return await super().handle_async_request(**kwargs)
