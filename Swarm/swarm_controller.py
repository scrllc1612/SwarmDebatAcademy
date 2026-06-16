from Models.toulmin_models import DebateState

from Swarm.round_manager import RoundManager


class SwarmController:
    """
    Controlador principal del sistema Swarm.

    Responsable de generar un debate completo
    compuesto por múltiples rondas.
    """

    def __init__(self):

        self.round_manager = RoundManager()

    def generate_debate(
        self,
        topic: str,
        total_rounds: int = 3
    ) -> DebateState:

        debate = DebateState(
            topic=topic
        )

        previous_round = None

        for round_number in range(1, total_rounds + 1):

            debate_round = self.round_manager.generate_round(
                topic=topic,
                round_number=round_number,
                previous_round=previous_round
            )

            debate.rounds.append(debate_round)

            previous_round = debate_round

            debate.current_round = round_number

        debate.is_finished = True

        return debate