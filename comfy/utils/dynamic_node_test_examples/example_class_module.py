# comfy/utils/dynamic_node_test_examples/example_class_module.py
class Greeter:
    """A simple class that greets."""
    def __init__(self, name: str = "World"):
        """Initializes the Greeter.

Args:
    name: The name to greet."""
        self.name = name
        self.message_count = 0

    def greet(self, punctuation: str = "!") -> str:
        """Generates a greeting message.

Args:
    punctuation: Punctuation to end the greeting with."""
        self.message_count += 1
        return f"Hello, {self.name}{punctuation}"

    def get_message_count(self) -> int:
        """Returns how many times greet() has been called."""
        return self.message_count

class NoInit:
    """A class with no explicit __init__ method."""
    greeting_text = "Hello from NoInit"

    def get_greeting(self):
        return self.greeting_text

class ErrorOnInit:
    """A class that raises an error during instantiation."""
    def __init__(self):
        raise ValueError("Failed to initialize ErrorOnInit")

# This class should not be directly listed by DynamicPyNode's _extract_ops
class _InternalHelperClass:
    pass
