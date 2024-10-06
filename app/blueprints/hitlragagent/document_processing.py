from langchain.document_loaders import PyPDFLoader
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from helper_functions import replace_t_with_space, extract_book_quotes_as_documents

def encode_book(path, chunk_size=1000, chunk_overlap=200):
    loader = PyPDFLoader(path)
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap, length_function=len
    )
    texts = text_splitter.split_documents(documents)
    cleaned_texts = replace_t_with_space(texts)
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(cleaned_texts, embeddings)
    return vectorstore

def encode_chapter_summaries(chapter_summaries):
    embeddings = OpenAIEmbeddings()
    chapter_summaries_vectorstore = FAISS.from_documents(chapter_summaries, embeddings)
    return chapter_summaries_vectorstore

def encode_quotes(book_quotes_list):
    embeddings = OpenAIEmbeddings()
    quotes_vectorstore = FAISS.from_documents(book_quotes_list, embeddings)
    return quotes_vectorstore

def load_or_create_vector_stores(pdf_path, chapters, book_quotes_list):
    if os.path.exists("chunks_vector_store") and os.path.exists("chapter_summaries_vector_store") and os.path.exists("book_quotes_vectorstore"):
        embeddings = OpenAIEmbeddings()
        chunks_vector_store = FAISS.load_local("chunks_vector_store", embeddings, allow_dangerous_deserialization=True)
        chapter_summaries_vector_store = FAISS.load_local("chapter_summaries_vector_store", embeddings, allow_dangerous_deserialization=True)
        book_quotes_vectorstore = FAISS.load_local("book_quotes_vectorstore", embeddings, allow_dangerous_deserialization=True)
    else:
        chunks_vector_store = encode_book(pdf_path)
        chapter_summaries_vector_store = encode_chapter_summaries(chapters)
        book_quotes_vectorstore = encode_quotes(book_quotes_list)
        
        chunks_vector_store.save_local("chunks_vector_store")
        chapter_summaries_vector_store.save_local("chapter_summaries_vector_store")
        book_quotes_vectorstore.save_local("book_quotes_vectorstore")

    return chunks_vector_store, chapter_summaries_vector_store, book_quotes_vectorstore
