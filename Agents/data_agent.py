# Agents/data_agent.py

from Utils.llm_client import LLMClient


class DataAgent:
    """
    Agente especializado en generar la evidencia
    (Data) que respalda un Claim.
    """

    def __init__(self):
        self.llm = LLMClient()

    def generate(
        self,
        topic: str,
        claim: str,
        stance: str
    ) -> str:

        if stance not in ["pro", "contra"]:
            raise ValueError(
                "La postura debe ser 'pro' o 'contra'."
            )

        system_prompt = """
Eres un experto en argumentación basado en el modelo de Toulmin.

Tu única tarea es generar el componente DATA.

Reglas:
- Genera evidencia que respalde el claim.
- Puedes utilizar estadísticas, ejemplos, hechos o tendencias.
- No generes el claim.
- No generes la justificación (warrant).
- No generes el respaldo (backing).
- No generes contraargumentos.
- Responde únicamente con la evidencia.
- La evidencia debe ser concreta y relevante para el claim.
"""

        user_prompt = f"""
Tema: {topic}

Postura: {stance}

Claim:
{claim}

Genera únicamente el componente Data.
"""

        return self.llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.5
        )