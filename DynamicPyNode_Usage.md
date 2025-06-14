# DynamicPyNode Usage Guide (Comfy Cortex)

## 1. Overview

The `DynamicPyNode` is a powerful and flexible node within Comfy Cortex that allows you to load any Python module (`.py` file) and execute its functions or class methods directly within your ComfyUI workflow. This promotes extreme modularity and allows for rapid prototyping and integration of custom Python code.

## 2. How it Works

1.  **Module Loading:** You provide a path to a Python file. The node parses this file to discover available functions, classes, and methods.
2.  **Operation Selection:** You select the specific function, class constructor (`__init__`), or class method you want to execute from a dropdown list populated from the loaded module.
3.  **Argument Provision:** Arguments for the selected operation are provided as a JSON string.
4.  **Execution:** The node calls the selected Python callable with the provided arguments.
5.  **State Management:** For classes, the node can maintain an instance of the class, allowing for stateful operations across multiple calls.

## 3. Node Inputs

*   **`module_path` (String):**
    *   The file path to the Python module you want to load.
    *   Example: `"comfy_extras/my_custom_logic.py"` or an absolute path.
    *   **Note:** After changing this path, you might need to queue the prompt once for the `selected_operation_id` list to refresh with operations from the new module. Check the `details` output for confirmation that the module loaded.

*   **`selected_operation_id` (Dropdown/COMBO):**
    *   A dropdown list of all discoverable operations from the loaded `module_path`.
    *   Format:
        *   Functions: `my_function_name`
        *   Class Constructors: `MyClassName.__init__`
        *   Class Methods: `MyClassName.my_method_name`
    *   This list is populated after the module specified in `module_path` is successfully parsed.

*   **`op_args_json` (String, Multiline):**
    *   A JSON formatted string representing a dictionary of arguments to pass to the selected operation.
    *   Keys in the JSON object should match the parameter names of the Python function or method.
    *   Example for `def greet(name, message="Hi"):`:
        ```json
        {
          "name": "Alice",
          "message": "Hello there!"
        }
        ```
    *   Or, if `message` should use its default:
        ```json
        {
          "name": "Bob"
        }
        ```
    *   For operations with no arguments (other than `self` for methods), use an empty JSON object: `{}`.

*   **`instance_action` (Dropdown/COMBO):**
    *   Controls behavior when the selected operation involves a class:
        *   **`CALL`**:
            *   If `selected_operation_id` is `MyClass.__init__`: Creates a new instance of `MyClass` and stores it in the node. The instance is also the `result`.
            *   If `selected_operation_id` is `MyClass.my_method`: Calls `my_method` on the currently stored instance. If no instance exists, it attempts to create one using the class's default `__init__` parameters.
        *   **`REINSTANTIATE_CALL`**:
            *   If `selected_operation_id` is `MyClass.__init__`: Creates a new instance, replacing any existing one.
            *   If `selected_operation_id` is `MyClass.my_method`: Always creates a *new* instance of `MyClass` (using its default `__init__`) before calling `my_method`. Any previously stored instance is replaced.
        *   **`GET_OR_CREATE_INSTANCE`**:
            *   If `selected_operation_id` is `MyClass.__init__`: Creates a new instance (if arguments are provided in `op_args_json` for `__init__`) or retrieves the existing one if compatible, and outputs the instance itself as the `result`.
            *   If `selected_operation_id` is `MyClass.my_method`: Ensures an instance exists (creating a default one if needed, similar to `CALL`). Then, outputs the *instance itself* as the `result`, *without calling the selected method*. This is useful to get a reference to a stateful object.

*   **`reset_instance_trigger` (Boolean, Optional):**
    *   If set to `True` during an execution, any currently stored class instance within the node will be discarded. The next operation requiring an instance will create a new one. Defaults to `False`.

## 4. Node Outputs

*   **`result` (ANY):**
    *   The return value from the executed Python function or method.
    *   If the operation was `MyClass.__init__` (and `instance_action` wasn't `GET_OR_CREATE_INSTANCE` specifically for a method), this will be the newly created class instance.
    *   If `instance_action` is `GET_OR_CREATE_INSTANCE` for any class-related operation, this will be the class instance itself.
    *   If the Python callable returns multiple values (e.g., `return a, b`), the `result` will be a tuple `(a, b)`.

*   **`details` (STRING):**
    *   Provides feedback about the node's operation:
        *   Confirmation of module loading.
        *   Number of operations found.
        *   Expected parameters for the currently selected operation (name, type hint, default value).
        *   Expected return type hint for the selected operation.
        *   Status of instance creation/usage.
        *   Any errors encountered during parsing, argument preparation, or execution.
    *   **Always check this output, especially when setting up a new operation or debugging!**

## 5. Creating Compatible Python Modules

Any standard Python (`.py`) file can be used.

*   **Functions:** Public top-level functions (not starting with `_`) will be listed.
    ```python
    def my_public_function(param1: str, param2: int = 0) -> dict:
        '''My docstring for the function.'''
        return {"input": param1, "value": param2}

    def _internal_helper(): # Won't be listed
        pass
    ```

*   **Classes:** Public classes (not starting with `_`) and their public methods (not starting with `_`, except for special methods like `__call__`) will be discoverable.
    *   The constructor `__init__` will be listed as `MyClassName.__init__`.
    *   Other methods will be listed as `MyClassName.my_method`.
    ```python
    class MyProcessor:
        '''Docstring for MyProcessor class.'''
        def __init__(self, api_key: str, retries: int = 3):
            '''Constructor docstring.'''
            self.api_key = api_key
            self.retries = retries
            self.state = 0

        def process_data(self, data: list) -> list:
            '''Processes the data.'''
            self.state += len(data)
            return [item * 2 for item in data]

        def get_state(self) -> int:
            return self.state

        def _internal_method(self): # Won't be listed
            pass
    ```

*   **Type Hinting:** While not strictly enforced by `DynamicPyNode` at runtime (Python is dynamically typed), providing type hints in your Python code (`param: str`, `-> int`) will improve the information shown in the `details` output, making it easier to construct the `op_args_json`.

*   **Docstrings:** Docstrings for functions, classes, and methods are extracted and may be shown in the `details` output or used by future UI enhancements.

*   **Imports:** Your Python module can have its own imports; ensure those dependencies are available in your ComfyUI environment.

## 6. Example Workflow (using `comfy_extras/example_module.py`)

The `DynamicPyNode` automatically creates `comfy_extras/example_module.py` if it doesn't exist. It contains:
```python
# comfy_extras/example_module.py
def greet(name: str = "World") -> str:
    '''Greets the person.'''
    return f"Hello, {name}!"

def add_numbers(a: int, b: int = 10) -> int:
    return a + b

class SimpleState:
    def __init__(self, initial_val: int = 0):
        self.val = initial_val
        print(f"SimpleState initialized with {initial_val}") # For server console log

    def increment(self, amount: int = 1) -> int:
        self.val += amount
        return self.val

    def get_current_val(self) -> int:
        return self.val
```

**Steps:**

1.  **Add Node:** Add a `Dynamic Python Node (Cortex)` to your graph.
2.  **Set Module Path:**
    *   Set `module_path` to: `"comfy_extras/example_module.py"`
3.  **Load Operations (Important!):**
    *   Queue the prompt once (Ctrl+Enter or click Queue Prompt).
    *   The `details` output should confirm module loading. The `selected_operation_id` dropdown will now be populated. If it doesn't update, you might need to manually trigger a refresh of the node in the UI if ComfyUI supports it, or sometimes just clicking off and on the node helps. Forcing another queue is the most reliable.
4.  **Execute `greet` function:**
    *   Select `greet` from `selected_operation_id`.
    *   Set `op_args_json` to:
        ```json
        {
          "name": "Comfy Cortex User"
        }
        ```
    *   Set `instance_action` to `CALL` (it's a function, so instance actions don't heavily apply but `CALL` is fine).
    *   Queue prompt.
    *   **Output:** `result` will be `"Hello, Comfy Cortex User!"`. Check `details` for parameter info.

5.  **Instantiate `SimpleState` class:**
    *   Select `SimpleState.__init__` from `selected_operation_id`.
    *   Set `op_args_json` to:
        ```json
        {
          "initial_val": 5
        }
        ```
    *   Set `instance_action` to `CALL` (or `GET_OR_CREATE_INSTANCE`).
    *   Queue prompt.
    *   **Output:** `result` will be the `SimpleState` instance. `details` confirms instantiation. The node now holds this instance.

6.  **Call `increment` method:**
    *   Select `SimpleState.increment` from `selected_operation_id`.
    *   Set `op_args_json` to:
        ```json
        {
          "amount": 3
        }
        ```
    *   Set `instance_action` to `CALL`.
    *   Queue prompt.
    *   **Output:** `result` will be `8` (5 + 3). The instance within the node now has `val = 8`.

7.  **Call `get_current_val` method:**
    *   Select `SimpleState.get_current_val` from `selected_operation_id`.
    *   Set `op_args_json` to: `{}` (no arguments needed).
    *   Set `instance_action` to `CALL`.
    *   Queue prompt.
    *   **Output:** `result` will be `8`.

8.  **Reset and Re-instantiate:**
    *   Set `reset_instance_trigger` to `True`.
    *   Select `SimpleState.__init__`, `op_args_json` to `{"initial_val": 100}`, `instance_action` to `CALL`.
    *   Queue prompt. The old instance (val=8) is gone. A new one (val=100) is created.
    *   Set `reset_instance_trigger` back to `False`.
    *   Select `SimpleState.get_current_val`, queue. `result` will be `100`.

## 7. Stateful Operations with Classes

As seen in the example:
- Call `MyClass.__init__` to create and store an instance.
- Subsequent calls to `MyClass.my_method` (with `instance_action="CALL"`) will operate on that stored instance, remembering changes to `self.attributes`.
- Use `REINSTANTIATE_CALL` if you want a fresh, default-initialized instance for a method call, or if you want to replace the stored instance when calling `__init__`.
- Use `GET_OR_CREATE_INSTANCE` (especially with `__init__`) to get a direct reference to the stateful object, which you could then potentially pass to other specialized nodes if needed (though `IO.ANY` connections require care).
- `reset_instance_trigger` explicitly clears the stored instance.

## 8. Tips and Troubleshooting

*   **Check `details` Output:** This is your best friend for debugging. It shows loaded operations, expected parameters, return types, and errors.
*   **JSON Syntax:** Ensure `op_args_json` is valid JSON. Keys and strings must be in double-quotes.
*   **Module Path:** Use relative paths from your ComfyUI root or absolute paths. Ensure the Python file exists and is readable.
*   **Operation Names:** Match the names in the `selected_operation_id` dropdown precisely.
*   **Refreshing Operations List:** If you change `module_path`, the `selected_operation_id` list might not update in the UI immediately. Queueing the prompt once usually forces the node to re-evaluate and update its internal list of operations, which should then refresh the combo box.
*   **Python Environment:** The Python code in your module runs within ComfyUI's Python environment. Ensure any libraries it imports are installed there.
*   **Server Logs:** Check the ComfyUI server console for print statements from your Python module (like the `print` in `SimpleState.__init__`) or more detailed error tracebacks.

This node provides a powerful way to extend ComfyUI with your own Python logic without needing to write full custom nodes for every small function or class.
