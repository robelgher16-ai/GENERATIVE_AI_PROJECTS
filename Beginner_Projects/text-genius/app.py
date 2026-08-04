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

# Custom Styling (CSS) for a glowing neon green look
# Custom Styling (CSS) for a glowing neon green look with bright text
st.markdown("""
    <style>
    .main {
        background-color: #06110e;
    }
    .stApp {
        background: radial-gradient(circle at 50% 0%, #0b2219 0%, #06110e 100%);
    }
    /* Force all standard text and paragraphs to be bright mint/white */
    p, span, label, .stMarkdown, div[data-testid="stMarkdownContainer"] p {
        color: #e2f8f0 !important;
    }
    /* Make headers glowing white */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        text-shadow: 0 0 10px rgba(16, 185, 129, 0.4);
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: #03120b !important;
        font-weight: 700;
        letter-spacing: 0.5px;
        border-radius: 10px;
        padding: 0.7rem;
        border: 1px solid rgba(16, 185, 129, 0.6);
        box-shadow: 0 0 25px rgba(16, 185, 129, 0.4);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #34d399 0%, #10b981 100%);
        border-color: rgba(52, 211, 153, 0.9);
        box-shadow: 0 0 30px rgba(16, 185, 129, 0.8);
        transform: translateY(-2px);
    }
    .stTextInput>div>div>input {
        background-color: #091a13;
        color: #ffffff !important;
        border-radius: 10px;
        border: 1px solid #0f382b;
        padding: 0.6rem;
    }
    .stTextInput>div>div>input:focus {
        border-color: #10b981;
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.4);
    }
    div.stForm {
        background: rgba(9, 26, 19, 0.75);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(4px);
    }
    </style>
""", unsafe_allow_html=True)
# App Header
st.title("🧠 TextGenius")
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