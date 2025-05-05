# 🎙️ TalkTale — Personalized English Conversation Coach

TalkTale is a voice-interactive AI tool designed to help users improve their English-speaking fluency. It listens to your speech, gives personalized responses based on your interests, and provides real-time feedback with fluency metrics, grammatical suggestions, and speaking improvements — all in a conversational style.

---

## 🚀 Features

* 🎤 **Speech Recognition** with OpenAI's Whisper
* 🗣️ **Text-to-Speech** playback using gTTS
* 🤖 **Conversational AI** powered by Groq’s LLaMA3
* 🧠 **Fluency Analysis**: Calculates speech rate, pauses, speaking time, and grammar error rate
* 💡 **Personalized Feedback**:

  * Key Improvements
  * Better Alternatives
* 🧭 **Interest-Based Conversations**: Tailors responses based on topics you like
* 🌐 **Friendly Web Interface** built with Gradio

---

## 🏗️ Project Structure

```
TalkTale/
│
├── web-app                # some frontend files
├── new1.py  
├── new2.py                 # Main Gradio app
├── requirements.txt       # List of dependencies
└── README.md              # Project documentation
```

---

## 🧰 Technologies Used

| Component      | Technology                                                            |
| -------------- | --------------------------------------------------------------------- |
| Speech-to-Text | [Whisper](https://github.com/openai/whisper)                          |
| AI Response    | [Groq + LLaMA3](https://groq.com)                                     |
| Text-to-Speech | [gTTS (Google TTS)](https://pypi.org/project/gTTS/)                   |
| Grammar Check  | [LanguageTool API](https://languagetool.org/)                         |
| Audio Analysis | [pydub](https://github.com/jiaaro/pydub), [scipy](https://scipy.org/) |
| Web UI         | [Gradio](https://gradio.app)                                          |

---

## 🛠️ Installation

1. **Clone the repo**

```bash
git clone https://github.com/yourusername/TalkTale.git
cd TalkTale
```

2. **Create a virtual environment (optional but recommended)**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Add your Groq API key**
   Replace the placeholder in `app.py`:

```python
client = Groq(api_key="your_groq_api_key")
```

---

## ▶️ Run the App

```bash
python app.py
```

The app will launch in your browser. Start by speaking into the microphone and engaging with your English coach.

---

## 📊 Sample Fluency Feedback

```
Speech Rate: 105 words/min
Speaking Time: 33.5 seconds
Pause Count: 4
Error Rate: 3.2%
```

---

## 🔒 Note

Make sure your microphone permissions are enabled in your browser. Also, for the best performance, use this app in a quiet environment.

---

## 🙌 Acknowledgments

* OpenAI Whisper for robust speech recognition
* Groq for blazing-fast inference with LLaMA3
* LanguageTool for grammar analysis
* Gradio for making deployment easy

---

## 📌 Future Enhancements

* Add a dashboard to track fluency progress
* Visualize speech rate and pauses over time
* Support for multiple languages
* Offline mode for limited-resource environments

---
