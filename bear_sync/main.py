from pathlib import Path
from typing import Optional

import click

from bear_sync.sync import DEFAULT_DB_PATH, sync


@click.command()
@click.argument("output-dir", type=str)
@click.option("--db-dir", type=str, help="Path to Bear's database directory.")
@click.option(
    "--overwrite",
    is_flag=True,
    help="Overwrite existing markdown files with the same name.",
)
@click.option(
    "--remove-existing",
    is_flag=True,
    help="Remove existing markdown files before syncing. WARNING: This will delete all markdown files in output-dir.",
)
def main(
    output_dir: str,
    db_dir: Optional[str],
    overwrite: bool,
    remove_existing: bool,
):
    sync(
        output_path=Path(output_dir),
        db_path=Path(db_dir) if db_dir else DEFAULT_DB_PATH,
        overwrite=overwrite,
        remove_existing=remove_existing,
    )
