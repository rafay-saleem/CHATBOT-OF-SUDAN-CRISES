import streamlit as st
import pdfplumber
import re
import time
import os
from difflib import get_close_matches
from transformers import pipeline

# ====== PAGE CONFIG ======
st.set_page_config(page_title="Sudan AI Chatbot", page_icon="🕶️", layout="centered")

# ====== STYLING ======
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
html, body, [class*="css"] {
    font-family: 'Orbitron', sans-serif;
    background-color: #0b0c10;
    color: #f5f5f5;
}
.title {
    font-size: 3rem;
    font-weight: 700;
    color: #ff4c4c;
    text-align: center;
    text-shadow: 0 0 10px #ff0000, 0 0 20px #ff4c4c;
    animation: neonGlow 1.5s ease-in-out infinite alternate;
}
.subtitle {
    font-size: 1.3rem;
    font-weight: 600;
    color: #ff6b6b;
    text-align: center;
}
.yourname {
    font-size: 1rem;
    color: #ffaaaa;
    text-align: center;
    margin-top: -10px;
}
.tagline {
    font-size: 1rem;
    color: #ff7f7f;
    text-align: center;
}
hr {
    border: none;
    height: 2px;
    background: linear-gradient(to right, #ff4c4c, #ff0000);
    margin: 1em 0;
    box-shadow: 0 0 10px #ff0000;
}
.user-msg {
    background-color: #1a0000;
    color: #ff4c4c;
    padding: 10px;
    border-radius: 10px;
    text-align: right;
    margin: 5px 0;
    max-width: 80%;
    word-wrap: break-word;
}
.bot-msg {
    background-color: #330000;
    color: #ff7f7f;
    padding: 10px;
    border-radius: 10px;
    text-align: left;
    margin: 5px 0;
    max-width: 80%;
    word-wrap: break-word;
    animation: neonGlow 2s ease-in-out infinite alternate;
}
.stButton>button {
    background-color: #1a0000;
    color: #ff4c4c;
    border: 2px solid #ff0000;
    border-radius: 12px;
    padding: 0.5em 1.2em;
    font-weight: 700;
    transition: all 0.3s ease;
}
.stButton>button:hover {
    background-color: #ff0000;
    color: #0b0c10;
    transform: scale(1.05);
}
input[type=text] {
    background-color: #1a0000;
    color: #ff4c4c;
    border: 2px solid #ff0000;
    border-radius: 12px;
    padding: 10px;
    font-weight: 600;
    width: 100%;
}
@keyframes neonGlow {
    from { text-shadow: 0 0 5px #ff4c4c, 0 0 10px #ff0000; }
    to { text-shadow: 0 0 20px #ff6b6b, 0 0 30px #ff0000; }
}
#chat-container {
    max-height: 500px;
    overflow-y: auto;
    padding-right: 10px;
}
</style>
""", unsafe_allow_html=True)

# ====== HEADER ======
st.markdown('<div class="title">🌍 Sudan AI Chatbot</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Developed by Rafay Boss 🚀</div>', unsafe_allow_html=True)
st.markdown('<div class="yourname">RAFAY BOSS</div>', unsafe_allow_html=True)
st.markdown('<div class="tagline">Ask in <b>English | Roman English | Urdu</b> (PDF + AI fallback)</div>', unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# ====== INTENTS ======
intents = {
    "history_sudan": ["history of sudan", "sudan ki history", "sudan ka taruf", "sudan azad kaisay hua", "sudan pehle kaisay tha", "british rule in sudan", "anglo egyptian sudan"],
    "rsf_origin": ["rsf origin", "rapid support forces", "janjaweed", "rsf formed", "rsf history", "rsf conflict"],
    "sharia_law": ["sharia law", "1983 sharia", "nimeiri sharia", "hudood laws", "sharia imposed"],
    "south_sudan": ["south sudan independence", "2011 south sudan", "secession", "south autonomy"],
    "oil_conflict": ["oil divide", "china oil pipeline", "north control oil", "south resources", "oil disputes", "oil revenue"],
    "civil_wars": ["first civil war", "second civil war", "anya nya", "civil war casualties", "rebellion", "addis ababa", "cpa"],
    "bashir_removal": ["bashir removal", "omar al bashir removed", "2019 sudan coup", "bashir arrest"],
    "genocide_silence": ["why no one talking about sudan", "genocide in sudan", "world silent on sudan", "sudan famine"],
    "nile_control": ["neil river", "white nile", "blue nile", "egypt nile", "sudan nile"],
    "gold_smuggling": ["gold smuggling", "rsf gold", "uae gold sudan", "darfur gold"],
    "uranium_russia": ["uranium sudan", "russia sudan uranium", "saf uranium"],
}

related_questions_map = {
    "history_sudan": ["What caused civil wars in Sudan?", "Why did South Sudan separate?", "What is RSF?"],
    "rsf_origin": ["Who formed RSF?", "Why RSF was created?", "RSF and 2019 conflict", "SAF vs RSF conflict"],
    "sharia_law": ["Who implemented Sharia?", "Consequences of Sharia law?", "Sharia law and civil wars"],
    "south_sudan": ["When did South Sudan become independent?", "Why South Sudan seceded?", "North-South divide impact"],
    "oil_conflict": ["Who controlled oil in Sudan?", "China pipelines and oil revenue?", "Oil disputes impact on South Sudan?"],
    "civil_wars": ["First Civil War key events?", "Second Civil War casualties?", "Addis Ababa and CPA agreements?"],
    "bashir_removal": ["How was Bashir removed?", "Who removed Bashir?", "2019 Sudan protests"],
    "genocide_silence": ["Why is world silent on Sudan?", "What is happening in Sudan now?", "Why no media coverage on Sudan?"],
    "nile_control": ["Who controls Nile river?", "Why is Nile important for Egypt?", "White vs Blue Nile"],
    "gold_smuggling": ["How RSF smuggles gold?", "Where does RSF sell gold?", "UAE role in Sudan gold"],
    "uranium_russia": ["Does Russia take uranium from Sudan?", "SAF and Russia relations", "Uranium mines in Sudan"],
}

# ====== PDF LOADING ======
@st.cache_data
def load_pdf_text(file_path):
    txt = ""
    if os.path.exists(file_path):
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_txt = page.extract_text()
                if page_txt:
                    txt += re.sub(r'\n+', '\n', page_txt) + "\n"
    return txt.lower()

knowledge_base = load_pdf_text("Circumstances of Sudan.pdf")

# ====== AI FALLBACK ======
@st.cache_resource
def load_qa_pipeline():
    return pipeline("question-answering", model="distilbert-base-uncased-distilled-squad")

qa_pipeline = load_qa_pipeline()

# ====== LANGUAGE DETECTION ======
def detect_language(text):
    text = text.strip()
    if any('\u0600' <= ch <= '\u06FF' for ch in text):
        return "urdu"
    roman_words = ["hai", "kya", "se", "aur", "nahi", "ko", "ki", "ka", "ke", "kaun", "kab", "hae", "ha"]
    if any(w in text.lower() for w in roman_words):
        return "roman"
    return "english"

# ====== INTENT MATCH ======
def detect_intent(text):
    text = text.lower()
    for intent, keywords in intents.items():
        for k in keywords:
            if k in text:
                return intent
        if get_close_matches(text, keywords, n=1, cutoff=0.6):
            return intent
    return "unknown"

# ====== SESSION STATE ======
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_user_input" not in st.session_state:
    st.session_state.last_user_input = ""

# ====== CHAT DISPLAY ======
st.markdown('<div id="chat-container">', unsafe_allow_html=True)
for m in st.session_state.messages:
    cls = "user-msg" if m["role"] == "user" else "bot-msg"
    st.markdown(f"<div class='{cls}'>{m['content']}</div>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ====== USER INPUT ======
user_input = st.text_input("💬 Ask me anything about Sudan...", placeholder="Type your question here...")

# ====== PROCESS INPUT ======
if user_input.strip() != "" and user_input.strip() != st.session_state.last_user_input:
    st.session_state.last_user_input = user_input.strip()
    st.session_state.messages.append({"role": "user", "content": user_input})

    lang = detect_language(user_input)
    intent = detect_intent(user_input)

    # PDF + AI fallback
    try:
        qa = qa_pipeline(question=user_input, context=knowledge_base)
        if qa['score'] > 0.2:
            reply = qa['answer']
        else:
            reply = {"english": "I couldn't find relevant info in the PDF.", "roman": "PDF me kuch nahi mila.", "urdu": "پی ڈی ایف میں کچھ نہیں ملا۔"}[lang]
    except:
        reply = {"english": "Error reading PDF.", "roman": "PDF me masla hai.", "urdu": "پی ڈی ایف میں مسئلہ ہے۔"}[lang]

    # Auto-clear previous reply placeholder
    placeholder = st.empty()
    typed = ""
    for ch in reply:
        typed += ch
        placeholder.markdown(f"<div class='bot-msg'>{typed}</div>", unsafe_allow_html=True)
        time.sleep(0.01)
    st.session_state.messages.append({"role": "assistant", "content": reply})

    # Related questions
    if intent in related_questions_map:
        st.markdown("<b>Related Questions:</b>", unsafe_allow_html=True)
        cols = st.columns(len(related_questions_map[intent]))
        for i, q in enumerate(related_questions_map[intent]):
            if cols[i].button(q):
                st.session_state.user_input = q
                st.experimental_rerun()

# ====== AUTO SCROLL ======
st.markdown("""
<script>
const chat = window.parent.document.getElementById('chat-container');
if (chat) chat.scrollTop = chat.scrollHeight;
</script>
""", unsafe_allow_html=True)
