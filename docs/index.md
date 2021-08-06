<p align="center" style="margin: 0 0 10px">
  <img width="350" height="208" src="https://raw.githubusercontent.com/encode/httpx/master/docs/img/butterfly.png" alt='HTTPX'>
</p>

<h1 align="center" style="font-size: 3rem; margin: -15px 0">
HTTPX
</h1>

---

<div align="center">
<p>
<a href="https://github.com/encode/httpx/actions">
    <img src="https://github.com/encode/httpx/workflows/Test%20Suite/badge.svg" alt="Test Suite">
</a>
<a href="https://pypi.org/project/httpx/">
    <img src="https://badge.fury.io/py/httpx.svg" alt="Package version">
</a>
</p>

<em>A next-generation HTTP client for Python.</em>
</div>

HTTPX is a fully featured HTTP client for Python 3, which provides sync and async APIs, and support for both HTTP/1.1 and HTTP/2.


!!! note
    HTTPX should currently be considered in beta.

    We believe we've got the public API to a stable point now, but would strongly recommend pinning your dependencies to the `0.18.*` release, so that you're able to properly review [API changes between package updates](https://github.com/encode/httpx/blob/master/CHANGELOG.md).

    A 1.0 release is expected to be issued sometime in 2021.

---



## Features

- httpxのapiに基づいたリクエストの一括管理
- レスポンスの検証
- テストとバッチ処理支援

## Documentation



## Dependencies

- `httpx`

## Installation

Install with pip:

```shell
$ pip install httpx
```

Or, to include the optional HTTP/2 support, use:

```shell
$ pip install httpx[http2]
```

To include the optional brotli decoder support, use:

```shell
$ pip install httpx[brotli]
```

HTTPX requires Python 3.6+

[sync-support]: https://github.com/encode/httpx/issues/572


# Getting Started

```python
import mink

jobs = mink.load("sample.yml")
jobs = jobs.filter(tags=["production", "daily"], name=lambda x: "" in x)
jobs = jobs.tasks.filter(tags={"15"})

jobs.run()

```
