# app/vector_store_manager/manager.py

import faiss
import numpy as np
import os
import pickle
from langchain_openai import OpenAIEmbeddings

VECTOR_STORE_DIR = 'hitlragagent/vector_stores/'  # Define the location of vector stores

class VectorStoreManager:
    def __init__(self, store_name):
        self.store_path = os.path.join(VECTOR_STORE_DIR, store_name)
        self.faiss_index_path = os.path.join(self.store_path, 'index.faiss')
        self.metadata_path = os.path.join(self.store_path, 'index.pkl')
        self.embeddings_model = OpenAIEmbeddings()
        self.load_or_initialize_store()

    def load_or_initialize_store(self):
        if not os.path.exists(self.store_path):
            os.makedirs(self.store_path)

        if os.path.exists(self.faiss_index_path) and os.path.exists(self.metadata_path):
            self.index = faiss.read_index(self.faiss_index_path)
            with open(self.metadata_path, 'rb') as f:
                self.metadata = pickle.load(f)
        else:
            self.index = faiss.IndexFlatL2(512)  # Example with 512 dimensions, adjust as needed
            self.metadata = {'documents': []}

    def add_documents(self, documents):
        embeddings = [self.embeddings_model.embed_text(doc) for doc in documents]
        embeddings_matrix = np.array(embeddings).astype('float32')
        self.index.add(embeddings_matrix)
        self.metadata['documents'].extend(documents)
        self._save_store()

    def delete_document(self, document_id):
        # Implement deletion logic based on the document ID and update index/metadata
        pass

    def _save_store(self):
        faiss.write_index(self.index, self.faiss_index_path)
        with open(self.metadata_path, 'wb') as f:
            pickle.dump(self.metadata, f)

    def search(self, query, k=5):
        query_embedding = np.array([self.embeddings_model.embed_text(query)]).astype('float32')
        _, indices = self.index.search(query_embedding, k)
        return [self.metadata['documents'][i] for i in indices[0]]

# Usage example
if __name__ == '__main__':
    vector_manager = VectorStoreManager('chunks_vector_store')
    vector_manager.add_documents(["New document to be added to the vector store."])
    results = vector_manager.search("document")
    print(results)
