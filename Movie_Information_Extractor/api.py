
import os
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

load_dotenv()


app = FastAPI(
    title="Movie Information Extractor API",
    description="FastAPI backend for extracting structured movie information using Gemini.",
    version="1.0.0",
)


class Movie(BaseModel):
    title: str
    release_year: Optional[int]
    genre: List[str]
    director: Optional[str]
    cast: List[str]
    rating: Optional[float]
    summery: str


class MovieRequest(BaseModel):
    paragraph: str


parser = PydanticOutputParser(pydantic_object=Movie)

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            Extract movie information from the paragraph.

            {format_instruction}
            """,
        ),
        ("human", "{paragraph}"),
    ]
)


def load_gemini_model():
    return ChatGoogleGenerativeAI(
        model="gemini-3.5-flash",
        temperature=0,
    )


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/extract", response_model=Movie)
def extract_movie(request: MovieRequest):
    try:
        model = load_gemini_model()

        final_prompt = prompt.invoke(
            {
                "paragraph": request.paragraph,
                "format_instruction": parser.get_format_instructions(),
            }
        )

        response = model.invoke(final_prompt)

        movie_data = parser.parse(response.text)

        return movie_data

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

