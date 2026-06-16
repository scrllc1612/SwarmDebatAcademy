import json

from Utils.llm_client import LLMClient
from Models.moderator_models import DebateSummary
from Models.toulmin_models import ToulminArgument


class ModeratorAgent:

    def __init__(self):

        self.llm = LLMClient()

    def summarize(
        self,
        topic: str,
        pro_argument: ToulminArgument,
        contra_argument: ToulminArgument
    ) -> DebateSummary:

        system_prompt = """
Eres un moderador de debates.

Responde únicamente con JSON válido.

No utilices markdown.
No utilices ```json.
No agregues explicaciones.

Formato:

{
  "pro_main_point": "...",
  "contra_main_point": "...",
  "main_conflict": "...",
  "unresolved_issue": "..."
}
"""

        user_prompt = f"""
Tema:
{topic}

POSTURA PRO:
Intervencion:
{pro_argument.speech}

Claim:
{pro_argument.claim}

Data:
{pro_argument.data}

Warrant:
{pro_argument.warrant}

Backing:
{pro_argument.backing}

Rebuttal:
{pro_argument.rebuttal}

POSTURA CONTRA:
Intervencion:
{contra_argument.speech}

Claim:
{contra_argument.claim}

Data:
{contra_argument.data}

Warrant:
{contra_argument.warrant}

Backing:
{contra_argument.backing}

Rebuttal:
{contra_argument.rebuttal}
"""

        response = self.llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3
        )

        data = json.loads(response)

        return DebateSummary(
            pro_main_point=data["pro_main_point"],
            contra_main_point=data["contra_main_point"],
            main_conflict=data["main_conflict"],
            unresolved_issue=data["unresolved_issue"]
        )
