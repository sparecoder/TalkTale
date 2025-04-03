import gradio as gr
import whisper
from gtts import gTTS
import base64
from groq import Groq
from tempfile import NamedTemporaryFile
import os
from pydub import AudioSegment
import numpy as np
from scipy.io import wavfile
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

def calculate_fluency_metrics(audio_path, transcription):
    # Calculate speech rate and other metrics
    try:
        audio = AudioSegment.from_file(audio_path)
        duration = len(audio) / 1000  # Convert to seconds
        
        # Word count
        words = transcription.split()
        word_count = len(words)
        
        # Calculate speech rate (words per minute)
        speech_rate = (word_count / duration) * 60 if duration > 0 else 0
        
        # Convert audio to numpy array for pause analysis
        sample_rate, audio_data = wavfile.read(audio_path)
        if len(audio_data.shape) > 1:  # If stereo, convert to mono
            audio_data = np.mean(audio_data, axis=1)
            
        # Normalize audio
        audio_data = audio_data / np.max(np.abs(audio_data)) if np.max(np.abs(audio_data)) > 0 else audio_data
        
        # Detect pauses (simplified)
        is_speech = np.abs(audio_data) > 0.1
        pauses = np.diff(is_speech.astype(int))
        pause_count = np.sum(pauses == 1)
        
        # Error analysis
        matches = language_tool.check(transcription)
        error_rate = len(matches) / word_count if word_count > 0 else 0
        
        return {
            "speech_rate": round(speech_rate, 1),  # Words per minute
            "speaking_time": round(duration, 1),   # Seconds
            "pause_count": pause_count,
            "error_rate": round(error_rate * 100, 1)  # Error percentage
        }
    except Exception as e:
        return {
            "speech_rate": 0,
            "speaking_time": 0,
            "pause_count": 0,
            "error_rate": 0,
            "error": str(e)
        }

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
    global user_interests, chat_history
    user_interests = interests
    
    try:
        # Speech to text
        user_text = speech_to_text(audio_path)
        
        # Calculate fluency metrics
        fluency_metrics = calculate_fluency_metrics(audio_path, user_text)
        
        # Get response components
        response_parts = generate_response(user_text, interests)
        
        # Format fluency feedback
        fluency_feedback = (
            f"Speech Rate: {fluency_metrics['speech_rate']} words/min\n"
            f"Speaking Time: {fluency_metrics['speaking_time']} seconds\n" 
            f"Pause Count: {fluency_metrics['pause_count']}\n"
            f"Error Rate: {fluency_metrics['error_rate']}% of words"
        )
        
        # Update chat history - format as tuples for Gradio Chatbot
        new_history = []
        new_history.extend([(user, asst) for user, asst in chat_history])  # Copy existing history
        new_history.append((user_text, response_parts['main']))  # Add new exchange
        
        # Generate audio response for playback
        audio_output = text_to_speech(response_parts['main'])
        
        # Update global chat history with dictionaries for the LLM context
        chat_history.append({"role": "user", "content": user_text})
        chat_history.append({"role": "assistant", "content": response_parts['main']})
        
        return (
            user_text,
            response_parts['main'],
            response_parts['improvements'],
            response_parts['suggestions'],
            fluency_feedback,
            audio_output,
            new_history  # Return tuples for Gradio display
        )
    
    except Exception as e:
        return (
            f"Error: {str(e)}",
            "",
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
    
    fluency_feedback_box = gr.Textbox(label="Fluency Metrics", lines=4)
    
    audio_output_player = gr.HTML(label="Voice Response")
    
    # Use standard Chatbot format without 'type' parameter
    chat_history_display = gr.Chatbot(label="Conversation History")

    submit_btn.click(
        process_conversation,
        inputs=[mic_input, interests_input],
        outputs=[
            user_transcription_box,
            tutor_response_box,
            improvements_box,
            suggestions_box,
            fluency_feedback_box,
            audio_output_player,
            chat_history_display
        ]
    )

app.launch()
