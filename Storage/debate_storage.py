from pathlib import Path
import json


class DebateStorage:

    def __init__(
        self,
        folder: str = "Experiments"
    ):

        self.folder = Path(folder)

        self.folder.mkdir(
            exist_ok=True
        )

    def save(
        self,
        debate_data: dict
    ) -> str:

        debate_id = debate_data["metadata"]["debate_id"]

        file_path = (
            self.folder /
            f"{debate_id}.json"
        )

        with open(
            file_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                debate_data,
                f,
                indent=4,
                ensure_ascii=False
            )

        return str(file_path)