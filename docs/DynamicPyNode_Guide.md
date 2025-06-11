# DynamicPyNode: A Guide to Dynamic Python Module Loading

## 1. Introduction

`DynamicPyNode` is a utility class within the ComfyUI ecosystem designed to dynamically load Python modules (`.py` files) and interact with their top-level functions and classes. It allows you to treat any Python file as a source of "operations" (ops) that can be introspected, executed, and managed.

**Key Use Cases:**
- Extending ComfyUI with custom Python logic without the need to write a full, formally structured custom node immediately.
- Rapid prototyping of new functionalities.
- Loading and using utility scripts or small libraries dynamically.
- Creating nodes whose behavior can be defined by an external, easily modifiable Python file.

## 2. Core Concepts

### 2.1. Loading Modules
You initialize `DynamicPyNode` with the filepath to a Python module.
```python
from comfy.utils.dynamic_py_node import DynamicPyNode
node = DynamicPyNode("path/to/your/module.py")
```
The module is imported, and its contents are analyzed.

### 2.2. Operations (Ops)
- **Discovery**: `DynamicPyNode` automatically discovers all top-level, non-private (not starting with `_`) functions and classes in the loaded module. These are referred to as "ops."
- **Listing Ops**: `node.list_ops()` returns a list of names of available ops.

### 2.3. Signatures and Docstrings
- **Docstrings**: `node.get_op_doc("op_name")` returns the docstring of the specified function or class.
- **Signatures**: `node.get_op_signature("op_name")` returns an `inspect.Signature` object for the function or the `__init__` method of a class. This allows you to determine its parameters, defaults, and annotations.

### 2.4. Running Ops
- `node.run_op("op_name", *args, **kwargs)` executes the specified op.
- **Functions**: If the op is a function, it's called directly, and its return value is provided.
- **Classes**: If the op is a class, it's instantiated (its `__init__` is called), and the new instance is returned. The instance is also stored internally by `DynamicPyNode`.

### 2.5. State Management for Class Instances
- When a class op is run (instantiated), `DynamicPyNode` stores information about this instance in its `self.state` dictionary.
- The key for this state is the class name (op name).
- The value is a dictionary containing:
    - `'instance'`: The actual class instance.
    - `'args'`: Positional arguments used during instantiation.
    - `'kwargs'`: Keyword arguments used during instantiation.
    - `'module_filepath'`: Path to the source `.py` file.
    - `'classname'`: The name of the class.
- **Limitation**: Currently, `DynamicPyNode` manages only one instance per class name. If you call `run_op` again for the same class, the previous instance in the state will be overwritten.

### 2.6. Calling Methods on Instances
- `node.call_method("op_name_of_class", "method_name", *args, **kwargs)` allows you to call a method on a class instance that was previously created via `run_op`.
- `op_name_of_class` refers to the class name used to store the instance in the state.

### 2.7. Reloading Modules
- `node.reload()` re-imports the Python module from its filepath.
- This updates the available ops, their docstrings, and signatures if the `.py` file has changed.
- **Important**: Reloading clears all internal state, including any instantiated class objects and their metadata.

## 3. Getting Started: Basic Usage Example

Let's use an example module, `example_math_utils.py`:
```python
# comfy/utils/dynamic_node_test_examples/example_math_utils.py
def add(a: int, b: int) -> int:
    """Adds two integers."""
    return a + b

def subtract(a: int, b: int) -> int:
    """Subtracts b from a."""
    return a - b
```

Now, let's use `DynamicPyNode` to interact with it:
```python
from comfy.utils.dynamic_py_node import DynamicPyNode
import logging

# Configure basic logging to see output from DynamicPyNode
logging.basicConfig(level=logging.INFO)

# Ensure the path is correct for your setup
math_module_path = "comfy/utils/dynamic_node_test_examples/example_math_utils.py"

try:
    math_node = DynamicPyNode(math_module_path)

    print("Available ops:", math_node.list_ops())
    # Output: Available ops: ['add', 'subtract', 'check_os_import'] (or similar)

    op_to_run = "add"
    if op_to_run in math_node.list_ops():
        print(f"Doc for '{op_to_run}':", math_node.get_op_doc(op_to_run))
        print(f"Signature for '{op_to_run}':", math_node.get_op_signature(op_to_run))

        result = math_node.run_op(op_to_run, 5, 3)
        print(f"Result of {op_to_run}(5, 3):", result)
        # Output: Result of add(5, 3): 8

    # Example with a class (assuming example_class_module.py is available)
    # class_module_path = "comfy/utils/dynamic_node_test_examples/example_class_module.py"
    # class_node = DynamicPyNode(class_module_path)
    # greeter_instance = class_node.run_op("Greeter", name="Dynamic User")
    # message = class_node.call_method("Greeter", "greet", punctuation="!!!")
    # print(message) # Output: Hello, Dynamic User!!!
    # print("Greeter state:", class_node.state["Greeter"]['args']) # ('Dynamic User',)

except Exception as e:
    print(f"An error occurred: {e}")
```

## 4. Error Handling

`DynamicPyNode` uses custom exceptions to signal specific error conditions:
- `DynamicNodeError`: Base class for errors specific to `DynamicPyNode`.
- `ModuleLoadError(DynamicNodeError, ImportError)`: Raised if the Python module cannot be loaded (e.g., file not found, syntax error in module).
- `OpNotFoundError(DynamicNodeError, NameError)`: Raised if a requested op (function/class name) does not exist in the loaded module.
- `InvalidOpError(DynamicNodeError, TypeError)`: Raised if an op is not of a supported type (e.g., trying to get a signature for something that isn't a function or class).
- `OpExecutionError(DynamicNodeError, RuntimeError)`: Raised if an error occurs during the execution of an op (e.g., an exception within the called function or class `__init__`).
- `MethodCallError(DynamicNodeError, RuntimeError)`: Raised if an error occurs when trying to call a method on a class instance (e.g., instance not found, method not found, error during method execution).

Always wrap calls to `DynamicPyNode` methods in `try...except` blocks to handle these potential errors gracefully.

## 5. Security Considerations

**CRITICAL: `DynamicPyNode` executes code from the Python files you provide. Only load modules from trusted sources.**

- The loaded code runs with the same permissions as the main ComfyUI Python process. It can access the filesystem, network, environment variables, etc.
- **No Sandboxing**: While `DynamicPyNode` has an *experimental* feature to attempt to remove certain imported modules (like `os`) from the loaded module's scope, this is **not a sandbox** and can be bypassed. Do not rely on it for security.
- Always vet the source and content of Python files before loading them with `DynamicPyNode`.

## 6. Conceptual Integration with ComfyUI (Custom Node Example)

While `DynamicPyNode` is a backend utility, here's a conceptual example of how it could be wrapped into a ComfyUI custom node:

```python
# (Conceptual - not a runnable file, but for illustration)
# from comfy.utils.dynamic_py_node import DynamicPyNode, DynamicNodeError
# import nodes # ComfyUI's way to get node_info_outputs, etc.

# class DynamicPyExecutorNode:
#     CATEGORY = "utils/dynamic"
#     # Output node since return types are dynamic
#     # For specific known return types, you'd define them.
#     OUTPUT_NODE = True

#     @classmethod
#     def INPUT_TYPES(cls):
#         return {
#             "required": {
#                 "module_path": ("STRING", {"default": "path/to/your/module.py", "multiline": False}),
#                 "op_name": ("STRING", {"default": "my_function", "multiline": False}),
#                 "json_args": ("STRING", {"default": "[]", "multiline": True}), # e.g., [1, 2]
#                 "json_kwargs": ("STRING", {"default": "{}", "multiline": True}), # e.g., {"param": "value"}
#             },
#             "optional": {
#                  "instance_name": ("STRING", {"default": "", "multiline": False}), # For call_method
#                  "method_name": ("STRING", {"default": "", "multiline": False}), # For call_method
#             }
#         }

#     # RETURN_TYPES and FUNCTION would need to be more dynamic or generic.
#     # ComfyUI's system might need more specific handling for dynamic outputs.
#     # This is a simplified concept.
#     RETURN_TYPES = ("*",) # Representing any type
#     FUNCTION = "execute_dynamic_op"

#     def execute_dynamic_op(self, module_path, op_name, json_args, json_kwargs, instance_name=None, method_name=None):
#         import json
#         try:
#             args = json.loads(json_args)
#             kwargs = json.loads(json_kwargs)

#             # This node would likely need to cache DynamicPyNode instances or manage them
#             node_instance_cache = {} # Simplistic cache

#             if module_path not in node_instance_cache:
#                 node_instance_cache[module_path] = DynamicPyNode(module_path)
#
#             dyn_node = node_instance_cache[module_path]

#             if instance_name and method_name:
#                 # Ensure class was instantiated if instance_name is given
#                 if instance_name not in dyn_node.state:
#                     # Maybe auto-instantiate if it's a class op? Or require prior run_op.
#                     # For this example, assume it was instantiated by a previous call or setup.
#                     # Alternatively, instance_name could be the op_name of the class itself.
#                     if instance_name in dyn_node.ops and inspect.isclass(dyn_node.ops[instance_name]):
#                         # Auto-instantiate with no args if not in state (simplification)
#                         # A real node would need better arg handling for instantiation here.
#                         dyn_node.run_op(instance_name)
#                     else:
#                         raise ValueError(f"Instance '{instance_name}' not found in state and not a known class op.")
#                 result = dyn_node.call_method(instance_name, method_name, *args, **kwargs)
#             else:
#                 result = dyn_node.run_op(op_name, *args, **kwargs)

#             # ComfyUI custom nodes return a tuple, where each element is an output.
#             # If the result is a single value, wrap it in a tuple.
#             # If the op returns multiple values (e.g. as a tuple), they might need to be
#             # mapped to multiple output slots if the node was defined with them.
#             return (result,)
#         except DynamicNodeError as dne:
#             # Log specific DynamicNode errors
#             # ComfyUI might have a way to show errors in the UI
#             print(f"[DynamicPyExecutorNode] DynamicNodeError: {dne}")
#             raise # Re-raise to be caught by ComfyUI's error handling
#         except json.JSONDecodeError as je:
#             print(f"[DynamicPyExecutorNode] JSON Error: Invalid JSON in args/kwargs: {je}")
#             raise
#         except Exception as e:
#             print(f"[DynamicPyExecutorNode] Error: {e}")
#             raise
# ```
# *Disclaimer: The above ComfyUI node is a rough conceptual sketch and would require significant refinement to be a robust, usable custom node, especially regarding dynamic input/output typing and state persistence across executions.*


## 7. API Reference (Summary)

- `DynamicPyNode(filepath: str)`: Constructor.
- `list_ops() -> List[str]`: Lists available function/class names.
- `get_op_doc(opname: str) -> str`: Gets docstring for an op.
- `get_op_signature(opname: str) -> inspect.Signature`: Gets signature for a function or class `__init__`.
- `run_op(opname: str, *args, **kwargs) -> Any`: Executes a function or instantiates a class.
- `call_method(opname_class: str, method_name: str, *args, **kwargs) -> Any`: Calls a method on a stored class instance.
- `reload()`: Reloads the module, updating ops and clearing state.

For detailed information on parameters, return types, and exceptions, please refer to the docstrings within the `dynamic_py_node.py` file.

## 8. Future Considerations & Limitations
- **Single Instance per Class**: Currently, only one instance of a given class is managed by `DynamicPyNode` state, keyed by class name.
- **Sandboxing**: The current module restriction feature is experimental and not a true sandbox.
- **State Serialization**: The stored `args` and `kwargs` for class instances could potentially be used for serialization and re-instantiation, but this is not implemented.
- **Asynchronous Operations**: `async` functions/methods are not specially handled.

---
End of DynamicPyNode_Guide.md
