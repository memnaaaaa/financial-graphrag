import json
from dataclasses import dataclass, field
from pathlib import Path

from . import config


@dataclass
class Chunk:
    chunk_id: str
    text: str
    meta: dict = field(default_factory=dict)


def _pick(row: dict, aliases: list[str], what: str, lineno: int):
    for a in aliases:
        if a in row:
            return a, row[a]
    raise KeyError(f"line {lineno}: no {what} field; looked for {aliases}, found {list(row)}")


def load_chunks(path) -> list[Chunk]:
    chunks, seen = [], set()
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            ik, cid = _pick(row, config.ID_FIELDS, "id", i)
            tk, text = _pick(row, config.TEXT_FIELDS, "text", i)
            cid = str(cid)
            if cid in seen:
                raise ValueError(f"duplicate chunk id {cid!r} at line {i}")
            seen.add(cid)
            meta = {k: v for k, v in row.items() if k not in (ik, tk)}
            chunks.append(Chunk(cid, text, meta))
    if not chunks:
        raise ValueError(f"{path} has no chunks")
    return chunks


def load_questions(path) -> list[dict]:
    qs = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    for q in qs:
        for key in ("qid", "question", "gold_chunk_ids", "gold_answer"):
            if key not in q:
                raise KeyError(f"question {q.get('qid')} missing {key}")
    return qs


def check_gold_ids(questions: list[dict], chunks: list[Chunk]) -> None:
    """Fail loudly if a question points at a chunk id that isn't in the file."""
    ids = {c.chunk_id for c in chunks}
    bad = {q["qid"]: [g for g in q["gold_chunk_ids"] if g not in ids] for q in questions}
    bad = {k: v for k, v in bad.items() if v}
    if bad:
        raise ValueError(f"gold chunk ids not found in chunks file: {bad}")
