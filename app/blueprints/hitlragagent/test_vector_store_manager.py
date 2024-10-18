import unittest
import os
import logging
from vector_store_manager import VectorStoreManager, split_into_sections, preprocess_pdf_for_vectorization, create_section_summary

logging.basicConfig(level=logging.INFO)

class TestVectorStoreManager(unittest.TestCase):

    def setUp(self):
        """
        Set up resources required for the tests.
        """
        self.store_name = 'test_vector_store'
        self.pdf_path = 'app/blueprints/vector_manager/Harry_Potter_Book_1_The_Sorcerers_Stone.pdf'
        self.vector_store_manager = VectorStoreManager(self.store_name)
        
    def tearDown(self):
        """
        Clean up resources created during the tests.
        """
        store_path = os.path.join(self.vector_store_manager.store_path, 'index.faiss')
        if os.path.exists(store_path):
            os.remove(store_path)
        metadata_path = os.path.join(self.vector_store_manager.store_path, 'metadata.json')
        if os.path.exists(metadata_path):
            os.remove(metadata_path)

    def test_split_into_sections(self):
        """
        Test if the text can be split into sections based on the keywords.
        """
        sample_text = "Chapter 1 This is some content. Chapter 2 This is another content."
        sections = split_into_sections(sample_text)
        self.assertEqual(len(sections), 3)  # Should be three sections (including the split points)
        
    def test_preprocess_pdf_for_vectorization(self):
        """
        Test if the PDF is preprocessed correctly into sections.
        """
        sections = preprocess_pdf_for_vectorization(self.pdf_path)
        self.assertGreater(len(sections), 0)  # Ensure there are sections found
        
    def test_create_section_summary(self):
        """
        Test if a summary is correctly created for a given section.
        """
        sample_section = "This is the text of a section that we want to summarize."
        summary = create_section_summary(sample_section)
        self.assertIsInstance(summary, str)  # Summary should be a string
        self.assertGreater(len(summary), 0)  # Summary should not be empty

    def test_initialize_store(self):
        """
        Test if the vector store is successfully initialized.
        """
        self.vector_store_manager.initialize_store()
        self.assertTrue(os.path.exists(self.vector_store_manager.faiss_index_path))
        self.assertTrue(os.path.exists(self.vector_store_manager.metadata_path))

    def test_add_documents_from_pdf(self):
        """
        Test if documents are added correctly from the PDF to the vector store.
        """
        self.vector_store_manager.add_documents_from_pdf(self.pdf_path, max_pages=5)
        self.assertGreater(len(self.vector_store_manager.metadata['documents']), 0)

if __name__ == "__main__":
    unittest.main()
