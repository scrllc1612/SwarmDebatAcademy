import json
from pathlib import Path
from typing import Any

from Models.toulmin_models import DebateState, DebateRound, ToulminArgument
from Models.moderator_models import DebateSummary


class SavedDebateLoader:
    @staticmethod
    def _argument_from_dict(argument_data: dict[str, Any]) -> ToulminArgument:
        return ToulminArgument(
            stance=argument_data["stance"],
            round_number=argument_data["round_number"],
            claim=argument_data["claim"],
            data=argument_data["data"],
            warrant=argument_data["warrant"],
            backing=argument_data["backing"],
            rebuttal=argument_data["rebuttal"],
            speech=argument_data["speech"],
        )

    @staticmethod
    def _summary_from_dict(summary_data: dict[str, Any]) -> DebateSummary:
        return DebateSummary(
            pro_main_point=summary_data["pro_main_point"],
            contra_main_point=summary_data["contra_main_point"],
            main_conflict=summary_data["main_conflict"],
            unresolved_issue=summary_data["unresolved_issue"],
        )

    @classmethod
    def _round_from_dict(cls, round_data: dict[str, Any]) -> DebateRound:
        return DebateRound(
            round_number=round_data["round_number"],
            pro_argument=cls._argument_from_dict(round_data["pro_argument"]),
            contra_argument=cls._argument_from_dict(round_data["contra_argument"]),
            moderator_summary=cls._summary_from_dict(round_data["moderator_summary"]),
        )

    @classmethod
    def load_as_debate_state(cls, file_path: str | Path) -> DebateState:
        file_path = Path(file_path)

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        metadata = data["metadata"]
        rounds_data = data["rounds"]

        rounds = [
            cls._round_from_dict(round_item)
            for round_item in rounds_data
        ]

        debate = DebateState(
            topic=metadata["topic"],
            current_round=metadata.get("current_round", metadata["total_rounds"]),
            rounds=rounds,
            is_finished=metadata["is_finished"],
        )

        if hasattr(debate, "debate_id") and "debate_id" in metadata:
            debate.debate_id = metadata["debate_id"]

        return debate
