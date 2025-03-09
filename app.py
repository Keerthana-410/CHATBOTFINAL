import streamlit as st
import googletrans
from googletrans import Translator, LANGUAGES
from gtts import gTTS
import os
import re
from io import BytesIO
from PyPDF2 import PdfReader
from docx import Document
import pytesseract
from PIL import Image
import tempfile

# Set Page Configuration
st.set_page_config(page_title="🌍 Language Translation Chatbot", layout="wide")
st.title("🌍 Language Translation Chatbot")

# Sidebar for Controls
with st.sidebar:
    st.header("⚙️ Settings")
    theme = st.radio("Select Theme:", ["Light", "Dark"], key="theme_select")  # Added unique key here
    if theme == "Dark":
        st.markdown("<style>body { background-color: #1e1e1e; color: white; }</style>", unsafe_allow_html=True)

# Functions

def clean_text(text):
    text = re.sub(r'[^\w\s.,!?]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def translate_text(text, dest_languages):
    translator = Translator()
    translations = {}
    try:
        for lang in dest_languages:
            translated = translator.translate(text, dest=lang)
            translations[LANGUAGES[lang]] = translated.text.encode('utf-8', 'ignore').decode('utf-8')
        return translations
    except Exception as e:
        return {"Error": str(e)}

def detect_language(text):
    try:
        translator = Translator()
        detected = translator.detect(text)
        return detected.lang
    except Exception:
        return "Unknown"

def text_to_speech(text, lang):
    lang_code = next((code for code, name in LANGUAGES.items() if name.lower() == lang.lower()), None)
    if not lang_code:
        st.error(f"❌ Text-to-speech not available for {lang}")
        return None
    tts = gTTS(text=text, lang=lang_code)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmpfile:
        tts.save(tmpfile.name)
        return tmpfile.name

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
            text = pytesseract.image_to_string(img)
            return clean_text(text)
        except Exception as e:
            st.error(f"Error extracting text from image: {e}")
            return ""
    else:
        return "Unsupported file type"

def save_history_as_txt(history):
    if not history:
        return None
    text = ""
    for entry in history:
        text += f"Original: {entry['Original']}\n"
        for lang, translation in entry['Translated'].items():
            text += f"Translated ({lang}): {translation}\n"
        text += "---\n"
    return text.encode()

# Target Languages Selection
dest_languages = st.multiselect("📌 Select target languages:", options=list(LANGUAGES.values()))

# File Upload & Translation Section
st.write("## 📂 File Upload & Translation")
uploaded_file = st.file_uploader("Upload a file (TXT, PDF, DOCX, PNG, JPG)", type=["txt", "pdf", "docx", "png", "jpg", "jpeg"])
if uploaded_file:
    extracted_text = extract_text_from_file(uploaded_file)
    st.write("### Extracted Text:")
    st.write(extracted_text)

    # Translate File Input
    if st.button("🔄 Translate File Input"):
        if extracted_text and dest_languages:
            lang_codes = [code for code, name in LANGUAGES.items() if name in dest_languages]
            translations = translate_text(extracted_text, lang_codes)
            st.write("### 📝 Translated File Input:")
            for lang, trans in translations.items():
                st.write(f"**{lang}:** {trans}")
                audio_file = text_to_speech(trans, lang)
                if audio_file:
                    st.audio(audio_file, format='audio/mp3')
            if "history" not in st.session_state:
                st.session_state.history = []
            st.session_state.history.append({"Original": extracted_text.strip(), "Translated": translations})
        else:
            st.write("⚠️ Please upload a file and select at least one language to translate.")

# Text Input for Translation
st.write("## ✏️ Enter Text for Translation")
text_input = st.text_area("Enter text to translate:", value="")

# Detect language of the entered text
detected_lang = detect_language(text_input) if text_input else None
if detected_lang:
    st.write(f"🌍 Detected Language: {LANGUAGES.get(detected_lang, 'Unknown')}")

# Translate Text Input
if st.button("🔄 Translate Text Input"):
    if text_input and dest_languages:
        lang_codes = [code for code, name in LANGUAGES.items() if name in dest_languages]
        translations = translate_text(text_input, lang_codes)
        st.write("### 📝 Translated Text Input:")
        for lang, trans in translations.items():
            st.write(f"**{lang}:** {trans}")
            audio_file = text_to_speech(trans, lang)
            if audio_file:
                st.audio(audio_file, format='audio/mp3')
        if "history" not in st.session_state:
            st.session_state.history = []
        st.session_state.history.append({"Original": text_input.strip(), "Translated": translations})
    else:
        st.write("⚠️ Please enter text or select at least one language to translate.")

# Right-Side Section for Download
with st.sidebar:
    st.write("### 🔍 Translation History")
    if st.button("📄 Download Translation History (TXT)"):
        txt_file = save_history_as_txt(st.session_state.history)
        if txt_file:
            st.download_button("⬇️ Download History (TXT)", data=txt_file, file_name="translation_history.txt", mime="text/plain")
