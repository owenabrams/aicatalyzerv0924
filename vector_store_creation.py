# vector_store_creation.py
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings

def create_vector_stores(pdf_path):
    try:
        # Load PDF document
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()

        # Initialize embeddings
        embeddings = OpenAIEmbeddings()

        # Create a vector store for book chunks
        chunks_vector_store = FAISS.from_documents(documents, embeddings)
        os.makedirs('vector_stores/chunks_vector_store', exist_ok=True)
        chunks_vector_store.save_local('vector_stores/chunks_vector_store')

        # Create additional vector stores for chapter summaries and book quotes if needed
        chapter_summaries_vector_store = FAISS.from_documents(documents, embeddings)
        os.makedirs('vector_stores/chapter_summaries_vector_store', exist_ok=True)
        chapter_summaries_vector_store.save_local('vector_stores/chapter_summaries_vector_store')

        # Create a vector store for book quotes
        book_quotes_vectorstore = FAISS.from_documents(documents, embeddings)
        os.makedirs('vector_stores/book_quotes_vectorstore', exist_ok=True)
        book_quotes_vectorstore.save_local('vector_stores/book_quotes_vectorstore')

    except Exception as e:
        print(f"Error loading PDF document: {e}")

if __name__ == "__main__":
    # Use the relative path to the PDF file in the vector_manager directory
    pdf_path = os.path.join(os.path.dirname(__file__), "Harry_Potter_Book_1_The_Sorcerers_Stone.pdf")
    create_vector_stores(pdf_path)
    print("Vector stores creation process completed.")
