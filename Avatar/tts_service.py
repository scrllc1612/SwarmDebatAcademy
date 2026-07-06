from __future__ import annotations

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class TTSService:
    """
    Convierte texto a voz usando OpenAI TTS.
    Devuelve los bytes del audio MP3.
    """

    def __init__(self) -> None:

        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError("OPENAI_API_KEY no encontrada.")

        self.client = OpenAI(api_key=api_key)

    def text_to_speech(
        self,
        text: str,
        voice: str,
    ) -> bytes:

        print("\n==============================")
        print("OPENAI TTS")
        print("==============================")
        print("Voice:", voice)
        print("Texto:", text[:120], "...")

        response = self.client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice=voice,
            input=text,
            response_format="mp3",
        )
        print(type(response))

        audio_bytes = response.read()

        print(f"Audio generado: {len(audio_bytes)} bytes")

        return audio_bytes