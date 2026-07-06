from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv

from Avatar.simli_service import SimliService
from Avatar.tts_service import TTSService

load_dotenv()

PRO_AVATAR_ID = os.getenv("PRO_AVATAR_ID")
CONTRA_AVATAR_ID = os.getenv("CONTRA_AVATAR_ID")

PRO_TTS_VOICE = os.getenv("PRO_TTS_VOICE")
CONTRA_TTS_VOICE = os.getenv("CONTRA_TTS_VOICE")


class VideoManager:
    """
    Gestiona la generación de videos utilizando:

        Texto
            ↓
        OpenAI TTS
            ↓
        Simli
            ↓
        HLS / MP4
    """

    def __init__(self) -> None:

        self.tts = TTSService()
        self.simli = SimliService()

    def generate_pro_video(
        self,
        text: str,
    ) -> dict[str, Any]:

        print("\n======================================")
        print("GENERANDO VIDEO DEL PROPONENTE")
        print("======================================")

        audio = self.tts.text_to_speech(
            text=text,
            voice=PRO_TTS_VOICE,
        )

        video = self.simli.generate_video(
            face_id=PRO_AVATAR_ID,
            audio_bytes=audio,
        )

        return {
            "video": video["mp4_url"],
            "hls": video["hls_url"],
            "eta": video["eta"],
        }

    def generate_contra_video(
        self,
        text: str,
    ) -> dict[str, Any]:

        print("\n======================================")
        print("GENERANDO VIDEO DEL OPONENTE")
        print("======================================")

        audio = self.tts.text_to_speech(
            text=text,
            voice=CONTRA_TTS_VOICE,
        )

        video = self.simli.generate_video(
            face_id=CONTRA_AVATAR_ID,
            audio_bytes=audio,
        )

        return {
            "video": video["mp4_url"],
            "hls": video["hls_url"],
            "eta": video["eta"],
        }