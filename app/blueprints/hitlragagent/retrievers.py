def create_retrievers(chunks_vector_store, chapter_summaries_vector_store, book_quotes_vectorstore):
    chunks_query_retriever = chunks_vector_store.as_retriever(search_kwargs={"k": 1})
    chapter_summaries_query_retriever = chapter_summaries_vector_store.as_retriever(search_kwargs={"k": 1})
    book_quotes_query_retriever = book_quotes_vectorstore.as_retriever(search_kwargs={"k": 10})
    return chunks_query_retriever, chapter_summaries_query_retriever, book_quotes_query_retriever
