from pathlib import Path
from openai import OpenAI
import pygame
import time
import os
from google.cloud import texttospeech

# def text_to_speech(text):
    
#     client = OpenAI()

#     speech_file_path = Path(__file__).parent / "speech2.mp3"
#     os.remove(speech_file_path)

#     with client.audio.speech.with_streaming_response.create(
#         model="tts-1",
#         voice="nova",
#         input=text,
#     ) as response:
#         response.stream_to_file(speech_file_path)

#     pygame.mixer.init()
#     pygame.mixer.music.load(speech_file_path)
#     pygame.mixer.music.play()

#     # Keep the program running long enough for the audio to play
#     while pygame.mixer.music.get_busy():
#         time.sleep(1)

#     pygame.mixer.quit()
def text_to_speech(text):
    client = texttospeech.TextToSpeechClient()
    input_text = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    response = client.synthesize_speech(
        input=input_text, voice=voice, audio_config=audio_config
    )

    with open("speech2.mp3", "wb") as out:
        out.write(response.audio_content)