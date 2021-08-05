import typer

from .worker import HttpxJob

app = typer.Typer()


@app.command()
def run(path: str, extension: str = None):
    job = HttpxJob.parse_file(path=path, extension=extension)
    job.run()


if __name__ == "__main__":
    app()
