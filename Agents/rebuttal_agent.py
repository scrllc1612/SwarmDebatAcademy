# Agents/rebuttal_agent.py

from Models.toulmin_models import ToulminArgument
from Utils.llm_client import LLMClient


class RebuttalAgent:
    """
    Agente especializado en generar una
    refutación directa al argumento rival.
    """

    def __init__(self):
        self.llm = LLMClient()

    def generate(
        self,
        topic: str,
        claim: str,
        data: str,
        warrant: str,
        backing: str,
        stance: str,
        rival_argument: ToulminArgument | None = None
    ) -> str:

        if stance not in ["pro", "contra"]:
            raise ValueError(
                "La postura debe ser 'pro' o 'contra'."
            )

        # ----------------------------------
        # RONDA 1
        # ----------------------------------

        if rival_argument is None:

            return (
                "No existe un argumento rival previo "
                "que requiera refutación."
            )

        # ----------------------------------
        # RONDAS 2+
        # ----------------------------------

        system_prompt = """
Eres un experto en argumentación y debate.

Tu tarea es generar una REFUTACIÓN DIRECTA
al argumento rival.

Debes:

1. Identificar la idea principal del rival.
2. Cuestionar o debilitar esa idea.
3. Defender la postura actual.
4. Mantener coherencia con el argumento actual.

Reglas:

- No inventes objeciones hipotéticas.
- No repitas literalmente el Claim.
- No repitas literalmente el Data.
- No generes una conclusión final.
- Responde al rival real.
- Devuelve un único párrafo.
"""

        user_prompt = f"""
Tema:
{topic}

POSTURA ACTUAL:
{stance}

ARGUMENTO ACTUAL

Claim:
{claim}

Data:
{data}

Warrant:
{warrant}

Backing:
{backing}

ARGUMENTO RIVAL

Claim:
{rival_argument.claim}

Data:
{rival_argument.data}

Warrant:
{rival_argument.warrant}

Rebuttal:
{rival_argument.rebuttal}

Genera únicamente la refutación.
"""

        return self.llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.6
        )