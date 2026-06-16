from Agents.claim_agent import ClaimAgent
from Agents.data_agent import DataAgent
from Agents.warrant_agent import WarrantAgent
from Agents.backing_agent import BackingAgent
from Agents.rebuttal_agent import RebuttalAgent

from Models.toulmin_models import ToulminArgument
from Models.moderator_models import DebateSummary
from Utils.llm_client import LLMClient


class OpponentAgent:
    """
    Equipo argumentativo CONTRA.

    Coordina los agentes Toulmin y puede
    considerar argumentos rivales y resúmenes
    del moderador en rondas posteriores.
    """

    def __init__(self):

        self.claim_agent = ClaimAgent()
        self.data_agent = DataAgent()
        self.warrant_agent = WarrantAgent()
        self.backing_agent = BackingAgent()
        self.rebuttal_agent = RebuttalAgent()
        self.llm = LLMClient()

    def _compose_speech(
        self,
        topic: str,
        round_number: int,
        claim: str,
        data: str,
        warrant: str,
        backing: str,
        rebuttal: str,
        rival_argument: ToulminArgument | None = None
    ) -> str:

        rival_context = "No hay intervencion rival previa en esta ronda."

        if rival_argument:
            rival_context = f"""
Claim rival:
{rival_argument.claim}

Data rival:
{rival_argument.data}

Rebuttal rival:
{rival_argument.rebuttal}
"""

        system_prompt = """
Eres un debatiente de la postura CONTRA.

Convierte los componentes Toulmin en una intervencion oral natural.

Reglas:
- Suena como una persona debatiendo, no como una ficha tecnica.
- Responde directamente al rival cuando exista.
- Usa conectores de debate: "ese punto falla porque", "sin embargo",
  "lo central aqui es".
- Integra claim, evidencia, warrant, backing y rebuttal sin nombrar esas etiquetas.
- No inventes datos nuevos.
- No uses markdown.
- Escribe un unico parrafo de 5 a 8 oraciones.
"""

        user_prompt = f"""
Tema:
{topic}

Ronda:
{round_number}

Argumento CONTRA

Claim:
{claim}

Data:
{data}

Warrant:
{warrant}

Backing:
{backing}

Rebuttal:
{rebuttal}

Intervencion rival:
{rival_context}

Genera la intervencion oral CONTRA.
"""

        return self.llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.75
        )

    def generate(
        self,
        topic: str,
        round_number: int = 1,
        rival_argument: ToulminArgument | None = None,
        debate_summary: DebateSummary | None = None
    ) -> ToulminArgument:

        stance = "contra"

        debate_context = ""

        # -----------------------------
        # CONTEXTO DEL RIVAL
        # -----------------------------

        if rival_argument:

            debate_context += f"""
ARGUMENTO RIVAL

CLAIM:
{rival_argument.claim}

DATA:
{rival_argument.data}

WARRANT:
{rival_argument.warrant}

REBUTTAL:
{rival_argument.rebuttal}

INSTRUCCIONES:

- No generes un argumento desde cero.
- Debes responder directamente al argumento rival.
- Debes cuestionar o refutar su idea principal.
- Debes fortalecer la postura CONTRA.
"""

        # -----------------------------
        # CONTEXTO DEL MODERADOR
        # -----------------------------

        if debate_summary:

            debate_context += f"""

RESUMEN DEL MODERADOR

PUNTO PRINCIPAL PRO:
{debate_summary.pro_main_point}

PUNTO PRINCIPAL CONTRA:
{debate_summary.contra_main_point}

CONFLICTO PRINCIPAL:
{debate_summary.main_conflict}

ASPECTO NO RESUELTO:
{debate_summary.unresolved_issue}

INSTRUCCIONES:

- Debes abordar el conflicto principal.
- Debes intentar responder el aspecto no resuelto.
- Tu argumento debe mostrar evolución respecto
  a la ronda anterior.
"""

        # -----------------------------
        # CLAIM
        # -----------------------------

        claim = self.claim_agent.generate(
            topic=topic,
            stance=stance,
            context=debate_context
        )

        # -----------------------------
        # DATA
        # -----------------------------

        data = self.data_agent.generate(
            topic=topic,
            claim=claim,
            stance=stance
        )

        # -----------------------------
        # WARRANT
        # -----------------------------

        warrant = self.warrant_agent.generate(
            topic=topic,
            claim=claim,
            data=data,
            stance=stance
        )

        # -----------------------------
        # BACKING
        # -----------------------------

        backing = self.backing_agent.generate(
            topic=topic,
            claim=claim,
            data=data,
            warrant=warrant,
            stance=stance
        )

        # -----------------------------
        # REBUTTAL
        # -----------------------------

        rebuttal = self.rebuttal_agent.generate(
            topic=topic,
            claim=claim,
            data=data,
            warrant=warrant,
            backing=backing,
            stance=stance,
            rival_argument=rival_argument
        )

        speech = self._compose_speech(
            topic=topic,
            round_number=round_number,
            claim=claim,
            data=data,
            warrant=warrant,
            backing=backing,
            rebuttal=rebuttal,
            rival_argument=rival_argument
        )

        return ToulminArgument(
            claim=claim,
            data=data,
            warrant=warrant,
            backing=backing,
            rebuttal=rebuttal,
            speech=speech,
            stance=stance,
            round_number=round_number
        )
