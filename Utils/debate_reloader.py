import json
from pathlib import Path

from Models.toulmin_models import DebateState, DebateRound, ToulminArgument
from Models.moderator_models import DebateSummary


class SavedDebateLoader:
    @staticmethod
    def load_as_debate_state(file_path: str | Path) -> DebateState:
        file_path = Path(file_path)

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        metadata = data["metadata"]
        rounds_data = data["rounds"]

        rounds = []

        for round_item in rounds_data:
            pro = ToulminArgument(
                stance=round_item["pro_argument"]["stance"],
                round_number=round_item["pro_argument"]["round_number"],
                claim=round_item["pro_argument"]["claim"],
                data=round_item["pro_argument"]["data"],
                warrant=round_item["pro_argument"]["warrant"],
                backing=round_item["pro_argument"]["backing"],
                rebuttal=round_item["pro_argument"]["rebuttal"],
                speech=round_item["pro_argument"]["speech"],
            )

            contra = ToulminArgument(
                stance=round_item["contra_argument"]["stance"],
                round_number=round_item["contra_argument"]["round_number"],
                claim=round_item["contra_argument"]["claim"],
                data=round_item["contra_argument"]["data"],
                warrant=round_item["contra_argument"]["warrant"],
                backing=round_item["contra_argument"]["backing"],
                rebuttal=round_item["contra_argument"]["rebuttal"],
                speech=round_item["contra_argument"]["speech"],
            )

            summary = DebateSummary(
                pro_main_point=round_item["moderator_summary"]["pro_main_point"],
                contra_main_point=round_item["moderator_summary"]["contra_main_point"],
                main_conflict=round_item["moderator_summary"]["main_conflict"],
                unresolved_issue=round_item["moderator_summary"]["unresolved_issue"],
            )

            debate_round = DebateRound(
                round_number=round_item["round_number"],
                pro_argument=pro,
                contra_argument=contra,
                moderator_summary=summary,
            )

            rounds.append(debate_round)

        debate = DebateState(
            topic=metadata["topic"],
            current_round=metadata.get("current_round", metadata["total_rounds"]),
            rounds=rounds,
            is_finished=metadata["is_finished"],
        )

        if hasattr(debate, "debate_id") and "debate_id" in metadata:
            debate.debate_id = metadata["debate_id"]

        return debate