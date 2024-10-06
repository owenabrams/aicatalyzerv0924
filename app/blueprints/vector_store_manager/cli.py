# app/vector_store_manager/cli.py

import argparse
from .manager import VectorStoreManager

def main():
    parser = argparse.ArgumentParser(description="Vector Store Management CLI")
    parser.add_argument('action', choices=['add', 'search'], help="Action to perform on the vector store")
    parser.add_argument('--documents', nargs='+', help="Documents to add to the vector store")
    parser.add_argument('--query', help="Query to search in the vector store")
    args = parser.parse_args()

    vector_manager = VectorStoreManager('chunks_vector_store')

    if args.action == 'add' and args.documents:
        vector_manager.add_documents(args.documents)
        print("Documents added successfully.")
    elif args.action == 'search' and args.query:
        results = vector_manager.search(args.query)
        print("Search results:", results)

if __name__ == '__main__':
    main()
