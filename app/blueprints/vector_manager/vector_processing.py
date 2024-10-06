# app/blueprints/vector_manager/vector_processing.py

import sys
print(sys.path)


import os

# Old imports (which need to be updated)
# from langchain.document_loaders import PyPDFLoader
# from langchain.vectorstores import FAISS
# from langchain.embeddings import OpenAIEmbeddings

# New imports (updated to langchain_community as recommended)
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings


from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.blueprints.hitlragagent.helper_functions import replace_t_with_space






import logging

VECTOR_STORE_PATH = "app/blueprints/hitlragagent/vector_store/"



def create_vector_store(pdf_path, store_type, chunk_size=1000, chunk_overlap=200):
    """
    Creates or updates a vector store based on the uploaded PDF file.

    Args:
        pdf_path (str): The path to the PDF file.
        store_type (str): The type of vector store ('chunks', 'summaries', or 'quotes').
        chunk_size (int): Size of each text chunk (for chunk-based vector stores).
        chunk_overlap (int): Overlap between consecutive text chunks.

    Returns:
        str: Status message.
    """
    try:
        # Load PDF document
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        documents = replace_t_with_space(documents)

        # Create the correct vector store
        if store_type == 'chunks':
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            texts = text_splitter.split_documents(documents)
            vector_store = FAISS.from_documents(texts, OpenAIEmbeddings())
            save_path = os.path.join(VECTOR_STORE_PATH, "chunks_vector_store")
        
        elif store_type == 'summaries':
            vector_store = FAISS.from_documents(documents, OpenAIEmbeddings())
            save_path = os.path.join(VECTOR_STORE_PATH, "chapter_summaries_vector_store")
        
        elif store_type == 'quotes':
            vector_store = FAISS.from_documents(documents, OpenAIEmbeddings())
            save_path = os.path.join(VECTOR_STORE_PATH, "book_quotes_vectorstore")
        
        else:
            raise ValueError(f"Invalid store_type: {store_type}")

        # Save the vector store
        vector_store.save_local(save_path)

        return f"Vector store '{store_type}' successfully created/updated."

    except Exception as e:
        logging.error(f"Error in creating/updating vector store: {str(e)}")
        return f"An error occurred while processing the vector store: {str(e)}"

def list_existing_stores():
    """
    Lists the existing vector stores.

    Returns:
        list: A list of existing vector store types.
    """
    existing_stores = []
    for store_type in ['chunks', 'summaries', 'quotes']:
        store_path = os.path.join(VECTOR_STORE_PATH, f"{store_type}_vector_store")
        if os.path.exists(store_path):
            existing_stores.append(store_type)
    return existing_stores
