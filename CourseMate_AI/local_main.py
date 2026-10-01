from dotenv import load_dotenv

from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama, OllamaEmbeddings

load_dotenv()


# Local embedding model
embedding_model = OllamaEmbeddings(
    model="nomic-embed-text"
)


# Load Chroma database
vectorstore = Chroma(
    collection_name="coursemate",
    persist_directory="chroma_db",
    embedding_function=embedding_model
)


# Retriever
retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 4,
        "fetch_k": 10,
        "lambda_mult": 0.5
    },
)


# Local LLM
llm = ChatOllama(
    model="qwen2.5:7b",
    temperature=0
)


# Prompt
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a helpful AI assistant.

Use ONLY the provided context to answer the question.

If the answer is not present in the context,
say: "I could not find the answer in the document."
"""
        ),
        (
            "human",
            """Context:
{context}

Question:
{question}
"""
        ),
    ]
)


print("Local RAG system created")
print("Type 0 to exit")


while True:

    query = input("You: ")

    if query == "0":
        break


    # Retrieve relevant documents
    docs = retriever.invoke(query)


    # Create context
    context = "\n\n".join(
        [doc.page_content for doc in docs]
    )


    # Create final prompt
    final_prompt = prompt.invoke(
        {
            "context": context,
            "question": query
        }
    )


    # Generate answer locally
    response = llm.invoke(final_prompt)


    print(f"\nAI: {response.content}\n")