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


# --------------------------------------------------
# Configuration
# --------------------------------------------------

PDF_PATH = "data/GRU.pdf"

COLLECTION_NAME = "coursemate_gemini"

CHROMA_DIR = "chroma_db"

BATCH_SIZE = 50


# --------------------------------------------------
# 1. Gemini embedding model
# --------------------------------------------------

embedding_model = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-001"
)


# --------------------------------------------------
# 2. Chroma
# --------------------------------------------------

vectorstore = Chroma(
    collection_name=COLLECTION_NAME,
    persist_directory=CHROMA_DIR,
    embedding_function=embedding_model,
)


# --------------------------------------------------
# 3. Check existing database
# --------------------------------------------------

existing_count = vectorstore._collection.count()

if existing_count > 0:

    print(
        f"Chroma already contains {existing_count} chunks."
    )

    print(
        "Skipping database creation."
    )

    exit()


# --------------------------------------------------
# 4. Load PDF
# --------------------------------------------------

data = PyPDFLoader(
    PDF_PATH
)

docs = data.load()

print(
    f"Loaded {len(docs)} pages."
)


# --------------------------------------------------
# 5. Split PDF into chunks
# --------------------------------------------------

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)

chunks = splitter.split_documents(
    docs
)

print(
    f"Created {len(chunks)} chunks."
)


# --------------------------------------------------
# 6. Add documents in batches
# --------------------------------------------------

for i in range(
    0,
    len(chunks),
    BATCH_SIZE,
):

    batch = chunks[
        i:i + BATCH_SIZE
    ]

    vectorstore.add_documents(
        batch
    )

    processed = min(
        i + BATCH_SIZE,
        len(chunks),
    )

    print(
        f"Embedded {processed}/{len(chunks)} chunks"
    )


# --------------------------------------------------
# 7. Finished
# --------------------------------------------------

print()

print(
    "Vector database created successfully "
    "with Gemini embeddings!"
)

print(
    f"Total chunks stored: "
    f"{vectorstore._collection.count()}"
)