# app/blueprints/hitlragagent/helper_functions.py

import logging
import textwrap
import pylcs
from langchain.docstore.document import Document
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from app.blueprints.hitlragagent.vector_retrievers import create_retrievers

# Create the retrievers by calling the function
chunks_query_retriever, chapter_summaries_query_retriever, book_quotes_query_retriever = create_retrievers()

def retrieve_context_per_question(state):
    """
    Retrieves relevant context for a given question. The context is retrieved from the book chunks, chapter summaries, and book quotes.
    Args:
        state: A dictionary containing the question to answer.
    """
    question = state["question"]
    
    try:
        # Use the updated `invoke` method to retrieve relevant documents
        logging.info(f"Retrieving chunks for question: {question}")
        chunks_docs = chunks_query_retriever.invoke(question)
        logging.info(f"Chunks documents retrieved: {len(chunks_docs)}")

        logging.info(f"Retrieving chapter summaries for question: {question}")
        summaries_docs = chapter_summaries_query_retriever.invoke(question)
        logging.info(f"Chapter summaries documents retrieved: {len(summaries_docs)}")

        logging.info(f"Retrieving book quotes for question: {question}")
        quotes_docs = book_quotes_query_retriever.invoke(question)
        logging.info(f"Book quotes documents retrieved: {len(quotes_docs)}")

        # Concatenate document content
        chunks_context = " ".join(doc.page_content for doc in chunks_docs)
        summaries_context = " ".join(f"{doc.page_content} (Chapter {doc.metadata.get('chapter')})" for doc in summaries_docs)
        quotes_context = " ".join(doc.page_content for doc in quotes_docs)

        all_contexts = chunks_context + summaries_context + quotes_context
        return {"context": all_contexts, "question": question}

    except Exception as e:
        logging.error(f"Error in retrieving context: {e}")
        return {"error": str(e)}




def keep_only_relevant_content(state):
    """
    Keeps only the relevant content from the retrieved documents that is relevant to the query.
    Args:
        state: A dictionary containing the question and context.
    """
    question = state["question"]
    context = state["context"]
    input_data = {"query": question, "retrieved_documents": context}

    # Placeholder for an LLM-based filtering process
    logging.info("Keeping only relevant content...")
    # Assuming a prompt template or other logic to filter relevant content
    relevant_content = "Filtered relevant content based on LLM"  # Replace with actual logic
    return {"relevant_context": relevant_content, "context": context, "question": question}

def answer_question_from_context(state):
    """
    Answers a question from a given context.
    Args:
        state: A dictionary containing the context and the question.
    """
    question = state["question"]
    context = state["relevant_context"]
    input_data = {"question": question, "context": context}

    # Placeholder for LLM to answer based on context
    logging.info("Answering question from context...")
    answer = "Generated answer from context using LLM"  # Replace with actual LLM call
    return {"answer": answer, "context": context, "question": question}

def replace_t_with_space(list_of_documents):
    """
    Replaces all tab characters ('\t') with spaces in the page content of each document.

    Args:
        list_of_documents: A list of document objects, each with a 'page_content' attribute.

    Returns:
        The modified list of documents with tab characters replaced by spaces.
    """
    for doc in list_of_documents:
        doc.page_content = doc.page_content.replace('\t', ' ')
    return list_of_documents

def escape_quotes(text):
    """
    Escapes both single and double quotes in a string.
    """
    return text.replace('"', '\\"').replace("'", "\\'")
