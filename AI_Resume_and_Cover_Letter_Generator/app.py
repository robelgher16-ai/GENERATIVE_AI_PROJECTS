import streamlit as st
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)
from reportlab.lib.units import mm

from src.generator import generate_application


# ==========================================
# Page configuration
# ==========================================

st.set_page_config(
    page_title="AI Resume & Cover Letter Generator",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==========================================
# Custom CSS
# ==========================================

st.markdown(
    """
    <style>

    /* ======================================
       Global
       ====================================== */

    .stApp {
        background:
            linear-gradient(
                135deg,
                #f8fafc 0%,
                #eef2ff 45%,
                #fdf4ff 100%
            );
    }

    .main {
        padding-top: 1.5rem;
    }


    /* ======================================
       Hero
       ====================================== */

    .hero {
        padding: 35px 30px;
        border-radius: 24px;
        background:
            linear-gradient(
                135deg,
                #4f46e5,
                #7c3aed,
                #db2777
            );
        box-shadow:
            0 15px 35px rgba(79, 70, 229, 0.25);
        text-align: center;
        margin-bottom: 30px;
    }

    .hero-title {
        color: white !important;
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 0;
    }


    /* ======================================
       Section headers
       ====================================== */

    .section-header {
        padding: 14px 20px;
        border-radius: 14px;
        background:
            linear-gradient(
                90deg,
                #4f46e5,
                #7c3aed
            );
        color: white !important;
        font-size: 22px;
        font-weight: 700;
        margin-top: 25px;
        margin-bottom: 15px;
        box-shadow:
            0 6px 15px rgba(79, 70, 229, 0.18);
    }


    /* ======================================
       Input labels
       ====================================== */

    label {
        font-weight: 700 !important;
    }


    /* ======================================
       Text areas
       ====================================== */

    textarea {
        border-radius: 14px !important;
        border: 2px solid #c7d2fe !important;
        background-color: white !important;
        color: #111827 !important;
    }

    textarea:focus {
        border: 2px solid #6366f1 !important;
        box-shadow:
            0 0 0 3px rgba(99, 102, 241, 0.15) !important;
    }


    /* ======================================
       Main Generate button
       ====================================== */

    div.stButton > button[kind="primary"] {
        background:
            linear-gradient(
                90deg,
                #4f46e5,
                #7c3aed,
                #db2777
            ) !important;

        color: white !important;

        border: none !important;
        border-radius: 14px;

        height: 55px;

        font-size: 18px;
        font-weight: 700;

        box-shadow:
            0 8px 20px rgba(79, 70, 229, 0.25);

        transition: all 0.2s ease;
    }

    div.stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);

        box-shadow:
            0 12px 25px rgba(79, 70, 229, 0.35);
    }

    div.stButton > button[kind="primary"] p {
        color: white !important;
    }


    /* ======================================
       Try Example button
       ====================================== */

    div.stButton > button[kind="secondary"] {
        background-color: white !important;

        color: black !important;

        border: 2px solid #6366f1 !important;

        border-radius: 12px;

        font-weight: 700;
    }

    div.stButton > button[kind="secondary"] p {
        color: black !important;
    }

    div.stButton > button[kind="secondary"]:hover {
        background-color: #eef2ff !important;

        color: black !important;

        border-color: #4f46e5 !important;
    }


    /* ======================================
       ALL DOWNLOAD BUTTONS
       ====================================== */

    div.stDownloadButton > button {
        background-color: white !important;

        color: black !important;

        border: 2px solid #c7d2fe !important;

        border-radius: 12px;

        font-weight: 700;

        min-height: 48px;

        transition: all 0.2s ease;
    }

    /* Force download button text to black */

    div.stDownloadButton > button p {
        color: black !important;
    }

    div.stDownloadButton > button span {
        color: black !important;
    }

    div.stDownloadButton > button div {
        color: black !important;
    }

    div.stDownloadButton > button svg {
        color: black !important;
        fill: black !important;
    }

    div.stDownloadButton > button:hover {
        border-color: #6366f1 !important;

        background-color: #eef2ff !important;

        color: black !important;
    }

    div.stDownloadButton > button:hover p {
        color: black !important;
    }


    /* ======================================
       Primary download buttons
       ====================================== */

    div.stDownloadButton > button[kind="primary"] {
        background-color: white !important;

        color: black !important;

        border: 2px solid #6366f1 !important;

        font-weight: 800;
    }

    div.stDownloadButton > button[kind="primary"] p {
        color: black !important;
    }

    div.stDownloadButton > button[kind="primary"] span {
        color: black !important;
    }

    div.stDownloadButton > button[kind="primary"] div {
        color: black !important;
    }

    div.stDownloadButton > button[kind="primary"]:hover {
        background-color: #eef2ff !important;

        color: black !important;
    }


    /* ======================================
       Result cards
       ====================================== */

    .result-card {
        background-color: white;

        padding: 25px;

        border-radius: 18px;

        border-left: 6px solid #6366f1;

        box-shadow:
            0 8px 25px rgba(15, 23, 42, 0.08);

        margin-bottom: 20px;
    }


    .skills-card {
        border-left-color: #06b6d4;
    }


    .resume-card {
        border-left-color: #4f46e5;
    }


    .cover-card {
        border-left-color: #db2777;
    }


    .improvement-card {
        border-left-color: #f59e0b;
    }


    /* ======================================
       Generated text
       ====================================== */

    .result-card p,
    .result-card li,
    .result-card h1,
    .result-card h2,
    .result-card h3,
    .result-card h4 {
        color: #111827 !important;
    }


    /* ======================================
       Alerts
       ====================================== */

    div[data-testid="stAlert"] {
        border-radius: 14px;
    }


    /* ======================================
       Sidebar
       ====================================== */

    section[data-testid="stSidebar"] {
        background:
            linear-gradient(
                180deg,
                #eef2ff 0%,
                #f5f3ff 50%,
                #fdf2f8 100%
            );
    }

    section[data-testid="stSidebar"] h2 {
        color: #4f46e5;
    }


    /* ======================================
       Expander
       ====================================== */

    div[data-testid="stExpander"] {
        background-color: white;

        border: 2px solid #c7d2fe;

        border-radius: 14px;
    }

    div[data-testid="stExpander"] summary {
        font-weight: 700;
    }


    /* ======================================
       Radio / Toggle text
       ====================================== */

    section[data-testid="stSidebar"] label {
        color: #111827 !important;
    }


    </style>
    """,
    unsafe_allow_html=True
)


# ==========================================
# Example data
# ==========================================

EXAMPLE_RESUME = """
Robel is an Information Technology student with experience in
Python, Machine Learning, Deep Learning, Git, and Streamlit.

He has built AI and machine learning projects.
"""


EXAMPLE_JOB_DESCRIPTION = """
We are looking for a Junior AI Engineer.

The candidate should have experience with Python,
Machine Learning, Deep Learning, Git, and APIs.

Responsibilities include developing AI applications,
working with machine learning models, and collaborating
with engineering teams.
"""


# ==========================================
# Demo results
# ==========================================

def get_demo_results():

    return {

        # ======================================
        # Skills Match
        # ======================================

        "skills_match": """
### Matching Skills

- Python
- Machine Learning
- Deep Learning
- Git
- Streamlit

### Missing Skills

- APIs

### Relevant Experience

The candidate has experience with Python, Machine Learning,
Deep Learning, Git, and Streamlit and has built AI and
machine learning projects.
""",

        # ======================================
        # Professional Resume
        # ======================================

        "tailored_resume": """
PROFESSIONAL SUMMARY

Information Technology student with hands-on experience in
Python, Machine Learning, Deep Learning, Git, and Streamlit.
Experienced in developing practical AI and machine learning
projects and building interactive applications. Interested in
applying AI engineering and machine learning skills to
real-world problems.


TECHNICAL SKILLS

Programming
• Python

Artificial Intelligence & Machine Learning
• Machine Learning
• Deep Learning

Development Tools
• Git
• Streamlit


PROJECT EXPERIENCE

AI & Machine Learning Projects

• Developed practical AI and machine learning projects using
  Python and machine learning technologies.

• Applied machine learning and deep learning concepts to
  practical projects.

• Built interactive applications using Streamlit.

• Used Git for project development and version control.


RELEVANT EXPERIENCE

• Developed practical experience working with Python and
  machine learning technologies.

• Built AI and machine learning applications through practical
  projects.

• Worked with Streamlit to create interactive interfaces for
  machine learning applications.

• Used Git to manage and maintain software projects.


EDUCATION

Bachelor of Science in Information Technology

Information Technology


AREAS OF INTEREST

• Artificial Intelligence
• Machine Learning
• Deep Learning
• AI Engineering
• AI Application Development
""",

        # ======================================
        # Cover Letter
        # ======================================

        "cover_letter": """
Dear Hiring Manager,

I am writing to express my interest in the Junior AI Engineer
position.

I am an Information Technology student with experience in
Python, Machine Learning, Deep Learning, Git, and Streamlit.
I have also built AI and machine learning projects that have
helped me develop practical experience in these technologies.

I am interested in applying my technical skills in an AI
engineering environment and continuing to develop my experience
through practical projects and collaboration.

Thank you for considering my application.

Sincerely,

Robel
""",

        # ======================================
        # Improvement Areas
        # ======================================

        "improvement_areas": """
### Technical Skills

Develop additional experience with APIs.

### Experience

Build more projects involving production-oriented AI systems.

### Tools / Technologies

Gain practical experience integrating APIs into AI applications.

### Other Areas

Continue developing practical AI engineering experience.
"""
    }


# ==========================================
# PDF generator
# ==========================================

def create_pdf(title, content):

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "PDFTitle",
        parent=styles["Title"],
        alignment=TA_LEFT,
        fontSize=20,
        leading=24,
        spaceAfter=15,
        textColor="#111827"
    )

    body_style = ParagraphStyle(
        "PDFBody",
        parent=styles["BodyText"],
        fontSize=10.5,
        leading=15,
        spaceAfter=7,
        textColor="#111827"
    )

    story = []

    story.append(
        Paragraph(
            title,
            title_style
        )
    )

    lines = content.split("\n")

    for line in lines:

        line = line.strip()

        if not line:

            story.append(
                Spacer(1, 5)
            )

            continue

        line = (
            line.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

        if line.startswith("### "):

            heading = line.replace(
                "### ",
                ""
            )

            story.append(
                Paragraph(
                    f"<b>{heading}</b>",
                    body_style
                )
            )

        elif line.startswith("**") and line.endswith("**"):

            heading = line[2:-2]

            story.append(
                Paragraph(
                    f"<b>{heading}</b>",
                    body_style
                )
            )

        elif line.startswith("- "):

            item = line[2:]

            story.append(
                Paragraph(
                    f"• {item}",
                    body_style
                )
            )

        elif line.startswith("• "):

            item = line[2:]

            story.append(
                Paragraph(
                    f"• {item}",
                    body_style
                )
            )

        else:

            story.append(
                Paragraph(
                    line,
                    body_style
                )
            )

    document.build(story)

    buffer.seek(0)

    return buffer.getvalue()


# ==========================================
# Hero
# ==========================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-title">
            AI Resume & Cover Letter Generator
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# ==========================================
# Sidebar
# ==========================================

with st.sidebar:

    st.header("Application Settings")

    demo_mode = st.toggle(
        "Demo Mode",
        value=False,
        help="Use sample results without calling Gemini."
    )

    st.divider()

    st.markdown("### How It Works")

    st.markdown(
        """
        **01 — Resume**

        Paste your resume.

        **02 — Job**

        Paste the job description.

        **03 — Generate**

        Let AI analyze the match.

        **04 — Review**

        Review your tailored materials.

        **05 — Download**

        Download TXT or PDF files.
        """
    )

    st.divider()

    st.info(
        "Demo Mode lets you test the interface without "
        "using your Gemini API quota."
    )


# ==========================================
# Example section
# ==========================================

with st.expander("Try an Example"):

    st.write(
        "Don't have a resume or job description ready? "
        "Load an example to test the application."
    )

    try_example = st.button(
        "Try Example",
        type="secondary",
        use_container_width=True
    )

    if try_example:

        st.session_state["resume"] = EXAMPLE_RESUME

        st.session_state[
            "job_description"
        ] = EXAMPLE_JOB_DESCRIPTION

        st.rerun()


# ==========================================
# Input section
# ==========================================

st.markdown(
    '<div class="section-header">'
    'Application Information'
    '</div>',
    unsafe_allow_html=True
)


col1, col2 = st.columns(2)


with col1:

    resume = st.text_area(
        "Your Resume",
        value=st.session_state.get(
            "resume",
            ""
        ),
        height=450,
        placeholder=(
            "Paste your complete resume here..."
        ),
        key="resume"
    )


with col2:

    job_description = st.text_area(
        "Job Description",
        value=st.session_state.get(
            "job_description",
            ""
        ),
        height=450,
        placeholder=(
            "Paste the complete job description here..."
        ),
        key="job_description"
    )


# ==========================================
# Generate button
# ==========================================

generate_button = st.button(
    "Generate Application Materials",
    type="primary",
    use_container_width=True
)


# ==========================================
# Generate application
# ==========================================

if generate_button:

    if not resume.strip():

        st.error(
            "Please enter your resume."
        )

    elif not job_description.strip():

        st.error(
            "Please enter the job description."
        )

    else:

        try:

            if demo_mode:

                with st.spinner(
                    "Loading demo results..."
                ):

                    result_data = get_demo_results()

            else:

                with st.spinner(
                    "Analyzing your resume and "
                    "job description..."
                ):

                    result_data = generate_application(
                        resume,
                        job_description
                    )

            st.session_state[
                "result_data"
            ] = result_data

            st.success(
                "Application materials generated successfully!"
            )

        except Exception as e:

            st.error(
                "The application could not generate "
                "the materials."
            )

            st.exception(e)


# ==========================================
# Display results
# ==========================================

if "result_data" in st.session_state:

    result_data = st.session_state[
        "result_data"
    ]


    # ======================================
    # Skills Match
    # ======================================

    st.markdown(
        '<div class="section-header">'
        'Skills Match'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="result-card skills-card">',
        unsafe_allow_html=True
    )

    st.markdown(
        result_data["skills_match"]
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


    # ======================================
    # Tailored Resume
    # ======================================

    st.markdown(
        '<div class="section-header">'
        'Tailored Resume'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="result-card resume-card">',
        unsafe_allow_html=True
    )

    st.text_area(
        "Generated Resume",
        value=result_data["tailored_resume"],
        height=550,
        key="generated_resume"
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


    # ======================================
    # Resume downloads
    # ======================================

    resume_col1, resume_col2 = st.columns(2)


    with resume_col1:

        st.download_button(
            label="Download Resume TXT",
            data=result_data["tailored_resume"],
            file_name="tailored_resume.txt",
            mime="text/plain",
            use_container_width=True
        )


    with resume_col2:

        resume_pdf = create_pdf(
            "Tailored Resume",
            result_data["tailored_resume"]
        )

        st.download_button(
            label="Download Resume PDF",
            data=resume_pdf,
            file_name="tailored_resume.pdf",
            mime="application/pdf",
            use_container_width=True
        )


    # ======================================
    # Cover Letter
    # ======================================

    st.markdown(
        '<div class="section-header">'
        'Cover Letter'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="result-card cover-card">',
        unsafe_allow_html=True
    )

    st.text_area(
        "Generated Cover Letter",
        value=result_data["cover_letter"],
        height=450,
        key="generated_cover_letter"
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


    # ======================================
    # Cover letter downloads
    # ======================================

    cover_col1, cover_col2 = st.columns(2)


    with cover_col1:

        st.download_button(
            label="Download Cover Letter TXT",
            data=result_data["cover_letter"],
            file_name="cover_letter.txt",
            mime="text/plain",
            use_container_width=True
        )


    with cover_col2:

        cover_pdf = create_pdf(
            "Cover Letter",
            result_data["cover_letter"]
        )

        st.download_button(
            label="Download Cover Letter PDF",
            data=cover_pdf,
            file_name="cover_letter.pdf",
            mime="application/pdf",
            use_container_width=True
        )


    # ======================================
    # Improvement Areas
    # ======================================

    st.markdown(
        '<div class="section-header">'
        'Improvement Areas'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="result-card improvement-card">',
        unsafe_allow_html=True
    )

    st.markdown(
        result_data["improvement_areas"]
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


    # ======================================
    # Complete application package
    # ======================================

    combined_result = f"""
AI RESUME & COVER LETTER GENERATOR
===================================


SKILLS MATCH
===================================

{result_data["skills_match"]}


TAILORED RESUME
===================================

{result_data["tailored_resume"]}


COVER LETTER
===================================

{result_data["cover_letter"]}


IMPROVEMENT AREAS
===================================

{result_data["improvement_areas"]}
"""


    # ======================================
    # Complete package section
    # ======================================

    st.markdown(
        '<div class="section-header">'
        'Complete Application Package'
        '</div>',
        unsafe_allow_html=True
    )


    package_col1, package_col2 = st.columns(2)


    with package_col1:

        st.download_button(
            label="Download Complete TXT",
            data=combined_result,
            file_name="application_package.txt",
            mime="text/plain",
            type="primary",
            use_container_width=True
        )


    with package_col2:

        package_pdf = create_pdf(
            "Complete Application Package",
            combined_result
        )

        st.download_button(
            label="Download Complete PDF",
            data=package_pdf,
            file_name="application_package.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )