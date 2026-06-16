from datetime import datetime


class DebateExporter:

    @staticmethod
    def export(
        debate,
        metrics,
        system: str = "swarm",
        model_name: str = "gpt-4o-mini",
        version: str = "1.0"
    ) -> dict:

        rounds = []

        for round_obj in debate.rounds:

            rounds.append(
                {
                    "round_number":
                        round_obj.round_number,

                    "pro_argument": {
                        "stance":
                            round_obj.pro_argument.stance,

                        "round_number":
                            round_obj.pro_argument.round_number,

                        "claim":
                            round_obj.pro_argument.claim,

                        "data":
                            round_obj.pro_argument.data,

                        "warrant":
                            round_obj.pro_argument.warrant,

                        "backing":
                            round_obj.pro_argument.backing,

                        "rebuttal":
                            round_obj.pro_argument.rebuttal,

                        "speech":
                            round_obj.pro_argument.speech
                    },

                    "contra_argument": {
                        "stance":
                            round_obj.contra_argument.stance,

                        "round_number":
                            round_obj.contra_argument.round_number,

                        "claim":
                            round_obj.contra_argument.claim,

                        "data":
                            round_obj.contra_argument.data,

                        "warrant":
                            round_obj.contra_argument.warrant,

                        "backing":
                            round_obj.contra_argument.backing,

                        "rebuttal":
                            round_obj.contra_argument.rebuttal,

                        "speech":
                            round_obj.contra_argument.speech
                    },

                    "moderator_summary":
                        round_obj.moderator_summary.model_dump()
                }
            )

        # =====================================
        # MÉTRICAS POR RONDA
        # =====================================

        round_metrics = []

        for round_result in metrics["rounds"]:

            round_metrics.append(

                {
                    "round_number":
                        round_result["round_number"],

                    "pro": {

                        "argument_score_100":
                            round_result["pro"][
                                "argument_score_100"
                            ],

                        "claim_quality":
                            round_result["pro"][
                                "claim_quality"
                            ]["score"] * 100,

                        "data_relevance":
                            round_result["pro"][
                                "data_relevance"
                            ]["score"] * 100,

                        "warrant_strength":
                            round_result["pro"][
                                "warrant_strength"
                            ]["score"] * 100,

                        "backing_adequacy":
                            round_result["pro"][
                                "backing_adequacy"
                            ]["score"] * 100,

                        "rebuttal_effectiveness":
                            round_result["pro"][
                                "rebuttal_effectiveness"
                            ]["score"] * 100
                    },

                    "contra": {

                        "argument_score_100":
                            round_result["contra"][
                                "argument_score_100"
                            ],

                        "claim_quality":
                            round_result["contra"][
                                "claim_quality"
                            ]["score"] * 100,

                        "data_relevance":
                            round_result["contra"][
                                "data_relevance"
                            ]["score"] * 100,

                        "warrant_strength":
                            round_result["contra"][
                                "warrant_strength"
                            ]["score"] * 100,

                        "backing_adequacy":
                            round_result["contra"][
                                "backing_adequacy"
                            ]["score"] * 100,

                        "rebuttal_effectiveness":
                            round_result["contra"][
                                "rebuttal_effectiveness"
                            ]["score"] * 100
                    }
                }
            )

        # =====================================
        # EXPORTACIÓN FINAL
        # =====================================

        return {

            "metadata": {

                "debate_id":
                    debate.debate_id,

                "system":
                    system,

                "version":
                    version,

                "model_name":
                    model_name,

                "topic":
                    debate.topic,

                "created_at":
                    datetime.now().isoformat(),

                "total_rounds":
                    len(debate.rounds),

                "is_finished":
                    debate.is_finished
            },

            "rounds":
                rounds,

            "round_metrics":
                round_metrics,

            "evaluation":
                {

                    "evaluator_version":
                        "1.0",

                    "tqs":
                        metrics[
                            "average_argument_score_100"
                        ],

                    "sc":
                        metrics[
                            "global_coherence"
                        ][
                            "global_coherence_score_100"
                        ],

                    "debate_score":
                        metrics[
                            "debate_score_100"
                        ]
                }
        }