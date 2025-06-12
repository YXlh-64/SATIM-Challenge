# utils.py

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import os
from dotenv import load_dotenv
import re

load_dotenv()

def load_documents(directory):
    """
    Loads PDF documents from the specified directory
    Returns a list of Document objects
    """
    docs = []
    for fname in os.listdir(directory):
        if fname.endswith(".pdf"):
            try:
                loader = PyPDFLoader(os.path.join(directory, fname))
                docs.extend(loader.load())
                print(f"Successfully loaded: {fname}")
            except Exception as e:
                print(f"Error loading {fname}: {str(e)}")
    
    if not docs:
        print("No PDF documents found in the directory")
    
    return docs

def preprocess_text(text):
    """
    Preprocesses the text by:
    - Converting to lowercase
    - Removing extra whitespace
    - Basic cleaning
    """
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters (keeping alphanumeric and basic punctuation)
    text = re.sub(r'[^a-zA-Z0-9\s.,!?-]', '', text)
    
    return text.strip()

def chunk_and_embed(docs, db_name):
    """
    Chunks documents and creates embeddings using free HuggingFace model
    """
    try:
        splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=100)
        split_docs = splitter.split_documents(docs)
        
        if not split_docs:
            raise ValueError("No documents to embed after splitting")

        # Replace OpenAI with HuggingFace embeddings
        model_name = "all-MiniLM-L6-v2"
        embeddings = HuggingFaceEmbeddings(model_name=model_name)
        
        vectordb = FAISS.from_documents(split_docs, embeddings)
        vectordb.save_local(f"vectorstores/{db_name}")
        return vectordb
    except Exception as e:
        raise Exception(f"Error in chunking and embedding: {str(e)}")

def create_vector_store(docs, is_public=True):
    """
    Creates either a public or private vector store
    """
    db_name = "public_db" if is_public else "private_db"
    
    # Create directory if it doesn't exist
    os.makedirs("vectorstores", exist_ok=True)
    
    return chunk_and_embed(docs, db_name)