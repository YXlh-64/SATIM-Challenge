from utils import load_documents, create_vector_store


def retrieve_similar_chunks(query, vectordb, k=3):
    """
    Retrieves k most similar chunks for a given query
    """
    similar_docs = vectordb.similarity_search(query, k=k)
    return similar_docs

def initialize_system(docs_directory):
    """
    Initializes the system with proper error handling
    """
    try:
        # Load documents
        docs = load_documents(docs_directory)
        if not docs:
            raise ValueError("No documents loaded")
            
        # Create public and private vector stores
        public_db = create_vector_store(docs, is_public=True)
        private_db = create_vector_store(docs, is_public=False)
        
        return public_db, private_db
    
    except Exception as e:
        print(f"Error initializing system: {str(e)}")
        return None, None

def compare_policies(internal_db, global_db):
    """
    Compares internal policies with global regulations and identifies mismatches
    Returns a list of discrepancies and missing regulations
    """
    try:
        # Get all chunks from both databases
        internal_docs = internal_db.similarity_search("policy regulation requirement", k=100)
        global_docs = global_db.similarity_search("policy regulation requirement", k=100)
        
        # Extract policy content
        internal_policies = [doc.page_content.lower() for doc in internal_docs]
        global_policies = [doc.page_content.lower() for doc in global_docs]
        
        # Find missing regulations
        missing_regulations = []
        for global_policy in global_policies:
            found = False
            for internal_policy in internal_policies:
                if any(phrase in internal_policy for phrase in global_policy.split('.')):
                    found = True
                    break
            if not found:
                missing_regulations.append(global_policy)
        
        # Generate report
        report = {
            "missing_regulations": missing_regulations,
            "total_internal_policies": len(internal_policies),
            "total_global_regulations": len(global_policies),
            "compliance_rate": (len(global_policies) - len(missing_regulations)) / len(global_policies)
        }
        
        return report
    
    except Exception as e:
        print(f"Error comparing policies: {str(e)}")
        return None

def analyze_policy_gaps():
    """
    Analyzes gaps between internal and global policies
    """
    try:
        # Initialize system with separate directories for internal and global policies
        internal_docs = load_documents("data/internal")
        global_docs = load_documents("data/global")
        
        if not internal_docs or not global_docs:
            raise ValueError("Both internal and global documents are required")
        
        # Create vector stores
        internal_db = create_vector_store(internal_docs, is_public=False)
        global_db = create_vector_store(global_docs, is_public=True)
        
        # Compare policies
        comparison_report = compare_policies(internal_db, global_db)
        
        if comparison_report:
            print("\nPolicy Comparison Report:")
            print("-" * 50)
            print(f"Total Internal Policies: {comparison_report['total_internal_policies']}")
            print(f"Total Global Regulations: {comparison_report['total_global_regulations']}")
            print(f"Compliance Rate: {comparison_report['compliance_rate']*100:.2f}%")
            
            if comparison_report['missing_regulations']:
                print("\nMissing Regulations:")
                for i, reg in enumerate(comparison_report['missing_regulations'], 1):
                    print(f"\n{i}. {reg}")
            else:
                print("\nNo missing regulations found.")
        
        return comparison_report
    
    except Exception as e:
        print(f"Error in policy analysis: {str(e)}")
        return None