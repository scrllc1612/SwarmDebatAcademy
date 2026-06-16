from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer

from Models.toulmin_models import DebateState, DebateRound, ToulminArgument


@dataclass
class ScoreWeights:
    claim_quality: float = 0.15
    data_relevance: float = 0.20
    data_sufficiency: float = 0.15
    warrant_strength: float = 0.20
    backing_adequacy: float = 0.10
    rebuttal_effectiveness: float = 0.20
    global_coherence: float = 0.15


STANCE_MARKERS = {
    "es", "debe", "deben", "debería", "deberian", "priorizar", "priorizarse",
    "mejor", "peor", "conviene", "necesita", "urge", "importa", "supera"
}

INFERENTIAL_MARKERS = {
    "porque", "por lo tanto", "por tanto", "dado que", "ya que", "puesto que",
    "si", "entonces", "por eso", "en consecuencia", "implica", "justifica"
}

SUPPORT_MARKERS = {
    "según", "estudio", "informe", "análisis", "teoría", "marco", "evidencia",
    "autoridad", "datos", "investigación", "fuente"
}

CONTRAST_MARKERS = {
    "pero", "sin embargo", "no obstante", "aunque", "mientras que", "aun así",
    "por el contrario", "ignora", "falla", "debil", "débil", "insuficiente", "incorrecto"
}

SPANISH_STOPWORDS = {
    "de", "la", "el", "los", "las", "un", "una", "unos", "unas", "y", "o", "u",
    "a", "ante", "bajo", "con", "contra", "desde", "durante", "en", "entre", "hacia",
    "hasta", "para", "por", "segun", "según", "sin", "sobre", "tras", "que", "como",
    "es", "son", "ser", "se", "su", "sus", "al", "del", "lo", "le", "les", "ya"
}


class ToulminScorer:
    def __init__(
        self,
        model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        weights: ScoreWeights | None = None,
    ) -> None:
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.weights = weights or ScoreWeights()

    @staticmethod
    def _safe_text(text: Any) -> str:
        if text is None:
            return ""
        return str(text).strip()

    @staticmethod
    def _normalize(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
        if max_value == min_value:
            return 0.0
        value = (value - min_value) / (max_value - min_value)
        return max(0.0, min(1.0, value))

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(r"\b\w+\b", text.lower(), flags=re.UNICODE)

    def _content_tokens(self, text: str) -> list[str]:
        return [t for t in self._tokenize(text) if t not in SPANISH_STOPWORDS and len(t) > 2]

    @staticmethod
    def _contains_any(text: str, markers: set[str]) -> float:
        text_low = text.lower()
        return 1.0 if any(marker in text_low for marker in markers) else 0.0

    @staticmethod
    def _count_any(text: str, markers: set[str]) -> int:
        text_low = text.lower()
        return sum(1 for marker in markers if marker in text_low)

    @lru_cache(maxsize=2048)
    def _embedding(self, text: str):
        text = self._safe_text(text)
        if not text:
            return np.zeros(384, dtype=np.float32)
        emb = self.model.encode(text, normalize_embeddings=True)
        return np.asarray(emb, dtype=np.float32)

    def cosine_similarity(self, text_a: str, text_b: str) -> float:
        a = self._embedding(self._safe_text(text_a))
        b = self._embedding(self._safe_text(text_b))
        if not a.any() or not b.any():
            return 0.0
        score = float(np.dot(a, b))
        return max(0.0, min(1.0, (score + 1.0) / 2.0))

    def _length_score(self, text: str, optimal_min: int = 12, optimal_max: int = 80) -> float:
        words = len(self._tokenize(text))
        if words == 0:
            return 0.0
        if optimal_min <= words <= optimal_max:
            return 1.0
        if words < optimal_min:
            return self._normalize(words, 0, optimal_min)
        overflow = min(words, optimal_max * 2)
        return 1.0 - self._normalize(overflow, optimal_max, optimal_max * 2) * 0.5

    def _lexical_diversity(self, text: str) -> float:
        tokens = self._content_tokens(text)
        if not tokens:
            return 0.0
        return len(set(tokens)) / len(tokens)

    def _specificity_score(self, text: str) -> float:
        tokens = self._tokenize(text)
        if not tokens:
            return 0.0
        num_count = len(re.findall(r"\b\d+(?:[\.,]\d+)?%?\b", text))
        proper_like = len(re.findall(r"\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\b", text))
        support_count = self._count_any(text, SUPPORT_MARKERS)
        raw = min(6, num_count + proper_like + support_count)
        return self._normalize(raw, 0, 6)

    def _evidence_units(self, text: str) -> float:
        if not text:
            return 0.0
        splitters = re.split(r"[\.;:]| además | asimismo | por ejemplo | según | también ", text.lower())
        units = len([s for s in splitters if s.strip()])
        return self._normalize(min(units, 6), 1, 6)

    def score_claim(self, argument: ToulminArgument, topic: str) -> dict[str, float]:
        claim = self._safe_text(argument.claim)
        speech = self._safe_text(argument.speech)
        stance_presence = self._contains_any(claim, STANCE_MARKERS)
        length = self._length_score(claim, 8, 35)
        sim_topic = self.cosine_similarity(claim, topic)
        sim_speech = self.cosine_similarity(claim, speech)
        score = 0.25 * length + 0.20 * stance_presence + 0.25 * sim_topic + 0.30 * sim_speech
        return {
            "score": round(score, 4),
            "length": round(length, 4),
            "stance_presence": round(stance_presence, 4),
            "sim_topic": round(sim_topic, 4),
            "sim_speech": round(sim_speech, 4),
        }

    def score_data_relevance(self, argument: ToulminArgument, topic: str) -> dict[str, float]:
        data = self._safe_text(argument.data)
        claim = self._safe_text(argument.claim)
        sim_claim = self.cosine_similarity(data, claim)
        sim_topic = self.cosine_similarity(data, topic)
        info = (self._specificity_score(data) + self._contains_any(data, SUPPORT_MARKERS)) / 2
        score = 0.50 * sim_claim + 0.25 * sim_topic + 0.25 * info
        return {
            "score": round(score, 4),
            "sim_claim": round(sim_claim, 4),
            "sim_topic": round(sim_topic, 4),
            "info": round(info, 4),
        }

    def score_data_sufficiency(self, argument: ToulminArgument) -> dict[str, float]:
        data = self._safe_text(argument.data)
        claim = self._safe_text(argument.claim)
        length = self._length_score(data, 20, 120)
        evidence_units = self._evidence_units(data)
        diversity = self._lexical_diversity(data)
        coverage = self.cosine_similarity(data, claim)
        score = 0.30 * length + 0.25 * evidence_units + 0.20 * diversity + 0.25 * coverage
        return {
            "score": round(score, 4),
            "length": round(length, 4),
            "evidence_units": round(evidence_units, 4),
            "diversity": round(diversity, 4),
            "coverage": round(coverage, 4),
        }

    def score_warrant(self, argument: ToulminArgument) -> dict[str, float]:
        warrant = self._safe_text(argument.warrant)
        claim = self._safe_text(argument.claim)
        data = self._safe_text(argument.data)
        sim_claim = self.cosine_similarity(warrant, claim)
        sim_data = self.cosine_similarity(warrant, data)
        inferential = self._contains_any(warrant, INFERENTIAL_MARKERS)

        redundancy = (sim_claim + sim_data) / 2
        if redundancy > 0.85:
            non_redundancy = max(0.0, 1.0 - (redundancy - 0.85) / 0.15)
        else:
            non_redundancy = 1.0

        score = 0.35 * sim_claim + 0.35 * sim_data + 0.20 * inferential + 0.10 * non_redundancy
        return {
            "score": round(score, 4),
            "sim_claim": round(sim_claim, 4),
            "sim_data": round(sim_data, 4),
            "inferential": round(inferential, 4),
            "non_redundancy": round(non_redundancy, 4),
        }

    def score_backing(self, argument: ToulminArgument) -> dict[str, float]:
        backing = self._safe_text(argument.backing)
        warrant = self._safe_text(argument.warrant)
        data = self._safe_text(argument.data)
        sim_warrant = self.cosine_similarity(backing, warrant)
        sim_data = self.cosine_similarity(backing, data)
        support_markers = self._contains_any(backing, SUPPORT_MARKERS)
        length = self._length_score(backing, 10, 80)
        distinctiveness = max(0.0, min(1.0, sim_warrant - max(0.0, sim_data - 0.1) + 0.3))
        score = 0.40 * sim_warrant + 0.20 * support_markers + 0.20 * length + 0.20 * distinctiveness
        return {
            "score": round(score, 4),
            "sim_warrant": round(sim_warrant, 4),
            "sim_data": round(sim_data, 4),
            "support_markers": round(support_markers, 4),
            "length": round(length, 4),
            "distinctiveness": round(distinctiveness, 4),
        }

    def score_rebuttal(
        self,
        argument: ToulminArgument,
        rival_argument: ToulminArgument | None = None
    ) -> dict[str, float]:
        rebuttal = self._safe_text(argument.rebuttal)

        if rival_argument is None:
            base = self._length_score(rebuttal, 8, 60)
            return {
                "score": round(base, 4),
                "sim_rival_claim": 0.0,
                "sim_rival_data": 0.0,
                "contrast_markers": round(self._contains_any(rebuttal, CONTRAST_MARKERS), 4),
                "specificity": round(self._specificity_score(rebuttal), 4),
            }

        rival_claim = self._safe_text(rival_argument.claim)
        rival_data = self._safe_text(rival_argument.data)
        sim_rival_claim = self.cosine_similarity(rebuttal, rival_claim)
        sim_rival_data = self.cosine_similarity(rebuttal, rival_data)
        contrast_markers = self._contains_any(rebuttal, CONTRAST_MARKERS)
        specificity = self._specificity_score(rebuttal)

        score = (
            0.35 * sim_rival_claim
            + 0.25 * sim_rival_data
            + 0.20 * contrast_markers
            + 0.20 * specificity
        )

        return {
            "score": round(score, 4),
            "sim_rival_claim": round(sim_rival_claim, 4),
            "sim_rival_data": round(sim_rival_data, 4),
            "contrast_markers": round(contrast_markers, 4),
            "specificity": round(specificity, 4),
        }

    def score_argument(
        self,
        argument: ToulminArgument,
        topic: str,
        rival_argument: ToulminArgument | None = None,
    ) -> dict[str, Any]:
        claim = self.score_claim(argument, topic)
        data_rel = self.score_data_relevance(argument, topic)
        data_suf = self.score_data_sufficiency(argument)
        warrant = self.score_warrant(argument)
        backing = self.score_backing(argument)
        rebuttal = self.score_rebuttal(argument, rival_argument)

        final_score = (
            self.weights.claim_quality * claim["score"]
            + self.weights.data_relevance * data_rel["score"]
            + self.weights.data_sufficiency * data_suf["score"]
            + self.weights.warrant_strength * warrant["score"]
            + self.weights.backing_adequacy * backing["score"]
            + self.weights.rebuttal_effectiveness * rebuttal["score"]
        )

        return {
            "claim_quality": claim,
            "data_relevance": data_rel,
            "data_sufficiency": data_suf,
            "warrant_strength": warrant,
            "backing_adequacy": backing,
            "rebuttal_effectiveness": rebuttal,
            "argument_score": round(final_score, 4),
            "argument_score_100": round(final_score * 100, 2),
        }

    def score_round(self, debate_round: DebateRound, topic: str) -> dict[str, Any]:
        pro_score = self.score_argument(
            debate_round.pro_argument,
            topic=topic,
            rival_argument=debate_round.contra_argument,
        )
        contra_score = self.score_argument(
            debate_round.contra_argument,
            topic=topic,
            rival_argument=debate_round.pro_argument,
        )
        round_average = (pro_score["argument_score"] + contra_score["argument_score"]) / 2

        return {
            "round_number": debate_round.round_number,
            "pro": pro_score,
            "contra": contra_score,
            "round_average": round(round_average, 4),
            "round_average_100": round(round_average * 100, 2),
        }

    def _side_coherence(self, arguments: list[ToulminArgument]) -> dict[str, float]:
        if len(arguments) < 2:
            return {
                "claim_consistency": 1.0,
                "speech_consistency": 1.0,
                "progressive_development": 0.5,
                "score": 0.85,
            }

        claim_sims = []
        speech_sims = []
        progress_scores = []

        for prev, curr in zip(arguments[:-1], arguments[1:]):
            claim_sim = self.cosine_similarity(prev.claim, curr.claim)
            speech_sim = self.cosine_similarity(prev.speech, curr.speech)

            claim_sims.append(claim_sim)
            speech_sims.append(speech_sim)

            if 0.45 <= speech_sim <= 0.85:
                progress = 1.0
            elif speech_sim < 0.45:
                progress = max(0.0, speech_sim / 0.45)
            else:
                progress = max(0.0, 1.0 - (speech_sim - 0.85) / 0.15)

            progress_scores.append(progress)

        claim_consistency = sum(claim_sims) / len(claim_sims)
        speech_consistency = sum(speech_sims) / len(speech_sims)
        progressive_development = sum(progress_scores) / len(progress_scores)

        score = (
            0.40 * claim_consistency
            + 0.30 * speech_consistency
            + 0.30 * progressive_development
        )

        return {
            "claim_consistency": round(claim_consistency, 4),
            "speech_consistency": round(speech_consistency, 4),
            "progressive_development": round(progressive_development, 4),
            "score": round(score, 4),
        }

    def score_global_coherence(self, debate: DebateState) -> dict[str, Any]:
        pro_arguments = [r.pro_argument for r in debate.rounds]
        contra_arguments = [r.contra_argument for r in debate.rounds]

        pro = self._side_coherence(pro_arguments)
        contra = self._side_coherence(contra_arguments)
        overall = (pro["score"] + contra["score"]) / 2

        return {
            "pro_coherence": pro,
            "contra_coherence": contra,
            "global_coherence_score": round(overall, 4),
            "global_coherence_score_100": round(overall * 100, 2),
        }

    def score_debate(self, debate: DebateState) -> dict[str, Any]:
        round_scores = [self.score_round(r, debate.topic) for r in debate.rounds]

        arg_scores = []
        for rs in round_scores:
            arg_scores.append(rs["pro"]["argument_score"])
            arg_scores.append(rs["contra"]["argument_score"])

        average_argument_score = sum(arg_scores) / len(arg_scores) if arg_scores else 0.0
        coherence = self.score_global_coherence(debate)
        final_score = 0.85 * average_argument_score + 0.15 * coherence["global_coherence_score"]

        return {
            "topic": debate.topic,
            "rounds": round_scores,
            "average_argument_score": round(average_argument_score, 4),
            "average_argument_score_100": round(average_argument_score * 100, 2),
            "global_coherence": coherence,
            "debate_score": round(final_score, 4),
            "debate_score_100": round(final_score * 100, 2),
        }