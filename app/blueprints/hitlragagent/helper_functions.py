# helper_functions.py
import re
import logging
import faiss
import pickle
import os
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Set up logging
logging.basicConfig(level=logging.INFO)

# Escape quotes function
def escape_quotes(input_string):
    """
    Escapes single and double quotes in the input string.

    Args:
        input_string (str): The string to escape quotes in.

    Returns:
        str: The string with escaped quotes.
    """
    if not isinstance(input_string, str):
        raise TypeError("Input must be a string.")

    # Replace single quotes and double quotes with escaped versions
    escaped_string = input_string.replace("'", "\\'").replace('"', '\\"')
    return escaped_string

# Preprocess text function
def preprocess_text(text):
    """
    Preprocesses the input text by lowercasing, removing stopwords, and lemmatizing.

    Args:
        text (str): The input text to preprocess.

    Returns:
        str: The preprocessed text.
    """
    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words('english'))
    text = text.lower()
    text = re.sub(r'\b\w{1,2}\b', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = ' '.join(lemmatizer.lemmatize(word) for word in text.split() if word not in stop_words)
    return text

# Determine vector store type
def determine_vector_store_type(question):
    """
    Determines which vector store type to use based on the question.

    Args:
        question (str): The user's question.

    Returns:
        str: The name of the vector store type.
    """
    if "quote" in question.lower():
        return "book_quotes_vector_store"
    elif "summary" in question.lower() or "chapter" in question.lower():
        return "chapter_summaries_vector_store"
    else:
        return "chunks_vector_store"

# Load vector store function
def load_vector_store(vector_store_path):
    """
    Loads a FAISS vector store from the given path.

    Args:
        vector_store_path (str): The path to the vector store directory.

    Returns:
        FAISS: The loaded FAISS vector store.
    """
    try:
        index_path = os.path.join(vector_store_path, 'index.faiss')
        config_path = os.path.join(vector_store_path, 'index.pkl')

        if not os.path.exists(index_path) or not os.path.exists(config_path):
            raise FileNotFoundError("FAISS index or configuration file not found.")

        logging.info(f"Loading FAISS index from {index_path} and configuration from {config_path}")

        with open(config_path, 'rb') as f:
            index_config = pickle.load(f)

        index = faiss.read_index(index_path)
        vector_store = FAISS(embeddings=index_config['embeddings'], index=index)
        logging.info("FAISS vector store loaded successfully.")
        return vector_store
    except Exception as e:
        logging.error(f"Error loading FAISS vector store: {e}")
        raise



# Retrieve context per question
def retrieve_context_per_question(inputs):
    """
    Retrieves context relevant to the question from the vector store.

    Args:
        inputs (dict): A dictionary containing 'question'.

    Returns:
        dict: Updated dictionary with retrieved 'context'.
    """
    question = inputs['question']
    vector_store_type = determine_vector_store_type(question)
    vector_store_path = f"app/blueprints/hitlragagent/vector_store/{vector_store_type}"

    try:
        vector_store = load_vector_store(vector_store_path)
        embeddings = OpenAIEmbeddings()
        question_embedding = embeddings.embed_text(question)

        logging.info(f"Retrieving context for question: {question}")

        # Using similarity search to get the top 3 most similar documents
        docs = vector_store.similarity_search_by_vector(question_embedding, k=3)

        if docs:
            # Extract the text from the retrieved documents
            retrieved_context = " ".join([doc.page_content for doc in docs])
            logging.info(f"Retrieved context: {retrieved_context}")
            inputs['context'] = retrieved_context
        else:
            logging.info("No relevant context found.")
            inputs['context'] = "No relevant context found."

        return inputs
    except Exception as e:
        logging.error(f"Error retrieving context: {e}")
        inputs['context'] = ""
        return inputs


# Filter content function
def keep_only_relevant_content(inputs):
    """
    Filters the retrieved context to retain only the content relevant to the question.

    Args:
        inputs (dict): A dictionary containing 'question' and 'context'.

    Returns:
        dict: Updated dictionary with filtered 'relevant_context'.
    """
    context = inputs['context']
    question = inputs['question']

    # Placeholder for an actual implementation using an LLM or heuristic to filter content
    logging.info(f"Filtering context for relevance to the question: {question}")
    relevant_context = context  # Assuming all context is relevant for now

    inputs['relevant_context'] = relevant_context
    return inputs

# Answer question from context function
def answer_question_from_context(inputs):
    """
    Generates an answer to the question based on the relevant context.

    Args:
        inputs (dict): A dictionary containing 'question' and 'relevant_context'.

    Returns:
        dict: Updated dictionary with generated 'answer'.
    """
    relevant_context = inputs['relevant_context']
    question = inputs['question']

    # Placeholder for an actual implementation using an LLM to generate the answer
    logging.info(f"Generating answer based on relevant context: {relevant_context}")
    answer = relevant_context  # Echoing the context for now as a placeholder

    inputs['answer'] = answer
    return inputs

# helper_functions.py (updated)
# ... other imports and functions ...

def replace_t_with_space(input_string):
    """
    Replaces all occurrences of 't' with a space in the input string.

    Args:
        input_string (str): The string to modify.

    Returns:
        str: The string with 't' replaced by a space.
    """
    return input_string.replace('t', ' ')



# helper_functions.py

from langchain.docstore.document import Document

# helper_functions.py (adding missing functions)

def split_into_chapters(documents):
    """
    Splits the input documents into chapter-level sections.

    Args:
        documents (list): A list of documents to split.

    Returns:
        list: A list of chapter summaries (strings).
    """
    # Placeholder: Assume each document represents a chapter
    return [doc.page_content for doc in documents]

def extract_book_quotes(documents):
    """
    Extracts quotes from the input documents.

    Args:
        documents (list): A list of documents to extract quotes from.

    Returns:
        list: A list of quotes (strings).
    """
    # Placeholder: Extract the first sentence as a quote from each document
    quotes = []
    for doc in documents:
        sentences = doc.page_content.split(".")
        if sentences:
            quotes.append(sentences[0] + ".")
    return quotes
