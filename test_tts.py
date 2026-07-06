from Avatar.tts_service import TTSService

tts = TTSService()

audio = tts.text_to_speech(
    text="Hola. Este es un audio de prueba para Simli.",
    voice="ash",   # o la voz que tengas en el .env
)

print(type(audio))
print(len(audio))