import os

from dotenv import load_dotenv

from Avatar.tts_service import TTSService
from Avatar.simli_service import SimliService

load_dotenv()

tts = TTSService()
simli = SimliService()

audio = tts.text_to_speech(
    text="Hola. Esta es una prueba del avatar utilizando Simli.",
    voice=os.getenv("PRO_TTS_VOICE"),
)

video_url = simli.generate_video(
    face_id=os.getenv("PRO_AVATAR_ID"),
    audio_bytes=audio,
)

print("\n======================")
print("VIDEO GENERADO")
print("======================")
print(video_url)