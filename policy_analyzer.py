from langchain.prompts import PromptTemplate
import requests
from datetime import datetime
from utils import load_documents, create_vector_store
import os

# Constants
API_URL = 'https://openrouter.ai/api/v1/chat/completions'

class PolicyAnalyzer:
    def __init__(self, api_key):
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://localhost:5000",
            "Content-Type": "application/json"
        }
        self.internal_db = None
        self.global_db = None
        
        # Initialize RAG prompt template
        self.analysis_template = PromptTemplate(
            input_variables=["context", "question"],
            template="""
            Context: {context}
            
            Question: {question}
            
            Analyze the given internal policy and identify any missing requirements 
            compared to the global regulations. List both:
            1. Missing policies
            2. Already implemented policies
            
            Response:"""
        )

    def query_llm(self, prompt):
        """Query the LLM through OpenRouter API"""
        try:
            payload = {
                "model": "mistralai/mistral-7b-instruct",
                "messages": [{"role": "user", "content": prompt}]
            }
            
            response = requests.post(API_URL, headers=self.headers, json=payload)
            response.raise_for_status()
            
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            print(f"Error querying LLM: {str(e)}")
            return None

    def initialize_databases(self, internal_path, global_path):
        """Initialize vector databases for both internal and global policies"""
        internal_docs = load_documents(internal_path)
        global_docs = load_documents(global_path)
        
        self.internal_db = create_vector_store(internal_docs, is_public=False)
        self.global_db = create_vector_store(global_docs, is_public=True)

    def analyze_new_policy(self, new_policy_path):
        """Analyze a new internal policy document against existing global regulations"""
        try:
            # Load and vectorize new policy
            new_policy = load_documents(new_policy_path)
            if not new_policy:
                raise ValueError("No policy document found")
            
            # Get relevant global policies
            relevant_globals = self.global_db.similarity_search(
                new_policy[0].page_content, 
                k=5
            )
            
            # Construct analysis prompt
            context = "\n".join([doc.page_content for doc in relevant_globals])
            question = f"Compare this internal policy:\n{new_policy[0].page_content}\n"
            question += "with the global regulations and identify missing requirements."
            
            formatted_prompt = self.analysis_template.format(
                context=context,
                question=question
            )
            
            # Get analysis from LLM
            llm_response = self.query_llm(formatted_prompt)
            
            return self._format_analysis_report(llm_response)
            
        except Exception as e:
            print(f"Error in policy analysis: {str(e)}")
            return None

    def _format_analysis_report(self, llm_response):
        """Format the analysis report in a structured way"""
        if not llm_response:
            return None
            
        return {
            "analysis": llm_response,
            "timestamp": datetime.now().isoformat(),
            "status": "completed"
        }