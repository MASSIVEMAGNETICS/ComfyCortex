import ast
import importlib.util
import inspect
import types
import os
import logging

# Custom Exceptions
class DynamicNodeError(Exception):
    """Base class for errors in DynamicPyNode."""
    pass

class ModuleLoadError(DynamicNodeError, ImportError):
    """Error during module loading."""
    pass

class OpNotFoundError(DynamicNodeError, NameError):
    """Requested operation (function/class) not found."""
    pass

class InvalidOpError(DynamicNodeError, TypeError):
    """Operation is not a valid type (e.g., not a function or class)."""
    pass

class OpExecutionError(DynamicNodeError, RuntimeError):
    """Error during execution of an operation."""
    pass

class MethodCallError(DynamicNodeError, RuntimeError):
    """Error during a method call on a class instance."""
    pass


class DynamicPyNode:
    """
    DynamicPyNode: Load, introspect, and execute Python modules dynamically.

    This class allows dynamic importing of Python modules from specified filepaths.
    It extracts top-level functions and classes (referred to as "ops"),
    their docstrings, and signatures. These ops can then be listed, inspected,
    and executed.

    When class ops are executed (instantiated), `DynamicPyNode` stores metadata
    about the instance (including the instance itself, constructor arguments,
    and filepath) in its `self.state` dictionary. This allows for method calls
    on these managed instances.

    The module can be reloaded to reflect changes in the source file, which
    updates available ops and their definitions, but clears any existing state.

    Basic Usage Example:
    ```python
    from comfy.utils.dynamic_py_node import DynamicPyNode
    import logging
    logging.basicConfig(level=logging.INFO)

    # Assuming 'my_module.py' contains: def greet(name): return f"Hello, {name}"
    # node = DynamicPyNode("path/to/my_module.py")
    # print(node.list_ops())  # Output: ['greet']
    # print(node.get_op_signature("greet")) # Output: (name)
    # result = node.run_op("greet", "World")
    # print(result)  # Output: Hello, World
    ```

    State Management (`self.state`):
    ---------------------------------
    - When a class op is instantiated via `run_op`, its instance and metadata
      are stored in `self.state`.
    - The key is the class name (`opname`).
    - The value is a dictionary:
        - `'instance'`: The actual class instance.
        - `'args'`: Positional arguments used for instantiation.
        - `'kwargs'`: Keyword arguments used for instantiation.
        - `'module_filepath'`: Path to the source `.py` file.
        - `'classname'`: The name of the class.
    - **Limitation**: Currently, only one managed instance per class name is
      stored. Calling `run_op` again for the same class overwrites the
      previous state entry.

    Reloading (`reload()`):
    -----------------------
    - Re-imports the module from its filepath.
    - Updates ops, docstrings, and signatures.
    - **Important**: Clears all `self.state`, discarding any stored class
      instances and their metadata.

    Security Considerations:
    ------------------------
    This class dynamically loads and executes Python code from an arbitrary filepath.
    This presents significant security risks if untrusted .py files are used.
    The loaded code will have the same permissions as the Python process running this script,
    which means it can potentially:
        - Access the filesystem (read, write, delete files).
        - Access environment variables.
        - Make network requests.
        - Import other modules and use their functionalities (e.g., `os`, `subprocess`).

    **It is CRITICAL to only use `DynamicPyNode` with .py files from trusted sources.**
    No sandboxing is currently implemented beyond basic filtering of dunder methods/classes
    during op extraction. The experimental module removal below is a superficial hardening attempt
    and not a robust sandbox.
    Future enhancements might consider more advanced sandboxing techniques, but these are complex
    and may not cover all attack vectors.
    """
    def __init__(self, filepath: str):
        """
        Initializes the DynamicPyNode by loading and processing the Python module.

        Args:
            filepath (str): The absolute or relative path to the .py module file.

        Raises:
            ModuleLoadError: If the module cannot be loaded (e.g., file not found, syntax error).
            DynamicNodeError: For other initialization errors.
        """
        self.filepath = filepath
        self.logger = logging.getLogger(f"ComfyUI.DynamicPyNode.{os.path.basename(self.filepath)}")
        self.logger.info(f"Initializing DynamicPyNode for {filepath}")
        try:
            self.module = self._import_module(filepath)
            self.ops = self._extract_ops(self.module)
            self.docs = self._extract_docs(filepath)
            self.state = {} # See class docstring for details on self.state structure
            self.logger.info(f"Successfully initialized DynamicPyNode for {filepath}")
        except DynamicNodeError as e:
            self.logger.error(f"Failed to initialize DynamicPyNode for {filepath}: {e}", exc_info=True)
            raise
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during initialization for {filepath}: {e}", exc_info=True)
            raise DynamicNodeError(f"Unexpected error initializing {filepath}: {e}") from e


    def _import_module(self, filepath: str) -> types.ModuleType:
        """
        Dynamically imports a .py file as a Python module.
        Includes an experimental feature to remove certain standard library modules
        (os, subprocess, shutil) from the loaded module's global scope if imported.

        Args:
            filepath (str): Path to the .py file.

        Returns:
            types.ModuleType: The loaded module object.

        Raises:
            ModuleLoadError: If the module cannot be found or loaded due to an error
                             (e.g., FileNotFoundError, SyntaxError during import).
        """
        self.logger.info(f"Attempting to import module: {filepath}")
        modulename = f"dynmod_{os.path.basename(filepath).replace('.', '_')}"
        try:
            spec = importlib.util.spec_from_file_location(modulename, filepath)
            if spec is None: # Check if spec is None, indicating file not found or other issue
                self.logger.error(f"Could not create module spec for {filepath}. File might not exist or is not accessible.")
                raise ModuleLoadError(f"Could not create module spec for {filepath}. File might not exist or is not accessible.")
            mod = importlib.util.module_from_spec(spec)

            # SECURITY: This is a critical point. exec_module executes the code from the file.
            # The loaded module 'mod' will have its own namespace, but can still access
            # global builtins and import any other modules available in the environment.
            spec.loader.exec_module(mod)

            # EXPERIMENTAL: Attempt to remove references to certain critical modules
            # if they were explicitly imported by the loaded module. This is a superficial
            # hardening attempt and not a robust sandbox.
            modules_to_restrict = ['os', 'subprocess', 'shutil']
            for module_name in modules_to_restrict:
                if module_name in mod.__dict__:
                    try:
                        del mod.__dict__[module_name]
                        self.logger.warning(f"Removed potentially harmful module '{module_name}' from loaded module '{modulename}'s scope.")
                    except Exception as e: # pylint: disable=broad-except
                        self.logger.error(f"Could not remove module '{module_name}' from '{modulename}'s scope: {e}", exc_info=True)

            self.logger.info(f"Successfully imported module: {modulename}")
            return mod
        except FileNotFoundError as e:
            self.logger.error(f"Module file not found: {filepath}", exc_info=True)
            raise ModuleLoadError(f"Module file not found: {filepath}") from e
        except Exception as e: # pylint: disable=broad-except
            self.logger.error(f"Failed to import module {filepath}: {e}", exc_info=True)
            raise ModuleLoadError(f"Failed to import module {filepath}: {e}") from e

    def _extract_ops(self, mod: types.ModuleType) -> dict:
        """
        Extracts top-level, non-private (not starting with '_') functions
        and classes from the given module.

        Args:
            mod (types.ModuleType): The module to inspect.

        Returns:
            dict: A dictionary where keys are op names (str) and values are
                  the corresponding function or class objects.

        Raises:
            DynamicNodeError: If an unexpected error occurs during inspection.
        """
        self.logger.info(f"Extracting ops from module: {mod.__name__}")
        ops = {}
        try:
            for name, obj in inspect.getmembers(mod):
                if inspect.isfunction(obj) or inspect.isclass(obj):
                    if not name.startswith('__'):
                        ops[name] = obj
            self.logger.info(f"Found {len(ops)} ops in {mod.__name__}: {list(ops.keys())}")
            return ops
        except Exception as e: # pylint: disable=broad-except
            self.logger.error(f"Failed to extract ops from module {mod.__name__}: {e}", exc_info=True)
            raise DynamicNodeError(f"Failed to extract ops from module {mod.__name__}: {e}") from e


    def _extract_docs(self, filepath: str) -> dict:
        """
        Extracts docstrings for all top-level functions and classes in the
        specified Python file using AST parsing.

        Args:
            filepath (str): Path to the .py file.

        Returns:
            dict: A dictionary where keys are op names (str) and values are
                  their corresponding docstrings (str). Returns empty strings
                  for ops without docstrings.

        Raises:
            ModuleLoadError: If the file cannot be found (re-uses for consistency).
            DynamicNodeError: If there's an AST parsing error or other IOError.
        """
        self.logger.info(f"Extracting docs from filepath: {filepath}")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                src = f.read()
            tree = ast.parse(src)
            docs = {}
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    docs[node.name] = ast.get_docstring(node) or "" # Ensure empty string if None
            self.logger.info(f"Extracted {len(docs)} docstrings from {filepath}")
            return docs
        except FileNotFoundError as e:
            self.logger.error(f"Documentation file not found: {filepath}", exc_info=True)
            raise ModuleLoadError(f"Documentation file not found: {filepath}") from e
        except (ast.ASTError, SyntaxError) as e:
            self.logger.error(f"Failed to parse AST for {filepath} to extract docs: {e}", exc_info=True)
            raise DynamicNodeError(f"Failed to parse AST for {filepath}: {e}") from e
        except IOError as e:
            self.logger.error(f"IOError reading file {filepath} for docs: {e}", exc_info=True)
            raise DynamicNodeError(f"IOError reading file {filepath} for docs: {e}") from e


    def list_ops(self) -> list[str]:
        """
        Lists all available operations (top-level functions and classes)
        discovered in the loaded module.

        Returns:
            List[str]: A list of names of the available operations.
        """
        return list(self.ops.keys())

    def get_op_signature(self, opname: str) -> inspect.Signature:
        """
        Retrieves the signature for a given operation (function or class constructor).

        For functions, it returns `inspect.signature(func)`.
        For classes, it attempts to return `inspect.signature(Class.__init__)`.
        If `__init__` is not an inspectable Python method or inspection fails,
        it tries `inspect.signature(Class)`.
        If all attempts fail, or if the op is not found or invalid, it may
        return an empty `inspect.Signature()` or raise an error.

        Args:
            opname (str): The name of the operation.

        Returns:
            inspect.Signature: The signature object for the operation.
                               Returns an empty signature on failure for functions/classes
                               if specific signatures cannot be determined.

        Raises:
            OpNotFoundError: If the `opname` does not correspond to a loaded op.
            InvalidOpError: If the op is not a function or class.
        """
        if opname not in self.ops:
            self.logger.error(f"Op {opname} not found in self.ops before getting signature.")
            raise OpNotFoundError(f"Op {opname} not found.")

        obj = self.ops[opname]
        self.logger.debug(f"Attempting to get signature for op '{opname}' of type {type(obj).__name__}")

        if inspect.isfunction(obj):
            try:
                signature = inspect.signature(obj)
                self.logger.debug(f"Retrieved signature for function {opname}: {signature}")
                return signature
            except (ValueError, TypeError) as e:
                self.logger.warning(f"Could not determine signature for function {opname} due to {type(e).__name__}: {e}. Falling back to empty signature.", exc_info=True)
                return inspect.Signature()

        elif inspect.isclass(obj):
            if hasattr(obj, '__init__'):
                try:
                    if callable(obj.__init__) and (inspect.isfunction(obj.__init__) or inspect.ismethod(obj.__init__)):
                        signature = inspect.signature(obj.__init__)
                        self.logger.debug(f"Retrieved signature for __init__ of class {opname}: {signature}")
                        return signature
                    else:
                        self.logger.debug(f"__init__ of class {opname} is not an inspectable Python function/method. Trying class signature.")
                except (ValueError, TypeError) as e_init:
                    self.logger.warning(f"Could not determine signature for __init__ of class {opname} due to {type(e_init).__name__}: {e_init}. Trying class signature itself.", exc_info=True)
                except AttributeError:
                     self.logger.warning(f"AttributeError on __init__ for class {opname} despite hasattr. Trying class signature.", exc_info=True)

            try:
                signature = inspect.signature(obj)
                self.logger.debug(f"Retrieved signature for class {opname} (using class type directly): {signature}")
                return signature
            except (ValueError, TypeError) as e_class:
                self.logger.warning(f"Could not determine signature for class {opname} (tried __init__ and class type) due to {type(e_class).__name__}: {e_class}. Falling back to empty signature.", exc_info=True)
                return inspect.Signature()

        else:
            self.logger.error(f"Op {opname} is not a recognized function or class. Type: {type(obj).__name__}")
            raise InvalidOpError(f"Op {opname} is not a function or class (type: {type(obj).__name__}), cannot get signature.")

    def get_op_doc(self, opname: str) -> str:
        """
        Retrieves the docstring for a given operation.

        Args:
            opname (str): The name of the operation.

        Returns:
            str: The docstring of the operation. Returns an empty string if
                 the op is not found or has no docstring.
        """
        self.logger.debug(f"Requesting docstring for op: {opname}")
        return self.docs.get(opname, "")

    def run_op(self, opname: str, *args, **kwargs) -> any:
        """
        Runs the selected operation (function or class).

        - If the op is a function, it's called directly with `*args` and `**kwargs`.
        - If the op is a class, it's instantiated (its `__init__` is called).
          The instance, along with its construction arguments (`args`, `kwargs`),
          module filepath, and classname, is stored in `self.state` keyed by `opname`.
          See class docstring for `self.state` structure and limitations.

        Args:
            opname (str): The name of the operation to run.
            *args: Positional arguments to pass to the function or class constructor.
            **kwargs: Keyword arguments to pass to the function or class constructor.

        Returns:
            Any: The return value of the function, or the new class instance.

        Raises:
            OpNotFoundError: If `opname` is not a found operation.
            InvalidOpError: If the operation is not a callable function or class.
            OpExecutionError: If an exception occurs during the execution of the op.
        """
        if opname not in self.ops:
            self.logger.error(f"Op not found: {opname}")
            raise OpNotFoundError(f"Op {opname} not found.")

        obj = self.ops[opname]
        self.logger.info(f"Running op '{opname}' of type {type(obj).__name__}")
        try:
            if inspect.isclass(obj):
                instance = obj(*args, **kwargs)
                # Store instance and its construction metadata.
                # The 'args' and 'kwargs' could potentially be used for re-instantiation
                # or serialization if they are themselves serializable.
                self.state[opname] = {
                    'instance': instance,
                    'args': args,
                    'kwargs': kwargs,
                    'module_filepath': self.filepath,
                    'classname': opname
                }
                self.logger.info(f"Instantiated class {opname} with args={args}, kwargs={kwargs} and stored in state with metadata.")
                return instance
            elif inspect.isfunction(obj):
                result = obj(*args, **kwargs)
                self.logger.info(f"Function {opname} executed successfully.")
                return result
            else:
                self.logger.error(f"Op {opname} is not a callable function or class.")
                raise InvalidOpError(f"Op {opname} is not a callable function or class.")
        except Exception as e: # pylint: disable=broad-except
            self.logger.error(f"Error executing op {opname}: {e}", exc_info=True)
            raise OpExecutionError(f"Error executing op {opname}: {e}") from e

    def call_method(self, opname_class: str, method_name: str, *args, **kwargs) -> any:
        """
        Calls a method on a class instance that was previously instantiated via `run_op`
        and stored in `self.state`.

        Args:
            opname_class (str): The name of the class op (used as the key in `self.state`).
            method_name (str): The name of the method to call on the instance.
            *args: Positional arguments for the method.
            **kwargs: Keyword arguments for the method.

        Returns:
            Any: The return value of the called method.

        Raises:
            MethodCallError: If the class instance is not found in state, the method
                             doesn't exist, is not callable, or if an error occurs
                             during method execution.
        """
        state_entry = self.state.get(opname_class)
        if not state_entry or 'instance' not in state_entry:
            self.logger.error(f"Instance for class op '{opname_class}' not found in state or state entry malformed for method call '{method_name}'.")
            raise MethodCallError(f"Class instance for '{opname_class}' has not been created, found in state, or state entry is malformed.")

        instance = state_entry['instance']
        self.logger.info(f"Calling method '{method_name}' on instance of '{opname_class}' (retrieved from state)")
        try:
            meth = getattr(instance, method_name)
        except AttributeError as e:
            self.logger.error(f"Method '{method_name}' not found on instance of '{opname_class}'.", exc_info=True)
            raise MethodCallError(f"Method '{method_name}' not found on instance of '{opname_class}'.") from e

        if not callable(meth):
            self.logger.error(f"Attribute '{method_name}' on instance of '{opname_class}' is not callable.")
            raise MethodCallError(f"Attribute '{method_name}' on instance of '{opname_class}' is not callable.")

        try:
            result = meth(*args, **kwargs)
            self.logger.info(f"Method '{method_name}' on '{opname_class}' executed successfully.")
            return result
        except Exception as e: # pylint: disable=broad-except
            self.logger.error(f"Error calling method '{method_name}' on '{opname_class}': {e}", exc_info=True)
            raise MethodCallError(f"Error calling method '{method_name}' on '{opname_class}': {e}") from e

    def reload(self):
        """
        Reloads the associated Python module.

        This re-imports the module, re-extracts operations (functions and classes)
        and their documentation/signatures.

        **Important**: All current state, including any instantiated class objects
        and their metadata stored in `self.state`, is cleared upon reload.
        A more advanced reload strategy that attempts to re-initialize instances
        based on stored arguments is a potential future enhancement but is not
        currently implemented.

        Raises:
            ModuleLoadError: If the module cannot be reloaded (e.g., file changed to have syntax error).
            DynamicNodeError: For other errors during the reload process.
        """
        self.logger.info(f"Attempting to reload module: {self.filepath}")
        try:
            self.module = self._import_module(self.filepath)
            self.ops = self._extract_ops(self.module)
            self.docs = self._extract_docs(self.filepath)
            self.state = {}
            self.logger.info(f"Successfully reloaded module {self.filepath} and reset state (all instances cleared).")
        except DynamicNodeError as e:
            self.logger.error(f"Failed to reload module {self.filepath}: {e}", exc_info=True)
            raise
        except Exception as e: # pylint: disable=broad-except
            self.logger.error(f"An unexpected error occurred during reload of {self.filepath}: {e}", exc_info=True)
            raise DynamicNodeError(f"Unexpected error reloading {self.filepath}: {e}") from e

# ---- EXAMPLE USAGE ----
# This section would typically be removed or adapted for integration into a larger application.
# For testing purposes, it can be kept, perhaps guarded by `if __name__ == "__main__":`
if __name__ == "__main__":
    # Basic logging setup for testing
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Create a dummy your_module.py for testing
    dummy_module_content = """
def my_func(a, b):
    '''This is a test function.'''
    return a + b

class MyClass:
    '''This is a test class.'''
    def __init__(self, val):
        self.val = val
        # Using logger now if available, otherwise print
        try:
            logger = logging.getLogger(f"ComfyUI.DynamicPyNode.your_module_py.MyClass")
            logger.info(f"MyClass instantiated with {val}")
        except NameError: # Fallback if logging not configured (e.g. direct use of module)
             print(f"MyClass instantiated with {val}")


    def some_method(self, x):
        '''A method in MyClass.'''
        return self.val * x
"""
    module_file = "your_module.py"
    with open(module_file, "w") as f:
        f.write(dummy_module_content)

    main_logger = logging.getLogger(__name__) # Logger for the main script
    main_logger.info(f"Attempting to initialize DynamicPyNode with '{module_file}'")

    node = None
    try:
        node = DynamicPyNode(module_file)
    except DynamicNodeError as e:
        main_logger.error(f"Failed to initialize DynamicPyNode: {e}", exc_info=True)
        exit(1)


    main_logger.info(f"\nAvailable ops: {node.list_ops()}")
    for opname in node.list_ops():
        main_logger.info(f"\n=== {opname} ===")
        main_logger.info(f"Doc: {node.get_op_doc(opname)}")
        try:
            sig = node.get_op_signature(opname)
            main_logger.info(f"Signature: {sig}")
            if sig:
                for param_name, param in sig.parameters.items():
                    main_logger.info(f"  Param: {param_name}, Kind: {param.kind}, Default: {param.default}")
        except OpNotFoundError as e:
             main_logger.error(f"Could not get signature for {opname}: {e}")


    # Example: run a function
    if "my_func" in node.ops:
        main_logger.info("\nRunning op 'my_func' with arguments (3, 5)")
        try:
            out = node.run_op("my_func", 3, 5)
            main_logger.info(f"my_func output: {out}")
        except OpExecutionError as e:
            main_logger.error(f"Error running my_func: {e}", exc_info=True)


    # Example: instantiate a class and call method
    if "MyClass" in node.ops:
        main_logger.info("\nRunning op 'MyClass' (instantiating) with argument (10)")
        try:
            obj = node.run_op("MyClass", 10)

            main_logger.info("\nCalling method 'some_method' on 'MyClass' instance with argument (4)")
            out_method = node.call_method("MyClass", "some_method", 4)
            main_logger.info(f"MyClass.some_method output: {out_method}")

            main_logger.info("\nTesting call to non-existent method:")
            try:
                node.call_method("MyClass", "non_existent_method", 5)
            except MethodCallError as e:
                main_logger.error(f"Caught expected error for non_existent_method: {e}")

        except OpExecutionError as e:
            main_logger.error(f"Error instantiating or calling method on MyClass: {e}", exc_info=True)
        except MethodCallError as e: # Catch if run_op succeeded but call_method failed
            main_logger.error(f"Error in method call for MyClass: {e}", exc_info=True)

    main_logger.info("\nTesting running a non-existent op:")
    try:
        node.run_op("non_existent_op", 1, 2)
    except OpNotFoundError as e:
        main_logger.error(f"Caught expected error for non_existent_op: {e}")


    # Test reload
    main_logger.info("\nTesting reload...")
    # Modify the dummy module to simulate a change
    # Modify the dummy module to simulate a change
    dummy_module_content_v2 = """
import os # Intentionally import os to test restriction

def my_func(a, b): # Changed functionality
    '''This is an updated test function.'''
    return a * b

class MyClass: # Changed functionality
    '''This is an updated test class.'''
    def __init__(self, val):
        self.val = val
        # Using logger now if available, otherwise print
        try:
            # Note: logger name should ideally be specific to the module's actual name if known
            # For this dummy module, this is fine.
            logger = logging.getLogger(f"ComfyUI.DynamicPyNode.your_module_py.MyClass")
            logger.info(f"MyClass v2 instantiated with {val}")
        except NameError: # Fallback if logging not configured
             print(f"MyClass v2 instantiated with {val}")


    def some_method(self, x): # Changed functionality
        '''A method in MyClass v2.'''
        return self.val + x

def new_func():
    '''A new function after reload.'''
    return "Hello from new_func"

def try_os_access():
    '''Attempts to list current directory using os module.'''
    try:
        # If 'os' was removed from module's globals by DynamicPyNode, this should fail
        return os.listdir(".")
    except NameError:
        # This NameError will be caught if 'os' is not defined in the module's scope
        # which is the intended effect of del mod.__dict__['os']
        return "os module not accessible due to NameError"
    except Exception as e:
        return f"Error during os access: {str(e)}"

def try_file_open(filename="test_output.txt"):
    '''Attempts to open and write to a file.'''
    try:
        # This uses the 'open' builtin, which is not being restricted by the current experimental code.
        with open(filename, "w") as f:
            f.write("This is a test from try_file_open.")
        # Attempt to clean up the file - this requires 'os' to be available.
        try:
            os.remove(filename)
            return f"Successfully wrote to and removed {filename}"
        except NameError: # os might not be available
            return f"Successfully wrote to {filename}, but os.remove failed (NameError)."
        except Exception as e_remove: # other errors during remove
            return f"Successfully wrote to {filename}, but os.remove failed: {str(e_remove)}"
    except NameError: # If 'open' itself was somehow made unavailable (not the case here)
       return "open function not accessible"
    except Exception as e:
       return f"Error during file open: {str(e)}"

class NoInitClass:
    '''A class without an explicit __init__ method.'''
    pass

class BuiltinWrapper:
    '''A class that might wrap a builtin or have a non-standard __init__.'''
    def __init__(self, data):
        self.data = list(data)

    def get_data(self):
        return self.data
"""
    with open(module_file, "w") as f:
        f.write(dummy_module_content_v2)

    try:
        node.reload()
        main_logger.info("Reload complete.")
        main_logger.info(f"Available ops after reload: {node.list_ops()}")

        if "new_func" in node.ops:
            main_logger.info("\nRunning 'new_func'")
            out_new = node.run_op("new_func")
            main_logger.info(f"new_func output: {out_new}")

        if "my_func" in node.ops: # Test updated my_func
            main_logger.info("\nRunning updated 'my_func' with arguments (3, 5)")
            out_updated = node.run_op("my_func", 3, 5) # Should be 3*5=15
            main_logger.info(f"Updated my_func output: {out_updated}")

        # Test instantiating MyClass again to see v2 message
        if "MyClass" in node.ops:
            main_logger.info("\nRunning op 'MyClass' (instantiating) again with argument (100)")
            instance_v2 = node.run_op("MyClass", 100) # This should trigger the MyClass v2 logger message
            main_logger.info(f"MyClass v2 instance created: {instance_v2}")
            if "MyClass" in node.state:
                main_logger.info(f"State for MyClass (args): {node.state['MyClass']['args']}")
                main_logger.info(f"State for MyClass (kwargs): {node.state['MyClass']['kwargs']}")
                main_logger.info(f"State for MyClass (filepath): {node.state['MyClass']['module_filepath']}")

        # Test security-related functions
        if "try_os_access" in node.ops:
            main_logger.info("\nAttempting to run 'try_os_access' (testing 'os' module restriction)")
            os_access_result = node.run_op("try_os_access")
            main_logger.info(f"try_os_access output: {os_access_result}")

        if "try_file_open" in node.ops:
            main_logger.info("\nAttempting to run 'try_file_open' (testing 'open' builtin)")
            file_open_result = node.run_op("try_file_open")
            main_logger.info(f"try_file_open output: {file_open_result}")

        # Test signature retrieval for new classes
        if "NoInitClass" in node.ops:
            main_logger.info("\n=== NoInitClass ===")
            main_logger.info(f"Doc: {node.get_op_doc('NoInitClass')}")
            main_logger.info(f"Signature: {node.get_op_signature('NoInitClass')}")
            # node.run_op("NoInitClass") # Can be run if needed

        if "BuiltinWrapper" in node.ops:
            main_logger.info("\n=== BuiltinWrapper ===")
            main_logger.info(f"Doc: {node.get_op_doc('BuiltinWrapper')}")
            main_logger.info(f"Signature: {node.get_op_signature('BuiltinWrapper')}")
            # instance_bw = node.run_op("BuiltinWrapper", [1,2,3])
            # main_logger.info(f"BuiltinWrapper instance data: {instance_bw.get_data()}")


    except DynamicNodeError as e:
        main_logger.error(f"Error during reload or post-reload operations: {e}", exc_info=True)


    # Clean up dummy module
    try:
        os.remove(module_file)
        main_logger.info(f"\nCleaned up dummy module '{module_file}'.")
    except OSError as e:
        main_logger.error(f"Error removing dummy module {module_file}: {e}")
