import tempfile
from pyvis.network import Network
import streamlit as st
import streamlit.components.v1 as components
from document_processing import load_or_create_vector_stores
from retrievers import create_retrievers
from functions_for_pipeline import *  # This includes all the helper functions and workflow functions from the notebook
import os

# Load vector stores or create if not existing
pdf_path = "Harry_Potter_Book_1_The_Sorcerers_Stone.pdf"

# Assuming chapters and book quotes are already preprocessed (as in the notebook)
chapters = split_into_chapters(pdf_path)
chapters = replace_t_with_space(chapters)
loader = PyPDFLoader(pdf_path)
document = loader.load()
document_cleaned = replace_t_with_space(document)
book_quotes_list = extract_book_quotes_as_documents(document_cleaned)

chunks_vector_store, chapter_summaries_vector_store, book_quotes_vectorstore = load_or_create_vector_stores(pdf_path, chapters, book_quotes_list)

# Create retrievers from vector stores
chunks_query_retriever, chapter_summaries_query_retriever, book_quotes_query_retriever = create_retrievers(
    chunks_vector_store, chapter_summaries_vector_store, book_quotes_vectorstore
)


def create_network_graph(current_state):
    net = Network(directed=True, notebook=True, height="250px", width="100%")
    net.toggle_physics(False)

    nodes = [
        {"id": "anonymize_question", "label": "anonymize_question", "x": 0, "y": 0},
        {"id": "planner", "label": "planner", "x": 175*1.75, "y": -100},
        {"id": "de_anonymize_plan", "label": "de_anonymize_plan", "x": 350*1.75, "y": -100},
        {"id": "break_down_plan", "label": "break_down_plan", "x": 525*1.75, "y": -100},
        {"id": "task_handler", "label": "task_handler", "x": 700*1.75, "y": 0},
        {"id": "retrieve_chunks", "label": "retrieve_chunks", "x": 875*1.75, "y": +200},
        {"id": "retrieve_summaries", "label": "retrieve_summaries", "x": 875*1.75, "y": +100},
        {"id": "retrieve_book_quotes", "label": "retrieve_book_quotes", "x": 875*1.75, "y": 0},
        {"id": "answer", "label": "answer", "x": 875*1.75, "y": -100},
        {"id": "replan", "label": "replan", "x": 1050*1.75, "y": 0},
        {"id": "can_be_answered_already", "label": "can_be_answered_already", "x": 1225*1.75, "y": 0},
        {"id": "get_final_answer", "label": "get_final_answer", "x": 1400*1.75, "y": 0}
    ]

    edges = [
        ("anonymize_question", "planner"),
        ("planner", "de_anonymize_plan"),
        ("de_anonymize_plan", "break_down_plan"),
        ("break_down_plan", "task_handler"),
        ("task_handler", "retrieve_chunks"),
        ("task_handler", "retrieve_summaries"),
        ("task_handler", "retrieve_book_quotes"),
        ("task_handler", "answer"),
        ("retrieve_chunks", "replan"),
        ("retrieve_summaries", "replan"),
        ("retrieve_book_quotes", "replan"),
        ("answer", "replan"),
        ("replan", "can_be_answered_already"),
        ("replan", "break_down_plan"),
        ("can_be_answered_already", "get_final_answer")
    ]
    
    # Add nodes with conditional coloring
    for node in nodes:
        color = "#00FF00" if node["id"] == current_state else "#FF69B4"  # Green if current, else pink
        net.add_node(node["id"], label=node["label"], x=node["x"], y=node["y"], color=color, physics=False, font={'size': 22})
    
    # Add edges with a default color
    for edge in edges:
        net.add_edge(edge[0], edge[1], color="#808080")  # Set edge color to gray
    
    net.options.edges.smooth.type = "straight"
    net.options.edges.width = 1.5
    
    return net


def save_and_display_graph(net):
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".html") as tmp_file:
        net.write_html(tmp_file.name, notebook=True)
        tmp_file.flush()
        with open(tmp_file.name, "r", encoding="utf-8") as f:
            return f.read()


def update_placeholders_and_graph(agent_state_value, placeholders, graph_placeholder, previous_values, previous_state):
    current_state = agent_state_value.get("curr_state")

    if current_state:
        net = create_network_graph(current_state)
        graph_html = save_and_display_graph(net)
        graph_placeholder.empty()
        with graph_placeholder.container():
            components.html(graph_html, height=400, scrolling=True)

    if current_state != previous_state and previous_state is not None:
        for key, placeholder in placeholders.items():
            if key in previous_values and previous_values[key] is not None:
                if isinstance(previous_values[key], list):
                    formatted_value = "\n".join([f"{i+1}. {item}" for i, item in enumerate(previous_values[key])])
                else:
                    formatted_value = previous_values[key]
                placeholder.markdown(f"{formatted_value}")

    for key in placeholders:
        if key in agent_state_value:
            previous_values[key] = agent_state_value[key]

    return previous_values, current_state


def execute_plan_and_print_steps(inputs, plan_and_execute_app, placeholders, graph_placeholder, recursion_limit=25):
    config = {"recursion_limit": recursion_limit}
    agent_state_value = None
    progress_bar = st.progress(0)
    step = 0
    previous_state = None
    previous_values = {key: None for key in placeholders}

    try:
        for plan_output in plan_and_execute_app.stream(inputs, config=config):
            step += 1
            for _, agent_state_value in plan_output.items():
                previous_values, previous_state = update_placeholders_and_graph(
                    agent_state_value, placeholders, graph_placeholder, previous_values, previous_state
                )
                progress_bar.progress(step / recursion_limit)
                if step >= recursion_limit:
                    break

        for key, placeholder in placeholders.items():
            if key in previous_values and previous_values[key] is not None:
                if isinstance(previous_values[key], list):
                    formatted_value = "\n".join([f"{i+1}. {item}" for i, item in enumerate(previous_values[key])])
                else:
                    formatted_value = previous_values[key]
                placeholder.markdown(f"{formatted_value}")

        response = agent_state_value.get('response', "No response found.") if agent_state_value else "No response found."
    except Exception as e:
        response = f"An error occurred: {str(e)}"
        st.error(f"Error: {e}")

    return response


def main():
    st.set_page_config(layout="wide")
    st.title("Real-Time Agent Execution Visualization")

    # Assuming the agent is already created as described in the notebook
    from agent_workflow import plan_and_execute_app

    question = st.text_input("Enter your question:", "what is the class that the professor who helped the villain is teaching?")

    if st.button("Run Agent"):
        inputs = {"question": question}
        
        # Create a row for the graph
        st.markdown("**Graph**")
        graph_placeholder = st.empty()

        # Create three columns for the other variables
        col1, col2, col3 = st.columns([1, 1, 4])
        
        with col1:
            st.markdown("**Plan**")
        with col2:
            st.markdown("**Past Steps**")
        with col3:
            st.markdown("**Aggregated Context**")

        # Initialize placeholders for each column
        placeholders = {
            "plan": col1.empty(),
            "past_steps": col2.empty(),
            "aggregated_context": col3.empty(),
        }

        response = execute_plan_and_print_steps(inputs, plan_and_execute_app, placeholders, graph_placeholder, recursion_limit=45)
        st.write("Final Answer:")
        st.write(response)


if __name__ == "__main__":
    main()
# app/blueprints/hitlragagent/simulate_agent.py

from .functions_for_pipeline import create_agent
from .helper_functions import text_wrap

def execute_agent(inputs, plan_and_execute_app, recursion_limit=25):
    try:
        for plan_output in plan_and_execute_app.stream(inputs, config={"recursion_limit": recursion_limit}):
            for _, agent_state_value in plan_output.items():
                pass  # Simulate agent processing (simplified for brevity)
        response = agent_state_value.get('response', "No response found.")
    except Exception as e:
        response = f"An error occurred: {str(e)}"
    return response
