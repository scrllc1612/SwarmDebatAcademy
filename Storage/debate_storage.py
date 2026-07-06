import json
from pathlib import Path
from typing import Any


class DebateStorage:

    def __init__(
        self,
        folder: str = "Experiments",
    ) -> None:
        self.folder = Path(folder)
        self.folder.mkdir(exist_ok=True)

    def save(
        self,
        debate_data: dict[str, Any],
    ) -> str:
        debate_id = debate_data["metadata"]["debate_id"]
        file_path = self.folder / f"{debate_id}.json"

        with file_path.open("w", encoding="utf-8") as file:
            json.dump(
                debate_data,
                file,
                indent=4,
                ensure_ascii=False,
            )

        return str(file_path)
