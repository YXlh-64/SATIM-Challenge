from langchain.prompts import PromptTemplate
import requests
from datetime import datetime

# Constants
API_URL = 'https://openrouter.ai/api/v1/chat/completions'

class UseCaseAnalyzer:
    def __init__(self, api_key):
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://localhost:5000",
            "Content-Type": "application/json"
        }
        self.internal_db = None

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

    def set_internal_db(self, internal_db):
        """Set the internal policy database"""
        self.internal_db = internal_db

    def analyze_use_case(self, use_case, language='en'):
        """Analyze a use case against internal policies and return KPIs
        
        Args:
            use_case (str): The use case to analyze (either CIS control ID or custom use case)
            language (str): The language for the analysis ('en' or 'fr')
            
        Returns:
            dict: Analysis report containing KPIs and comparison results
        """
        try:
            if not self.internal_db:
                raise ValueError("Internal database not initialized. Call set_internal_db first.")

            # Get relevant internal policies
            relevant_internals = self.internal_db.similarity_search(
                use_case, 
                k=5
            )
            
            # Construct analysis prompt
            context = "\n".join([doc.page_content for doc in relevant_internals])
            
            # Create use case specific prompt
            use_case_prompt = f"""
            Analyze the following use case: {use_case}

Provide a structured analysis comparing the use case to internal policies, focusing on the following KPIs. Format the response with clear sections, using bullet points or tables for readability, and ensure all metrics are actionable and prioritized.

1. Compliance Score
   - Start this section with "Compliance Score: X%" where X is a number between 0 and 100
   - Calculate the score based on alignment with internal policies
   - Factor in the current implementation status
   - Provide a brief justification for the score

2. Risk Assessment
   - Identify specific risks associated with the use case
   - Assign severity levels (Low, Medium, High) for each risk
   - Recommend targeted mitigation strategies for each risk

3. Implementation Status
   - List specific actions required to align the use case with policies
   - Prioritize actions based on urgency and impact
   - Estimate effort for each action

4. Policy Coverage
   - List internal policies that align with the use case
   - Highlight any gaps where the use case lacks policy coverage
   - Suggest actionable improvements to address gaps

IMPORTANT: Always start the Compliance Score section with "Compliance Score: X%" where X is a number between 0 and 100.
            """
            
            if language == 'fr':
                use_case_prompt = f"""
                Analysez le cas d'usage suivant : {use_case}

Fournissez une analyse structurée comparant le cas d'usage aux politiques internes, en vous concentrant sur les KPI suivants. Formatez la réponse avec des sections claires, en utilisant des listes à puces ou des tableaux pour une meilleure lisibilité.

1. Score de Conformité
   - Commencez cette section par "Score de Conformité : X%" où X est un nombre entre 0 et 100
   - Calculez le score en fonction de l'alignement avec les politiques internes
   - Tenez compte de l'état d'implémentation actuel
   - Fournissez une brève justification pour le score

2. Évaluation des risques
   - Identifiez les risques spécifiques associés au cas d'usage
   - Attribuez un niveau de gravité à chaque risque (Faible, Moyen, Élevé)
   - Recommandez des stratégies de mitigation ciblées pour chaque risque

3. État d'implémentation
   - Listez les actions spécifiques nécessaires pour aligner le cas d'usage sur les politiques
   - Priorisez les actions en fonction de leur urgence et de leur impact
   - Estimez l'effort pour chaque action

4. Couverture des politiques
   - Listez les politiques internes alignées avec le cas d'usage
   - Identifiez les écarts où le cas d'usage manque de couverture politique
   - Suggérez des améliorations exploitables pour combler ces écarts

IMPORTANT : Commencez toujours la section Score de Conformité par "Score de Conformité : X%" où X est un nombre entre 0 et 100.
                """
            
            # Get analysis from LLM
            llm_response = self.query_llm(use_case_prompt, language)
            
            return self._format_analysis_report(llm_response)
            
        except Exception as e:
            print(f"Error in use case analysis: {str(e)}")
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