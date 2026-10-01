
from dotenv import load_dotenv

from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    GoogleGenerativeAIEmbeddings,
)

load_dotenv()


# 1. Gemini embedding model
embedding_model = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-001"
)


# 2. Load Gemini Chroma database
vectorstore = Chroma(
    collection_name="coursemate_gemini",
    persist_directory="chroma_db",
    embedding_function=embedding_model,
)


# 3. Retriever
retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 4,
        "fetch_k": 10,
        "lambda_mult": 0.5,
    },
)


# 4. Gemini LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-3.8-flash",
    temperature=0,
)


# 5. Prompt template
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a helpful AI assistant.

Use ONLY the provided context to answer the question.

If the answer is not present in the context,
say: "I could not find the answer in the document."
""",
        ),
        (
            "human",
            """Context:

{context}

Question:

{question}
""",
        ),
    ]
)


print("Gemini RAG system created")
print("Press 0 to exit")


# 6. Question-answer loop
while True:

    query = input("You: ")

    if query == "0":
        break


    # 7. Retrieve relevant documents
    docs = retriever.invoke(query)


    # 8. Create context
    context = "\n\n".join(
        [doc.page_content for doc in docs]
    )


    # 9. Create final prompt
    final_prompt = prompt.invoke(
        {
            "context": context,
            "question": query,
        }
    )


    # 10. Generate answer using Gemini
    response = llm.invoke(final_prompt)


    # 11. Display clean answer
    print(f"\nAI: {response.text}\n")

