import os
import time
import cv2
import gradio as gr
from dotenv import load_dotenv
import speech_recognition as sr

# === Import helper modules ===
from ai_agent import ask_agent
from text_to_speech import text_to_speech_with_elevenlabs

# === Load environment variables ===
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# === Globals ===
audio_filepath = "audio_question.mp3"
is_speaking = False  # 🚫 Prevent Dora from self-triggering

# =====================================================
# 🎤 SMART SPEECH LISTENING FUNCTION
# =====================================================
def listen_to_user():
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 500  # Raise threshold to ignore background noise
    recognizer.pause_threshold = 0.8   # Wait after you stop speaking

    with sr.Microphone() as source:
        print("🎙 Listening for your voice...")
        recognizer.adjust_for_ambient_noise(source, duration=1.5)
        try:
            audio = recognizer.listen(source, timeout=8, phrase_time_limit=10)
            text = recognizer.recognize_google(audio)
            print(f"🗣 You said: {text}")
            return text
        except sr.WaitTimeoutError:
            print("⌛ No speech detected.")
            return None
        except sr.UnknownValueError:
            print("❌ Couldn’t understand speech.")
            return None
        except Exception as e:
            print(f"❌ Speech recognition error: {e}")
            return None


# =====================================================
# 🧠 MAIN CHAT LOGIC
# =====================================================
def process_audio_and_chat():
    global is_speaking
    chat_history = []

    while True:
        try:
            if not is_speaking:
                user_input = listen_to_user()
                if not user_input:
                    continue

                if "goodbye" in user_input.lower():
                    print("👋 Goodbye detected. Ending conversation.")
                    break

                response = ask_agent(user_query=user_input)
                print(f"🤖 Dora replied: {response}")

                # === Prevent self-trigger ===
                is_speaking = True
                print(f"🗣 Speaking: {response}")
                text_to_speech_with_elevenlabs(
                    input_text=response,
                    output_filepath="final.mp3"
                )
                # ❌ Removed playsound() – ElevenLabs already plays the audio
                is_speaking = False

                chat_history.append([user_input, response])
                yield chat_history

                time.sleep(1)

        except Exception as e:
            print(f"❌ Error in chat loop: {e}")
            break


# =====================================================
# 🎥 WEBCAM SETUP
# =====================================================
camera = None
is_running = False
last_frame = None

def initialize_camera():
    """Initialize the webcam."""
    global camera
    if camera is None:
        camera = cv2.VideoCapture(0)
        if camera.isOpened():
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            camera.set(cv2.CAP_PROP_FPS, 30)
            camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return camera is not None and camera.isOpened()

def start_webcam():
    global is_running, last_frame
    is_running = True
    if not initialize_camera():
        return None
    ret, frame = camera.read()
    if ret:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        last_frame = frame
        return frame
    return last_frame

def stop_webcam():
    global is_running, camera
    is_running = False
    if camera is not None:
        camera.release()
        camera = None
    return None

def get_webcam_frame():
    global camera, is_running, last_frame
    if not is_running or camera is None:
        return last_frame
    if camera.get(cv2.CAP_PROP_BUFFERSIZE) > 1:
        for _ in range(int(camera.get(cv2.CAP_PROP_BUFFERSIZE)) - 1):
            camera.read()
    ret, frame = camera.read()
    if ret:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        last_frame = frame
        time.sleep(0.033)
        return frame
    return last_frame


# =====================================================
# 🧠 ENHANCED GRADIO UI (VOICE + CHAT)
# =====================================================
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("<h1 style='color: orange; text-align: center;'>👧🏼 Dora – Your Smart Personal AI Assistant</h1>")

    with gr.Row():
        # 🎥 LEFT COLUMN: WEBCAM
        with gr.Column(scale=1):
            gr.Markdown("### 🎥 Live Vision Feed")
            start_btn = gr.Button("▶️ Start Camera", variant="primary")
            stop_btn = gr.Button("⏹ Stop Camera", variant="secondary")
            webcam_output = gr.Image(label="Camera", streaming=True, width=640, height=480)
            webcam_timer = gr.Timer(0.033)

        # 💬 RIGHT COLUMN: CHAT + VOICE
        with gr.Column(scale=1):
            gr.Markdown("### 💬 Chat & Voice Interface")

            chatbot = gr.Chatbot(
                label="Dora Chat",
                height=450,
                show_label=False,
                bubble_full_width=False,
                avatar_images=("https://cdn-icons-png.flaticon.com/512/2202/2202112.png",
                               "https://cdn-icons-png.flaticon.com/512/4712/4712100.png"),
            )

            user_input = gr.Textbox(
                placeholder="Type your question here...",
                show_label=False,
                lines=1,
                container=False,
            )

            with gr.Row():
                mic_btn = gr.Button("🎙️ Speak", variant="primary")
                send_btn = gr.Button("📩 Send", variant="secondary")
                clear_btn = gr.Button("🧹 Clear Chat", variant="secondary")

    # === Webcam bindings ===
    start_btn.click(fn=start_webcam, outputs=webcam_output)
    stop_btn.click(fn=stop_webcam, outputs=webcam_output)
    webcam_timer.tick(fn=get_webcam_frame, outputs=webcam_output, show_progress=False)

    # === Chat functions ===
    def handle_text_input(message, history):
        if not message.strip():
            return history, ""
        response = ask_agent(user_query=message)
        text_to_speech_with_elevenlabs(input_text=response, output_filepath="final.mp3")
        history = history + [[message, response]]
        return history, ""

    def handle_voice_input(history):
        user_query = listen_to_user()
        if not user_query:
            return history
        response = ask_agent(user_query=user_query)
        text_to_speech_with_elevenlabs(input_text=response, output_filepath="final.mp3")
        history = history + [[user_query, response]]
        return history

    send_btn.click(fn=handle_text_input, inputs=[user_input, chatbot], outputs=[chatbot, user_input])
    mic_btn.click(fn=handle_voice_input, inputs=[chatbot], outputs=[chatbot])
    clear_btn.click(fn=lambda: [], outputs=chatbot)

    # Event bindings
    start_btn.click(fn=start_webcam, outputs=webcam_output)
    stop_btn.click(fn=stop_webcam, outputs=webcam_output)
    webcam_timer.tick(fn=get_webcam_frame, outputs=webcam_output, show_progress=False)
    clear_btn.click(fn=lambda: [], outputs=chatbot)

    demo.load(fn=process_audio_and_chat, outputs=chatbot)


# =====================================================
# 🚀 RUN APP
# =====================================================
if __name__ == "__main__":
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,       # Set True if you want a public link
        debug=True,
        inbrowser=True
    )
