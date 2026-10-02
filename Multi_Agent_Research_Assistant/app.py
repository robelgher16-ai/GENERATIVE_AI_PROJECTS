
import streamlit as st
import json
from datetime import datetime

from pipeline import run_research_pipeline

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Multi-Agent Research Assistant",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    /* Main container */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }

    /* Main title */
    .main-title {
        font-size: 42px;
        font-weight: 750;
        letter-spacing: -1px;
        margin-bottom: 5px;
    }

    .subtitle {
        font-size: 18px;
        color: #6b7280;
        margin-bottom: 30px;
    }

    /* Metric cards */
    .metric-card {
        padding: 18px;
        border-radius: 12px;
        border: 1px solid rgba(128, 128, 128, 0.25);
        background: rgba(128, 128, 128, 0.05);
        text-align: center;
        min-height: 110px;
    }

    .metric-number {
        font-size: 28px;
        font-weight: 700;
    }

    .metric-label {
        font-size: 14px;
        color: #6b7280;
    }

    /* Agent cards */
    .agent-card {
        padding: 16px;
        border-radius: 12px;
        border: 1px solid rgba(128, 128, 128, 0.25);
        background: rgba(128, 128, 128, 0.04);
        min-height: 125px;
    }

    .agent-title {
        font-size: 18px;
        font-weight: 650;
    }

    .agent-description {
        font-size: 14px;
        color: #6b7280;
    }

    /* Report */
    .report-container {
        padding: 25px;
        border-radius: 14px;
        border: 1px solid rgba(128, 128, 128, 0.25);
    }

    /* Footer */
    .footer {
        text-align: center;
        color: #6b7280;
        font-size: 13px;
        padding-top: 25px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">Multi-Agent Research Assistant</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    'AI-powered research using Search, Reader, Writer, and Critic agents.'
    '</div>',
    unsafe_allow_html=True,
)

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("Research Assistant")

    st.write(
        """
        This system uses multiple AI components to transform
        a research question into a structured research report.
        """
    )

    st.divider()

    st.markdown("### Research Pipeline")

    st.markdown(
        """
        **01 — Search Agent**

        Finds relevant web sources.

        **02 — Reader Agent**

        Selects and scrapes a relevant webpage.

        **03 — Writer**

        Produces the research report.

        **04 — Critic**

        Reviews the generated report.
        """
    )

    st.divider()

    st.caption(
        "Multi-Agent Research Assistant"
    )

    st.caption(
        "Search → Reader → Writer → Critic"
    )

# ============================================================
# RESEARCH INPUT
# ============================================================

st.markdown("### Research Topic")

topic = st.text_input(
    "Enter your research question",
    placeholder="Example: What is machine learning?",
    label_visibility="collapsed",
)

# ============================================================
# RUN BUTTON
# ============================================================

run_button = st.button(
    "🔎 Start Research",
    type="primary",
    use_container_width=True,
)

# ============================================================
# RUN PIPELINE
# ============================================================

if run_button:

    if not topic.strip():

        st.warning(
            "Please enter a research topic before starting."
        )

    else:

        # Clear previous results
        st.session_state["research_state"] = None

        # ----------------------------------------------------
        # RUN PIPELINE
        # ----------------------------------------------------

        with st.spinner(
            "Running Search → Reader → Writer → Critic..."
        ):

            try:

                state = run_research_pipeline(topic)

                st.session_state["research_state"] = state
                st.session_state["research_topic"] = topic
                st.session_state["research_time"] = (
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                )

            except Exception as e:

                st.error(
                    f"Research pipeline failed: {e}"
                )

                st.stop()

# ============================================================
# DISPLAY RESULTS
# ============================================================

if st.session_state.get("research_state"):

    state = st.session_state["research_state"]

    research_topic = st.session_state.get(
        "research_topic",
        topic
    )

    research_time = st.session_state.get(
        "research_time",
        ""
    )

    # ========================================================
    # SUCCESS MESSAGE
    # ========================================================

    st.success(
        "Research pipeline completed successfully."
    )

    # ========================================================
    # RESEARCH INFORMATION
    # ========================================================

    st.markdown("### Research Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-number">4</div>
                <div class="metric-label">Pipeline Stages</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:

        search_available = (
            "search_results" in state
        )

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-number">
                    {"✓" if search_available else "—"}
                </div>
                <div class="metric-label">
                    Search Results
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:

        reader_available = (
            "scraped_content" in state
        )

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-number">
                    {"✓" if reader_available else "—"}
                </div>
                <div class="metric-label">
                    Web Content
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:

        report_available = (
            "report" in state
        )

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-number">
                    {"✓" if report_available else "—"}
                </div>
                <div class="metric-label">
                    Final Report
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")

    st.markdown(
        f"**Topic:** {research_topic}"
    )

    st.caption(
        f"Research completed: {research_time}"
    )

    # ========================================================
    # AGENT PIPELINE
    # ========================================================

    st.markdown("### Agent Pipeline")

    agent1, agent2, agent3, agent4 = st.columns(4)

    with agent1:

        st.markdown(
            """
            <div class="agent-card">
                <div class="agent-title">
                    🔎 Search Agent
                </div>
                <div class="agent-description">
                    Finds relevant web sources.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with agent2:

        st.markdown(
            """
            <div class="agent-card">
                <div class="agent-title">
                    📖 Reader Agent
                </div>
                <div class="agent-description">
                    Scrapes and reads a selected source.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with agent3:

        st.markdown(
            """
            <div class="agent-card">
                <div class="agent-title">
                    ✍️ Writer
                </div>
                <div class="agent-description">
                    Generates the research report.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with agent4:

        st.markdown(
            """
            <div class="agent-card">
                <div class="agent-title">
                    🧐 Critic
                </div>
                <div class="agent-description">
                    Reviews the generated report.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")

    # ========================================================
    # RESULTS TABS
    # ========================================================

    search_tab, reader_tab, report_tab, critic_tab = st.tabs(
        [
            "🔎 Search",
            "📖 Reader",
            "📝 Report",
            "🧐 Critic",
        ]
    )

    # ========================================================
    # SEARCH TAB
    # ========================================================

# SEARCH TAB
# ========================================================

    with search_tab:

        st.subheader("Search Results")

        if "search_results" in state:

            search_results = state["search_results"]

            # Display each search result on a separate line
            search_results = search_results.replace(
                "] [",
                "]\n\n["
            )

            st.markdown(
                search_results
            )

        else:

            st.info(
                "No search results were returned."
            )
    # ========================================================
    # READER TAB
    # ========================================================

    with reader_tab:

        st.subheader(
            "Scraped Webpage Content"
        )

        if "scraped_content" in state:

            scraped_content = state[
                "scraped_content"
            ]

            st.caption(
                f"{len(scraped_content):,} characters retrieved"
            )

            with st.expander(
                "View scraped content",
                expanded=True
            ):

                st.write(
                    scraped_content
                )

        else:

            st.info(
                "No webpage content was returned."
            )

    # ========================================================
    # REPORT TAB
    # ========================================================

    with report_tab:

        st.subheader(
            "Research Report"
        )

        if "report" in state:

            report = state["report"]

            st.markdown(
                '<div class="report-container">',
                unsafe_allow_html=True,
            )

            st.markdown(
                report
            )

            st.markdown(
                '</div>',
                unsafe_allow_html=True,
            )

            st.write("")

            # ------------------------------------------------
            # DOWNLOAD REPORT
            # ------------------------------------------------

            st.markdown(
                "### Download Research"
            )

            download_col1, download_col2, download_col3 = (
                st.columns(3)
            )

            # ------------------------------------------------
            # TXT DOWNLOAD
            # ------------------------------------------------

            with download_col1:

                st.download_button(
                    label="⬇️ Download TXT",
                    data=report,
                    file_name="research_report.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

            # ------------------------------------------------
            # MARKDOWN DOWNLOAD
            # ------------------------------------------------

            with download_col2:

                st.download_button(
                    label="⬇️ Download Markdown",
                    data=report,
                    file_name="research_report.md",
                    mime="text/markdown",
                    use_container_width=True,
                )

            # ------------------------------------------------
            # JSON DOWNLOAD
            # ------------------------------------------------

            with download_col3:

                full_research = {
                    "topic": research_topic,
                    "timestamp": research_time,
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
                    ),
                }

                json_data = json.dumps(
                    full_research,
                    indent=4,
                    ensure_ascii=False,
                )

                st.download_button(
                    label="⬇️ Download JSON",
                    data=json_data,
                    file_name="research_project.json",
                    mime="application/json",
                    use_container_width=True,
                )

        else:

            st.info(
                "No research report was generated."
            )

    # ========================================================
    # CRITIC TAB
    # ========================================================

    with critic_tab:

        st.subheader(
            "Critic Feedback"
        )

        if "feedback" in state:

            st.write(
                state["feedback"]
            )

        else:

            st.info(
                "No critic feedback was returned."
            )

    # ========================================================
    # RAW STATE
    # ========================================================

    st.divider()

    with st.expander(
        "Developer View — Pipeline State"
    ):

        st.json(
            {
                key: value
                for key, value in state.items()
            }
        )

    # ========================================================
    # NEW RESEARCH
    # ========================================================

    st.divider()

    if st.button(
        "🔄 Start New Research",
        use_container_width=True
    ):

        st.session_state["research_state"] = None
        st.session_state["research_topic"] = ""
        st.rerun()

# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
        Multi-Agent Research Assistant
        <br>
        Search → Reader → Writer → Critic
    </div>
    """,
    unsafe_allow_html=True,
)

