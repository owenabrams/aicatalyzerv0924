import faiss
import numpy as np
import os
import json
import logging
import PyPDF2
from langchain_openai import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.schema import Document
#from langchain_community.chat_models import ChatOpenAI
from langchain_openai import ChatOpenAI
from time import monotonic
from pydantic import BaseModel, Field
from typing import List, Dict
import nltk
from nltk.tokenize import sent_tokenize
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
import spacy
import nltk


# Download necessary NLTK data
nltk.download('punkt')

# Load spaCy model for named entity recognition
nlp = spacy.load("en_core_web_sm")

VECTOR_STORE_DIR = os.path.abspath('app/blueprints/hitlragagent/vector_store/')
PDF_SOURCE_PATH = os.path.abspath('app/blueprints/vector_manager/Harry_Potter_Book_1_The_Sorcerers_Stone.pdf')

class VectorStoreManager:
    def __init__(self, store_name):
        self.store_name = store_name
        self.store_path = os.path.join(VECTOR_STORE_DIR, store_name)
        self.faiss_index_path = os.path.join(self.store_path, 'index.faiss')
        self.metadata_path = os.path.join(self.store_path, 'metadata.json')
        self.embeddings_model = OpenAIEmbeddings()
        self.ensure_directory_exists(self.store_path)
        self.initialize_store()

    def ensure_directory_exists(self, path):
        if not os.path.exists(path):
            os.makedirs(path)
            logging.info(f"Created directory: {path}")

    def initialize_store(self):
        if not os.path.exists(self.faiss_index_path) or not os.path.exists(self.metadata_path):
            logging.info(f"No existing vector store found at {self.store_path}, initializing new store.")
            self.index = faiss.IndexFlatL2(1536)
            self.metadata = {'documents': []}
            self._save_store()
            logging.info(f"Initialized new vector store at {self.store_path}")
        else:
            self.load_store()

    
    def load_store(self):
        logging.info(f"Loading existing vector store from {self.store_path}")
        try:
            self.index = faiss.read_index(self.faiss_index_path)
            with open(self.metadata_path, 'r') as f:
                self.metadata = json.load(f)
            logging.info(f"Loaded existing vector store from {self.store_path}")
            
            # Ensure metadata and index count match
            if self.index.ntotal != len(self.metadata['documents']):
                logging.warning("Mismatch between FAISS index total vectors and metadata documents. Consider reinitializing the store.")

        except Exception as e:
            logging.error(f"Failed to load existing vector store: {e}")
            self.initialize_new_store()


    def initialize_new_store(self):
        logging.info(f"Reinitializing vector store at {self.store_path}")
        self.index = faiss.IndexFlatL2(1536)
        self.metadata = {'documents': []}
        self._save_store()
        logging.info(f"Reinitialized vector store at {self.store_path}")

    # Improved add_documents method
    
    def add_documents(self, documents):
        try:
            embeddings = self.embeddings_model.embed_documents(documents)
            if embeddings is None or len(embeddings) == 0:
                logging.error("Generated embeddings are empty. No documents were added.")
                return
            embeddings_matrix = np.array(embeddings).astype('float32')
            if embeddings_matrix.shape[0] > 0:
                self.index.add(embeddings_matrix)
                self.metadata['documents'].extend(documents)
                self._save_store()
                logging.info(f"Added {len(documents)} documents to the vector store.")
                logging.info(f"Total number of vectors in the store: {self.index.ntotal}")
            else:
                logging.error("Embeddings were empty. No documents were added.")
        except Exception as e:
            logging.error(f"Error in add_documents: {str(e)}")
            raise

    
    def load_and_process_pdf(self, pdf_path, max_pages=None):
        """
        Load and process the PDF into chapters, summaries, and quotes.
        Then encode the combined content into the vector store.
        """
        # Extract text from the PDF file and split it into chapters
        chapters = self.split_into_chapters(pdf_path, max_pages)

        # Preprocess chapters and generate combined content
        processed_chapters = [self.preprocess_text(chapter) for chapter in chapters]
        
        # Generate summaries for each chapter
        summaries = [self.create_chapter_summary(chapter) for chapter in processed_chapters]
        
        # Create book quotes database
        quotes_db = self.create_book_quotes_database(processed_chapters)
        quotes_content = [quote['quote'] for quote in quotes_db]

        # Create keyword-based content chunks
        keywords = ["Sorcerer's Stone", "Harry Potter", "Hogwarts", "magic"]
        keyword_chunks = self.create_keyword_chunks(processed_chapters, keywords)

        # Combine all content
        all_content = processed_chapters + summaries + quotes_content + keyword_chunks

        # Encode the combined content into the vector store
        self.encode_to_vector_store(all_content, "combined_store")

        return chapters, summaries


    def create_keyword_chunks(self, chapters, keywords, chunk_size=1000, overlap=200):
        keyword_chunks = []
        for chapter in chapters:
            for keyword in keywords:
                if keyword.lower() in chapter.lower():
                    start = max(0, chapter.lower().index(keyword.lower()) - chunk_size // 2)
                    end = min(len(chapter), start + chunk_size)
                    chunk = chapter[start:end]
                    keyword_chunks.append(f"Keyword context for '{keyword}': {chunk}")
        return keyword_chunks


    def split_into_chapters(self, pdf_path, max_pages=None):
        """
        Split the PDF into chapters based on content structure.
        Optionally limit the number of pages processed.
        """
        chapters = []
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            current_chapter = ""
            for i, page in enumerate(reader.pages):
                if max_pages is not None and i >= max_pages:
                    break
                text = page.extract_text()
                if "Chapter" in text:  # Simple chapter detection, can be improved
                    if current_chapter:
                        chapters.append(current_chapter)
                    current_chapter = text
                else:
                    current_chapter += " " + text
            if current_chapter:
                chapters.append(current_chapter)
        return chapters
    
    def process_content(self, chapters):
        """
        Process chapters to create a combined representation of each chapter,
        including its summary and relevant quotes.
        """
        summaries = [self.create_chapter_summary(chapter) for chapter in chapters]
        quotes = self.create_book_quotes_database(chapters)

        combined_content = []
        for i, (chapter, summary) in enumerate(zip(chapters, summaries)):
            chapter_quotes = [q['quote'] for q in quotes if q['chapter'] == i + 1]
            combined_content.append(
                f"Chapter {i+1}:\n{chapter}\n\nSummary:\n{summary}\n\nQuotes:\n" + "\n".join(chapter_quotes)
            )

        return combined_content


    def preprocess_text(self, text):
        """
        Clean and preprocess the text.
        """
        text = ' '.join(text.split())
        text = text.lower()
        return text

               
    def create_chapter_summary(self, chapter):
        """
        Generate an extensive summary of a chapter using a large language model.
        """
        try:
            llm = ChatOpenAI(model_name="gpt-3.5-turbo-16k")
            chain = load_summarize_chain(llm, chain_type="map_reduce")
            doc = Document(page_content=chapter)
            summary_response = chain.invoke({"input_documents": [doc]})

            # Extract the output_text if response is a dictionary
            if isinstance(summary_response, dict) and 'output_text' in summary_response:
                summary = summary_response['output_text']
            elif hasattr(summary_response, 'content'):
                summary = summary_response.content
            elif isinstance(summary_response, str):
                summary = summary_response
            else:
                raise ValueError("Unexpected summary response type: could not extract string content")

            if not summary or len(summary.strip()) == 0:
                logging.warning("Generated summary is empty or invalid.")
            return summary

        except Exception as e:
            logging.error(f"Error generating summary: {str(e)}")
            raise

    
    def create_book_quotes_database(self, chapters):
        quotes_db = []
        key_terms = ["Sorcerer's Stone", "Harry", "Voldemort", "magic", "Hogwarts"]
        for i, chapter in enumerate(chapters):
            sentences = sent_tokenize(chapter)
            for sentence in sentences:
                if len(sentence.split()) > 10 and any(term.lower() in sentence.lower() for term in key_terms):
                    quotes_db.append({"chapter": i + 1, "quote": sentence})
        return quotes_db

    
    def encode_to_vector_store(self, content, store_name):
        """
        Encode content into a vector store.
        """
        logging.info(f"Starting encoding process for {store_name}")
        
        if not content:
            logging.warning(f"No content to encode for {store_name}. Skipping.")
            return

        # Ensure all items in content are strings
        if not all(isinstance(item, str) for item in content):
            non_string_items = [item for item in content if not isinstance(item, str)]
            logging.error(f"Non-string items found in content: {non_string_items[:5]}...")
            raise ValueError("All items in content must be strings for embedding")
        
        try:
            logging.info(f"Generating embeddings for {len(content)} items")
            embeddings = self.embeddings_model.embed_documents(content)
            
            if not embeddings:
                logging.warning(f"No embeddings generated for {store_name}. Skipping.")
                return

            logging.info(f"Created {len(embeddings)} embeddings")
            logging.debug(f"Shape of first embedding: {np.array(embeddings[0]).shape}")

            index = faiss.IndexFlatL2(len(embeddings[0]))
            embeddings_matrix = np.array(embeddings).astype('float32')
            logging.info(f"Shape of embeddings matrix: {embeddings_matrix.shape}")
            
            index.add(embeddings_matrix)
            logging.info(f"Added {index.ntotal} vectors to the index")

            faiss.write_index(index, f"{store_name}.faiss")
            logging.info(f"Wrote index to {store_name}.faiss")

            with open(f"{store_name}_metadata.json", 'w') as f:
                json.dump(content, f)
            logging.info(f"Wrote metadata to {store_name}_metadata.json")

            logging.info(f"Successfully encoded {len(content)} items into {store_name}")
        except Exception as e:
            logging.error(f"Error in encode_to_vector_store for {store_name}: {str(e)}")
            logging.error(traceback.format_exc())
            raise

    def anonymize_question(self, question):
        """
        Anonymize the question by replacing named entities with variables.
        """
        doc = nlp(question)
        anonymized_question = question
        entity_map = {}
        for ent in doc.ents:
            if ent.label_ not in entity_map:
                entity_map[ent.label_] = []
            entity_map[ent.label_].append(ent.text)
            anonymized_question = anonymized_question.replace(ent.text, f"[{ent.label_}_{len(entity_map[ent.label_])}]")
        return anonymized_question, entity_map

    def generate_high_level_plan(self, anonymized_question):
        """
        Generate a high-level plan to answer the anonymized question.
        """
        llm = ChatOpenAI(model_name="gpt-3.5-turbo")
        prompt = PromptTemplate(
            input_variables=["question"],
            template="Using this accumulated context, answer the following question: {question}"
        )
        # Ensure to pass {'question': question} to the invoke method
        chain = prompt | llm
        plan = chain.invoke({"question": anonymized_question})
        return plan
    
    def de_anonymize_plan(self, plan, entity_map):
        """
        De-anonymize the plan and break it down into retrievable or answerable tasks.
        """
        # Extract the content if `plan` is an AIMessage object
        if hasattr(plan, 'content'):
            de_anonymized_plan = plan.content
        else:
            de_anonymized_plan = plan

        for entity_type, entities in entity_map.items():
            for i, entity in enumerate(entities, 1):
                de_anonymized_plan = de_anonymized_plan.replace(f"[{entity_type}_{i}]", entity)
        
        tasks = de_anonymized_plan.split('\n')
        return tasks


    def execute_task(self, task, context):
        """
        Execute a single task, either by retrieving information or answering based on context.
        """
        llm = ChatOpenAI(model_name="gpt-3.5-turbo")
        if "retrieve" in task.lower():
            search_results = self.search(task)
            source = search_results['source']
            relevant_info = search_results['results']
            distilled_info = self.distill_information(relevant_info)
            return distilled_info, source
        else:
            prompt = PromptTemplate(
                input_variables=["task", "context"],
                template="Based on this context: {context}\nAnswer this task: {task}"
            )
            chain = prompt | llm
            answer = chain.invoke({"task": task, "context": context})
            return answer, "language_model"

    def distill_information(self, information):
        """
        Distill retrieved information to the most relevant parts.
        """
        llm = ChatOpenAI(model_name="gpt-3.5-turbo")
        prompt = PromptTemplate(
            input_variables=["information"],
            template="Distill the following information to the most relevant parts:\n{information}"
        )
        chain = prompt | llm
        distilled = chain.invoke({"information": information})
        return distilled
   

    # Verification Logic
    
    def verify_content(self, content, original_context):
        """
        Verify that generated content is grounded in the original context.
        """
        llm = ChatOpenAI(model_name="gpt-3.5-turbo")
        prompt = PromptTemplate(
            input_variables=["content", "context"],
            template="Given this context: {context}\nIs the following content related and accurate? Content: {content}\nRespond with 'Mostly Verified', 'Partially Verified', or 'Not Verified'."
        )
        chain = prompt | llm
        verification = chain.invoke({"content": content, "context": original_context})
        return verification


    def re_plan_steps(self, remaining_tasks, new_information):
        """
        Re-plan remaining steps based on new information.
        """
        llm = ChatOpenAI(model_name="gpt-3.5-turbo")
        prompt = PromptTemplate(
            input_variables=["tasks", "info"],
            template="Given these remaining tasks: {tasks}\nAnd this new information: {info}\nRe-plan the steps to complete the tasks."
        )
        chain = prompt | llm
        new_plan = chain.invoke({"tasks": "\n".join(remaining_tasks), "info": new_information})
        
        # Extract the content if `new_plan` is an AIMessage object
        if hasattr(new_plan, 'content'):
            new_plan_content = new_plan.content
        else:
            new_plan_content = new_plan

        # Ensure the task is present in the remaining tasks
        return [task for task in new_plan_content.split('\n') if task in remaining_tasks or task not in new_plan_content.split('\n')]
    
    def generate_final_answer(self, accumulated_context):
        """
        Produce the final answer using accumulated context and chain-of-thought reasoning.
        """
        llm = ChatOpenAI(model_name="gpt-3.5-turbo")
        prompt = PromptTemplate(
            input_variables=["context"],
            template="Using this accumulated context: {context}\nGenerate a final answer using chain-of-thought reasoning."
        )
        chain = prompt | llm
        # Ensure that we pass the expected variable 'context' correctly
        final_answer = chain.invoke({"context": accumulated_context})
        return final_answer

    
    
            
    def answer_question(self, question):
        try:
            # Retrieve relevant context from the vector store
            search_results = self.search(question, k=20)
            vector_store_context = "\n".join(search_results['results'])
            
            # Use the language model to generate an answer based on the context
            llm = ChatOpenAI(model_name="gpt-3.5-turbo")
            prompt = PromptTemplate(
                input_variables=["context", "question"],
                template=(
                    "You are an expert on Harry Potter books. Based on the following context, answer the question. "
                    "If the context doesn't contain enough information, use your general knowledge about Harry Potter to provide a relevant answer. "
                    "Always strive to give the most accurate and comprehensive answer possible.\n\n"
                    "Context: {context}\n\nQuestion: {question}\n\nAnswer:"
                )
            )
            chain = prompt | llm
            answer = chain.invoke({"context": vector_store_context, "question": question})

            return {
                "answer": answer.content if hasattr(answer, 'content') else str(answer),
                "source": "vector_store" if search_results['source'] == "vector_store" else "language_model",
                "vector_store_used": search_results['source'] == "vector_store"
            }

        except Exception as e:
            logging.error(f"Error in answer_question: {str(e)}")
            logging.error(traceback.format_exc())
            return {
                "answer": "An error occurred while generating the answer.",
                "source": "error",
                "vector_store_used": False
            }

    def _save_store(self):
        try:
            faiss.write_index(self.index, self.faiss_index_path)
            with open(self.metadata_path, 'w') as f:
                json.dump(self.metadata, f, indent=4)
            logging.info(f"Saved vector store at {self.store_path}")
        except Exception as e:
            logging.error(f"Failed to save vector store: {e}")
            raise

    # Improved search method   
    
  
    def search(self, query, k=20):
        try:
            logging.info(f"Searching for query: {query}")

            # Generate query embedding
            query_embedding = self.embeddings_model.embed_query(query)
            query_embedding = np.array(query_embedding).astype('float32').reshape(1, -1)

            # Perform the search in the FAISS index
            distances, indices = self.index.search(query_embedding, k)

            # Extract and process the search results
            results = []
            for i in indices[0]:
                if 0 <= i < len(self.metadata['documents']):
                    result = self.metadata['documents'][i]
                    if result not in results:  # Avoid duplicates
                        results.append(result)

            # Sort results by relevance (you might need to implement a relevance scoring function)
            results = self.sort_by_relevance(results, query)

            logging.info(f"Returning {len(results)} valid results from vector store")
            return {"source": "vector_store", "results": results}

        except Exception as e:
            logging.error(f"Error in search: {str(e)}")
            logging.error(traceback.format_exc())
            return {"source": "language_model", "results": ["An error occurred during the search process."]}

    def sort_by_relevance(self, results, query):
        # Implement a simple relevance scoring based on keyword matching
        def relevance_score(result):
            return sum(query.lower().count(word.lower()) for word in result.split())

        return sorted(results, key=relevance_score, reverse=True)
    

    # Helper function to get vector store answer (needs implementation)
    def get_vector_store_answer(self, question):
        search_results = self.search(question, k=5)
        vector_store_context = "\n".join(search_results['results'])
        
        if search_results['source'] == "vector_store":
            return {
                "answer": vector_store_context,
                "context": vector_store_context,
                "confidence": 0.8  # Placeholder confidence score (implement actual scoring logic)
            }
        else:
            return {
                "answer": "No relevant information found.",
                "context": "",
                "confidence": 0.0
            }

    # Helper function to get LLM answer (needs implementation)
    def get_llm_answer(self, question, context):
        llm = ChatOpenAI(model_name="gpt-3.5-turbo")
        prompt = PromptTemplate(
            input_variables=["context", "question"],
            template="Based on the following context from the Harry Potter books, answer the question. "
                    "If the context doesn't contain enough information, say so.\n\nContext: {context}\n\nQuestion: {question}\n\nAnswer:"
        )
        chain = prompt | llm
        return chain.invoke({"context": context, "question": question})




    def summarize_query(self, query):
        """
        Use the language model to summarize the query.
        """
        llm = ChatOpenAI(model_name="gpt-3.5-turbo")
        prompt = PromptTemplate(
            input_variables=["query"],
            template="Summarize the main topics of the following query: {query}"
        )
        chain = prompt | llm
        summarized_query = chain.invoke({"query": query})
        return summarized_query if isinstance(summarized_query, str) and summarized_query.strip() else query


# Usage example
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    vector_manager = VectorStoreManager('enhanced_vector_store')
    
    try:
        # Process the PDF with a limit of 100 pages for testing
        chapters, summaries = vector_manager.load_and_process_pdf(PDF_SOURCE_PATH, max_pages=110)
        
        print(f"Processed {len(chapters)} chapters from the first 50 pages.")

        # Create book quotes database
        quotes_db = vector_manager.create_book_quotes_database(chapters)
        
        # Extract just the quotes text from quotes_db
        quotes_content = [quote['quote'] for quote in quotes_db]

        # Encode content into vector stores
        vector_manager.encode_to_vector_store(chapters, "chapters_store")
        vector_manager.encode_to_vector_store(summaries, "summaries_store")
        vector_manager.encode_to_vector_store(quotes_content, "quotes_store")

        # Add quotes to the vector store
        vector_manager.add_documents(quotes_content)

        # Test search functionality
        query = "Sorcerer's Stone"
        results = vector_manager.search(query)
        logging.info(f"Search results for '{query}':")
        logging.info(results)
        
        # Example question answering
        question = "What is the significance of the Sorcerer's Stone in the story?"
        answer = vector_manager.answer_question(question)
        logging.info(f"\nQuestion: {question}")
        logging.info(f"Answer: {answer}")
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")

