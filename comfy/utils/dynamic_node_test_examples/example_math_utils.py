# comfy/utils/dynamic_node_test_examples/example_math_utils.py
import os # For testing restriction

def add(a: int, b: int) -> int:
    """Adds two integers.

Args:
    a: The first integer.
    b: The second integer.

Returns:
    The sum of a and b."""
    return a + b

def subtract(a: int, b: int) -> int:
    """Subtracts the second integer from the first."""
    return a - b

def check_os_import():
    """Checks if the 'os' module is available and usable."""
    try:
        # This will fail if 'os' was removed from module globals by DynamicPyNode
        os.listdir('.')
        return "os module is accessible"
    except NameError:
        return "os module is NOT accessible (NameError)"
    except Exception as e:
        return f"os module access failed: {str(e)}"

_private_helper = lambda x: x*2 # Should not be listed as an op
