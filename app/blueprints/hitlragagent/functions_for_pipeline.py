import faiss
import json
import os
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.docstore import InMemoryDocstore
from collections import defaultdict

VECTOR_STORE_DIR = os.path.abspath('app/blueprints/hitlragagent/vector_store')

def load_vector_store(index_name, embeddings):
    # Load the FAISS index
    faiss_index_path = os.path.join(VECTOR_STORE_DIR, index_name, 'index.faiss')
    metadata_path = os.path.join(VECTOR_STORE_DIR, index_name, 'metadata.json')

    try:
        # Step 1: Load FAISS index from file
        index = faiss.read_index(faiss_index_path)

        # Step 2: Load metadata from JSON
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)


        docstore = InMemoryDocstore(documents)

        # Step 4: Create index_to_docstore_id mapping
        index_to_docstore_id = {i: str(i) for i in range(len(documents))}

        # Step 5: Create FAISS vector store using the index, embeddings, docstore, and index mapping
        vector_store = FAISS(index=index, embedding_function=embeddings, docstore=docstore, index_to_docstore_id=index_to_docstore_id)

        return vector_store

    except FileNotFoundError as e:
        raise RuntimeError(f"Error loading vector store {index_name}: {e}")

def create_retrievers():
    
    
    # Load the vector stores using the new loading method
    chunks_vector_store = load_vector_store("chunks_vector_store", embeddings)
    chapter_summaries_vector_store = load_vector_store("chapter_summaries_vector_store", embeddings)
    book_quotes_vector_store = load_vector_store("book_quotes_vector_store", embeddings)
    
    return (
        chunks_vector_store.as_retriever(search_kwargs={"k": 1}),
        chapter_summaries_vector_store.as_retriever(search_kwargs={"k": 1}),
        book_quotes_vector_store.as_retriever(search_kwargs={"k": 10})
    )

chunks_query_retriever, chapter_summaries_query_retriever, book_quotes_query_retriever = create_retrievers()
