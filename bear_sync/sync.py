import os
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path


@dataclass
class Note:
    title: str
    tag: str
    trashed: bool
    text: str
    creation_date: datetime
    modification_date: datetime


DEFAULT_DB_PATH = (
    Path.home()
    / "Library"
    / "Group Containers"
    / "9K33E3U3T4.net.shinyfrog.bear"
    / "Application Data"
    / "database.sqlite"
)


class BearDB:

    def __init__(self, db_path: Path):
        self.con = sqlite3.connect(db_path)
        self.cursor = self.con.cursor()

    def get_tables(self):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        res = self.cursor.fetchall()
        return [name[0] for name in res]

    def raw_notes(self):
        query = """
        SELECT
            ZSFNOTE.ZTITLE AS title,
            ZSFNOTETAG.ZTITLE AS tag,
            ZSFNOTE.ZTRASHED AS trashed,
            ZSFNOTE.ZTEXT AS text,
            ZCREATIONDATE AS creation_date,
            ZSFNOTE.ZMODIFICATIONDATE AS modification_date
        FROM
            ZSFNOTE
        LEFT JOIN
            Z_5TAGS ON ZSFNOTE.Z_PK = Z_5TAGS.Z_5NOTES
        LEFT JOIN
            ZSFNOTETAG ON Z_5TAGS.Z_13TAGS = ZSFNOTETAG.Z_PK
        ORDER BY
            LENGTH(tag),
            creation_date ASC;
        """
        self.cursor.execute(query)
        res = self.cursor.fetchall()
        return res

    def __core_date_time_to_datetime(self, core_date_time):
        return datetime(2001, 1, 1) + timedelta(seconds=int(core_date_time))

    def save_notes(self, path: Path, overwrite=False):
        notes = defaultdict(list)
        for (
            title,
            tag,
            trashed,
            text,
            creation_date,
            modification_date,
        ) in self.raw_notes():
            if trashed or (not text):
                continue
            if not tag:
                tag = "untagged"
            if not title:
                title = "untitled"

            notes[(tag, title)].append(
                Note(
                    title=title,
                    tag=tag,
                    trashed=trashed,
                    text=text,
                    creation_date=self.__core_date_time_to_datetime(creation_date),
                    modification_date=self.__core_date_time_to_datetime(
                        modification_date
                    ),
                )
            )

        # notes with the same tag and title are ordered by creation date

        notes_synced = 0
        notes_skipped = 0
        for (tag, title), note_set in notes.items():
            base_path = path / tag

            os.makedirs(base_path, exist_ok=True)
            for i, note in enumerate(note_set):
                text = note.text

                if i == 0:
                    suffix = ""
                else:
                    suffix = f"_{i}"

                file_name = f"{note.title.replace('/', '_')}{suffix}.md"
                file_path = base_path / file_name

                if not file_path.exists() or overwrite:
                    with open(file_path, "w") as f:
                        print(f"Writing {file_path}")
                        f.write(text)
                        notes_synced += 1
                else:
                    print(f"{file_path} already exists. Skipping.")
                    notes_skipped += 1

        print(f"Synced {notes_synced} notes. Skipped {notes_skipped} notes.")

    def get_non_trashed_notes(self):
        notes = self.raw_notes()
        return [note for note in notes if note[2] == 0]

    def dissconnect(self):
        self.con.close()


def sync(
    output_path: Path,
    db_path: Path = DEFAULT_DB_PATH,
    overwrite: bool = False,
    remove_existing: bool = False,
):
    if remove_existing:
        for path in output_path.glob("**/*.md"):
            print("Deleting ", path)
            path.unlink()

    # Connect to Bear database
    db = BearDB(db_path)
    db.save_notes(Path(output_path), overwrite)
    db.dissconnect()
