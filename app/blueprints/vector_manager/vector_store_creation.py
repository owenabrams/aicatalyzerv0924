import os
import sys
import pickle
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from app.blueprints.hitlragagent.helper_functions import split_into_chapters, extract_book_quotes
from langchain.docstore.document import Document

# Load environment variables from a .env file
load_dotenv()

# Get OpenAI API key
openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    print("Error: OPENAI_API_KEY not found in environment variables.")
    exit(1)

def create_vector_store(documents, output_dir):
    try:
        embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        vector_store = FAISS.from_documents(documents, embeddings)
        os.makedirs(output_dir, exist_ok=True)
        vector_store.save_local(output_dir)
        
        with open(os.path.join(output_dir, "index.pkl"), "wb") as f:
            pickle.dump({"embeddings": embeddings}, f)
        print(f"Vector store created and saved at: {output_dir}")
    except Exception as e:
        print(f"An error occurred while creating the vector store for {output_dir}: {str(e)}")

def create_vector_stores(pdf_path):
    try:
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        print(f"Successfully loaded documents from {pdf_path}")
    except Exception as e:
        print(f"Error loading PDF document: {str(e)}")
        return

    create_vector_store(documents, 'app/blueprints/hitlragagent/vector_store/chunks_vector_store')
    try:
        chapter_summaries = split_into_chapters(documents)
        chapter_documents = [Document(page_content=chapter) if isinstance(chapter, str) else chapter for chapter in chapter_summaries]
        create_vector_store(chapter_documents, 'app/blueprints/hitlragagent/vector_store/chapter_summaries_vector_store')
    except Exception as e:
        print(f"An error occurred while creating chapter summaries vector store: {str(e)}")

    try:
        book_quotes = extract_book_quotes(documents)
        book_quote_documents = [Document(page_content=quote) if isinstance(quote, str) else quote for quote in book_quotes]
        create_vector_store(book_quote_documents, 'app/blueprints/hitlragagent/vector_store/book_quotes_vector_store')
    except Exception as e:
        print(f"An error occurred while creating book quotes vector store: {str(e)}")

if __name__ == "__main__":
    pdf_path = "app/blueprints/vector_manager/Harry_Potter_Book_1_The_Sorcerers_Stone.pdf"
    create_vector_stores(pdf_path)
    print("Vector stores creation process completed.")

