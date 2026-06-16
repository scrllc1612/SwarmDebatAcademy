# Utils/llm_client.py

from openai import OpenAI

from config import OPENAI_API_KEY


class LLMClient:
    """
    Cliente centralizado para interactuar con GPT.

    Todos los agentes del sistema utilizarán esta clase
    para generar contenido.
    """

    def __init__(self):

        if not OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY no encontrada en las variables de entorno."
            )

        self.client = OpenAI(
            api_key=OPENAI_API_KEY
        )

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        model: str = "gpt-4o"
    ) -> str:
        """
        Genera una respuesta simple usando un único prompt.
        """

        response = self.client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.choices[0].message.content.strip()

    def generate_with_system(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        model: str = "gpt-4o"
    ) -> str:
        """
        Genera una respuesta utilizando un prompt de sistema
        y un prompt de usuario.
        """

        response = self.client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )

        return response.choices[0].message.content.strip()