from __future__ import annotations

import base64
import os
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()


class SimliService:
    """
    Servicio encargado de generar videos utilizando Simli.

    Entrada:
        - face_id
        - audio MP3 (bytes)

    Salida:
        {
            "mp4_url": "...",
            "hls_url": "...",
            "eta": 5.2
        }
    """

    def __init__(self) -> None:

        self.api_key = os.getenv("SIMLI_API_KEY")

        if not self.api_key:
            raise ValueError("SIMLI_API_KEY no encontrada en el archivo .env")

        self.base_url = "https://api.simli.ai"

        self.headers = {
            "x-simli-api-key": self.api_key,
            "Content-Type": "application/json",
        }

    def generate_video(
        self,
        face_id: str,
        audio_bytes: bytes,
    ) -> dict[str, Any]:

        print("\n==============================")
        print("GENERANDO VIDEO SIMLI")
        print("==============================")
        print("Face ID :", face_id)
        print("Audio   :", len(audio_bytes), "bytes")

        audio_base64 = base64.b64encode(
            audio_bytes
        ).decode("utf-8")

        payload = {
            "faceId": face_id,
            "audioBase64": audio_base64,
            "audioFormat": "mp3",
        }

        print("\n=========== REQUEST ===========")
        print(payload.keys())
        print("===============================")

        response = requests.post(
            f"{self.base_url}/static/audio",
            headers=self.headers,
            json=payload,
            timeout=300,
        )

        print("\n=========== RESPONSE ===========")
        print("Status:", response.status_code)
        print(response.text)
        print("================================")

        response.raise_for_status()

        data = response.json()

        mp4_url = data.get("mp4_url")
        hls_url = data.get("hls_url")
        eta = data.get(
            "mp4_availablility_eta_seconds",
            0,
        )

        if not mp4_url:
            raise RuntimeError(
                f"Simli no devolvió mp4_url.\n\n{data}"
            )

        print("\n==============================")
        print("VIDEO GENERADO")
        print("==============================")
        print("MP4 :", mp4_url)
        print("HLS :", hls_url)
        print("ETA :", eta)

        return {
            "mp4_url": mp4_url,
            "hls_url": hls_url,
            "eta": eta,
        }