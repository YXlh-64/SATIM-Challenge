from langchain.prompts import PromptTemplate
import requests
from datetime import datetime
from utils import load_documents, create_vector_store
import os
from langchain.document_loaders import PyPDFLoader

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
        
        # Initialize RAG prompt templates for both languages
        self.analysis_templates = {
            'en': PromptTemplate(
                input_variables=["context", "question"],
                template="""
                You are a policy compliance analyzer. Your task is to analyze internal policies against global regulations.
                Please provide your analysis in English.

                Context: {context}
                
                Question: {question}
                
                Analyze the given internal policy and provide a comprehensive analysis with the following sections:
                1. Missing Policies
                   - List all policies that are missing compared to global regulations
                   - Explain why each missing policy is important
                
                2. Implemented Policies
                   - List all policies that are already properly implemented
                   - Highlight any particularly strong implementations
                
                3. Suggestions for Improvement
                   - Provide specific recommendations for implementing missing policies
                   - Suggest ways to enhance existing policies
                   - Include best practices and implementation strategies
                   - Prioritize suggestions based on importance and feasibility
                
                Format your response in English with clear sections, bullet points, and sub-bullets where appropriate.
                Be specific, detailed, and actionable in your analysis and suggestions.
                
                Response:"""
            ),
            'fr': PromptTemplate(
                input_variables=["context", "question"],
                template="""
                Vous êtes un analyseur de conformité des politiques. Votre tâche est d'analyser les politiques internes par rapport aux réglementations globales.
                Veuillez fournir votre analyse en français.

                Contexte: {context}
                
                Question: {question}
                
                Analysez la politique interne donnée et fournissez une analyse complète avec les sections suivantes:
                1. Politiques Manquantes
                   - Listez toutes les politiques manquantes par rapport aux réglementations globales
                   - Expliquez pourquoi chaque politique manquante est importante
                
                2. Politiques Implémentées
                   - Listez toutes les politiques déjà correctement mises en œuvre
                   - Mettez en évidence les implémentations particulièrement solides
                
                3. Suggestions d'Amélioration
                   - Fournissez des recommandations spécifiques pour l'implémentation des politiques manquantes
                   - Suggérez des moyens d'améliorer les politiques existantes
                   - Incluez les meilleures pratiques et les stratégies d'implémentation
                   - Priorisez les suggestions en fonction de l'importance et de la faisabilité
                
                Formatez votre réponse en français avec des sections claires, des points à puces et des sous-points si nécessaire.
                Soyez spécifique, détaillé et concret dans votre analyse et vos suggestions.
                
                Réponse:"""
            )
        }

    def query_llm(self, prompt, language='en'):
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

    def analyze_new_policy(self, new_policy_path, language='en'):
        """Analyze a new internal policy document against existing global regulations"""
        try:
            # Load single policy document
            try:
                loader = PyPDFLoader(new_policy_path)
                new_policy = loader.load()
                if not new_policy:
                    raise ValueError("No policy document found")
            except Exception as e:
                print(f"Error loading policy document: {str(e)}")
                return None
            
            # Get relevant global policies
            relevant_globals = self.global_db.similarity_search(
                new_policy[0].page_content, 
                k=5
            )
            
            # Construct analysis prompt
            context = "\n".join([doc.page_content for doc in relevant_globals])
            question = f"Compare this internal policy:\n{new_policy[0].page_content}\n"
            question += "with the global regulations and identify missing requirements."
            
            formatted_prompt = self.analysis_templates[language].format(
                context=context,
                question=question
            )
            
            # Get analysis from LLM
            llm_response = self.query_llm(formatted_prompt, language)
            
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

    def analyze_new_policy_from_text(self, policy_text, language='en'):
        """Analyze a new internal policy from text input against existing global regulations
        
        Args:
            policy_text (str): The text content of the policy to analyze
            language (str): The language for the analysis ('en' or 'fr')
            
        Returns:
            dict: Analysis report containing the comparison results
        """
        try:
            if not policy_text:  # Only check for empty/None input
                return None
                
            # Get relevant global policies
            relevant_globals = self.global_db.similarity_search(
                policy_text, 
                k=5
            )
            
            # Construct analysis prompt
            context = "\n".join([doc.page_content for doc in relevant_globals])
            question = f"Compare this internal policy:\n{policy_text}\n"
            question += "with the global regulations and identify missing requirements."
            
            formatted_prompt = self.analysis_templates[language].format(
                context=context,
                question=question
            )
            
            # Get analysis from LLM
            llm_response = self.query_llm(formatted_prompt, language)
            
            return self._format_analysis_report(llm_response)
            
        except Exception as e:
            print(f"Error in policy analysis from text: {str(e)}")
            return None