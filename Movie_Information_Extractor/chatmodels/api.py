# ============================================================
# IMPORTS
# ============================================================
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
# CREATE GEMINI MODEL
# ============================================================
model = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash",
    temperature=0
)

# ============================================================
# CREATE PYDANTIC MOVIE MODEL
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
# CREATE PYDANTIC OUTPUT PARSER
# ============================================================
parser = PydanticOutputParser(
    pydantic_object=Movie
)

# ============================================================
# CREATE PROMPT TEMPLATE
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
# GET MOVIE PARAGRAPH
# ============================================================
para = input("Give your paragraph:- ")

# ============================================================
# CREATE FINAL PROMPT
# ============================================================
final_prompt = prompt.invoke(
    {
        "paragraph": para,

        "format_instruction":
            parser.get_format_instructions()
    }
)

# ============================================================
# SEND PROMPT TO GEMINI
# ============================================================
response = model.invoke(final_prompt)

# ============================================================
# PARSE MODEL RESPONSE
# ============================================================
movie_data = parser.parse(response.text)


# ============================================================
# DISPLAY STRUCTURED OUTPUT
# ============================================================
print(movie_data.model_dump_json(indent=2))