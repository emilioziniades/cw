import click
from cw.fetch import fetch as cw_fetch


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
    click.echo(repr(number))
    click.echo(style)
    click.echo("fetching " + style)
    cw_fetch(number, style)
