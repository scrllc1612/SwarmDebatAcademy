from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from Models.toulmin_models import DebateState
from Storage.debate_storage import DebateStorage
from Swarm.swarm_controller import SwarmController
from Utils.debate_reloader import SavedDebateLoader


APP_DIR = Path(__file__).resolve().parent
EXPERIMENTS_DIR = APP_DIR / "Experiments"
FRONTEND_DIR = APP_DIR / "frontend"


class DebateCreateRequest(BaseModel):
    topic: str = Field(..., min_length=5)
    total_rounds: int = Field(default=3, ge=1, le=5)


app = FastAPI(
    title="Generador Academico de Debates",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _argument_to_dict(argument) -> dict[str, Any]:
    return {
        "stance": argument.stance,
        "round_number": argument.round_number,
        "claim": argument.claim,
        "data": argument.data,
        "warrant": argument.warrant,
        "backing": argument.backing,
        "rebuttal": argument.rebuttal,
        "speech": argument.speech,
    }


def _round_to_dict(round_obj) -> dict[str, Any]:
    summary = None
    if round_obj.moderator_summary is not None:
        summary = round_obj.moderator_summary.model_dump()

    return {
        "round_number": round_obj.round_number,
        "pro_argument": _argument_to_dict(round_obj.pro_argument),
        "contra_argument": _argument_to_dict(round_obj.contra_argument),
        "moderator_summary": summary,
    }


def _round_metrics(metrics: dict[str, Any] | None) -> list[dict[str, Any]]:
    if metrics is None:
        return []

    rows = []
    for round_result in metrics["rounds"]:
        rows.append(
            {
                "round_number": round_result["round_number"],
                "pro": {
                    "argument_score_100": round_result["pro"]["argument_score_100"],
                    "claim_quality": round_result["pro"]["claim_quality"]["score"] * 100,
                    "data_relevance": round_result["pro"]["data_relevance"]["score"] * 100,
                    "data_sufficiency": round_result["pro"]["data_sufficiency"]["score"] * 100,
                    "warrant_strength": round_result["pro"]["warrant_strength"]["score"] * 100,
                    "backing_adequacy": round_result["pro"]["backing_adequacy"]["score"] * 100,
                    "rebuttal_effectiveness": round_result["pro"]["rebuttal_effectiveness"]["score"] * 100,
                },
                "contra": {
                    "argument_score_100": round_result["contra"]["argument_score_100"],
                    "claim_quality": round_result["contra"]["claim_quality"]["score"] * 100,
                    "data_relevance": round_result["contra"]["data_relevance"]["score"] * 100,
                    "data_sufficiency": round_result["contra"]["data_sufficiency"]["score"] * 100,
                    "warrant_strength": round_result["contra"]["warrant_strength"]["score"] * 100,
                    "backing_adequacy": round_result["contra"]["backing_adequacy"]["score"] * 100,
                    "rebuttal_effectiveness": round_result["contra"]["rebuttal_effectiveness"]["score"] * 100,
                },
            }
        )
    return rows


def _payload_from_debate(
    debate: DebateState,
    metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "metadata": {
            "debate_id": debate.debate_id,
            "system": "swarm",
            "version": "1.0",
            "model_name": "gpt-4o-mini",
            "topic": debate.topic,
            "total_rounds": len(debate.rounds),
            "is_finished": debate.is_finished,
        },
        "rounds": [_round_to_dict(round_obj) for round_obj in debate.rounds],
        "round_metrics": _round_metrics(metrics),
        "evaluation": None,
    }

    if metrics is not None:
        payload["evaluation"] = {
            "evaluator_version": "1.0",
            "tqs": metrics["average_argument_score_100"],
            "sc": metrics["global_coherence"]["global_coherence_score_100"],
            "debate_score": metrics["debate_score_100"],
        }

    return payload


def _debate_file(debate_id: str) -> Path:
    safe_id = Path(debate_id).name
    return EXPERIMENTS_DIR / f"{safe_id}.json"


def _read_debate_file(file_path: Path) -> dict[str, Any]:
    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _load_saved_debate(debate_id: str) -> dict[str, Any]:
    file_path = _debate_file(debate_id)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Debate no encontrado")
    return _read_debate_file(file_path)


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/debates")
def list_debates() -> list[dict[str, Any]]:
    EXPERIMENTS_DIR.mkdir(exist_ok=True)
    debates = []

    for file_path in sorted(
        EXPERIMENTS_DIR.glob("*.json"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    ):
        try:
            data = _read_debate_file(file_path)
            metadata = data.get("metadata", {})
            debates.append(
                {
                    "debate_id": metadata.get("debate_id", file_path.stem),
                    "topic": metadata.get("topic", "Tema sin titulo"),
                    "total_rounds": metadata.get("total_rounds", len(data.get("rounds", []))),
                    "is_finished": metadata.get("is_finished", False),
                    "has_evaluation": bool(data.get("evaluation")),
                }
            )
        except (json.JSONDecodeError, OSError):
            continue

    return debates


@app.post("/api/debates")
def create_debate(request: DebateCreateRequest) -> dict[str, Any]:
    controller = SwarmController()
    debate = controller.generate_debate(
        topic=request.topic.strip(),
        total_rounds=request.total_rounds,
    )

    payload = _payload_from_debate(debate)
    DebateStorage(folder=str(EXPERIMENTS_DIR)).save(payload)
    return payload


@app.get("/api/debates/{debate_id}")
def get_debate(debate_id: str) -> dict[str, Any]:
    return _load_saved_debate(debate_id)


@app.post("/api/debates/{debate_id}/evaluate")
def evaluate_debate(debate_id: str) -> dict[str, Any]:
    from Evaluation.toulmin_score import ToulminScorer

    file_path = _debate_file(debate_id)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Debate no encontrado")

    debate = SavedDebateLoader.load_as_debate_state(file_path)
    metrics = ToulminScorer().score_debate(debate)
    payload = _payload_from_debate(debate, metrics)
    DebateStorage(folder=str(EXPERIMENTS_DIR)).save(payload)
    return payload


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
