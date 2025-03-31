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

# Initialize LanguageTool
language_tool = language_tool_python.LanguageToolPublicAPI('en-US')

# Global variables
TUTOR_PROMPT = {}

def create_tutor_prompt(interests):
    return {
        "role": "system",
        "content": f"""You are an engaging English conversation partner. The user is interested in: {interests}. Your goals are:
1. Maintain natural, flowing dialogue about the user's interests
2. Ask thoughtful follow-up questions
3. Expand on topics the user mentions
4. Use appropriate vocabulary related to the discussion topics
5. Keep responses concise (1-2 sentences)
6. Never mention grammar corrections - focus entirely on conversation"""
    }

def speech_to_text(audio_path):
    result = model.transcribe(audio_path)
    return result["text"]

def generate_response(user_input, chat_history):
    messages = [TUTOR_PROMPT] + chat_history[-6:]  # Keep last 3 exchanges
    response = client.chat.completions.create(
        messages=messages + [{"role": "user", "content": user_input}],
        model="llama3-8b-8192",
        temperature=0.7
    )
    return response.choices[0].message.content

def text_to_speech(text):
    tts = gTTS(text=text, lang='en', slow=False)
    with NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        audio_data = base64.b64encode(open(fp.name, "rb").read()).decode()
    os.unlink(fp.name)
    return f'<audio autoplay><source src="data:audio/mpeg;base64,{audio_data}"></audio>'

def analyze_errors(text):
    matches = language_tool.check(text)
    suggestions = []
    for match in matches[:3]:  # Show max 3 suggestions
        context = text[max(0, match.offset-10):match.offset+match.errorLength+10]
        suggestions.append(
            f"📌 {match.message}\n"
            f"   Example: {context.replace(match.context, '→'+match.replacements[0]+'←' if match.replacements else match.context)}"
        )
    return "\n\n".join(suggestions) if suggestions else "Great job! No major errors detected."

def process_conversation(audio_path, interests, chat_history):
    global TUTOR_PROMPT
    TUTOR_PROMPT = create_tutor_prompt(interests)
    try:
        # Speech to text
        user_text = speech_to_text(audio_path)
        
        # Generate conversational response
        response_text = generate_response(user_text, chat_history)
        audio_output = text_to_speech(response_text)
        
        # Analyze errors separately
        error_feedback = analyze_errors(user_text)
        
        # Update chat history
        chat_history.append({"role": "user", "content": user_text})
        chat_history.append({"role": "assistant", "content": response_text})
        
        return user_text, response_text, error_feedback, audio_output, chat_history
    
    except Exception as e:
        return f"Error: {str(e)}", "", "", None, chat_history

# Gradio Interface
with gr.Blocks(theme=gr.themes.Soft()) as app:
    gr.Markdown("# 🗣️ Interactive English Conversation Coach")
    
    interests = gr.Textbox(label="What are your interests? (e.g., photography, AI, travel)", lines=2)
    start_btn = gr.Button("Start Conversation", variant="primary")
    
    with gr.Row(visible=False) as main_interface:
        with gr.Column(scale=2):
            mic_input = gr.Microphone(type="filepath", label="Speak Now")
            chat_history = gr.Chatbot(label="Conversation Flow", height=400)
            submit_btn = gr.Button("Send", variant="primary")
        
        with gr.Column(scale=1):
            user_transcript = gr.Textbox(label="Your Speech")
            tutor_response = gr.Textbox(label="Tutor's Response")
            error_feedback = gr.Textbox(label="Suggestions", lines=8, interactive=False)
            audio_output = gr.HTML()
    
    chat_state = gr.State([])
    
    def start_conversation(interests):
        return gr.update(visible=True), [], "", "", ""
    
    start_btn.click(
        start_conversation,
        inputs=interests,
        outputs=[main_interface, chat_history, user_transcript, tutor_response, error_feedback]
    )
    
    submit_btn.click(
        process_conversation,
        inputs=[mic_input, interests, chat_state],
        outputs=[user_transcript, tutor_response, error_feedback, audio_output, chat_history, chat_state]
    )

app.launch()
