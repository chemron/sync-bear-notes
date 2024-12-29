import click

from bear_sync.sync import sync


@click.command()
@click.argument("output-dir", type=str)
@click.option("--overwrite", is_flag=True, help="Overwrite output-dir if it exists")
def main(output_dir: str, overwrite: bool):
    sync(output_dir, overwrite)
