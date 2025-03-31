# -*- coding: utf-8 -*-
import gradio as gr
import whisper
from gtts import gTTS
import os
import base64
from groq import Groq
from tempfile import NamedTemporaryFile

# Initialize Groq API Client
client = Groq(
    api_key="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",
)

# Initialize Whisper model
model = whisper.load_model("base")

# Chat history storage
chat_history = []

def speech_to_text(audio_path):
    transcription = model.transcribe(audio_path)["text"]
    return transcription

def generate_response(text):
    # Add current message to history
    chat_history.append({"role": "user", "content": text})
    
    response = client.chat.completions.create(
        messages=chat_history,
        model="llama3-8b-8192",
    )
    
    assistant_response = response.choices[0].message.content
    # Add assistant response to history
    chat_history.append({"role": "assistant", "content": assistant_response})
    
    return assistant_response

def text_to_speech(text):
    tts = gTTS(text)
    with NamedTemporaryFile(suffix=".mp3", delete=False) as temp_audio:
        tts.save(temp_audio.name)
        with open(temp_audio.name, "rb") as f:
            audio_bytes = f.read()
    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
    os.unlink(temp_audio.name)
    return f"data:audio/mpeg;base64,{audio_base64}"

def chatbot_pipeline(audio_path):
    try:
        # Convert speech to text
        text_input = speech_to_text(audio_path)
        
        # Generate response with history
        response_text = generate_response(text_input)
        
        # Convert response to audio with autoplay
        response_audio = text_to_speech(response_text)
        
        # Create HTML audio element with autoplay
        audio_html = f'<audio controls autoplay><source src="{response_audio}" type="audio/mpeg"></audio>'
        
        # Format chat history for display
        display_history = [(chat_history[i]["content"], chat_history[i+1]["content"]) 
                          for i in range(0, len(chat_history)-1, 2)]
        
        return response_text, audio_html, display_history
    
    except Exception as e:
        return str(e), None, chat_history

# Create Gradio Interface
with gr.Blocks() as demo:
    gr.Markdown("# Voice Assistant with Memory")
    
    with gr.Row():
        audio_input = gr.Microphone(type="filepath", label="Speak", interactive=True)
        submit_btn = gr.Button("Submit", variant="primary")
    
    with gr.Row():
        text_output = gr.Textbox(label="Response Text")
        audio_output = gr.HTML(label="Response Audio")
    
    history_display = gr.Chatbot(label="Conversation History")
    
    submit_btn.click(
        fn=chatbot_pipeline,
        inputs=audio_input,
        outputs=[text_output, audio_output, history_display]
    )

demo.launch()
