# Bear Sync

This is a small python package to export notes from [Bear](https://bear.app/) to a local directory as markdown files.

## Installation

via [pip](https://pip.pypa.io/en/stable/installation/):

```bash
pip install bear-sync
```

## Usage

```bash
bear-sync [options] <directory>
```

Where `<directory>` should be the directory that the notes should be written to.

Options:

`--db-dir TEXT`: Path to Bear's database directory. Defaults to `~/Library/Group Containers/9K33E3U3T4.net.shinyfrog.bear/Application Data/database.sqlite`

`--overwrite`: Overwrite existing markdown files with the same name.

`--remove-existing`: Remove existing markdown files before syncing. WARNING: This will delete all markdown files in output-dir.

## Behaviour

This package attempts to mimic the behaviour of bear with a directory structure. At the moment, this results some duplication of files.
If you have a document in bear like follows:

```text
# My Bear Document

#tag/subtag #tag2

This is my bear document.
```

then the resulting directory structure will be:

```text
bear_sync_folder/
├── tag/
|   ├── My Bear Document.md
│   ├── subtag/
│   │   ├── My Bear Document.md
├── tag2/
|   ├── My Bear Document.md
```

## Example - using bear-sync with git

Setup a new git repository:

```bash
mkdir bear_notes
cd bear_notes
git init
```

Create a shell script to sync the bear notes:

```bash
cat <<EOF > bear_sync.sh
NOTES_PATH="$HOME/bear_notes"

bear-sync --overwrite --remove-existing "$NOTES_PATH"
git -C "$NOTES_PATH" add .
git -C "$NOTES_PATH" commit -m "notes backup: $(date)"
EOF
```

Give the new script execution permissions:

```bash
chmod +x ./bear_sync.sh
```

Run!

```bash
./bear_sync.sh
```
