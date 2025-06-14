from __future__ import annotations
import json
import importlib.util
import inspect # Required for inspect.Parameter.empty comparison
from typing import Any, Callable

from comfy.comfy_types.node_typing import IO, InputTypeDict
from .cognitive_nodes import GenericCognitiveNode # Assuming GenericCognitiveNode is in cognitive_nodes.py
from .dynamic_py_utils import parse_python_file, CallableInfo, ParameterInfo # Utils from previous step

class DynamicPyNode(GenericCognitiveNode):
    DESCRIPTION = "Dynamically loads a Python module and executes a selected function or class method from it."
    CATEGORY = "CognitiveCortex/Dynamic"

    # Store parsed ops at class level for COMBO population if module_path is fixed per instance type
    # However, if module_path is an input, this needs to be instance-level and COMBO needs a way to refresh.
    # For now, let's make it instance-level. The COMBO will use a method from the instance.

    # _parsed_ops_cache: Dict[str, Dict[str, CallableInfo]] = {} # Cache per module path at class level

    def __init__(self):
        super().__init__()
        self.current_module_path: str | None = None
        self.parsed_ops: dict[str, CallableInfo] = {}
        self.selected_op_info: CallableInfo | None = None
        self.class_instance: Any | None = None
        self.error_details: str = ""

    @classmethod
    def INPUT_TYPES(cls) -> InputTypeDict:
        # This function is called by ComfyUI when the node is instantiated.
        # It needs to return the input types. For dynamic COMBOs, the list
        # of items is often provided by a function.

        # The actual list of operations will be populated by the instance method _get_operation_choices
        # when module_path is processed by the node instance.
        return {
            "required": {
                "module_path": (IO.STRING, {"default": "comfy_extras/example_module.py",
                                            "tooltip": "Path to the Python module to load (e.g., 'folder/mymodule.py')."}),
                "selected_operation_id": (cls.get_operation_choices_for_input(), {}), # Uses instance method via wrapper
                "op_args_json": (IO.STRING, {"multiline": True, "default": "{}",
                                           "tooltip": "JSON dictionary of arguments for the operation."}),
                "instance_action": (["CALL", "REINSTANTIATE_CALL", "GET_OR_CREATE_INSTANCE"],
                                    {"default": "CALL",
                                     "tooltip": "Action for class instances: CALL (on existing/new), REINSTANTIATE_CALL (always new), GET_OR_CREATE_INSTANCE (returns instance)."}),
            },
            "optional": {
                 "reset_instance_trigger": ("BOOLEAN", {"default": False, "tooltip": "If True, resets stored class instance."}),
            }
        }

    RETURN_TYPES = (IO.ANY, IO.STRING) # result, details_or_error
    RETURN_NAMES = ("result", "details")
    OUTPUT_TOOLTIPS = (
        "The result of the executed operation. Can be any Python object.",
        "Details about the loaded module, selected operation, or any errors encountered."
    )
    FUNCTION = "execute_dynamic_op"

    # ComfyUI INPUT_TYPES combo box expects a classmethod that returns a list of strings
    # or a function that will be called ON THE INSTANCE to get the list of strings.
    # This wrapper allows the instance to provide its dynamic choices.
    @classmethod
    def get_operation_choices_for_input(cls):
        # This function is called by ComfyUI to get the *function* that will provide the choices.
        # That function will be called on the node instance.
        return cls._instance_get_operation_choices

    def _instance_get_operation_choices(self):
        # This method is called on the instance.
        # It should ideally parse the module if module_path is available and different.
        # However, module_path is an input field, and its value might not be set when the UI is built.
        # For now, it returns what's currently parsed. A manual "refresh" or execution might be needed
        # to update the list if module_path changes significantly.
        if self.parsed_ops:
            return sorted(list(self.parsed_ops.keys()))
        return ["Load module to see operations"]


    def _load_and_parse_module(self, module_path: str, force_reload: bool = False) -> bool:
        if not module_path:
            self.error_details = "Module path is empty."
            self.parsed_ops = {}
            return False

        if self.current_module_path == module_path and self.parsed_ops and not force_reload:
            return True # Already loaded and parsed

        # print(f"[DynamicPyNode] Loading module: {module_path}") # Debug
        self.current_module_path = module_path
        self.parsed_ops = parse_python_file(module_path)
        self.class_instance = None # Reset instance when module changes

        if not self.parsed_ops:
            self.error_details = f"No operations found or error parsing module: {module_path}"
            # Check dynamic_py_utils print statements for more specific errors from the parser
            return False
        self.error_details = f"Loaded {len(self.parsed_ops)} ops from {module_path}."
        return True

    def execute_dynamic_op(self, module_path: str, selected_operation_id: str,
                           op_args_json: str, instance_action: str,
                           reset_instance_trigger: bool = False):

        self.error_details = "" # Reset error details for this run

        if reset_instance_trigger:
            self.class_instance = None
            self.error_details += "Class instance reset. "

        if self.current_module_path != module_path or not self.parsed_ops or selected_operation_id not in self.parsed_ops:
            if not self._load_and_parse_module(module_path):
                return (None, self.error_details or "Failed to load module.")

        # After loading, if selected_operation_id is still not in parsed_ops (e.g. "Load module..." placeholder)
        if selected_operation_id not in self.parsed_ops:
            details = self.error_details + f" Operation '{selected_operation_id}' not found or module not fully processed. Available: {list(self.parsed_ops.keys())}"
            return (None, details)


        self.selected_op_info = self.parsed_ops[selected_operation_id]
        op_info = self.selected_op_info

        try:
            spec = importlib.util.spec_from_file_location(op_info.module_name, module_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not create module spec for {module_path}")
            live_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(live_module)
        except Exception as e:
            return (None, f"Failed to import live module {module_path}: {e}")

        try:
            user_provided_args = json.loads(op_args_json)
            if not isinstance(user_provided_args, dict):
                raise ValueError("op_args_json must be a JSON dictionary.")
        except json.JSONDecodeError as e:
            return (None, f"Invalid JSON in op_args_json: {e}")
        except ValueError as e:
            return (None, str(e))

        prepared_args = []
        prepared_kwargs = {}

        try:
            temp_user_args = user_provided_args.copy() # To remove consumed args for **kwargs
            for param_info in op_info.parameters:
                if param_info.kind == inspect.Parameter.VAR_POSITIONAL:
                    pass
                elif param_info.kind == inspect.Parameter.VAR_KEYWORD:
                    pass # Handled later
                elif param_info.name in temp_user_args:
                    prepared_args.append(temp_user_args.pop(param_info.name))
                elif param_info.default_value_is_set:
                    prepared_args.append(param_info.default)
                else:
                    return (None, f"Missing required argument '{param_info.name}' for {op_info.display_name}")

            # Remaining temp_user_args are for **kwargs
            if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in op_info.parameters):
                prepared_kwargs.update(temp_user_args)

        except Exception as e:
            return (None, f"Error preparing arguments: {e}")


        result: Any = None
        executable_callable: Callable | None = None

        try:
            if op_info.type == "function":
                executable_callable = getattr(live_module, op_info.qual_name)
                result = executable_callable(*prepared_args, **prepared_kwargs)
                self.error_details += f"Executed function '{op_info.display_name}'. "

            elif op_info.type == "class_constructor":
                TheClass = getattr(live_module, op_info.class_name)
                self.class_instance = TheClass(*prepared_args, **prepared_kwargs)
                result = self.class_instance
                self.error_details += f"Instantiated class '{op_info.class_name}'. "

            elif op_info.type == "class_method":
                LiveClass = getattr(live_module, op_info.class_name) # Get the class from the live module
                if instance_action == "REINSTANTIATE_CALL" or self.class_instance is None or not isinstance(self.class_instance, LiveClass):
                    if instance_action != "REINSTANTIATE_CALL" and self.class_instance is not None and not isinstance(self.class_instance, LiveClass):
                         self.error_details += f"Warning: Stored instance type mismatch. Re-instantiating {op_info.class_name}. "

                    constructor_id = f"{op_info.class_name}.__init__"
                    if constructor_id not in self.parsed_ops:
                        return (None, f"Constructor info for {op_info.class_name} not found for instantiation.")

                    constructor_op_info = self.parsed_ops[constructor_id]
                    init_args_list = []
                    init_kwargs_dict = {} # Support kwargs for constructor too
                    # This simplified constructor call assumes that if op_args_json was meant for the method,
                    # then the constructor must be callable with defaults or no args.
                    # A more complex system might require separate arg inputs for constructor vs method.
                    # For REINSTANTIATE_CALL, it's ambiguous where constructor args come from if not from current op_args_json.
                    # Let's assume for now that REINSTANTIATE_CALL uses default constructor args.
                    for p_info_init in constructor_op_info.parameters:
                        if p_info_init.default_value_is_set:
                            if p_info_init.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD or p_info_init.kind == inspect.Parameter.POSITIONAL_ONLY:
                                init_args_list.append(p_info_init.default)
                            # else: KEYWORD_ONLY default handled by passing **init_kwargs_dict
                        # If a required param has no default, this would fail.

                    self.class_instance = LiveClass(*init_args_list, **init_kwargs_dict)
                    self.error_details += f"Instantiated/Re-instantiated {op_info.class_name}. "

                if self.class_instance is None: # Should not happen if logic above is correct
                    return (None, f"No class instance of {op_info.class_name} to call method '{op_info.qual_name}'.")

                executable_callable = getattr(self.class_instance, op_info.qual_name)

                if instance_action == "GET_OR_CREATE_INSTANCE":
                    result = self.class_instance
                    self.error_details += f"Instance of {op_info.class_name} provided/ensured. Method not called. "
                else:
                    result = executable_callable(*prepared_args, **prepared_kwargs)
                    self.error_details += f"Executed method '{op_info.display_name}'. "
            else:
                return (None, f"Unknown operation type: {op_info.type}")

        except Exception as e:
            import traceback
            tb_str = traceback.format_exc()
            return (None, f"Error executing '{op_info.display_name}': {e}\nTraceback:\n{tb_str}")

        details = self.error_details + f"Result type: {type(result).__name__}. "
        if self.class_instance:
             details += f"Instance type: {type(self.class_instance).__name__}."

        return (result, details)


NODE_CLASS_MAPPINGS = {
    "DynamicPyNode": DynamicPyNode
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "DynamicPyNode": "Dynamic Python Node (Cortex)"
}

# Create a dummy example_module.py for testing in comfy_extras
dummy_module_content = """
def greet(name: str = "World") -> str:
    '''Greets the person.'''
    return f"Hello, {name}!"

def add_numbers(a: int, b: int = 10) -> int:
    return a + b

class SimpleState:
    def __init__(self, initial_val: int = 0):
        self.val = initial_val
        print(f"SimpleState initialized with {initial_val}")

    def increment(self, amount: int = 1) -> int:
        self.val += amount
        return self.val

    def get_current_val(self) -> int:
        return self.val

def _helper_func(): # Should not be listed
    return "hidden"
"""

import os
extras_dir = os.path.join(os.path.dirname(__file__))
example_module_path = os.path.join(extras_dir, "example_module.py")

# Check if running in a context where __file__ is defined (e.g. not a bare exec)
if __file__ and not os.path.exists(example_module_path):
    try:
        with open(example_module_path, "w") as f:
            f.write(dummy_module_content)
        # print(f"[DynamicPyNode] Created dummy file: {example_module_path}") # Debug
    except Exception as e:
        # print(f"[DynamicPyNode] Error creating dummy file {example_module_path}: {e}") # Debug
        pass # Avoid crashing if file ops fail in some restricted env
elif not __file__ and not os.path.exists(example_module_path):
    # Fallback for environments where __file__ might not be set, though less likely for nodes.py loading
    # This part is mainly for the self-contained nature of the example.
    # In a real ComfyUI setup, nodes.py would handle loading this file.
    pass
    # print(f"[DynamicPyNode] __file__ not defined, cannot reliably create dummy module relative to this script if it's not already loaded as a file.")
