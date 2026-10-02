from dotenv import load_dotenv

from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from tools import web_search, scrape_url

load_dotenv()

# =====================================================
# LLM (Shared by all agents)
# =====================================================

llm = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    temperature=0,
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

Your job is to:
1. Understand the user's research topic.
2. Use the web_search tool.
3. Return the most relevant search results with titles, URLs and snippets.

Always use the tool before answering.
"""
    )


# =====================================================
# AGENT 2 : READER AGENT
# Purpose : Read the selected webpage
# Tool : scrape_url
# =====================================================

def build_reader_agent():

    return create_agent(
        model=llm,
        tools=[scrape_url],
        system_prompt="""
You are a web reader agent.

Your responsibilities:
1. Read the search results.
2. Identify the most useful URL.
3. Use scrape_url to extract the article.
4. Return the cleaned article content only.

Always use scrape_url before responding.
"""
    )


# =====================================================
# AGENT 3 : WRITER AGENT
# Purpose : Write the final report
# =====================================================

writer_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are a senior academic research writer.

Create detailed, factual and professional reports.
Use only the provided research.
Do not invent facts.
"""
    ),

    (
        "human",
        """
Research Topic:
{topic}

Collected Research:
{research}

Write a complete report with:

# Introduction

# Background

# Key Findings
(Explain at least 3 findings)

# Discussion

# Conclusion

# Sources
(List every URL found)
"""
    )
])

writer_chain = writer_prompt | llm | StrOutputParser()


# =====================================================
# AGENT 4 : CRITIC AGENT
# Purpose : Review the report
# =====================================================

critic_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are an expert research reviewer.

Evaluate reports for:
- factual quality
- structure
- clarity
- completeness
- academic writing
"""
    ),

    (
        "human",
        """
Review this report carefully.

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