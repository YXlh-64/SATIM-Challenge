from policy_analyzer import PolicyAnalyzer
import os
from dotenv import load_dotenv

def test_policy_analysis():
    """Test the policy analysis system"""
    load_dotenv()
    
    # Initialize analyzer with OpenRouter API key
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not found in environment variables")
    
    analyzer = PolicyAnalyzer(api_key)
    
    try:
        # Initialize databases
        analyzer.initialize_databases(
            internal_path="data/internal",
            global_path="data/global"
        )
        
        # Test with new policy
        result = analyzer.analyze_new_policy("data/test/new_internal_policy.pdf")
        
        if result:
            print("\nPolicy Analysis Report")
            print("=" * 50)
            print(result['analysis'])
            print("\nAnalysis completed at:", result['timestamp'])
        else:
            print("Analysis failed to complete")
            
    except Exception as e:
        print(f"Test failed: {str(e)}")

if __name__ == "__main__":
    test_policy_analysis()