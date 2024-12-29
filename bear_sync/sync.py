import os
import shutil
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


DB_PATH = (
    Path.home()
    / "Library"
    / "Group Containers"
    / "9K33E3U3T4.net.shinyfrog.bear"
    / "Application Data"
    / "database.sqlite"
)

NOTES_PATH = Path.home() / "Notes" / "note_sync"
try:
    shutil.rmtree(NOTES_PATH)
except FileNotFoundError:
    pass


class BearDB:
    # Tables in Bear database
    # ZSFCHANGE
    # ZSFCHANGEITEM
    # ZSFEXTERNALCHANGES
    # ZSFINTERNALCHANGES
    # ZSFNOTE Z_PK, ZTITLE: title, ZTEXT: text , ZTRASHED: trashed 1/0,
    #   ZMODIFICATIONDATE: seconds since 2001-01-01, ZCREATIONDATE: seconds since 2001-01-01
    # Z_5TAGS Z_5NOTES: note pk, Z_13TAGS: tag pk
    # ZSFNOTEBACKLINK
    # ZSFNOTEFILE
    # ZSFNOTEFILESERVERDATA
    # ZSFNOTESERVERDATA
    # ZSFNOTETAG   z_pk , ZTITLE: tag - parent_tag/child_tag is distinct from parent_tag
    # ZSFPASSWORD
    # ZSFSERVERMETADATA
    # Z_PRIMARYKEY
    # Z_METADATA
    # Z_MODELCACHE

    def __init__(self, db_path):
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

    def save_notes(self, path):
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
                with open(file_path, "w") as f:
                    f.write(text)

    def get_non_trashed_notes(self):
        notes = self.raw_notes()
        return [note for note in notes if note[2] == 0]

    def dissconnect(self):
        self.con.close()


# Connect to Bear database
db = BearDB(DB_PATH)
db.save_notes(NOTES_PATH)
db.dissconnect()
