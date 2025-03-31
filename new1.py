import gradio as gr
import whisper
from gtts import gTTS
import base64
from groq import Groq
from tempfile import NamedTemporaryFile
import os
from pydub import AudioSegment
import language_tool_python
import numpy as np
from scipy.io import wavfile
import statistics

# Initialize APIs and tools
client = Groq(api_key="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")
model = whisper.load_model("base")

# Initialize LanguageTool (local or remote)
try:
    language_tool = language_tool_python.LanguageTool('en-US')  # Local server
except Exception:
    print("Falling back to public API...")
    language_tool = language_tool_python.LanguageToolPublicAPI('en-US')  # Remote API fallback

# System prompt for English tutoring
TUTOR_PROMPT = {
    "role": "system",
    "content": """You are a friendly English conversation tutor. Your objectives are:
1. Engage in natural dialogues while correcting grammar.
2. Highlight 1-2 key improvements per interaction.
3. Suggest better vocabulary/phrases.
4. Ask follow-up questions to continue practice.
5. Maintain an encouraging tone with positive reinforcement.

Respond using this format:
**Correction:** [if needed, otherwise omit]
[Regular response with follow-up question]"""
}

chat_history = []

def speech_to_text(audio_path):
    result = model.transcribe(audio_path)
    return result["text"]

def generate_response(user_input):
    chat_history.append({"role": "user", "content": user_input})
    messages = [TUTOR_PROMPT] + chat_history
    response = client.chat.completions.create(
        messages=messages,
        model="llama3-8b-8192",
        temperature=0.7
    )
    full_response = response.choices[0].message.content
    chat_history.append({"role": "assistant", "content": full_response})
    return full_response

def text_to_speech(text):
    tts = gTTS(text=text, lang='en', slow=False)
    with NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        audio_data = base64.b64encode(open(fp.name, "rb").read()).decode()
    os.unlink(fp.name)
    return f'<audio autoplay><source src="data:audio/mpeg;base64,{audio_data}"></audio>'

def calculate_fluency(audio_path, transcription):
    audio = AudioSegment.from_file(audio_path)
    duration = len(audio) / 1000  # Seconds
    word_count = len(transcription.split())
    
    # Basic speech rate
    speech_rate = word_count / duration
    
    # Pause analysis (simplified)
    sample_rate, audio_data = wavfile.read(audio_path)
    audio_data = audio_data / np.max(np.abs(audio_data))
    is_speech = np.abs(audio_data) > 0.1
    pauses = np.diff(is_speech.astype(int))
    pause_count = np.sum(pauses == 1)
    
    # Articulation rate (speech rate without pauses)
    speaking_time = np.sum(is_speech) / sample_rate
    articulation_rate = word_count / speaking_time if speaking_time > 0 else 0
    
    return {
        'speech_rate': speech_rate,
        'articulation_rate': articulation_rate,
        'pause_frequency': pause_count / duration
    }

def linguistic_analysis(text):
    errors = language_tool.check(text)
    words = text.split()
    sentences = text.split('.')
    
    return {
        'error_rate': len(errors) / len(words),
        'lexical_diversity': len(set(words)) / len(words),
        'avg_sentence_length': statistics.mean([len(s.split()) for s in sentences if s])
    }

def generate_feedback(fluency_metrics, linguistic_metrics):
    feedback = []
    
    if fluency_metrics['speech_rate'] < 2.0:
        feedback.append(f"**Pace:** Try speaking slightly faster. Current rate: {fluency_metrics['speech_rate']:.1f} words/second")
    elif fluency_metrics['speech_rate'] > 3.5:
        feedback.append(f"**Pace:** Consider slowing down a bit. Current rate: {fluency_metrics['speech_rate']:.1f} words/second")
    
    if fluency_metrics['pause_frequency'] > 0.5:
        feedback.append("**Fluency:** Work on reducing pauses between words for smoother speech")
    
    if linguistic_metrics['error_rate'] > 0.1:
        feedback.append(f"**Accuracy:** Focus on grammatical accuracy. Error frequency: 1 per {1/linguistic_metrics['error_rate']:.1f} words")
    
    if linguistic_metrics['lexical_diversity'] < 0.5:
        feedback.append("**Vocabulary:** Try to use a wider range of words in your responses")
    
    if linguistic_metrics['avg_sentence_length'] < 5:
        feedback.append("**Complexity:** Aim for slightly longer, more complex sentences")
    elif linguistic_metrics['avg_sentence_length'] > 15:
        feedback.append("**Clarity:** Consider breaking up some longer sentences for clarity")
    
    return "\n".join(feedback) if feedback else "Great job! Keep practicing to maintain your skills."

def process_conversation(audio_path):
    try:
        # Speech to text
        user_text = speech_to_text(audio_path)
        
        # Fluency and linguistic analysis
        fluency_metrics = calculate_fluency(audio_path, user_text)
        linguistic_metrics = linguistic_analysis(user_text)
        feedback = generate_feedback(fluency_metrics, linguistic_metrics)
        
        # Get tutoring response
        raw_response = generate_response(user_text)
        
        # Separate correction from main response
        if "**Correction:**" in raw_response:
            correction, response_text = raw_response.split("\n", 1)
        else:
            correction, response_text = "", raw_response
        
        # Generate audio
        audio_output = text_to_speech(response_text)
        
        # Format chat history for display
        display_history = [
            (chat_history[i]["content"], chat_history[i+1]["content"]) 
            for i in range(0, len(chat_history)-1, 2)
        ]
        
        return user_text, response_text, correction, audio_output, feedback, display_history
    
    except Exception as e:
        return f"Error: {str(e)}", "", "", None, "", chat_history

# Gradio Interface
with gr.Blocks(theme=gr.themes.Soft()) as app:
    gr.Markdown("# 🇬🇧 English Conversation Coach with Fluency Assessment")
    
    with gr.Row():
        mic = gr.Microphone(type="filepath", label="Record Your Speech")
        submit_btn = gr.Button("Analyze & Respond", variant="primary")
    
    with gr.Row():
        user_text = gr.Textbox(label="Your Speech (Transcribed)")
        response_text = gr.Textbox(label="Tutor's Response", interactive=False)
    
    with gr.Row():
        correction_box = gr.Textbox(label="Grammar Feedback", visible=True)
        fluency_feedback = gr.Textbox(label="Fluency Feedback", visible=True)
    
    audio_output = gr.HTML(label="Tutor's Voice Response")
    history = gr.Chatbot(label="Conversation Flow")
    
    submit_btn.click(
        process_conversation,
        inputs=mic,
        outputs=[user_text, response_text, correction_box, audio_output, fluency_feedback, history]
    )

app.launch()
