# ============================================================
# IMPORTS
# ============================================================
from langchain_huggingface import (
    ChatHuggingFace,
    HuggingFacePipeline
)
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
from typing import List, Optional
from langchain_core.output_parsers import PydanticOutputParser

# ===========================================================
# LOAD LOCAL MODEL
# ===========================================================
llm = HuggingFacePipeline.from_model_id(
    model_id="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    task="text-generation",
    pipeline_kwargs=dict(
        max_new_tokens=512,
        do_sample=False,
        repetition_penalty=1.03,
    ),
)

# ============================================================
# CREATE CHAT MODEL
# ============================================================
chat_model = ChatHuggingFace(
    llm=llm
)
# ============================================================
# CREATE PYDANTIC MOVIE MODEL
# ===========================================================
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
# SEND PROMPT TO LOCAL MODEL
# ============================================================
print("\nInvoking local model...")
response = chat_model.invoke(
    final_prompt
)

# ============================================================
# PARSE MODEL RESPONSE
# ============================================================
movie_data = parser.parse(
    response.content
)

# ============================================================
# DISPLAY STRUCTURED OUTPUT
# ============================================================
print(
    movie_data.model_dump_json(indent=2)
)