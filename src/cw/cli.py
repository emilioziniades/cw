import click
from cw.fetch import fetch as cw_fetch
from cw import db

db.migrate()


@click.group()
def cli():
    pass


@cli.command()
@click.option("--number", type=int)
@click.option(
    "--style",
    required=True,
    type=click.Choice(["quick", "mini", "cryptic"]),
)
def fetch(number, style):
    puzzle_json = cw_fetch(number, style)
    if not db.has_crossword(puzzle_json):
        db.add_crossword(puzzle_json)

    click.echo("Fetched crossword")
