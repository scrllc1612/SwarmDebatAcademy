from Utils.llm_client import LLMClient


class ClaimAgent:

    def __init__(self):
        self.llm = LLMClient()

    def generate(
        self,
        topic: str,
        stance: str,
        context: str = ""
    ) -> str:

        system_prompt = """
Eres un experto en argumentación basado en el modelo de Toulmin.

Tu tarea es generar el CLAIM (tesis principal).

Reglas:

- Genera una única tesis clara.
- Mantén coherencia con la postura asignada.
- Si existe contexto de debate, debes responder
  explícitamente a las ideas rivales.
- No repitas simplemente la tesis de rondas anteriores.
- La tesis debe evolucionar el debate.
- No agregues evidencia.
- No agregues estadísticas.
- Responde únicamente con el claim.
"""

        user_prompt = f"""
Tema:
{topic}

Postura:
{stance}

Contexto del debate:
{context}

IMPORTANTE:

Si el contexto contiene argumentos rivales
o un resumen del moderador:

- Responde a la postura rival.
- Aborda el conflicto principal.
- Intenta resolver el aspecto no resuelto.
- Fortalece tu postura frente al rival.

Genera únicamente el Claim.
"""

        return self.llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7
        )