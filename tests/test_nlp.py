import pytest
import dspy
import sys
# Print sys.path to debug the module import issue
print("Current sys.path:")
for path in sys.path:
    print(path)
from backend.nlp import MathTutor

@pytest.fixture
def math_tutor():
    return MathTutor()

def test_basic_initialization(math_tutor):
    # Test that the MathTutor class initializes correctly
    assert math_tutor is not None
    assert hasattr(math_tutor, 'understand_query')
    assert hasattr(math_tutor, 'explain_step')
    assert hasattr(math_tutor, 'summarize')

def test_forward_basic_query(math_tutor):
    # Test a basic forward operation with a mock query
    basic_query = "Simplify x + x"
    
    try:
        result = math_tutor.forward(query=basic_query)
        
        # Assert that the result is an instance of the Prediction class
        assert isinstance(result, dspy.Prediction)

        # Check that the result has the expected attributes
        assert hasattr(result, 'problem_type')
        assert hasattr(result, 'steps')
        assert hasattr(result, 'summary')
        
        # Optionally, you can further assert on the content of these attributes
        assert isinstance(result.problem_type, str)
        assert isinstance(result.steps, list)
        assert isinstance(result.summary, str)

    except Exception as e:
        pytest.fail(f"Test failed with exception: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
