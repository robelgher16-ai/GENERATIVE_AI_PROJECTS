import os
import streamlit as st
from google import genai
from dotenv import load_dotenv
load_dotenv()

# Page Config
st.set_page_config(
    page_title="TextGenius - Psychological Insight Generator",
    page_icon="🧠",
    layout="centered"
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=Inter:wght@400;500;700&display=swap');

    :root {
        --neon: #10b981;
        --neon-bright: #34d399;
        --neon-soft: #6ee7b7;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Animated deep-space gradient background that slowly drifts.
       Multiple selectors + !important so this can't be overridden by
       Streamlit's own container styles or a config.toml theme. */
    html, body,
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    .main {
        background: radial-gradient(circle at 20% 20%, #0d2a20 0%, #06110e 45%, #030a08 100%) !important;
        background-size: 200% 200% !important;
        animation: bgDrift 18s ease-in-out infinite;
        min-height: 100vh !important;
    }
    .stApp {
        position: relative;
        overflow-x: hidden;
    }
    [data-testid="stHeader"] {
        background: transparent !important;
    }

    @keyframes bgDrift {
        0%   { background-position: 0% 50%; }
        50%  { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* Floating glow orbs behind content for depth */
    .stApp::before, .stApp::after {
        content: "";
        position: fixed;
        border-radius: 50%;
        filter: blur(90px);
        opacity: 0.35;
        z-index: 0;
        pointer-events: none;
    }
    .stApp::before {
        width: 380px; height: 380px;
        background: var(--neon);
        top: -100px; left: -120px;
        animation: floatOrb1 12s ease-in-out infinite;
    }
    .stApp::after {
        width: 320px; height: 320px;
        background: #059669;
        bottom: -80px; right: -100px;
        animation: floatOrb2 14s ease-in-out infinite;
    }
    @keyframes floatOrb1 {
        0%, 100% { transform: translate(0, 0) scale(1); }
        50% { transform: translate(40px, 60px) scale(1.15); }
    }
    @keyframes floatOrb2 {
        0%, 100% { transform: translate(0, 0) scale(1); }
        50% { transform: translate(-30px, -40px) scale(1.1); }
    }

    /* Bright, high-contrast body text */
    p, span, label, .stMarkdown, div[data-testid="stMarkdownContainer"] p {
        color: #f2fdf9 !important;
        position: relative !important;
        z-index: 1;
    }

    /* Make sure the whole content block sits above the glow orbs */
    [data-testid="stVerticalBlock"], [data-testid="stForm"] {
        position: relative;
        z-index: 1;
    }

    h1 {
        position: relative !important;
        z-index: 1;
    }

    /* The gradient/shimmer effect applies ONLY to this span, not the emoji,
       so the 🧠 keeps its natural color instead of being clipped transparent */
    .gradient-text {
        background: linear-gradient(90deg, #6ee7b7, #10b981, #34d399, #6ee7b7);
        background-size: 300% auto;
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shimmer 4s linear infinite;
        text-shadow: 0 0 30px rgba(16, 185, 129, 0.35);
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
    }
    @keyframes shimmer {
        to { background-position: 300% center; }
    }

    /* Emoji logo: keep its real color, just add a soft glow */
    .emoji-icon {
        -webkit-text-fill-color: initial !important;
        background: none !important;
        -webkit-background-clip: initial !important;
        background-clip: initial !important;
        filter: drop-shadow(0 0 8px rgba(16, 185, 129, 0.6));
    }

    h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        text-shadow: 0 0 12px rgba(16, 185, 129, 0.55);
        font-family: 'Space Grotesk', sans-serif;
        position: relative !important;
        z-index: 1;
    }

    /* Glassmorphic, pulsing-border form container */
    div.stForm {
        background: rgba(9, 26, 19, 0.65);
        border: 1px solid rgba(16, 185, 129, 0.4);
        border-radius: 16px;
        padding: 1.8rem;
        box-shadow:
            0 8px 32px rgba(0, 0, 0, 0.45),
            0 0 25px rgba(16, 185, 129, 0.15);
        backdrop-filter: blur(10px);
        animation: borderPulse 3.5s ease-in-out infinite;
        position: relative;
        z-index: 1;
    }
    @keyframes borderPulse {
        0%, 100% { box-shadow: 0 8px 32px rgba(0,0,0,0.45), 0 0 20px rgba(16,185,129,0.15); border-color: rgba(16,185,129,0.35); }
        50%      { box-shadow: 0 8px 40px rgba(0,0,0,0.5), 0 0 40px rgba(16,185,129,0.4); border-color: rgba(52,211,153,0.7); }
    }

    /* Glowing animated gradient button — div.stButton > button[kind] is
       more specific than Streamlit's own button[kind="secondary"] rules,
       so ours always wins the fight instead of falling back to default white */
    div.stButton > button[kind] {
        width: 100%;
        background: linear-gradient(135deg, #10b981 0%, #059669 50%, #10b981 100%) !important;
        background-size: 200% auto !important;
        color: #ffffff !important;
        font-weight: 700;
        letter-spacing: 0.5px;
        border-radius: 10px;
        padding: 0.75rem;
        border: 1px solid rgba(52, 211, 153, 0.7) !important;
        box-shadow: 0 0 25px rgba(16, 185, 129, 0.45);
        transition: all 0.35s ease;
        animation: buttonGlow 3s ease-in-out infinite;
    }
    @keyframes buttonGlow {
        0%, 100% { box-shadow: 0 0 20px rgba(16, 185, 129, 0.35); }
        50%      { box-shadow: 0 0 35px rgba(16, 185, 129, 0.7); }
    }
    div.stButton > button[kind]:hover {
        background-position: right center !important;
        border-color: #6ee7b7 !important;
        box-shadow: 0 0 45px rgba(52, 211, 153, 0.9);
        transform: translateY(-3px) scale(1.01);
        color: #000000 !important;
    }
    div.stButton > button[kind]:active {
        transform: translateY(-1px) scale(0.99);
    }

    /* Force the button label black — targets the inner <p>/span/div
       Streamlit renders the text in, with matching high specificity */
    div.stButton > button[kind] p,
    div.stButton > button[kind] span,
    div.stButton > button[kind] div {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }

    /* Glowing input field */
    .stTextInput>div>div>input {
        background-color: #091a13;
        color: #ffffff !important;
        border-radius: 10px;
        border: 1px solid #0f382b;
        padding: 0.7rem;
        transition: all 0.3s ease;
    }
    .stTextInput>div>div>input::placeholder {
        color: #7fdbb5 !important;
        opacity: 0.6;
    }
    .stTextInput>div>div>input:focus {
        border-color: var(--neon-bright);
        box-shadow: 0 0 20px rgba(16, 185, 129, 0.55);
    }

    /* Output card: fades and glows in when results appear */
    div[data-testid="stMarkdownContainer"] {
        animation: fadeInGlow 0.8s ease-out;
    }
    @keyframes fadeInGlow {
        0%   { opacity: 0; transform: translateY(12px); filter: blur(4px); }
        100% { opacity: 1; transform: translateY(0); filter: blur(0); }
    }

    /* Divider glow */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--neon-bright), transparent);
        box-shadow: 0 0 10px rgba(52, 211, 153, 0.6);
        margin: 1.5rem 0;
    }

    /* Spinner text glow while generating */
    .stSpinner > div {
        color: var(--neon-soft) !important;
        text-shadow: 0 0 10px rgba(16, 185, 129, 0.6);
    }

    /* Success/warning/error boxes with matching glow */
    div[data-testid="stAlert"] {
        border-radius: 10px;
        box-shadow: 0 0 20px rgba(16, 185, 129, 0.2);
        backdrop-filter: blur(6px);
    }
    /* Remove Streamlit's built-in Deploy button, menu, and footer
       so the app looks like a clean standalone product */
    [data-testid="stToolbar"] {
        visibility: hidden !important;
        display: none !important;
    }
    .stDeployButton {
        display: none !important;
    }
    #MainMenu {
        visibility: hidden !important;
        display: none !important;
    }
    footer {
        visibility: hidden !important;
        display: none !important;
    }
    [data-testid="stStatusWidget"] {
        visibility: hidden !important;
        display: none !important;
    }
    / *to change label color to black for lable in sthe summit button*/
    button > label {
    color: black;
    }
    div[data-testid="stFormSubmitButton"] button {
    color: black !important;
}

    div[data-testid="stFormSubmitButton"] button p {
    color: black !important;
    -webkit-text-fill-color: black !important;
}
    </style>
""", unsafe_allow_html=True)

# App Header
st.markdown(
    '<h1><span class="emoji-icon">🧠</span> <span class="gradient-text">TextGenius</span></h1>',
    unsafe_allow_html=True
)
st.subheader("Mindset-Building & Psychological Quote Generator")
st.write("Enter any theme, emotion, or mindset challenge below to receive a profound psychological quote and cognitive breakdown.")

# Input Form
with st.form("quote_form"):
    theme_input = st.text_input(
        "Enter your theme or focus:",
        placeholder="e.g., overcoming procrastination, mental resilience, discipline"
    )
    submit_button = st.form_submit_button(label="Generate Insight 🚀")

# Handle Generation
if submit_button:
    if not theme_input.strip():
        st.warning("Please enter a valid theme or topic.")
    else:
        # Retrieve API key from environment variable
        api_key = os.environ.get("GEMINI_API_KEY")

        if not api_key:
            st.error("Error: GEMINI_API_KEY environment variable is not set in your terminal!")
        else:
            try:
                with st.spinner("Generating your psychological insight... Please wait..."):
                    client = genai.Client(api_key=api_key)

                    system_instruction = (
                        "You are an expert in psychology, human behavior, and mindset-building. "
                        "When given a theme, emotion, or topic, you must provide:\n"
                        "1. A profound, original psychological quote about discipline, growth, or the mind.\n"
                        "2. A short, summarized 2-3 sentence explanation breaking down the cognitive or psychological insight behind it."
                    )

                    prompt = f"Theme / Focus: {theme_input}"

                    response = client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=prompt,
                        config={
                            "system_instruction": system_instruction,
                            "temperature": 0.8,
                        }
                    )

                    # Display Result in a clean card container
                    st.markdown("---")
                    st.markdown("### 💡 Generated Output")
                    st.markdown(response.text)

            except Exception as e:
                st.error(f"An error occurred: {e}")
