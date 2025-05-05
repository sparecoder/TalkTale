import gradio as gr
import whisper
from gtts import gTTS
import base64
from groq import Groq
from tempfile import NamedTemporaryFile
import os
import language_tool_python

# Initialize APIs and tools
client = Groq(api_key="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")
model = whisper.load_model("base")
language_tool = language_tool_python.LanguageToolPublicAPI('en-US')

# System prompt with interest integration
def TUTOR_PROMPT(interests):
    return {
        "role": "system",
        "content": f"""You are an English conversation partner. Follow these rules:
1. Keep responses conversational (1-2 sentences max).
2. Focus on {interests} when possible.
3. After each response, add:
##Improvements: [1-2 key areas].
##Suggestions: [better alternatives].
4. Always ask engaging questions.
5. Be supportive and friendly."""
    }

chat_history = []
user_interests = "general topics"  # Default interests

def speech_to_text(audio_path):
    result = model.transcribe(audio_path)
    return result["text"]

def text_to_speech(text):
    tts = gTTS(text=text, lang='en', slow=False)
    with NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        audio_data = base64.b64encode(open(fp.name, "rb").read()).decode()
    os.unlink(fp.name)
    return f'<audio autoplay><source src="data:audio/mpeg;base64,{audio_data}"></audio>'

def generate_response(user_input, interests):
    system_msg = TUTOR_PROMPT(interests)
    messages = [system_msg] + chat_history + [{"role": "user", "content": user_input}]
    
    try:
        response = client.chat.completions.create(
            messages=messages,
            model="llama3-8b-8192",
            temperature=0.7
        )
        full_response = response.choices[0].message.content
        return parse_response(full_response)
    except Exception as e:
        return {"main": "Sorry, I couldn't process your request.", "improvements": "", "suggestions": ""}

def parse_response(response):
    parts = {"main": "", "improvements": "", "suggestions": ""}
    current_section = "main"
    
    for line in response.split('\n'):
        if "##Improvements:" in line:
            current_section = "improvements"
            line = line.replace("##Improvements:", "").strip()
        elif "##Suggestions:" in line:
            current_section = "suggestions"
            line = line.replace("##Suggestions:", "").strip()
        
        parts[current_section] += line + "\n"
    
    # Ensure all parts are populated
    parts = {key: value.strip() if value.strip() else "No feedback provided." for key, value in parts.items()}
    return parts

def process_conversation(audio_path, interests):
    global user_interests
    user_interests = interests
    
    try:
        # Speech to text
        user_text = speech_to_text(audio_path)
        
        # Get response components
        response_parts = generate_response(user_text, interests)
        
        # Update chat history
        chat_history.extend([
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": response_parts['main']}
        ])
        
        # Generate audio response for playback
        audio_output = text_to_speech(response_parts['main'])
        
        return (
            user_text,
            response_parts['main'],
            response_parts['improvements'],
            response_parts['suggestions'],
            audio_output,
            chat_history  # Ensure this is a list of dictionaries for Chatbot component
        )
    
    except Exception as e:
        return (
            f"Error: {str(e)}",
            "",
            "",
            "",
            None,
            []  # Return empty chat history in case of error
        )

# Gradio Interface
with gr.Blocks(theme=gr.themes.Soft()) as app:
    gr.Markdown("""
    # 🎯 Personalized English Coach  
    *Start by sharing your interests below!*
    """)
    
    with gr.Row():
        interests_input = gr.Textbox(
            label="Your Interests (e.g., technology, sports, movies)",
            placeholder="What topics do you want to discuss?"
        )
    
    with gr.Row():
        mic_input = gr.Microphone(type="filepath", label="Speak Now")
        submit_btn = gr.Button("Send", variant="primary")
    
    with gr.Row():
        user_transcription_box = gr.Textbox(label="Your Message")
        tutor_response_box = gr.Textbox(label="Tutor's Response")
    
    with gr.Row():
        gr.HTML("<h3 style='text-align:center'>Feedback Section</h3>")
    
    with gr.Row():
        improvements_box = gr.Textbox(label="Key Improvements", lines=2)
        suggestions_box = gr.Textbox(label="Better Alternatives", lines=2)
    
    audio_output_player = gr.HTML(label="Voice Response")
    chat_history_display = gr.Chatbot(label="Conversation History", type="messages")

    submit_btn.click(
        process_conversation,
        inputs=[mic_input, interests_input],
        outputs=[
            user_transcription_box,
            tutor_response_box,
            improvements_box,
            suggestions_box,
            audio_output_player,
            chat_history_display
        ]
    )

app.launch()
