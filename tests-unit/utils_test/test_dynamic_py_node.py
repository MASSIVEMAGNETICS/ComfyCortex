# tests-unit/utils_test/test_dynamic_py_node.py
import unittest
import os
import sys
import shutil
import logging
from inspect import Signature, Parameter

# Add the parent directory of 'comfy' to sys.path to allow importing DynamicPyNode
# This might need adjustment based on how ComfyUI structures its test execution environment
# For now, assuming 'comfy' is a top-level directory relative to where tests are run from,
# or that PYTHONPATH is set up appropriately.
# A common pattern:
current_dir = os.path.dirname(os.path.abspath(__file__)) # .../tests-unit/utils_test
project_root = os.path.abspath(os.path.join(current_dir, '..', '..')) # Assumed to be repo root

# Ensure 'comfy' can be imported by adding project_root to sys.path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from comfy.utils.dynamic_py_node import DynamicPyNode, ModuleLoadError, OpNotFoundError, OpExecutionError, MethodCallError, InvalidOpError
except ImportError as e:
    print(f"Failed to import DynamicPyNode. Current sys.path: {sys.path}")
    print(f"Attempted project_root: {project_root}")
    # This import error is critical for tests to run.
    # If this occurs, it means the path logic needs adjustment for the test environment.
    raise ImportError(f"Could not import DynamicPyNode for testing: {e}. Check sys.path setup in test_dynamic_py_node.py.")


# Test file paths
EXAMPLES_DIR_NAME = "dynamic_node_test_examples"
# Path to examples dir relative to project_root/comfy/utils/
EXAMPLES_BASE_PATH = os.path.join(project_root, 'comfy', 'utils', EXAMPLES_DIR_NAME)

MATH_MODULE_PATH = os.path.join(EXAMPLES_BASE_PATH, "example_math_utils.py")
CLASS_MODULE_PATH = os.path.join(EXAMPLES_BASE_PATH, "example_class_module.py")
SYNTAX_ERROR_MODULE_PATH = os.path.join(EXAMPLES_BASE_PATH, "example_syntax_error_module.py")
NON_EXISTENT_MODULE_PATH = os.path.join(EXAMPLES_BASE_PATH, "non_existent_module.py")

# Configure logging for tests to see output from DynamicPyNode
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestDynamicPyNode(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logger.info(f"Project root (for sys.path): {project_root}")
        logger.info(f"Examples base path (absolute): {os.path.abspath(EXAMPLES_BASE_PATH)}")
        logger.info(f"Math module path (absolute): {os.path.abspath(MATH_MODULE_PATH)}")
        logger.info(f"Class module path (absolute): {os.path.abspath(CLASS_MODULE_PATH)}")

        # Ensure example files exist
        if not os.path.exists(EXAMPLES_BASE_PATH):
             logger.warning(f"EXAMPLES_BASE_PATH does not exist: {EXAMPLES_BASE_PATH}. Some tests might fail if files are not found.")
        elif not os.path.isdir(EXAMPLES_BASE_PATH):
             logger.warning(f"EXAMPLES_BASE_PATH is not a directory: {EXAMPLES_BASE_PATH}.")


        # Check individual files and log errors if missing, but don't halt all tests.
        # Individual tests will fail if their specific module is missing.
        for path_to_check, name in [(MATH_MODULE_PATH, "Math"), (CLASS_MODULE_PATH, "Class"), (SYNTAX_ERROR_MODULE_PATH, "Syntax Error")]:
            if not os.path.exists(path_to_check):
                logger.error(f"{name} example module not found at {path_to_check}. Ensure Part 1 of subtask ran correctly.")


    def test_01_module_loading_success(self):
        logger.info("Running test_01_module_loading_success")
        self.assertTrue(os.path.exists(MATH_MODULE_PATH), f"Math module not found for test: {MATH_MODULE_PATH}")
        node = DynamicPyNode(MATH_MODULE_PATH)
        self.assertIsNotNone(node.module)
        self.assertTrue(len(node.ops) > 0, "No ops found in math module.")
        self.assertTrue(len(node.docs) > 0, "No docs found in math module.")

    def test_02_module_loading_non_existent(self):
        logger.info("Running test_02_module_loading_non_existent")
        with self.assertRaises(ModuleLoadError):
            DynamicPyNode(NON_EXISTENT_MODULE_PATH)

    def test_03_module_loading_syntax_error(self):
        logger.info("Running test_03_module_loading_syntax_error")
        self.assertTrue(os.path.exists(SYNTAX_ERROR_MODULE_PATH), f"Syntax error module not found for test: {SYNTAX_ERROR_MODULE_PATH}")
        # Depending on when the syntax error is caught (import time vs. AST parsing for docs)
        # It's usually ModuleLoadError due to spec.loader.exec_module(mod) failing.
        with self.assertRaises((ModuleLoadError, SyntaxError)): # SyntaxError can be raised by ast.parse or exec_module
            DynamicPyNode(SYNTAX_ERROR_MODULE_PATH)

    def test_04_list_ops(self):
        logger.info("Running test_04_list_ops")
        self.assertTrue(os.path.exists(MATH_MODULE_PATH), f"Math module not found for test: {MATH_MODULE_PATH}")
        node = DynamicPyNode(MATH_MODULE_PATH)
        ops = node.list_ops()
        self.assertIn("add", ops)
        self.assertIn("subtract", ops)
        self.assertNotIn("_private_helper", ops)

        self.assertTrue(os.path.exists(CLASS_MODULE_PATH), f"Class module not found for test: {CLASS_MODULE_PATH}")
        node_class = DynamicPyNode(CLASS_MODULE_PATH)
        ops_class = node_class.list_ops()
        self.assertIn("Greeter", ops_class)
        self.assertIn("NoInit", ops_class)
        self.assertNotIn("_InternalHelperClass", ops_class)


    def test_05_get_op_doc(self):
        logger.info("Running test_05_get_op_doc")
        self.assertTrue(os.path.exists(MATH_MODULE_PATH), f"Math module not found for test: {MATH_MODULE_PATH}")
        node = DynamicPyNode(MATH_MODULE_PATH)
        self.assertIn("Adds two integers.", node.get_op_doc("add"))
        self.assertEqual("", node.get_op_doc("non_existent_op"))

    def test_06_get_op_signature(self):
        logger.info("Running test_06_get_op_signature")
        self.assertTrue(os.path.exists(MATH_MODULE_PATH), f"Math module not found for test: {MATH_MODULE_PATH}")
        node_math = DynamicPyNode(MATH_MODULE_PATH)
        add_sig = node_math.get_op_signature("add")
        self.assertEqual(len(add_sig.parameters), 2)
        self.assertIn('a', add_sig.parameters)
        self.assertIn('b', add_sig.parameters)

        self.assertTrue(os.path.exists(CLASS_MODULE_PATH), f"Class module not found for test: {CLASS_MODULE_PATH}")
        node_class = DynamicPyNode(CLASS_MODULE_PATH)
        greeter_sig = node_class.get_op_signature("Greeter") # Signature of __init__
        self.assertIn('name', greeter_sig.parameters)
        self.assertEqual(greeter_sig.parameters['name'].default, "World")

        no_init_sig = node_class.get_op_signature("NoInit") # Expects empty signature from class itself
        self.assertEqual(len(no_init_sig.parameters), 0)

        with self.assertRaises(OpNotFoundError):
            node_math.get_op_signature("fake_op")


    def test_07_run_op_function(self):
        logger.info("Running test_07_run_op_function")
        self.assertTrue(os.path.exists(MATH_MODULE_PATH), f"Math module not found for test: {MATH_MODULE_PATH}")
        node = DynamicPyNode(MATH_MODULE_PATH)
        result = node.run_op("add", 5, 3)
        self.assertEqual(result, 8)
        result_kw = node.run_op("subtract", a=10, b=3)
        self.assertEqual(result_kw, 7)
        with self.assertRaises(OpExecutionError): # Too many args -> TypeError -> OpExecutionError
            node.run_op("add", 1,2,3)


    def test_08_run_op_class_instantiation_and_state(self):
        logger.info("Running test_08_run_op_class_instantiation_and_state")
        self.assertTrue(os.path.exists(CLASS_MODULE_PATH), f"Class module not found for test: {CLASS_MODULE_PATH}")
        node = DynamicPyNode(CLASS_MODULE_PATH)
        greeter_instance = node.run_op("Greeter", name="Tester")
        self.assertIsInstance(greeter_instance, node.ops["Greeter"])
        self.assertEqual(greeter_instance.name, "Tester")

        self.assertIn("Greeter", node.state)
        state_entry = node.state["Greeter"]
        self.assertEqual(state_entry['classname'], "Greeter")
        self.assertEqual(state_entry['args'], ("Tester",))
        self.assertIs(state_entry['instance'], greeter_instance)

        no_init_instance = node.run_op("NoInit")
        self.assertIsInstance(no_init_instance, node.ops["NoInit"])

    def test_09_run_op_error_on_init(self):
        logger.info("Running test_09_run_op_error_on_init")
        self.assertTrue(os.path.exists(CLASS_MODULE_PATH), f"Class module not found for test: {CLASS_MODULE_PATH}")
        node = DynamicPyNode(CLASS_MODULE_PATH)
        with self.assertRaises(OpExecutionError): # ValueError in __init__ -> OpExecutionError
            node.run_op("ErrorOnInit")


    def test_10_call_method(self):
        logger.info("Running test_10_call_method")
        self.assertTrue(os.path.exists(CLASS_MODULE_PATH), f"Class module not found for test: {CLASS_MODULE_PATH}")
        node = DynamicPyNode(CLASS_MODULE_PATH)
        node.run_op("Greeter", name="Alice")

        greeting = node.call_method("Greeter", "greet", punctuation="!!!")
        self.assertEqual(greeting, "Hello, Alice!!!")

        count = node.call_method("Greeter", "get_message_count")
        self.assertEqual(count, 1)

    def test_11_call_method_errors(self):
        logger.info("Running test_11_call_method_errors")
        self.assertTrue(os.path.exists(CLASS_MODULE_PATH), f"Class module not found for test: {CLASS_MODULE_PATH}")
        node = DynamicPyNode(CLASS_MODULE_PATH)
        with self.assertRaises(MethodCallError): # Instance not created
            node.call_method("Greeter", "greet")

        node.run_op("Greeter", "Bob")
        with self.assertRaises(MethodCallError): # Non-existent method
            node.call_method("Greeter", "non_existent_method")

    def test_12_reload_module(self):
        logger.info("Running test_12_reload_module")
        # Create a temporary, modifiable copy of a simple module for this test
        temp_module_name = "temp_reload_test_module.py"
        # Place it in EXAMPLES_BASE_PATH to ensure the directory exists
        temp_module_path = os.path.join(EXAMPLES_BASE_PATH, temp_module_name)

        original_content = """
def multiply(x, y):
    return x * y
class TempStateful: # Add a class to test state clearing
    def __init__(self, val=0): self.val = val
    def get_val(self): return self.val
"""
        with open(temp_module_path, "w") as f:
            f.write(original_content)

        node = DynamicPyNode(temp_module_path)
        self.assertIn("multiply", node.list_ops())
        self.assertIn("TempStateful", node.list_ops())
        self.assertNotIn("divide", node.list_ops())
        self.assertEqual(node.run_op("multiply", 2, 3), 6)

        # Instantiate TempStateful to put something in state
        node.run_op("TempStateful", val=100)
        self.assertTrue(len(node.state) > 0, "State should not be empty after instantiation.")

        # Modify the module content
        modified_content = """
def multiply(x, y):
    return x * y * 1
def divide(x, y):   # Add a new op
    return x / y
class TempStateful: # Keep the class
    def __init__(self, val=0): self.val = val + 1 # Modify __init__ slightly
    def get_val(self): return self.val
    def new_method(self): return "new" # Add new method
"""
        with open(temp_module_path, "w") as f:
            f.write(modified_content)

        node.reload()

        self.assertIn("multiply", node.list_ops())
        self.assertIn("divide", node.list_ops())
        self.assertIn("TempStateful", node.list_ops())
        self.assertTrue(len(node.state) == 0, "State should be cleared after reload.")

        self.assertEqual(node.run_op("divide", 10, 2), 5)

        # Test that new class behavior / new methods are available
        ts_instance = node.run_op("TempStateful", val=50) # __init__ now adds 1
        self.assertEqual(ts_instance.val, 51)
        self.assertEqual(node.call_method("TempStateful", "get_val"), 51)
        self.assertEqual(node.call_method("TempStateful", "new_method"), "new")

        os.remove(temp_module_path)

    def test_13_security_module_restriction(self):
        logger.info("Running test_13_security_module_restriction")
        self.assertTrue(os.path.exists(MATH_MODULE_PATH), f"Math module not found for test: {MATH_MODULE_PATH}")
        node = DynamicPyNode(MATH_MODULE_PATH) # example_math_utils.py imports os
        result = node.run_op("check_os_import")
        self.assertEqual(result, "os module is NOT accessible (NameError)")

    def test_14_run_op_non_existent(self):
        logger.info("Running test_14_run_op_non_existent")
        self.assertTrue(os.path.exists(MATH_MODULE_PATH), f"Math module not found for test: {MATH_MODULE_PATH}")
        node = DynamicPyNode(MATH_MODULE_PATH)
        with self.assertRaises(OpNotFoundError):
            node.run_op("non_existent_function")

if __name__ == '__main__':
    # This allows running the tests directly from this file: python path/to/test_dynamic_py_node.py
    # It's also discoverable by `python -m unittest discover tests-unit`
    unittest.main()
