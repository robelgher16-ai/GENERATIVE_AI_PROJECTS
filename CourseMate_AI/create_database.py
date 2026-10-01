
# Load PDF
# Split into chunks
# Create embeddings
# Store into Chroma

from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()


# 1. Load PDF
data = PyPDFLoader("data/GRU.pdf")

docs = data.load()

print(f"Loaded {len(docs)} pages.")


# 2. Split PDF into chunks
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

chunks = splitter.split_documents(docs)

print(f"Created {len(chunks)} chunks.")


# 3. Gemini embedding model
embedding_model = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-001"
)


# 4. Chroma
vectorstore = Chroma(
    collection_name="coursemate_gemini",
    persist_directory="chroma_db",
    embedding_function=embedding_model
)


# 5. Add documents
vectorstore.add_documents(chunks)


print()
print("Vector database created successfully with Gemini embeddings!")
print(f"Total chunks stored: {vectorstore._collection.count()}")

