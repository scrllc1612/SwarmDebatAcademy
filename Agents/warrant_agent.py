# Agents/warrant_agent.py

from Utils.llm_client import LLMClient


class WarrantAgent:
    """
    Agente especializado en generar el WARRANT
    (justificación lógica) de un argumento.
    """

    def __init__(self):
        self.llm = LLMClient()

    def generate(
        self,
        topic: str,
        claim: str,
        data: str,
        stance: str
    ) -> str:

        if stance not in ["pro", "contra"]:
            raise ValueError(
                "La postura debe ser 'pro' o 'contra'."
            )

        system_prompt = """
Genera únicamente la regla o principio lógico general
que conecta la evidencia con la tesis.

No repitas cifras.
No repitas fuentes.
No repitas el claim.
No concluyas.
No uses expresiones como:
"por lo tanto"
"en consecuencia"
"esto demuestra"

El warrant debe ser una premisa general.
"""

        user_prompt = f"""
Tema:
{topic}

Postura:
{stance}

Claim:
{claim}

Data:
{data}

Genera únicamente el WARRANT.
"""

        return self.llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.5
        )