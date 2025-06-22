import importlib.util
import os
import sys
import inspect
import hashlib
import logging # Added for ComfyUI style logging
from types import ModuleType

# ComfyUI specific imports - these will be needed for integration
# import nodes # This will be imported in functions that need it, to avoid circular deps if this file is imported by nodes.py

MODULES_DIR = "modules" # Standardized directory name
loaded_modules = {} # Internal registry for VictorModules

def hash_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:10]

def load_victor_modules():
    """
    Loads VictorModules from the MODULES_DIR.
    - Identifies .py files.
    - Imports them as Python modules.
    - Checks for a class named 'VictorModule'.
    - Validates that VictorModule has __init__, forward, and get_metadata methods.
    - Registers valid modules into `loaded_modules`.
    - Integrates with ComfyUI's NODE_CLASS_MAPPINGS and NODE_DISPLAY_NAME_MAPPINGS.
    """
    logging.info(f"[VictorLoader] Starting to load modules from '{MODULES_DIR}'...")

    # Ensure access to ComfyUI's global node mappings
    # This import is deferred to function scope if victor_loader itself is imported early.
    # However, for clarity during this step, assuming `nodes` can be imported or its mappings passed.
    # For now, we'll assume direct access for modification during this step.
    # In a final version, these might be passed as arguments or accessed via a getter/setter.
    import nodes

    # Clear previously loaded VictorModules for this loader
    # We need to be careful if this function is also used for hot-reloading.
    # For an initial load, clearing is fine. For reload, we'd need to unregister old ones first.
    # This will be handled more explicitly in the hot-reload function.
    # For now, this function is for initial loading.

    # Store a list of module names that were successfully loaded in this run
    # to compare against `loaded_modules` if this is part of a reload sequence.
    current_load_successes = {}


    if not os.path.isdir(MODULES_DIR):
        logging.warning(f"[VictorLoader] Modules directory '{MODULES_DIR}' not found. No VictorModules will be loaded.")
        os.makedirs(MODULES_DIR) # Create it if it doesn't exist
        logging.info(f"[VictorLoader] Created modules directory: '{MODULES_DIR}'")
        return loaded_modules # Return the (empty) global `loaded_modules`

    for fname in os.listdir(MODULES_DIR):
        if not fname.endswith(".py"):
            continue
        if fname.startswith('_'): # Skip __init__.py or other private-like files
            continue

        path = os.path.join(MODULES_DIR, fname)
        modname_short = fname.replace('.py','')
        modname_unique = f"victormodule_{modname_short}_{hash_file(path)}" # Ensure unique module name for sys.modules

        try:
            spec = importlib.util.spec_from_file_location(modname_unique, path)
            if spec is None:
                logging.error(f"[VictorLoader] [ERROR] Could not create spec for {fname}")
                continue
            module = importlib.util.module_from_spec(spec)
            sys.modules[modname_unique] = module # Add to sys.modules before exec to handle circular imports within the module
            spec.loader.exec_module(module)
        except Exception as e:
            logging.error(f"[VictorLoader] [ERROR] Failed to import {fname}: {e}", exc_info=True)
            if modname_unique in sys.modules: # Clean up if exec failed
                del sys.modules[modname_unique]
            continue

        victor_module_class = None
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and name == "VictorModule":
                # Basic validation for essential methods
                methods = {"__init__", "forward", "get_metadata"}
                class_methods = set(dir(obj)) # Get all attributes, including inherited ones

                # Check if obj is defined in the currently loaded module, not imported
                if obj.__module__ != modname_unique:
                    logging.debug(f"[VictorLoader] Skipping class '{name}' in {fname} as it's imported from {obj.__module__}, not defined locally.")
                    continue

                if not methods.issubset(class_methods):
                    logging.warning(f"[VictorLoader] [WARN] {fname} - Class 'VictorModule' is missing required methods (need __init__, forward, get_metadata). Skipping.")
                    continue

                victor_module_class = obj
                break # Found the target class

        if victor_module_class:
            try:
                instance_for_metadata = victor_module_class() # Instantiate to get metadata
                metadata = instance_for_metadata.get_metadata()

                # Use a unique name for NODE_CLASS_MAPPINGS to avoid collisions if multiple files define "VictorModule"
                # The unique name should be descriptive. Using the short module name (filename without .py)
                # Or, ideally, the metadata provides a node name.
                node_class_name = metadata.get("node_name", modname_short) # Prefer metadata name
                if not node_class_name or node_class_name in nodes.NODE_CLASS_MAPPINGS:
                    # If metadata name is missing or conflicts, use a more unique name
                    node_class_name = f"VictorModule_{modname_short}"
                    if node_class_name in nodes.NODE_CLASS_MAPPINGS and nodes.NODE_CLASS_MAPPINGS[node_class_name] != victor_module_class : # Still a conflict with a *different* class
                         logging.warning(f"[VictorLoader] [WARN] Node class name '{node_class_name}' from {fname} conflicts with an existing node. Appending hash.")
                         node_class_name = f"VictorModule_{modname_short}_{hash_file(path)[:4]}"


                display_name = metadata.get("display_name", node_class_name.replace("_", " "))
                category = metadata.get("category", "VictorModules") # Default category

                # Register with ComfyUI
                nodes.NODE_CLASS_MAPPINGS[node_class_name] = victor_module_class
                nodes.NODE_DISPLAY_NAME_MAPPINGS[node_class_name] = display_name

                # Set category for the class if not already set (ComfyUI convention)
                if not hasattr(victor_module_class, 'CATEGORY'):
                    victor_module_class.CATEGORY = category

                # Store in our internal loader registry
                module_info = {
                    "module_obj": module, # The Python module object
                    "class_obj": victor_module_class, # The VictorModule class object
                    "path": path,
                    "sys_module_name": modname_unique,
                    "file_hash": hash_file(path),
                    "version": getattr(victor_module_class, "VERSION", metadata.get("version", "unknown")),
                    "metadata": metadata,
                    "comfy_node_class_name": node_class_name, # The name used in NODE_CLASS_MAPPINGS
                    "comfy_display_name": display_name,
                    "comfy_category": category
                }
                loaded_modules[node_class_name] = module_info # Use the ComfyUI node name as key
                current_load_successes[node_class_name] = module_info

                logging.info(f"[VictorLoader] [OK] Loaded '{display_name}' (Class: {node_class_name}, Version: {module_info['version']}) from {fname}")

            except Exception as e:
                logging.error(f"[VictorLoader] [ERROR] Could not instantiate or get metadata for VictorModule in {fname}: {e}", exc_info=True)
        else:
            logging.debug(f"[VictorLoader] No 'VictorModule' class found in {fname} or it was invalid/imported.")
            if modname_unique in sys.modules: # Clean up if no valid class found
                del sys.modules[modname_unique]


    logging.info(f"[VictorLoader] Finished loading. {len(current_load_successes)} VictorModules registered with ComfyUI.")
    return current_load_successes # Return what was loaded in *this* run

# Placeholder for hot-reloading logic, to be developed in a later step
def reload_victor_modules_command():
    logging.info("[VictorLoader] Hot-reload requested...")

    import nodes # Ensure nodes module is available for mappings

    # 1. Identify modules loaded by this loader (use keys from `loaded_modules`)
    previously_loaded_node_names = list(loaded_modules.keys())

    for node_name in previously_loaded_node_names:
        module_info = loaded_modules.get(node_name)
        if module_info:
            # Unregister from ComfyUI
            if node_name in nodes.NODE_CLASS_MAPPINGS:
                del nodes.NODE_CLASS_MAPPINGS[node_name]
            if node_name in nodes.NODE_DISPLAY_NAME_MAPPINGS:
                del nodes.NODE_DISPLAY_NAME_MAPPINGS[node_name]

            # Remove from sys.modules
            sys_module_name = module_info.get('sys_module_name')
            if sys_module_name and sys_module_name in sys.modules:
                del sys.modules[sys_module_name]
                logging.debug(f"[VictorLoader] Unloaded module '{sys_module_name}' from sys.modules for reload.")

    # Clear our internal registry before reloading
    loaded_modules.clear()

    # Call the main loading function again
    newly_loaded = load_victor_modules() # This will re-populate `loaded_modules` and ComfyUI mappings

    msg = f"[VictorLoader] Hot-reload complete. {len(newly_loaded)} VictorModules active."
    logging.info(msg)
    return msg

# Placeholder for API data retrieval
def get_loaded_modules_info():
    info_list = []
    for node_name, data in loaded_modules.items(): # Iterate over our internal registry
        info_list.append({
            "node_name": node_name, # The name used in ComfyUI's mappings
            "filename": os.path.basename(data.get("path", "unknown_path")),
            "version": data.get("version", "unknown"),
            "hash": data.get("file_hash", "none"),
            "metadata": data.get("metadata", {}),
            "display_name": data.get("comfy_display_name", node_name),
            "category": data.get("comfy_category", "VictorModules"),
        })
    return info_list

if __name__ == "__main__":
    # Example usage (for testing victor_loader.py directly)
    # This part won't run when imported by ComfyUI
    print("Running VictorLoader directly for testing...")
    # Mock ComfyUI's nodes module for standalone testing
    class MockNodesModule:
        def __init__(self):
            self.NODE_CLASS_MAPPINGS = {}
            self.NODE_DISPLAY_NAME_MAPPINGS = {}

    mock_nodes = MockNodesModule()
    sys.modules['nodes'] = mock_nodes # Mock the nodes module

    if not os.path.exists(MODULES_DIR):
        os.makedirs(MODULES_DIR)
        print(f"Created '{MODULES_DIR}' directory for testing.")
        # Create a dummy echo_victor.py for testing
        with open(os.path.join(MODULES_DIR, "echo_victor.py"), "w") as f:
            f.write("""
class VictorModule:
    VERSION = "v0.1-echo-test"
    def __init__(self, **kwargs):
        self.name = "EchoTester"
        self.params = kwargs
    def forward(self, input_data):
        print(f"[EchoTester] Input: {input_data}, Params: {self.params}")
        return input_data
    def get_metadata(self):
        return {
            "node_name": "EchoVictorTestNode", # Unique name for ComfyUI
            "display_name": "Echo Victor Test",
            "version": self.VERSION,
            "category": "VictorModules_Test",
            "description": "A test echo module for Victor pipeline."
        }
""")
        print(f"Created dummy 'echo_victor.py' in '{MODULES_DIR}'.")

    load_victor_modules()
    print("\nLoaded modules info:")
    for item in get_loaded_modules_info():
        print(item)

    print("\nComfyUI Mappings (mocked):")
    print("NODE_CLASS_MAPPINGS:", mock_nodes.NODE_CLASS_MAPPINGS)
    print("NODE_DISPLAY_NAME_MAPPINGS:", mock_nodes.NODE_DISPLAY_NAME_MAPPINGS)

    # Test reload
    print("\nSimulating a change and reloading...")
    # (In a real scenario, you'd modify a file in modules/)
    # For this test, just call reload.
    reload_victor_modules_command()
    print("\nLoaded modules info after reload:")
    for item in get_loaded_modules_info():
        print(item)

    # Clean up dummy module and directory if created by this test
    # if os.path.exists(os.path.join(MODULES_DIR, "echo_victor.py")):
    #     os.remove(os.path.join(MODULES_DIR, "echo_victor.py"))
    # if os.listdir(MODULES_DIR) == []:
    #     os.rmdir(MODULES_DIR)

    # Remove mock nodes module
    del sys.modules['nodes']
    print("\nVictorLoader test finished.")
