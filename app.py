import streamlit as st
from transformers import pipeline
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from langdetect import detect
import speech_recognition as sr
import io
from datetime import datetime

# ---------------- LOGIN ---------------- #
def login():
    st.title("🔐 Secure Login")
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")

    if st.button("Login"):
        if user == "admin" and pwd == "1234":
            st.session_state.logged_in = True
        else:
            st.error("Invalid credentials")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login()
    st.stop()

# ---------------- UI STYLE ---------------- #
st.markdown("""
<style>
.stApp {
    background: linear-gradient(270deg, #0f2027, #203a43, #2c5364);
    color: white;
}
.card {
    padding:15px;
    border-radius:10px;
    background:#1e1e1e;
    margin-bottom:10px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- SIDEBAR ---------------- #
menu = st.sidebar.selectbox("📂 Menu", ["Home", "Dashboard", "Logs"])

# ---------------- MODEL ---------------- #
@st.cache_resource
def load_model():
    return pipeline("text-classification")

classifier = load_model()

# ---------------- LOGIC ---------------- #
def detect_attack(text):
    t = text.lower()
    if "ignore" in t:
        return "Prompt Injection", 80, "Overrides system rules"
    elif "password" in t:
        return "Data Leak", 90, "Sensitive data request"
    elif "bypass" in t:
        return "Jailbreak", 85, "Trying to bypass security"
    return "Safe", 10, "Normal usage"

def suggest_safe():
    return "Try asking about general information instead of restricted content."

def analyze(text):
    result = classifier(text)[0]
    confidence = result['score'] * 100

    attack, base, reason = detect_attack(text)
    risk = int((result['score'] * 50) + base)

    status = "❌ Blocked" if attack != "Safe" else "✅ Allowed"
    response = "⚠️ Blocked" if attack != "Safe" else "✔ Safe"

    return status, attack, risk, reason, confidence, response

# ---------------- SPEECH INPUT ---------------- #
def speech_to_text():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎤 Speak now...")
        audio = r.listen(source)
        try:
            return r.recognize_google(audio)
        except:
            return ""

# ---------------- PDF ---------------- #
def create_pdf(text, status, attack, risk, reason):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    content = [
        Paragraph(f"Input: {text}", styles["Normal"]),
        Paragraph(f"Status: {status}", styles["Normal"]),
        Paragraph(f"Attack: {attack}", styles["Normal"]),
        Paragraph(f"Risk: {risk}", styles["Normal"]),
        Paragraph(f"Reason: {reason}", styles["Normal"]),
    ]

    doc.build(content)
    buffer.seek(0)
    return buffer

# ================= HOME ================= #
if menu == "Home":

    st.title("🛡️ GenAI Security Agent Premium")

    user_input = st.text_area("Enter prompt")

    if st.button("🎤 Speak"):
        user_input = speech_to_text()
        st.write("You said:", user_input)

    if st.button("Analyze"):

        if user_input.strip() == "":
            st.warning("Enter input")
        else:
            lang = detect(user_input)

            status, attack, risk, reason, conf, output = analyze(user_input)

            safe_risk = min(risk, 100)

            # 🔔 ALERT
            if safe_risk > 80:
                st.toast("🚨 Critical Attack Detected!")

            # 🎨 CARD UI
            st.markdown(f"""
            <div class="card">
            <h3>{status}</h3>
            <p><b>Attack:</b> {attack}</p>
            <p><b>Risk:</b> {risk}</p>
            <p><b>Confidence:</b> {conf:.2f}%</p>
            <p><b>Language:</b> {lang}</p>
            <p><b>Reason:</b> {reason}</p>
            </div>
            """, unsafe_allow_html=True)

            st.progress(safe_risk / 100)

            if attack != "Safe":
                st.warning("💡 Suggestion: " + suggest_safe())

            # SAVE LOGS WITH TIME
            with open("logs.txt", "a") as f:
                f.write(f"{datetime.now()} | {user_input} | {attack} | {risk}\n")

            # PDF
            pdf = create_pdf(user_input, status, attack, risk, reason)
            st.download_button("📥 Download Report", pdf, "report.pdf")

# ================= DASHBOARD ================= #
elif menu == "Dashboard":

    st.title("📊 Security Dashboard")

    logs = []
    try:
        with open("logs.txt") as f:
            logs = f.readlines()
    except:
        pass

    total = len(logs)
    safe = 0
    high = 0

    attack_counts = {}
    risk_scores = []

    for log in logs:
        parts = log.strip().split(" | ")
        if len(parts) == 4:
            _, _, attack, risk = parts
            risk = int(risk)

            if attack == "Safe":
                safe += 1
            if risk > 70:
                high += 1

            attack_counts[attack] = attack_counts.get(attack, 0) + 1
            risk_scores.append(risk)

    # KPI
    st.metric("Total Requests", total)
    st.metric("Safe Requests", safe)
    st.metric("High Risk", high)

    # BAR
    colors = ["blue" if k == "Safe" else "red" for k in attack_counts]
    if attack_counts:
        fig, ax = plt.subplots()
        ax.bar(attack_counts.keys(), attack_counts.values(), color=colors)
        st.pyplot(fig)

    # LINE
    if risk_scores:
        fig2, ax2 = plt.subplots()
        for i, r in enumerate(risk_scores):
            ax2.plot(i, r, 'bo' if r < 50 else 'ro')
        st.pyplot(fig2)

# ================= LOGS ================= #
elif menu == "Logs":

    st.title("📜 Logs Viewer")

    try:
        with open("logs.txt") as f:
            logs = f.readlines()

        for log in reversed(logs[-10:]):
            st.code(log)
    except:
        st.write("No logs available")