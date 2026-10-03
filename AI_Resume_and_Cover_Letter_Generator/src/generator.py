import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI


# ==========================================
# Load environment variables
# ==========================================

load_dotenv()


# ==========================================
# Initialize Gemini
# ==========================================

llm = ChatGoogleGenerativeAI(
    model="gemini-3.8-flash",
    timeout=60
)


# ==========================================
# Generate application materials
# ==========================================

def generate_application(resume, job_description):

    # --------------------------------------
    # Validate inputs
    # --------------------------------------

    if not resume.strip():
        raise ValueError("Resume cannot be empty.")

    if not job_description.strip():
        raise ValueError("Job description cannot be empty.")

    # --------------------------------------
    # Create AI prompt
    # --------------------------------------

    prompt = f"""
You are an expert AI career assistant specializing in resumes,
job matching, and professional cover letters.

Your task is to analyze the candidate's resume against the
job description and create application materials specifically
tailored to this job.

========================
CANDIDATE RESUME
========================

{resume}

========================
JOB DESCRIPTION
========================

{job_description}

========================
INSTRUCTIONS
========================

Analyze the candidate carefully.

Only use information that is explicitly provided in the
candidate resume.

Never invent:

- Skills
- Work experience
- Education
- Certifications
- Projects
- Achievements
- Job titles
- Years of experience

You may reorganize, summarize, and rewrite the existing
information to make it more relevant to the job.

========================
SECTION 1: SKILLS MATCH
========================

Identify:

1. Matching Skills

List the skills from the candidate's resume that directly
match the job requirements.

2. Missing Skills

List important requirements from the job description that
are not demonstrated in the candidate's resume.

3. Relevant Experience

Briefly explain which existing experience or projects are
relevant to the position.

========================
SECTION 2: TAILORED RESUME
========================

Create a concise, professional resume tailored specifically
to this job.

Use the candidate's existing information.

Prioritize information that is relevant to the job description.

Use clear sections such as:

Professional Summary
Technical Skills
Projects
Education

Do not invent information.

========================
SECTION 3: COVER LETTER
========================

Write a professional cover letter specifically for this job.

The cover letter should:

- Explain the candidate's interest in the position.
- Connect the candidate's existing skills to the job.
- Mention relevant projects or experience when appropriate.
- Show enthusiasm professionally.
- Avoid unsupported claims.
- Avoid inventing company information.
- Be concise and professional.

========================
SECTION 4: IMPROVEMENT AREAS
========================

Identify the most important areas the candidate could improve
based on the job description.

Separate them into:

Technical Skills
Experience
Tools / Technologies
Other Areas

Only identify gaps based on the provided job description.

========================
OUTPUT FORMAT
========================

Return your answer using exactly these four section headings:

=== SKILLS MATCH ===

=== TAILORED RESUME ===

=== COVER LETTER ===

=== IMPROVEMENT AREAS ===
"""

    # --------------------------------------
    # Generate response
    # --------------------------------------

    try:

        response = llm.invoke(prompt)

        # Convert response to text
        result = response.text()

        # ----------------------------------
        # Validate AI response
        # ----------------------------------

        required_sections = [
            "=== SKILLS MATCH ===",
            "=== TAILORED RESUME ===",
            "=== COVER LETTER ===",
            "=== IMPROVEMENT AREAS ==="
        ]

        for section in required_sections:

            if section not in result:
                raise ValueError(
                    f"AI response is missing section: {section}"
                )

        # ----------------------------------
        # Parse sections
        # ----------------------------------

        skills_match = result.split(
            "=== TAILORED RESUME ==="
        )[0]

        tailored_resume = result.split(
            "=== TAILORED RESUME ==="
        )[1].split(
            "=== COVER LETTER ==="
        )[0]

        cover_letter = result.split(
            "=== COVER LETTER ==="
        )[1].split(
            "=== IMPROVEMENT AREAS ==="
        )[0]

        improvement_areas = result.split(
            "=== IMPROVEMENT AREAS ==="
        )[1]

        # ----------------------------------
        # Store results
        # ----------------------------------

        result_data = {
            "skills_match": skills_match.strip(),
            "tailored_resume": tailored_resume.strip(),
            "cover_letter": cover_letter.strip(),
            "improvement_areas": improvement_areas.strip()
        }

        return result_data

    # --------------------------------------
    # Handle errors
    # --------------------------------------

    except Exception as e:

        raise RuntimeError(
            f"Failed to generate application materials: {e}"
        )