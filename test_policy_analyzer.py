from policy_analyzer import PolicyAnalyzer
import os
from dotenv import load_dotenv
import unittest

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

def setup_analyzer():
    """Setup and return a PolicyAnalyzer instance with initialized databases"""
    load_dotenv()
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable not set")
    
    analyzer = PolicyAnalyzer(api_key)
    analyzer.initialize_databases(
        internal_path="data/internal",
        global_path="data/global"
    )
    return analyzer

def test_analyze_new_policy_from_text():
    """Test analyzing a policy from text input"""
    analyzer = setup_analyzer()
    
    # Test with a sample policy text
    sample_policy = """
    Data Protection Policy:
    1. All personal data must be encrypted at rest
    2. Access to personal data requires two-factor authentication
    3. Regular security audits must be conducted quarterly
    """
    
    result = analyzer.analyze_new_policy_from_text(sample_policy)
    
    # Print the LLM response for inspection
    print("\nLLM Response:")
    print(result['analysis'])
    print("\n")
    
    # Verify the result structure
    assert result is not None, "Result should not be None"
    assert 'analysis' in result, "Result should contain 'analysis'"
    assert 'timestamp' in result, "Result should contain 'timestamp'"
    assert 'status' in result, "Result should contain 'status'"
    assert result['status'] == 'completed', "Status should be 'completed'"
    
    # Verify the analysis content
    assert isinstance(result['analysis'], str), "Analysis should be a string"
    assert len(result['analysis']) > 0, "Analysis should not be empty"

def test_analyze_new_policy_from_text_invalid_input():
    """Test analyzing a policy with invalid input"""
    analyzer = setup_analyzer()
    
    # Test with empty string
    result = analyzer.analyze_new_policy_from_text("")
    assert result is None, "Empty string should return None"
    
    # Test with None
    result = analyzer.analyze_new_policy_from_text(None)
    assert result is None, "None should return None"

if __name__ == "__main__":
    #test_policy_analysis()
    test_analyze_new_policy_from_text()
    test_analyze_new_policy_from_text_invalid_input()
    print("All tests passed!")