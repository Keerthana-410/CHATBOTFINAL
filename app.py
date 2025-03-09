import streamlit as st
import googletrans
from googletrans import Translator, LANGUAGES
from gtts import gTTS
import os
import speech_recognition as sr
import textwrap
import re
import sounddevice as sd
import numpy as np
from io import BytesIO
from PyPDF2 import PdfReader
from docx import Document
import pytesseract
from PIL import Image
import tempfile

# Page Configuration
st.set_page_config(page_title="🌍 Language Translator", layout="wide")
st.title("🌍 Language Translation Chatbot")

# Sidebar for Controls
with st.sidebar:
    st.header("⚙️ Settings")
    theme = st.radio("Select Theme:", ["Light", "Dark"], key="theme_select")
    if theme == "Dark":
        st.markdown("<style>body { background-color: #1e1e1e; color: white; }</style>", unsafe_allow_html=True)

# Initialize Session State Variables
if "speech_text" not in st.session_state:
    st.session_state.speech_text = ""
if "file_text" not in st.session_state:
    st.session_state.file_text = ""
if "manual_text" not in st.session_state:
    st.session_state.manual_text = ""
if "history" not in st.session_state:
    st.session_state.history = []

# Functions
def clean_text(text):
    text = re.sub(r'[^\w\s.,!?]', '', text)
    return re.sub(r'\s+', ' ', text).strip()

def translate_text(text, dest_languages):
    translator = Translator()
    translations = {}
    try:
        for lang in dest_languages:
            translated = translator.translate(text, dest=lang)
            translations[LANGUAGES[lang]] = translated.text
        return translations
    except Exception as e:
        return {"Error": str(e)}

def detect_language(text):
    translator = Translator()
    detected = translator.detect(text)
    return detected.lang if detected.lang in LANGUAGES else "Unknown"

def text_to_speech(text, lang):
    lang_code = next((code for code, name in LANGUAGES.items() if name.lower() == lang.lower()), None)
    if not lang_code:
        st.error(f"❌ Text-to-speech not available for {lang}")
        return None
    tts = gTTS(text=text, lang=lang_code)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmpfile:
        tts.save(tmpfile.name)
        return tmpfile.name

def speech_to_text():
    recognizer = sr.Recognizer()
    try:
        fs = 44100  # Sampling frequency
        duration = 5  # Recording duration in seconds
        st.write("🎤 Listening... Speak now!")
        audio_data = sd.rec(int(fs * duration), samplerate=fs, channels=1, dtype=np.int16)
        sd.wait()
        audio_np = np.array(audio_data, dtype=np.int16)
        audio = sr.AudioData(audio_np.tobytes(), fs, 2)
        return recognizer.recognize_google(audio)
    except Exception as e:
        return str(e)

def extract_text_from_file(uploaded_file):
    file_type = uploaded_file.type
    if "text" in file_type:
        return uploaded_file.read().decode()
    elif "pdf" in file_type:
        pdf_reader = PdfReader(uploaded_file)
        return "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
    elif "docx" in file_type:
        doc = Document(uploaded_file)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])
    elif "image" in file_type:
        try:
            img = Image.open(uploaded_file)
            return clean_text(pytesseract.image_to_string(img))
        except Exception as e:
            return f"Error extracting text: {e}"
    else:
        return "Unsupported file type"

# Target Languages Selection
dest_languages = st.multiselect("📌 Select target languages:", options=list(LANGUAGES.values()))

# Voice Input Section
st.write("## 🎤 Voice Input for Translation")
if st.button("🎙️ Speak for Translation"):
    st.session_state.speech_text = speech_to_text()

if st.session_state.speech_text:
    st.text_area("🎤 Recognized Speech:", st.session_state.speech_text, height=150)
    detected_lang = detect_language(st.session_state.speech_text)
    st.write(f"🌍 Detected Language: {LANGUAGES.get(detected_lang, 'Unknown')}")

# Translate Voice Input
if st.button("🔄 Translate Voice Input"):
    if st.session_state.speech_text and dest_languages:
        lang_codes = [code for code, name in LANGUAGES.items() if name in dest_languages]
        translations = translate_text(st.session_state.speech_text, lang_codes)
        st.write("### 📝 Translated Voice Input:")
        for lang, trans in translations.items():
            st.write(f"**{lang}:** {trans}")
            audio_file = text_to_speech(trans, lang)
            if audio_file:
                st.download_button("🔊 Download Audio", data=open(audio_file, "rb"), file_name="translated_audio.mp3", mime="audio/mp3")
    else:
        st.write("⚠️ Speak first and select a language.")

# File Upload & Translation
st.write("## 📂 File Upload & Translation")
uploaded_file = st.file_uploader("Upload a file (TXT, PDF, DOCX, PNG, JPG)", type=["txt", "pdf", "docx", "png", "jpg", "jpeg"])
if uploaded_file:
    st.session_state.file_text = extract_text_from_file(uploaded_file)
    st.text_area("📜 Extracted Text:", st.session_state.file_text, height=150)

if st.button("🔄 Translate File Input"):
    if st.session_state.file_text and dest_languages:
        lang_codes = [code for code, name in LANGUAGES.items() if name in dest_languages]
        translations = translate_text(st.session_state.file_text, lang_codes)
        st.write("### 📝 Translated File Input:")
        for lang, trans in translations.items():
            st.write(f"**{lang}:** {trans}")
            audio_file = text_to_speech(trans, lang)
            if audio_file:
                st.download_button("🔊 Download Audio", data=open(audio_file, "rb"), file_name="translated_audio.mp3", mime="audio/mp3")
    else:
        st.write("⚠️ Upload a file and select a language.")

# Text Input for Translation
st.write("## ✏️ Enter Text for Translation")
text_input = st.text_area("Enter text:", key="manual_text")

if st.button("🔄 Translate Text Input"):
    if text_input and dest_languages:
        lang_codes = [code for code, name in LANGUAGES.items() if name in dest_languages]
        translations = translate_text(text_input, lang_codes)
        st.write("### 📝 Translated Text:")
        for lang, trans in translations.items():
            st.write(f"**{lang}:** {trans}")
            audio_file = text_to_speech(trans, lang)
            if audio_file:
                st.download_button("🔊 Download Audio", data=open(audio_file, "rb"), file_name="translated_audio.mp3", mime="audio/mp3")
    else:
        st.write("⚠️ Enter text and select a language.")
