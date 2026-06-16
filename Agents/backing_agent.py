# Agents/backing_agent.py

from Utils.llm_client import LLMClient


class BackingAgent:
    """
    Agente especializado en generar el BACKING
    (respaldo del warrant) de un argumento.
    """

    def __init__(self):
        self.llm = LLMClient()

    def generate(
        self,
        topic: str,
        claim: str,
        data: str,
        warrant: str,
        stance: str
    ) -> str:

        if stance not in ["pro", "contra"]:
            raise ValueError(
                "La postura debe ser 'pro' o 'contra'."
            )

        system_prompt = """
Eres un experto en argumentación basado en el modelo de Toulmin.

Tu única tarea es generar el BACKING.

El Backing debe respaldar el WARRANT.

Reglas:

- NO repitas el Claim.
- NO repitas el Data.
- NO repitas el Warrant.
- NO generes una conclusión.
- NO generes un Rebuttal.
- NO uses frases como:
  "por lo tanto"
  "en consecuencia"
  "esto demuestra"

- El Backing debe mencionar principios,
  teorías, marcos regulatorios,
  organismos reconocidos o conocimiento experto
  que respalde la validez del Warrant.

- Responde únicamente con el Backing.
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

Warrant:
{warrant}

Genera únicamente el BACKING.
"""

        return self.llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.5
        )