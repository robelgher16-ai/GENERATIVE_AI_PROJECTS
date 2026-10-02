
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from pipeline import run_research_pipeline


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Multi-Agent Research Assistant API",
    description="API for the Multi-Agent Research Assistant",
    version="1.0.0"
)


# ============================================================
# REQUEST MODEL
# ============================================================

class ResearchRequest(BaseModel):
    topic: str


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
def root():

    return {
        "message": "Multi-Agent Research Assistant API is running.",
        "docs": "/docs"
    }


# ============================================================
# RESEARCH ENDPOINT
# ============================================================

@app.post("/ask")
def ask_question(request: ResearchRequest):

    topic = request.topic.strip()

    if not topic:

        raise HTTPException(
            status_code=400,
            detail="Research topic cannot be empty."
        )

    try:

        state = run_research_pipeline(topic)

        return {
            "topic": topic,
            "search_results": state.get(
                "search_results",
                ""
            ),
            "scraped_content": state.get(
                "scraped_content",
                ""
            ),
            "report": state.get(
                "report",
                ""
            ),
            "critic_feedback": state.get(
                "feedback",
                ""
            )
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
