# app/blueprints/hitlragagent/functions_for_pipeline.py

from langchain_openai import ChatOpenAI


# Replace these imports
# from langchain.vectorstores import FAISS

# With these updated imports
from langchain_community.vectorstores import FAISS


# Replace 
from langchain_openai import OpenAIEmbeddings
# from langchain_community.embeddings import OpenAIEmbeddings

from langchain.prompts import PromptTemplate
from langgraph.graph import END, StateGraph
#from langchain_core.pydantic_v1 import BaseModel, Field
from pydantic import BaseModel, Field


def create_retrievers():
    embeddings = OpenAIEmbeddings()
    chunks_vector_store = FAISS.load_local("app/blueprints/hitlragagent/vector_store/chunks_vector_store", embeddings, allow_dangerous_deserialization=True)
    chapter_summaries_vector_store = FAISS.load_local("app/blueprints/hitlragagent/vector_store/chapter_summaries_vector_store", embeddings, allow_dangerous_deserialization=True)
    book_quotes_vectorstore = FAISS.load_local("app/blueprints/hitlragagent/vector_store/book_quotes_vector_store", embeddings, allow_dangerous_deserialization=True)
    return chunks_vector_store.as_retriever(search_kwargs={"k": 1}), \
           chapter_summaries_vector_store.as_retriever(search_kwargs={"k": 1}), \
           book_quotes_vectorstore.as_retriever(search_kwargs={"k": 10})

chunks_query_retriever, chapter_summaries_query_retriever, book_quotes_query_retriever = create_retrievers()

def create_agent():
    class QualitativeRetrievalGraphState(BaseModel):
        question: str
        context: str
        relevant_context: str

    qualitative_chunks_retrieval_workflow = StateGraph(QualitativeRetrievalGraphState)
    # Define nodes, edges, and the workflow (simplified for brevity)
    qualitative_chunks_retrieval_workflow_app = qualitative_chunks_retrieval_workflow.compile()

    return qualitative_chunks_retrieval_workflow_app
