import typer

from .parser import load_profile

app = typer.Typer()


@app.command()
def run(path: str):
    profile = load_profile(path)


if __name__ == "__main__":
    app()
