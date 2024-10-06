# app/blueprints/vector_manager/frontend.py

import streamlit as st
import requests

API_BASE_URL = "http://localhost:5000/vector_manager"

def main():
    st.title("Vector Store Manager")

    st.header("Upload PDF and Create/Update Vector Store")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    store_type = st.selectbox("Select Store Type", ["chunks", "summaries", "quotes"])

    if st.button("Upload and Process"):
        if uploaded_file and store_type:
            files = {'pdf': uploaded_file.getvalue()}
            data = {'store_type': store_type}
            response = requests.post(f"{API_BASE_URL}/upload_pdf", files=files, data=data)

            if response.status_code == 200:
                st.success(response.json().get("message"))
            else:
                st.error(response.json().get("error"))
        else:
            st.warning("Please select a file and store type.")

    st.header("List Existing Vector Stores")
    if st.button("List Stores"):
        response = requests.get(f"{API_BASE_URL}/list_stores")

        if response.status_code == 200:
            stores = response.json().get("existing_stores", [])
            if stores:
                st.write(f"Existing Stores: {', '.join(stores)}")
            else:
                st.write("No vector stores found.")
        else:
            st.error(response.json().get("error"))

if __name__ == "__main__":
    main()
