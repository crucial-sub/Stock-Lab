"""Build Vector Embeddings for RAG Knowledge Base.

This script processes markdown documents and creates embeddings in ChromaDB.
Embeddings are generated using AWS Bedrock Titan via LangChain.
"""
import os
from pathlib import Path
from typing import List

try:
    from langchain_aws import BedrockEmbeddings
    from langchain_community.document_loaders import DirectoryLoader, UnstructuredMarkdownLoader
    from langchain_community.vectorstores import Chroma
    from langchain.text_splitter import RecursiveCharacterTextSplitter
except ImportError:
    print("Warning: dependencies not installed")
    print("Run: pip install -r requirements.txt")


class EmbeddingBuilder:
    """Build embeddings for markdown documents."""

    def __init__(
        self,
        docs_dir: str = "../documents",
        db_dir: str = "../vectordb/chroma",
        model_name: str = "amazon.titan-embed-text-v2:0"
    ):
        self.docs_dir = Path(docs_dir)
        self.db_dir = Path(db_dir)
        self.model_name = model_name

        # Text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

        # Bedrock client and LangChain embeddings wrapper
        region = os.getenv("AWS_REGION", "us-east-1")
        self.embeddings = BedrockEmbeddings(
            region_name=region,
            model_id=self.model_name
        )

    def load_documents(self) -> List:
        """Load all markdown documents."""
        print(f"Loading documents from {self.docs_dir}")

        loader = DirectoryLoader(
            str(self.docs_dir),
            glob="**/*.md",
            loader_cls=UnstructuredMarkdownLoader,
            show_progress=True
        )

        documents = loader.load()
        print(f"Loaded {len(documents)} documents")

        return documents

    def split_documents(self, documents: List) -> List:
        """Split documents into chunks."""
        print("Splitting documents into chunks...")

        chunks = self.text_splitter.split_documents(documents)
        print(f"Created {len(chunks)} chunks")

        return chunks

    def create_vectorstore(self, chunks: List):
        """Create ChromaDB vectorstore."""
        print(f"Creating vectorstore at {self.db_dir}")

        # Create directory if not exists
        self.db_dir.mkdir(parents=True, exist_ok=True)

        # Create vectorstore
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=str(self.db_dir),
            collection_name="quant_advisor"
        )

        print(f"Vectorstore created with {vectorstore._collection.count()} embeddings")

        return vectorstore

    def build(self):
        """Build complete embedding pipeline."""
        # Load documents
        documents = self.load_documents()

        if not documents:
            print("No documents found!")
            return

        # Split into chunks
        chunks = self.split_documents(documents)

        # Create vectorstore
        vectorstore = self.create_vectorstore(chunks)

        print("✅ Embeddings built successfully!")

        return vectorstore


def main():
    """Main entry point."""
    # Get script directory
    script_dir = Path(__file__).parent

    # Build embeddings
    builder = EmbeddingBuilder(
        docs_dir=script_dir / "../documents",
        db_dir=script_dir / "../vectordb/chroma"
    )

    builder.build()


if __name__ == "__main__":
    main()
