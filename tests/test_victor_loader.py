import unittest
import os
import sys
import shutil
import importlib

# Adjust path to import from the root of the ComfyUI project
# This assumes the tests are run from the ComfyUI root directory or PYTHONPATH is set.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import victor_loader
    import nodes # For accessing NODE_CLASS_MAPPINGS
    import server # For conceptually testing endpoint logic
except ImportError as e:
    print(f"CRITICAL ERROR: Could not import necessary modules for testing: {e}")
    print("Ensure tests are run from ComfyUI root or PYTHONPATH is correctly set.")
    sys.exit(1)

# Store original modules dir and loaded_modules to restore after tests
ORIGINAL_MODULES_DIR_NAME = "modules_original_for_test"
TEST_MODULES_DIR_NAME = "modules_test_temp"

class TestVictorModuleLoader(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """ Set up a temporary test modules directory. """
        cls.comfy_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        cls.original_modules_dir_path = os.path.join(cls.comfy_root, victor_loader.MODULES_DIR)
        cls.test_modules_dir_path = os.path.join(cls.comfy_root, TEST_MODULES_DIR_NAME)

        # If 'modules' dir exists, rename it to save its content
        if os.path.exists(cls.original_modules_dir_path):
            os.rename(cls.original_modules_dir_path, os.path.join(cls.comfy_root, ORIGINAL_MODULES_DIR_NAME))

        # Create a fresh test modules directory
        if os.path.exists(cls.test_modules_dir_path):
            shutil.rmtree(cls.test_modules_dir_path)
        os.makedirs(cls.test_modules_dir_path, exist_ok=True)

        # Point victor_loader to the test directory
        victor_loader.MODULES_DIR = TEST_MODULES_DIR_NAME

        # Backup original ComfyUI node mappings and victor_loader's internal registry
        cls.original_node_class_mappings = nodes.NODE_CLASS_MAPPINGS.copy()
        cls.original_node_display_name_mappings = nodes.NODE_DISPLAY_NAME_MAPPINGS.copy()
        cls.original_victor_loaded_modules = victor_loader.loaded_modules.copy()


    @classmethod
    def tearDownClass(cls):
        """ Clean up: remove test modules directory and restore original. """
        shutil.rmtree(cls.test_modules_dir_path, ignore_errors=True)

        # Restore original 'modules' dir if it was renamed
        original_renamed_path = os.path.join(cls.comfy_root, ORIGINAL_MODULES_DIR_NAME)
        if os.path.exists(original_renamed_path):
            # If a 'modules' dir was created by the loader (because original didn't exist)
            if os.path.exists(cls.original_modules_dir_path):
                 shutil.rmtree(cls.original_modules_dir_path) # remove the one created by loader
            os.rename(original_renamed_path, cls.original_modules_dir_path)

        # Restore original MODULES_DIR path in victor_loader
        victor_loader.MODULES_DIR = os.path.basename(cls.original_modules_dir_path) # Should be "modules"

        # Restore ComfyUI node mappings and victor_loader's registry
        nodes.NODE_CLASS_MAPPINGS = cls.original_node_class_mappings
        nodes.NODE_DISPLAY_NAME_MAPPINGS = cls.original_node_display_name_mappings
        victor_loader.loaded_modules = cls.original_victor_loaded_modules

    def setUp(self):
        """ Clear mappings and loaded modules before each test. """
        nodes.NODE_CLASS_MAPPINGS.clear()
        nodes.NODE_CLASS_MAPPINGS.update(self.original_node_class_mappings) # Keep non-Victor nodes

        nodes.NODE_DISPLAY_NAME_MAPPINGS.clear()
        nodes.NODE_DISPLAY_NAME_MAPPINGS.update(self.original_node_display_name_mappings)

        victor_loader.loaded_modules.clear()

        # Ensure the test modules directory is clean for each test run if needed
        # For now, we create files per test.
        for f in os.listdir(self.test_modules_dir_path):
            os.remove(os.path.join(self.test_modules_dir_path, f))


    def _create_test_module_file(self, filename, content):
        path = os.path.join(self.test_modules_dir_path, filename)
        with open(path, "w") as f:
            f.write(content)
        return path

    def test_01_load_valid_echo_module(self):
        """ Test loading a correctly structured VictorModule. """
        content = """
class VictorModule:
    VERSION = "v1.test"
    FUNCTION = "execute"
    CATEGORY = "TestModules"
    @classmethod
    def INPUT_TYPES(s): return {"required": {"text": ("STRING", {"default": "echo"})}}
    RETURN_TYPES = ("STRING",)
    def __init__(self): pass
    def execute(self, text): return (text + " processed",)
    def get_metadata(self): return {"node_name": "TestEchoNode", "display_name": "Test Echo"}
"""
        self._create_test_module_file("echo_test_module.py", content)

        loaded_in_run = victor_loader.load_victor_modules()
        self.assertIn("TestEchoNode", nodes.NODE_CLASS_MAPPINGS)
        self.assertEqual(nodes.NODE_DISPLAY_NAME_MAPPINGS.get("TestEchoNode"), "Test Echo")
        self.assertIn("TestEchoNode", victor_loader.loaded_modules)
        self.assertEqual(len(loaded_in_run), 1)

        # Test basic execution
        node_instance = nodes.NODE_CLASS_MAPPINGS["TestEchoNode"]()
        result = node_instance.execute(text="hello")
        self.assertEqual(result, ("hello processed",))

    def test_02_reject_module_missing_victor_class(self):
        """ Test that a module without VictorModule class is skipped. """
        content = "class NotVictorModule: pass"
        self._create_test_module_file("no_victor_class.py", content)

        loaded_in_run = victor_loader.load_victor_modules()
        self.assertEqual(len(loaded_in_run), 0)
        self.assertEqual(len(victor_loader.loaded_modules), 0)


    def test_03_reject_module_missing_required_method(self):
        """ Test rejection if VictorModule misses a required method (e.g., forward/FUNCTION). """
        content = """
class VictorModule:
    VERSION = "v1.broken"
    FUNCTION = "execute_forward" # Correctly named function is missing
    CATEGORY = "TestModules"
    @classmethod
    def INPUT_TYPES(s): return {}
    RETURN_TYPES = ()
    def __init__(self): pass
    # Missing execute_forward method
    def get_metadata(self): return {"node_name": "BrokenNode", "display_name": "Broken"}
"""
        self._create_test_module_file("broken_method_module.py", content)

        # The loader checks for __init__, forward, get_metadata on the class itself,
        # not necessarily the one pointed to by FUNCTION.
        # The current loader logic in victor_loader.py checks for presence of these three specific names.
        # Let's adjust the test to reflect that check for "forward".
        content_missing_forward = """
class VictorModule:
    VERSION = "v1.broken"
    FUNCTION = "execute"
    CATEGORY = "TestModules"
    @classmethod
    def INPUT_TYPES(s): return {}
    RETURN_TYPES = ()
    def __init__(self): pass
    # def forward(self, **kwargs): pass # This is missing
    def get_metadata(self): return {"node_name": "BrokenForwardNode", "display_name": "Broken Forward"}
"""
        self._create_test_module_file("broken_forward_module.py", content_missing_forward)

        loaded_in_run = victor_loader.load_victor_modules()
        self.assertNotIn("BrokenForwardNode", nodes.NODE_CLASS_MAPPINGS)
        self.assertEqual(len(loaded_in_run), 0)


    def test_04_get_loaded_modules_info_api_function(self):
        """ Test the get_loaded_modules_info function. """
        content = """
class VictorModule:
    VERSION = "v1.info"
    FUNCTION = "run"
    CATEGORY = "InfoCategory"
    @classmethod
    def INPUT_TYPES(s): return {}
    RETURN_TYPES = ()
    def __init__(self): pass
    def run(self): pass
    def get_metadata(self): return {"node_name": "InfoNode", "display_name": "Info Node Test", "custom_field": "test_value"}
"""
        self._create_test_module_file("info_module.py", content)
        victor_loader.load_victor_modules()

        info_list = victor_loader.get_loaded_modules_info()
        self.assertEqual(len(info_list), 1)
        info_item = info_list[0]
        self.assertEqual(info_item["node_name"], "InfoNode")
        self.assertEqual(info_item["display_name"], "Info Node Test")
        self.assertEqual(info_item["version"], "v1.info")
        self.assertEqual(info_item["filename"], "info_module.py")
        self.assertIn("custom_field", info_item["metadata"])
        self.assertEqual(info_item["metadata"]["custom_field"], "test_value")

    def test_05_reload_victor_modules_command(self):
        """ Test the hot-reloading functionality. """
        # Initial load
        module_v1_content = """
class VictorModule:
    VERSION = "v1.0"
    FUNCTION = "execute"
    CATEGORY = "ReloadTest"
    @classmethod
    def INPUT_TYPES(s): return {"required": {"val": ("INT", {"default": 1})}}
    RETURN_TYPES = ("INT",)
    def __init__(self): pass
    def execute(self, val): return (val * 10,)
    def get_metadata(self): return {"node_name": "ReloadableNode", "display_name": "Reloadable V1"}
"""
        self._create_test_module_file("reload_module.py", module_v1_content)
        victor_loader.load_victor_modules()

        self.assertIn("ReloadableNode", nodes.NODE_CLASS_MAPPINGS)
        self.assertEqual(victor_loader.loaded_modules["ReloadableNode"]["version"], "v1.0")
        instance_v1 = nodes.NODE_CLASS_MAPPINGS["ReloadableNode"]()
        self.assertEqual(instance_v1.execute(val=5), (50,))

        # Simulate a file change and reload
        module_v2_content = """
class VictorModule:
    VERSION = "v2.0" # Changed version
    FUNCTION = "execute"
    CATEGORY = "ReloadTest"
    @classmethod
    def INPUT_TYPES(s): return {"required": {"val": ("INT", {"default": 1})}}
    RETURN_TYPES = ("INT",)
    def __init__(self): pass
    def execute(self, val): return (val * 100,) # Changed logic
    def get_metadata(self): return {"node_name": "ReloadableNode", "display_name": "Reloadable V2"} # Changed display name
"""
        self._create_test_module_file("reload_module.py", module_v2_content) # Overwrite

        # Before calling reload, ensure the module is not cached in a way that importlib.reload would be needed
        # Our current reload_victor_modules_command deletes from sys.modules, so this should be fine.

        victor_loader.reload_victor_modules_command()

        self.assertIn("ReloadableNode", nodes.NODE_CLASS_MAPPINGS)
        self.assertEqual(nodes.NODE_DISPLAY_NAME_MAPPINGS.get("ReloadableNode"), "Reloadable V2")
        self.assertIn("ReloadableNode", victor_loader.loaded_modules)
        self.assertEqual(victor_loader.loaded_modules["ReloadableNode"]["version"], "v2.0")

        instance_v2 = nodes.NODE_CLASS_MAPPINGS["ReloadableNode"]()
        self.assertEqual(instance_v2.execute(val=5), (500,))

    # Conceptual tests for API endpoints (testing the underlying functions)
    def test_06_conceptual_api_reload(self):
        """ Conceptually test the function called by /reload_victor_modules. """
        # This is largely covered by test_05_reload_victor_modules_command
        # In a real server environment, one would use an HTTP client to test the endpoint.
        # Here, we just ensure the command function itself works.
        self.test_05_reload_victor_modules_command() # Re-run for sanity
        # Assertions are inside that test method.

    def test_07_conceptual_api_modules_info(self):
        """ Conceptually test the function called by /victor_modules_info. """
        # This is covered by test_04_get_loaded_modules_info_api_function
        self.test_04_get_loaded_modules_info_api_function()
        # Assertions are inside that test method.

if __name__ == '__main__':
    # Ensure ComfyUI's logging is suppressed or managed if it's too verbose for tests
    # logging.getLogger('some_comfyui_logger').setLevel(logging.CRITICAL)

    # Important: The tests modify global state (victor_loader.MODULES_DIR, nodes.NODE_CLASS_MAPPINGS etc.)
    # setUpClass and tearDownClass try to manage this.

    print(f"Running tests from: {os.getcwd()}")
    print(f"Test modules directory will be: {os.path.join(os.getcwd(), TEST_MODULES_DIR_NAME)}")

    unittest.main()
