import os
import pygame
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
import elevenlabs
from gtts import gTTS

# -------------------------------
# 🔹 Load Environment Variables
# -------------------------------
load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

if not ELEVENLABS_API_KEY:
    raise ValueError("❌ ELEVENLABS_API_KEY not found! Please check your .env file.")

print("✅ ElevenLabs API key loaded successfully!")

# -------------------------------
# 🔹 Audio Playback Function
# -------------------------------
def play_audio(filepath):
    """Play audio inside Python using pygame (no external player)."""
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(filepath)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.quit()
    except Exception as e:
        print(f"❌ Audio playback failed: {e}")

# -------------------------------
# 🔹 ElevenLabs Text-to-Speech
# -------------------------------
def text_to_speech_with_elevenlabs(input_text, output_filepath):
    """Convert text to speech using ElevenLabs API"""
    try:
        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        audio = client.text_to_speech.convert(
            text=input_text,
            voice_id="ZF6FPAbjXT4488VcRRnw",  # Fixed Dora Voice ID
            model_id="eleven_multilingual_v2",
            output_format="mp3_22050_32",
            voice_settings={
                "stability": 1.0,          # Keep tone consistent
                "similarity_boost": 1.0,   # Keep same voice every time
            },
        )

        elevenlabs.save(audio, output_filepath)
        print(f"✅ Audio saved to {output_filepath}")

        # 🔊 Play the file directly inside Python
        play_audio(output_filepath)

    except Exception as e:
        print(f"❌ ElevenLabs TTS failed: {e}")
        print("➡️ Switching to Google TTS fallback...")
        text_to_speech_with_gtts(input_text, output_filepath)

# -------------------------------
# 🔹 Google Text-to-Speech Fallback
# -------------------------------
def text_to_speech_with_gtts(input_text, output_filepath):
    """Fallback TTS using Google Text-to-Speech"""
    try:
        tts = gTTS(text=input_text, lang="en", slow=False)
        tts.save(output_filepath)
        print(f"✅ Audio saved with gTTS to {output_filepath}")

        # 🔊 Play the generated file
        play_audio(output_filepath)

    except Exception as e:
        print(f"❌ gTTS failed: {e}")

# -------------------------------
# 🔹 Example Usage
# -------------------------------
if __name__ == "__main__":
    input_text = "Hi, I am Dora AI speaking from ElevenLabs. How are you, Ankit?"
    output_filepath = "test_text_to_speech.mp3"
    #text_to_speech_with_elevenlabs(input_text, output_filepath)
    text_to_speech_with_gtts(input_text, output_filepath)
