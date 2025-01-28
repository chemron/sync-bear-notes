import os
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path


@dataclass
class RawNote:
    raw_path: Path
    title: str
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
            Z_PK AS note_id,
            ZTITLE AS title,
            ZTRASHED AS trashed,
            ZTEXT AS text,
            ZCREATIONDATE AS creation_date,
            ZMODIFICATIONDATE AS modification_date
        FROM
            ZSFNOTE
        ORDER BY
            creation_date ASC;
        """
        self.cursor.execute(query)
        res = self.cursor.fetchall()
        return res

    def raw_tags(self):
        query = """
        SELECT
            Z_5TAGS.Z_5NOTES AS note_id,
            ZSFNOTETAG.ZTITLE AS tag
        FROM
            Z_5TAGS
        LEFT JOIN
            ZSFNOTETAG ON Z_5TAGS.Z_13TAGS = ZSFNOTETAG.Z_PK
        ORDER BY
            LENGTH(tag);
        """
        self.cursor.execute(query)
        res = self.cursor.fetchall()
        return res

    def __core_date_time_to_datetime(self, core_date_time):
        return datetime(2001, 1, 1) + timedelta(seconds=int(core_date_time))

    def save_notes(self, base_path: Path, overwrite=False):
        raw_notes = self.raw_notes()
        raw_tags = self.raw_tags()
        raw_note_dir = base_path / ".raw_notes"
        os.makedirs(raw_note_dir, exist_ok=True)

        id_to_raw_note = {}
        for (
            note_id,
            title,
            trashed,
            text,
            creation_date,
            modification_date,
        ) in raw_notes:
            if trashed or (not text):
                continue
            note_path = raw_note_dir / f"{note_id}.md"
            if not note_path.exists() or overwrite:
                with open(note_path, "w") as f:
                    f.write(text)
                id_to_raw_note[note_id] = RawNote(
                    raw_path=note_path,
                    title=title.removeprefix(".") or "untitled",
                    text=text,
                    creation_date=self.__core_date_time_to_datetime(creation_date),
                    modification_date=self.__core_date_time_to_datetime(
                        modification_date
                    ),
                )

        tagged_notes = {note_id for note_id, _ in raw_tags}
        untagged_notes = [
            (note_id, "untagged")
            for note_id in id_to_raw_note
            if note_id not in tagged_notes
        ]

        # group notes by tag and title
        notes = defaultdict(list)
        for note_id, tag in raw_tags + untagged_notes:
            # ignore trashed notes
            if note_id in id_to_raw_note:
                notes[(tag, title)].append(note_id)

        # notes with the same tag and title are ordered by creation date
        notes_synced = 0
        notes_skipped = 0
        for (tag, title), note_ids in notes.items():
            note_dir = base_path / tag

            os.makedirs(note_dir, exist_ok=True)
            for i, note_id in enumerate(note_ids):
                note = id_to_raw_note[note_id]
                text = note.text

                if i == 0:
                    suffix = ""
                else:
                    suffix = f"_{i}"

                file_name = f"{note.title.replace('/', '_')}{suffix}.md"
                file_path = note_dir / file_name

                if not file_path.exists() or overwrite:
                    os.link(note.raw_path, file_path)
                    notes_synced += 1
                else:
                    print(f"{file_path} already exists. Skipping.")
                    notes_skipped += 1

        print(f"Synced {notes_synced} notes. Skipped {notes_skipped} notes.")

    def get_non_trashed_notes(self):
        notes = self.raw_notes()
        return [note for note in notes if note[2] == 0]

    def disconnect(self):
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
    db.disconnect()
