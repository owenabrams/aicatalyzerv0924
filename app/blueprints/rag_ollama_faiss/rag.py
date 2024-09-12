import os
import logging
import pickle
import pinecone
from typing import List



from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS, Pinecone


#
#from langchain.embeddings import LlamaEmbeddings
#from langchain_community.embeddings import LlamaEmbeddings  # If it was moved
#from langchain.embeddings.ollama import OllamaEmbeddings

from langchain_community.embeddings.ollama import OllamaEmbeddings
from langchain_community.llms import Llama  # Update this import as well


from langchain.llms import Llama

# Initialize logging
logging.basicConfig(level=logging.INFO)


class MultiDocRAGSystem:
    def __init__(self, vectorstore_path: str = "vectorstore.faiss", model_name: str = "llama3.1", chunk_size: int = 1500, chunk_overlap: int = 100, cache_dir: str = "embeddings_cache", pinecone_api_key: str = None, pinecone_index_name: str = None, use_faiss: bool = True):
        self.vectorstore_path = vectorstore_path
        self.model_name = model_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunks = []
        self.vectorstore = None
        self.llm = None
        self.cache_dir = cache_dir
        self.pinecone_api_key = pinecone_api_key
        self.pinecone_index_name = pinecone_index_name
        self.use_faiss = use_faiss
        os.makedirs(self.cache_dir, exist_ok=True)

    def load_pdfs_and_create_vector_store(self, folder_path: str):
        logging.info(f"Loading PDFs from folder: {folder_path}")
        pdf_files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]

        for file_name in pdf_files:
            pdf_path = os.path.join(folder_path, file_name)
            cache_file = os.path.join(self.cache_dir, f"{file_name}.pkl")

            if os.path.exists(cache_file):
                logging.info(f"Loading cached embeddings for {file_name}")
                with open(cache_file, 'rb') as f:
                    cached_chunks = pickle.load(f)
                    self.chunks.extend(cached_chunks)
            else:
                logging.info(f"Processing PDF: {file_name}")
                loader = PyPDFLoader(pdf_path)
                pages = loader.load()
                splitter = RecursiveCharacterTextSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)
                chunks = splitter.split_documents(pages)

                for chunk in chunks:
                    chunk.metadata['source'] = file_name

                self.chunks.extend(chunks)

                with open(cache_file, 'wb') as f:
                    pickle.dump(chunks, f)

        self.create_vector_store()

    def create_vector_store(self):
        logging.info(f"Creating/updating vector store.")
        if self.use_faiss:
            self._create_faiss_vector_store()
        else:
            self._create_pinecone_vector_store()

    def _create_faiss_vector_store(self):
        #embedding_model = LlamaEmbeddings(model_name=self.model_name)
        embedding_model = OllamaEmbeddings(model_name=self.model_name)
        try:
            if os.path.exists(self.vectorstore_path):
                self.vectorstore = FAISS.load_local(self.vectorstore_path, embedding_model)
                self.vectorstore.add_documents(self.chunks)
            else:
                self.vectorstore = FAISS.from_documents(self.chunks, embedding_model)
            self.vectorstore.save_local(self.vectorstore_path)
            logging.info(f"FAISS vector store saved at: {self.vectorstore_path}")
        except Exception as e:
            logging.error(f"Error creating FAISS vector store: {e}. Switching to Pinecone.")
            self.use_faiss = False
            self._create_pinecone_vector_store()

    def _create_pinecone_vector_store(self):
        if not self.pinecone_api_key or not self.pinecone_index_name:
            raise ValueError("Pinecone API key and index name must be provided for Pinecone vector store.")

        pinecone.init(api_key=self.pinecone_api_key, environment="us-east1-aws")
        if self.pinecone_index_name not in pinecone.list_indexes():
            logging.info(f"Creating Pinecone index: {self.pinecone_index_name}")
            pinecone.create_index(name=self.pinecone_index_name, dimension=768)
        index = pinecone.Index(self.pinecone_index_name)
        self.vectorstore = Pinecone(index=index, embedding_model=LlamaEmbeddings(model_name=self.model_name))
        self.vectorstore.add_documents(self.chunks)
        logging.info(f"Documents added to Pinecone index: {self.pinecone_index_name}")

    def load_vector_store(self):
        if self.use_faiss:
            try:
                embedding_model = LlamaEmbeddings(model_name=self.model_name)
                self.vectorstore = FAISS.load_local(self.vectorstore_path, embedding_model)
                logging.info(f"Loaded FAISS vector store from: {self.vectorstore_path}")
            except Exception as e:
                logging.error(f"Error loading FAISS vector store: {e}. Switching to Pinecone.")
                self.use_faiss = False
                self._load_pinecone_vector_store()
        else:
            self._load_pinecone_vector_store()

    def _load_pinecone_vector_store(self):
        if not self.pinecone_api_key or not self.pinecone_index_name:
            raise ValueError("Pinecone API key and index name must be provided for Pinecone vector store.")
        pinecone.init(api_key=self.pinecone_api_key, environment="us-east1-aws")
        index = pinecone.Index(self.pinecone_index_name)
        self.vectorstore = Pinecone(index=index, embedding_model=LlamaEmbeddings(model_name=self.model_name))
        logging.info(f"Loaded Pinecone vector store from index: {self.pinecone_index_name}")

    def setup_llm(self):
        logging.info(f"Initializing Llama model: {self.model_name}")
        self.llm = Llama(model_name=self.model_name)

    def query(self, question: str):
        if not self.vectorstore:
            raise ValueError("Vector store not loaded. Call load_vector_store first.")
        logging.info(f"Querying vector store with question: {question}")
        retriever = self.vectorstore.as_retriever(search_type='approximate')
        relevant_docs = retriever.get_relevant_documents(question)

        context = "\n".join([f"Source: {doc.metadata['source']}\n{doc.page_content}" for doc in relevant_docs])
        response = self.llm.generate(prompt=f"{context}\n\nQuestion: {question}\nAnswer:")
        return response
