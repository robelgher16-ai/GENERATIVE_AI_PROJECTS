from Agents import (
    build_search_agent,
    build_reader_agent,
    writer_chain,
    critic_chain
)


def run_research_pipeline(topic: str):

    state = {}

    # =====================================================
    # STEP 1 : SEARCH
    # =====================================================

    print("\n" + "=" * 60)
    print("STEP 1 : SEARCH AGENT")
    print("=" * 60)

    try:

        search_agent = build_search_agent()

        search_result = search_agent.invoke({
            "messages": [
                (
                    "user",
                    f"Find reliable recent information about {topic}"
                )
            ]
        })

        # Get the final response from the Search Agent
        search_content = search_result["messages"][-1].content

        # Handle Gemini content blocks
        if isinstance(search_content, list):

            search_content = "\n".join(
                item.get("text", "")
                for item in search_content
                if isinstance(item, dict)
            )

        state["search_results"] = search_content

        print(state["search_results"])

    except Exception as e:

        print(f"\nSearch Agent Error:\n{e}")
        return state


    # =====================================================
    # STEP 2 : READER
    # =====================================================

    print("\n" + "=" * 60)
    print("STEP 2 : READER AGENT")
    print("=" * 60)

    try:

        reader_agent = build_reader_agent()

        reader_result = reader_agent.invoke({
            "messages": [
                (
                    "user",
                    f"""
Choose the most relevant URL from the search results below.

You MUST use the scrape_url tool with the selected URL.

Do not answer from your own knowledge.

Return the content obtained from the webpage.

SEARCH RESULTS:

{state["search_results"]}
"""
                )
            ]
        })

        # Get the final response from the Reader Agent
        reader_content = reader_result["messages"][-1].content

        # Handle Gemini content blocks
        if isinstance(reader_content, list):

            reader_content = "\n".join(
                item.get("text", "")
                for item in reader_content
                if isinstance(item, dict)
            )

        state["scraped_content"] = reader_content

        print(state["scraped_content"][:1500])

    except Exception as e:

        print(f"\nReader Agent Error:\n{e}")
        return state


    # =====================================================
    # STEP 3 : WRITER
    # =====================================================

    print("\n" + "=" * 60)
    print("STEP 3 : WRITER")
    print("=" * 60)

    try:

        research = f"""
SEARCH RESULTS

{state["search_results"]}


SCRAPED CONTENT

{state["scraped_content"]}
"""

        state["report"] = writer_chain.invoke({
            "topic": topic,
            "research": research
        })

        print(state["report"][:1500])

    except Exception as e:

        print(f"\nWriter Error:\n{e}")
        return state


    # =====================================================
    # STEP 4 : CRITIC
    # =====================================================

    print("\n" + "=" * 60)
    print("STEP 4 : CRITIC")
    print("=" * 60)

    try:

        state["feedback"] = critic_chain.invoke({
            "report": state["report"]
        })

        print(state["feedback"])

    except Exception as e:

        print(f"\nCritic Error:\n{e}")
        return state


    # =====================================================
    # PIPELINE COMPLETE
    # =====================================================

    return state


# =====================================================
# RUN PROGRAM
# =====================================================

if __name__ == "__main__":

    topic = input("Enter research topic: ")

    run_research_pipeline(topic)