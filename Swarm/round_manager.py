from Agents.proponent_agent import ProponentAgent
from Agents.opponent_agent import OpponentAgent
from Agents.moderator_agent import ModeratorAgent

from Models.toulmin_models import DebateRound


class RoundManager:
    """
    Responsable de generar una ronda completa
    del debate y producir el resumen del moderador.
    """

    def __init__(self):

        self.proponent = ProponentAgent()
        self.opponent = OpponentAgent()
        self.moderator = ModeratorAgent()

    def generate_round(
        self,
        topic: str,
        round_number: int = 1,
        previous_round: DebateRound | None = None
    ) -> DebateRound:

        # ----------------------------------
        # RONDA 1
        # ----------------------------------

        if previous_round is None:

            pro_argument = self.proponent.generate(
                topic=topic,
                round_number=round_number
            )

            contra_argument = self.opponent.generate(
                topic=topic,
                round_number=round_number,
                rival_argument=pro_argument
            )

        # ----------------------------------
        # RONDAS 2+
        # ----------------------------------

        else:

            pro_argument = self.proponent.generate(
                topic=topic,
                round_number=round_number,
                rival_argument=previous_round.contra_argument,
                debate_summary=previous_round.moderator_summary
            )

            contra_argument = self.opponent.generate(
                topic=topic,
                round_number=round_number,
                rival_argument=pro_argument,
                debate_summary=previous_round.moderator_summary
            )

        # ----------------------------------
        # CREAR RONDA
        # ----------------------------------

        debate_round = DebateRound(
            round_number=round_number,
            pro_argument=pro_argument,
            contra_argument=contra_argument
        )

        # ----------------------------------
        # MODERADOR
        # ----------------------------------

        summary = self.moderator.summarize(
            topic=topic,
            pro_argument=pro_argument,
            contra_argument=contra_argument
        )

        debate_round.moderator_summary = summary

        return debate_round
