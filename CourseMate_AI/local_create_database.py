from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
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


# 3. Local embedding model
embedding_model = OllamaEmbeddings(
    model="nomic-embed-text"
)


# 4. Chroma
vectorstore = Chroma(
    collection_name="coursemate",
    persist_directory="chroma_db",
    embedding_function=embedding_model
)

vectorstore.delete_collection()

vectorstore = Chroma(
    collection_name="coursemate",
    persist_directory="chroma_db",
    embedding_function=embedding_model
)


# 5. Add documents in batches
batch_size = 50

for i in range(0, len(chunks), batch_size):

    batch = chunks[i:i + batch_size]

    vectorstore.add_documents(batch)

    processed = min(i + batch_size, len(chunks))

    print(f"Embedded {processed}/{len(chunks)} chunks")


print()
print("Local Chroma vector database created successfully!")
print(f"Total chunks stored: {vectorstore._collection.count()}")