import random
from typing import Any, AsyncGenerator, Dict, List

from aiofiles.tempfile import NamedTemporaryFile
from aiofiles.threadpool.binary import AsyncBufferedIOBase
from fastapi import Body, Depends, FastAPI, File, Request, UploadFile
from starlette.responses import FileResponse, Response

from .auth import router as auth_router

app = FastAPI(debug=True)
app.include_router(auth_router, prefix="/auth")

db: Dict[int, Any] = {}

count_startup = 0
count_shutdown = 0


@app.on_event("startup")
async def on_startup():
    global count_startup
    count_startup += 1


@app.on_event("shutdown")
async def on_shutdown():
    global count_shutdown
    count_shutdown += 1


def clear_count():
    global count_startup, count_shutdown
    count_startup = 0
    count_shutdown = 0


@app.get("/")
def get_data():
    return list(db.values())


@app.post("/post_record")
def post_record(body: dict):
    assert not hasattr(body, "id")
    obj = {"id": random.randint(0, 100), **body}
    id = obj["id"]
    db[id] = obj
    return obj


@app.get("/get_record/{id}")
def get_record(id: int):
    # return db[id]
    return True


@app.put("/put_record/{id}")
def put_record(id: int, body: dict):
    obj = {"id": id, **body}
    db[id] = obj
    return obj


@app.patch("/patch_record/{id}")
def patch_record(id: int, body: dict):
    current = db[id]
    updated = {**current, **body}
    db[id] = updated
    return updated


@app.delete("/delete_record/{id}")
def delete_record(id: int):
    del db[id]
    return 1


def get_files_path():
    from pathlib import Path

    import requests_job

    return Path(requests_job.__file__).parent / "files"


@app.get("/file")
async def download_file(id: int):
    return FileResponse(
        path=get_files_path() / "sample.txt",
        filename="sample.txt",
    )


async def get_tmp_file() -> AsyncGenerator[Any, AsyncBufferedIOBase]:
    async with NamedTemporaryFile("wb") as f:
        yield f


@app.post("/file")
async def upload_file(
    *,
    file: UploadFile = File(...),
    request: Request,
    tmp: AsyncBufferedIOBase = Depends(get_tmp_file)
):
    await tmp.write(await file.read())
    await tmp.flush()
    return FileResponse(str(tmp.name))


@app.post("/file/upload_multiple")
async def upload_multiple_file(files: List[UploadFile] = File(...)):
    results = []
    for file in files:
        content = await file.read()
        results.append({"name": file.filename, "content": content})
    return results


@app.post("/wait")
async def wait_request(wait: float = Body(0, embed=True)):
    import asyncio

    await asyncio.sleep(wait)
    return None
