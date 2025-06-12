import time
from utils import *
from main import initialize_system, retrieve_similar_chunks

def test_system_performance(test_queries, docs_directory):
    """
    Test system performance with multiple queries
    """
    # Initialize system
    start_time = time.time()
    public_db, private_db = initialize_system(docs_directory)
    init_time = time.time() - start_time
    
    if not (public_db and private_db):
        print("System initialization failed")
        return
    
    results = []
    for query in test_queries:
        # Measure retrieval time
        start_time = time.time()
        chunks = retrieve_similar_chunks(query, public_db)
        retrieval_time = time.time() - start_time
        
        # Get number of relevant chunks
        num_chunks = len(chunks)
        
        results.append({
            'query': query,
            'retrieval_time': retrieval_time,
            'num_chunks': num_chunks,
        })
    
    # Print performance metrics
    print(f"\nSystem Performance Metrics:")
    print(f"Initialization time: {init_time:.2f} seconds")
    print(f"\nQuery Performance:")
    for result in results:
        print(f"\nQuery: {result['query']}")
        print(f"Retrieval time: {result['retrieval_time']:.2f} seconds")
        print(f"Retrieved chunks: {result['num_chunks']}")

if __name__ == "__main__":
    # Test queries
    test_queries = [
        "What are the main security policies?",
        "How are documents processed?",
        "What is the system architecture?"
    ]
    
    # Specify your documents directory
    docs_directory = "./data/public"  # Create this directory and add PDF files
    
    # Run performance test
    test_system_performance(test_queries, docs_directory)