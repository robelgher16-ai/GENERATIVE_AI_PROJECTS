from dotenv import load_dotenv

from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from tools import web_search, scrape_url


# =====================================================
# LOAD ENVIRONMENT VARIABLES
# =====================================================

load_dotenv()


# =====================================================
# SHARED LLM
# =====================================================

llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    timeout=60
)


# =====================================================
# AGENT 1 : SEARCH AGENT
# Purpose : Search the web for reliable sources
# Tool : web_search
# =====================================================

def build_search_agent():

    return create_agent(
        model=llm,
        tools=[web_search],
        system_prompt="""
You are a professional research search agent.

Your task is to search the web for the user's research topic.

Follow these rules exactly:

1. ALWAYS use the web_search tool.
2. Use the user's research topic as the search query.
3. The web_search tool returns search results containing:
   - Title
   - URL
   - Snippet
4. After using the tool, return the search results from the tool.
5. DO NOT answer the research question yourself.
6. DO NOT replace the search results with your own explanation.
7. DO NOT summarize the search results.
8. DO NOT remove URLs.
9. DO NOT modify URLs.
10. DO NOT create URLs.
11. Preserve the Title, URL, and Snippet of each result.

Your final response MUST contain the actual URLs
returned by the web_search tool.

Always use web_search before responding.
"""
    )


# =====================================================
# AGENT 2 : READER AGENT
# Purpose : Select and scrape the best webpage
# Tool : scrape_url
# =====================================================

def build_reader_agent():

    return create_agent(
        model=llm,
        tools=[scrape_url],
        system_prompt="""
You are a professional web reader agent.

Your task is to read the most useful webpage from
the search results provided by the user.

Follow these rules exactly:

1. Read the provided search results.
2. Identify a relevant URL from the search results.
3. Select an actual URL that appears in the search results.
4. ALWAYS use the scrape_url tool with the selected URL.
5. Do not answer using your own knowledge.
6. Do not invent webpage content.
7. Do not simply repeat the search results.
8. Base your response on the content returned by scrape_url.
9. Return the useful scraped webpage content.

If a URL cannot be found in the search results,
clearly state that no usable URL was found.

Always use scrape_url before responding
when a valid URL is available.
"""
    )


# =====================================================
# AGENT 3 : WRITER
# Purpose : Create the research report
# Type : LCEL Chain
# =====================================================

writer_prompt = ChatPromptTemplate.from_messages([

    (
        "system",
        """
You are a senior academic research writer.

Create detailed, factual, and professional research reports.

Rules:

- Use only the provided research.
- Do not invent facts.
- Do not add unsupported information.
- Keep the report focused on the research topic.
- Clearly organize the information.
- Use the collected research as the primary source.
- Preserve the URLs provided in the research.
"""
    ),

    (
        "human",
        """
Research Topic:

{topic}


Collected Research:

{research}


Write a complete research report using exactly this structure:

# Introduction

Introduce the research topic and explain its importance.


# Background

Provide relevant background information supported by
the collected research.


# Key Findings

Explain at least 3 important findings from the research.


# Discussion

Discuss the important findings and information discovered
during the research.


# Conclusion

Summarize the main findings of the research.


# Sources

List the URLs found in the collected research.
Do not invent URLs.
"""
    )

])


writer_chain = writer_prompt | llm | StrOutputParser()


# =====================================================
# AGENT 4 : CRITIC
# Purpose : Review the research report
# Type : LCEL Chain
# =====================================================

critic_prompt = ChatPromptTemplate.from_messages([

    (
        "system",
        """
You are an expert academic research reviewer.

Evaluate the research report based on:

- factual quality
- structure
- clarity
- completeness
- academic writing
- source usage

Do not rewrite the entire report.

Identify specific strengths, weaknesses,
and improvements.
"""
    ),

    (
        "human",
        """
Review this research report carefully.

REPORT:

{report}


Return exactly in this format:

Score: X/10

Strengths:
- ...
- ...
- ...

Weaknesses:
- ...
- ...
- ...

Suggestions:
- ...
- ...

Final Verdict:
...
"""
    )

])


critic_chain = critic_prompt | llm | StrOutputParser()