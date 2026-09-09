# ============================================================
# PHASE 6 — MOVIE INFORMATION EXTRACTOR
# GEMINI API + STREAMLIT
# ============================================================

# ============================================================
# IMPORTS
# ============================================================

import streamlit as st

from dotenv import load_dotenv

from langchain_core.prompts import ChatPromptTemplate

from langchain_google_genai import ChatGoogleGenerativeAI

from pydantic import BaseModel

from typing import List, Optional

from langchain_core.output_parsers import PydanticOutputParser


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Movie Information Extractor - Gemini",
    page_icon="🎬",
    layout="wide"
)


# ============================================================
# TITLE
# ============================================================

st.title("🎬 Movie Information Extractor")

st.caption(
    "Gemini API + LangChain + Pydantic + Streamlit"
)

st.divider()


# ============================================================
# CREATE GEMINI MODEL
# ============================================================

@st.cache_resource
def load_gemini_model():

    model = ChatGoogleGenerativeAI(

        model="gemini-3.5-flash",

        temperature=0

    )

    return model


# ============================================================
# PYDANTIC MOVIE MODEL
# ============================================================

class Movie(BaseModel):

    title: str

    release_year: Optional[int]

    genre: List[str]

    director: Optional[str]

    cast: List[str]

    rating: Optional[float]

    summery: str


# ============================================================
# OUTPUT PARSER
# ============================================================

parser = PydanticOutputParser(
    pydantic_object=Movie
)


# ============================================================
# PROMPT
# ============================================================

prompt = ChatPromptTemplate.from_messages([

    (
        "system",
        """
        Extract movie information from the paragraph.

        {format_instruction}
        """
    ),

    (
        "human",
        "{paragraph}"
    )

])


# ============================================================
# INPUT
# ============================================================

st.subheader("📝 Movie Paragraph")

paragraph = st.text_area(

    "Enter movie paragraph:",

    height=220,

    placeholder=(
        "Example: Inception is a 2010 science fiction "
        "film directed by Christopher Nolan..."
    )

)


# ============================================================
# EXAMPLE
# ============================================================

if st.button("💡 Use Example"):

    paragraph = """
    Inception is a 2010 science fiction action film directed by
    Christopher Nolan. The movie stars Leonardo DiCaprio,
    Joseph Gordon-Levitt, Ellen Page, Tom Hardy, and Ken Watanabe.
    It has a rating of 8.8 and follows a skilled thief who enters
    people's dreams to steal their secrets.
    """

    st.text_area(
        "Example paragraph:",
        paragraph,
        height=220
    )


# ============================================================
# EXTRACT BUTTON
# ============================================================

if st.button(
    "🎬 Extract Movie Information",
    type="primary",
    use_container_width=True
):

    if not paragraph.strip():

        st.warning(
            "⚠️ Please enter a movie paragraph."
        )

        st.stop()


    # ========================================================
    # CREATE FINAL PROMPT
    # ========================================================

    final_prompt = prompt.invoke(

        {
            "paragraph": paragraph,

            "format_instruction":
                parser.get_format_instructions()
        }

    )


    # ========================================================
    # CALL GEMINI API
    # ========================================================

    try:

        with st.spinner(
            "🤖 Calling Gemini API..."
        ):

            model = load_gemini_model()

            response = model.invoke(
                final_prompt
            )


        # ====================================================
        # PARSE RESPONSE
        # ====================================================

        movie_data = parser.parse(
            response.text
        )


        # ====================================================
        # SUCCESS
        # ====================================================

        st.success(
            "✅ Movie information extracted successfully!"
        )


        # ====================================================
        # DISPLAY
        # ====================================================

        st.divider()

        st.subheader(
            "🎬 Movie Information"
        )


        col1, col2 = st.columns(2)


        with col1:

            st.markdown("### 🎞️ Basic Information")

            st.write(
                f"**Title:** {movie_data.title}"
            )

            st.write(
                f"**Release Year:** "
                f"{movie_data.release_year}"
            )

            st.write(
                f"**Director:** "
                f"{movie_data.director}"
            )

            st.write(
                f"**Rating:** "
                f"{movie_data.rating}"
            )


        with col2:

            st.markdown("### 🎭 Details")

            st.write(
                f"**Genre:** "
                f"{', '.join(movie_data.genre)}"
            )

            st.write(
                f"**Cast:** "
                f"{', '.join(movie_data.cast)}"
            )


        # ====================================================
        # SUMMARY
        # ====================================================

        st.markdown("### 📖 Summary")

        st.info(
            movie_data.summery
        )


        # ====================================================
        # JSON
        # ====================================================

        st.markdown("### 🔹 Structured JSON")

        st.json(
            movie_data.model_dump()
        )


        # ====================================================
        # RAW RESPONSE
        # ====================================================

        with st.expander(
            "🔍 Raw Gemini Response"
        ):

            st.write(
                response.text
            )


    except Exception as e:

        st.error(
            "❌ Error while extracting movie information."
        )

        st.exception(e)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    " Gemini API Movie Information Extractor"
)