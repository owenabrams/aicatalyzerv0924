# app/blueprints/hitlragagent/vector_retrievers.py

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

def create_retrievers():
    # Assuming OpenAI API key is already set up in the environment
    embeddings = OpenAIEmbeddings()

    # Load vector stores
    chunks_vector_store = FAISS.load_local(
        "app/blueprints/hitlragagent/vector_store/chunks_vector_store",
        embeddings,
        allow_dangerous_deserialization=True
    )

    chapter_summaries_vector_store = FAISS.load_local(
        "app/blueprints/hitlragagent/vector_store/chapter_summaries_vector_store",
        embeddings,
        allow_dangerous_deserialization=True
    )

    book_quotes_vector_store = FAISS.load_local(
        "app/blueprints/hitlragagent/vector_store/book_quotes_vector_store",
        embeddings,
        allow_dangerous_deserialization=True
    )

    # Create retrievers
    chunks_query_retriever = chunks_vector_store.as_retriever(search_kwargs={"k": 1})
    chapter_summaries_query_retriever = chapter_summaries_vector_store.as_retriever(search_kwargs={"k": 1})
    book_quotes_query_retriever = book_quotes_vector_store.as_retriever(search_kwargs={"k": 10})

    return chunks_query_retriever, chapter_summaries_query_retriever, book_quotes_query_retriever

