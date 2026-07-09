"""File-based message bus over shared/{input,processing,output,results}/."""
from __future__ import annotations

import json
from pathlib import Path

STAGES = ("input", "processing", "output", "results")


class SharedBus:
    def __init__(self, root: Path):
        self.root = Path(root)

    def stage_dir(self, stage: str) -> Path:
        if stage not in STAGES:
            raise ValueError(f"unknown stage: {stage}")
        return self.root / stage

    def setup(self) -> None:
        for stage in STAGES:
            self.stage_dir(stage).mkdir(parents=True, exist_ok=True)

    def clear(self) -> None:
        for stage in STAGES:
            d = self.stage_dir(stage)
            if d.exists():
                for f in d.glob("*.json"):
                    f.unlink()

    def _path(self, stage: str, message: dict) -> Path:
        return self.stage_dir(stage) / f"{message['message_id']}.json"

    def write(self, stage: str, message: dict) -> Path:
        path = self._path(stage, message)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(message, indent=2), encoding="utf-8")
        tmp.replace(path)  # atomic write
        return path

    def read_all(self, stage: str) -> list[dict]:
        d = self.stage_dir(stage)
        if not d.exists():
            return []
        return [json.loads(f.read_text(encoding="utf-8")) for f in sorted(d.glob("*.json"))]

    def move(self, message: dict, from_stage: str, to_stage: str) -> Path:
        src = self._path(from_stage, message)
        if src.exists():
            src.unlink()
        return self.write(to_stage, message)
