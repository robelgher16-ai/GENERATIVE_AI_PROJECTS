# ============================================================
# LOCAL TINYLLAMA + STREAMLIT
# MOVIE INFORMATION EXTRACTOR
# ============================================================


# ============================================================
# IMPORTS
# ============================================================

import json
import re

import streamlit as st

from langchain_huggingface import (
    ChatHuggingFace,
    HuggingFacePipeline
)

from langchain_core.prompts import ChatPromptTemplate

from pydantic import BaseModel, Field

from typing import List, Optional


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Movie Information Extractor",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CUSTOM CSS (UI ONLY — no logic here)
# ============================================================

st.markdown(
    """
    <style>
        /* App background */
        .stApp {
            background: linear-gradient(180deg, #0f1116 0%, #171923 100%);
        }

        /* Hero header */
        .hero {
            padding: 2.2rem 2rem;
            border-radius: 18px;
            background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
            margin-bottom: 1.6rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.35);
        }
        .hero h1 {
            color: white;
            font-size: 2.1rem;
            margin: 0;
            font-weight: 800;
        }
        .hero p {
            color: rgba(255,255,255,0.85);
            margin-top: 0.4rem;
            font-size: 1rem;
        }

        /* Section cards */
        .section-card {
            background: #1a1d29;
            border: 1px solid #2a2e3d;
            border-radius: 14px;
            padding: 1.4rem 1.5rem;
            margin-bottom: 1.2rem;
        }

        /* Movie result card */
        .movie-card {
            background: linear-gradient(135deg, #1f2333 0%, #14161f 100%);
            border: 1px solid #2f3346;
            border-radius: 16px;
            padding: 1.6rem;
        }
        .movie-title {
            font-size: 1.6rem;
            font-weight: 800;
            color: #ffffff;
            margin-bottom: 0.2rem;
        }
        .movie-meta {
            color: #9aa0b4;
            font-size: 0.95rem;
            margin-bottom: 1rem;
        }
        .pill {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 999px;
            background: rgba(37, 117, 252, 0.18);
            color: #7fb0ff;
            font-size: 0.8rem;
            font-weight: 600;
            margin: 0.15rem 0.3rem 0.15rem 0;
            border: 1px solid rgba(37, 117, 252, 0.35);
        }
        .rating-badge {
            display: inline-block;
            padding: 0.35rem 0.9rem;
            border-radius: 10px;
            background: rgba(255, 193, 7, 0.15);
            border: 1px solid rgba(255, 193, 7, 0.4);
            color: #ffc107;
            font-weight: 700;
            font-size: 1rem;
        }

        /* Buttons */
        .stButton > button {
            border-radius: 10px;
            font-weight: 700;
            border: none;
            transition: transform 0.15s ease;
        }
        .stButton > button:hover {
            transform: translateY(-1px);
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background: #12141c;
        }
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HERO HEADER (UI ONLY)
# ============================================================

st.markdown(
    """
    <div class="hero">
        <h1>🎬 Movie Information Extractor</h1>
        <p>Local TinyLlama + LangChain + Pydantic — runs fully on your machine, no API keys.</p>
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SIDEBAR (UI ONLY)
# ============================================================

with st.sidebar:

    st.markdown("### ℹ️ About")
    st.write(
        "This app extracts structured movie details "
        "(title, year, genre, director, cast, rating, summary) "
        "from a plain-text paragraph using a **local TinyLlama** model."
    )

    st.markdown("### ⚙️ How it works")
    st.markdown(
        "1. Paste or write a paragraph about a movie\n"
        "2. Click **Extract Movie Information**\n"
        "3. TinyLlama returns structured JSON\n"
        "4. View results, download JSON"
    )

    st.markdown("### 🧠 Model")
    st.code("TinyLlama/TinyLlama-1.1B-Chat-v1.0", language="text")

    st.divider()
    st.caption("Runs 100% locally — your data never leaves your machine.")


# ============================================================
# LOAD LOCAL MODEL
# ============================================================

@st.cache_resource
def load_local_model():

    llm = HuggingFacePipeline.from_model_id(

        model_id="TinyLlama/TinyLlama-1.1B-Chat-v1.0",

        task="text-generation",

        pipeline_kwargs={

            "max_new_tokens": 180,

            "do_sample": False,

            "repetition_penalty": 1.05,

            "return_full_text": False,

        },

    )

    chat_model = ChatHuggingFace(
        llm=llm
    )

    return chat_model


# ============================================================
# PYDANTIC MODEL
# ============================================================

class Movie(BaseModel):

    title: str

    release_year: Optional[int] = None

    genre: List[str] = Field(
        default_factory=list
    )

    director: Optional[str] = None

    cast: List[str] = Field(
        default_factory=list
    )

    rating: Optional[float] = None

    summery: str = ""


# ============================================================
# EXAMPLE
# ============================================================

example_text = """
Inception is a 2010 science fiction action film directed by
Christopher Nolan. The movie stars Leonardo DiCaprio,
Joseph Gordon-Levitt, Ellen Page, Tom Hardy, and Ken Watanabe.
It has a rating of 8.8 and follows a skilled thief who enters
people's dreams to steal their secrets.
"""


# ============================================================
# PROMPT
# ============================================================

prompt = ChatPromptTemplate.from_messages([

    (
        "system",
        """
You extract movie information.

IMPORTANT:
Return ONLY ONE JSON OBJECT.

The output must contain exactly these fields:

title
release_year
genre
director
cast
rating
summery

Example:

{{
"title": "Inception",
"release_year": 2010,
"genre": ["Science Fiction", "Action"],
"director": "Christopher Nolan",
"cast": ["Leonardo DiCaprio", "Tom Hardy"],
"rating": 8.8,
"summery": "A thief enters dreams to steal information."
}}

If information is unknown:
release_year = null
director = null
rating = null
genre = []
cast = []
summery = ""

NO explanation.
NO Python.
NO Markdown.
NO code.
NO numbered list.
NO JSON schema.
NO additional text.

OUTPUT ONLY JSON.
"""
    ),

    (
        "human",
        """
Extract the movie information from this paragraph:

{paragraph}

Remember:

OUTPUT ONLY JSON.
"""
    )

])


# ============================================================
# SESSION STATE
# ============================================================

if "paragraph" not in st.session_state:

    st.session_state["paragraph"] = ""


# ============================================================
# INPUT (UI enhanced with section card + columns)
# ============================================================

st.markdown('<div class="section-card">', unsafe_allow_html=True)

st.subheader("📝 Movie Paragraph")

st.text_area(

    "Enter movie paragraph:",

    height=220,

    key="paragraph",

    placeholder=(
        "Example: Inception is a 2010 science fiction "
        "action film directed by Christopher Nolan..."
    )

)

col_a, col_b = st.columns([1, 1])

with col_a:
    example_clicked = st.button(
        "💡 Use Example",
        use_container_width=True
    )

with col_b:
    extract_clicked = st.button(
        "🎬 Extract Movie Information",
        type="primary",
        use_container_width=True
    )

st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# EXAMPLE BUTTON
# ============================================================

if example_clicked:

    st.session_state["paragraph"] = example_text

    st.rerun()


# ============================================================
# GET PARAGRAPH
# ============================================================

paragraph = st.session_state["paragraph"]


# ============================================================
# JSON EXTRACTION FUNCTION
# ============================================================

def extract_json_object(text: str):
    """
    Find and parse the first valid JSON object
    from the model response.
    """

    # --------------------------------------------------------
    # Clean response
    # --------------------------------------------------------

    text = text.strip()

    # --------------------------------------------------------
    # Remove markdown fences
    # --------------------------------------------------------

    text = re.sub(
        r"```json",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = text.replace(
        "```",
        ""
    )

    text = text.strip()

    # --------------------------------------------------------
    # Find first {
    # --------------------------------------------------------

    start = text.find("{")

    if start == -1:

        return None


    # --------------------------------------------------------
    # JSON decoder
    # --------------------------------------------------------

    decoder = json.JSONDecoder()

    try:

        data, _ = decoder.raw_decode(
            text[start:]
        )

        return data

    except json.JSONDecodeError:

        return None


# ============================================================
# EXTRACT BUTTON
# ============================================================

if extract_clicked:

    # ========================================================
    # INPUT VALIDATION
    # ========================================================

    if not paragraph.strip():

        st.warning(
            "⚠️ Please enter a movie paragraph."
        )

        st.stop()


    # ========================================================
    # CREATE PROMPT
    # ========================================================

    final_prompt = prompt.invoke(

        {
            "paragraph": paragraph
        }

    )


    # ========================================================
    # RUN MODEL
    # ========================================================

    try:

        with st.spinner(
            "🤖 Running TinyLlama locally..."
        ):

            chat_model = load_local_model()

            response = chat_model.invoke(
                final_prompt
            )


        # ====================================================
        # GET RESPONSE
        # ====================================================

        raw_response = response.content


        if not isinstance(
            raw_response,
            str
        ):

            raw_response = str(
                raw_response
            )


        raw_response = raw_response.strip()


        # ====================================================
        # DEBUG OUTPUT
        # ====================================================

        with st.expander(
            "🔍 Raw TinyLlama Response",
            expanded=False
        ):

            st.code(
                raw_response,
                language="text"
            )


        # ====================================================
        # CHECK EMPTY RESPONSE
        # ====================================================

        if not raw_response:

            st.error(
                "❌ TinyLlama returned an empty response."
            )

            st.stop()


        # ====================================================
        # EXTRACT JSON
        # ====================================================

        data = extract_json_object(
            raw_response
        )


        # ====================================================
        # JSON NOT FOUND
        # ====================================================

        if data is None:

            st.error(
                "❌ TinyLlama did not generate usable JSON."
            )

            st.warning(
                "TinyLlama is following the instruction "
                "as a coding task instead of performing "
                "structured extraction."
            )

            st.info(
                "The raw response above shows exactly "
                "what the local model generated."
            )

            st.stop()


        # ====================================================
        # JSON MUST BE OBJECT
        # ====================================================

        if not isinstance(
            data,
            dict
        ):

            st.error(
                "❌ The model returned JSON, "
                "but it was not a JSON object."
            )

            st.json(
                data
            )

            st.stop()


        # ====================================================
        # DEFAULT VALUES
        # ====================================================

        data.setdefault(
            "title",
            "Unknown"
        )

        data.setdefault(
            "release_year",
            None
        )

        data.setdefault(
            "genre",
            []
        )

        data.setdefault(
            "director",
            None
        )

        data.setdefault(
            "cast",
            []
        )

        data.setdefault(
            "rating",
            None
        )

        data.setdefault(
            "summery",
            ""
        )


        # ====================================================
        # NORMALIZE LIST FIELDS
        # (TinyLlama sometimes returns cast/genre as objects
        # like {"name": ..., "role": ...} instead of plain
        # strings — flatten those into strings here)
        # ====================================================

        def normalize_string_list(items):

            if not isinstance(items, list):
                return []

            normalized = []

            for item in items:

                if isinstance(item, str):

                    normalized.append(item)

                elif isinstance(item, dict):

                    name = (
                        item.get("name")
                        or item.get("actor")
                        or item.get("title")
                        or item.get("role")
                    )

                    if name:
                        normalized.append(str(name))
                    else:
                        normalized.append(str(item))

                else:

                    normalized.append(str(item))

            return normalized


        data["cast"] = normalize_string_list(
            data.get("cast")
        )

        data["genre"] = normalize_string_list(
            data.get("genre")
        )


        # ====================================================
        # PYDANTIC VALIDATION
        # ====================================================

        movie_data = Movie.model_validate(
            data
        )


        # ====================================================
        # SUCCESS
        # ====================================================

        st.success(
            "✅ Movie information extracted successfully!"
        )

        st.divider()


        # ====================================================
        # MOVIE INFORMATION — styled card (UI ONLY)
        # ====================================================

        genre_pills = "".join(
            f'<span class="pill">{g}</span>' for g in movie_data.genre
        ) if movie_data.genre else '<span class="pill">Not available</span>'

        cast_pills = "".join(
            f'<span class="pill">{c}</span>' for c in movie_data.cast
        ) if movie_data.cast else '<span class="pill">Not available</span>'

        rating_html = (
            f'<span class="rating-badge">⭐ {movie_data.rating}</span>'
            if movie_data.rating is not None
            else '<span class="rating-badge">⭐ N/A</span>'
        )

        st.markdown(
            f"""
            <div class="movie-card">
                <div class="movie-title">🎞️ {movie_data.title}</div>
                <div class="movie-meta">
                    {movie_data.release_year or "Year unknown"} ·
                    Directed by {movie_data.director or "Unknown"}
                </div>
                {rating_html}
                <div style="margin-top: 1.2rem;">
                    <div style="color:#9aa0b4; font-size:0.85rem; margin-bottom:0.4rem;">GENRE</div>
                    {genre_pills}
                </div>
                <div style="margin-top: 1rem;">
                    <div style="color:#9aa0b4; font-size:0.85rem; margin-bottom:0.4rem;">CAST</div>
                    {cast_pills}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("### 📖 Summary")

        if movie_data.summery:

            st.info(
                movie_data.summery
            )

        else:

            st.info(
                "No summary available."
            )


        # ====================================================
        # STRUCTURED JSON + DOWNLOAD — tabs (UI ONLY)
        # ====================================================

        tab1, tab2 = st.tabs(["🔹 Structured JSON", "🧩 Raw Parsed JSON"])

        with tab1:
            st.json(
                movie_data.model_dump()
            )

        with tab2:
            st.json(
                data
            )


        # ====================================================
        # DOWNLOAD JSON
        # ====================================================

        json_output = movie_data.model_dump_json(
            indent=2
        )

        st.download_button(

            "⬇️ Download JSON",

            data=json_output,

            file_name="movie_information.json",

            mime="application/json",

            use_container_width=True

        )


    # ========================================================
    # ERROR HANDLING
    # ========================================================

    except Exception as e:

        st.error(
            "❌ Error while extracting movie information."
        )

        with st.expander(
            "🔍 Error Details"
        ):

            st.exception(e)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Local Movie Information Extractor | "
    "TinyLlama + LangChain + Pydantic"
)