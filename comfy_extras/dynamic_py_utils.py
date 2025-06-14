from __future__ import annotations
import inspect
import importlib.util
from typing import List, Dict, Any, Callable, Union
from dataclasses import dataclass, field

@dataclass
class ParameterInfo:
    name: str
    annotation: Any = field(default=inspect.Parameter.empty)
    default: Any = field(default=inspect.Parameter.empty)
    kind: Any = field(default=inspect.Parameter.POSITIONAL_OR_KEYWORD)

    def __post_init__(self):
        # Make default truly empty if it's the sentinel
        if self.default is inspect.Parameter.empty:
            self.default_value_is_set = False
        else:
            self.default_value_is_set = True

        # Simplify annotation for display if possible
        if self.annotation is inspect.Parameter.empty:
            self.annotation_str = "Any"
        elif hasattr(self.annotation, '__name__'):
            self.annotation_str = self.annotation.__name__
        else:
            self.annotation_str = str(self.annotation)


@dataclass
class CallableInfo:
    id_name: str # Unique identifier: "my_function", "MyClass.__init__", "MyClass.my_method"
    display_name: str # User-friendly: "my_function", "MyClass (Constructor)", "MyClass.my_method"
    type: str  # "function", "class_constructor", "class_method"

    # Store information to retrieve the callable later, rather than the callable itself,
    # to avoid issues with module reloading or state if the utils are separate.
    module_name: str
    qual_name: str # e.g., "my_function" or "MyClass" or "MyClass.my_method" (for methods, this is just method name)
    class_name: str | None = None # Name of the class if type is "class_constructor" or "class_method"

    parameters: List[ParameterInfo] = field(default_factory=list)
    return_annotations: Any = field(default=inspect.Parameter.empty)
    docstring: str | None = None

    @property
    def return_annotation_str(self) -> str:
        if self.return_annotations is inspect.Parameter.empty:
            return "Any"
        elif hasattr(self.return_annotations, '__name__'):
            return self.return_annotations.__name__
        else:
            return str(self.return_annotations)

def _extract_callable_details(name: str, callable_obj: Callable, sig_callable_obj: Callable | None = None) -> tuple[List[ParameterInfo], Any, str | None]:
    if sig_callable_obj is None:
        sig_callable_obj = callable_obj

    params_info = []
    try:
        sig = inspect.signature(sig_callable_obj)
        for param_name, param_obj in sig.parameters.items():
            if param_obj.kind == inspect.Parameter.KEYWORD_ONLY and param_name == '_ comfy_extras_dynamic_py_utils_SENTINEL_': # Skip internal sentinel
                continue
            params_info.append(ParameterInfo(
                name=param_name,
                annotation=param_obj.annotation,
                default=param_obj.default,
                kind=param_obj.kind
            ))
        return_annotation = sig.return_annotation
    except ValueError: # Happens with some built-ins or C functions
        # Attempt to get a simplified signature if possible, or mark as unknown
        # For now, we'll just leave params empty and return_annotation as empty
        # if full signature inspection fails.
        # A more robust solution might try other ways to get argspec for builtins.
        params_info = [ParameterInfo(name="*args", kind=inspect.Parameter.VAR_POSITIONAL), ParameterInfo(name="**kwargs", kind=inspect.Parameter.VAR_KEYWORD)]
        return_annotation = inspect.Parameter.empty

    doc = inspect.getdoc(callable_obj)
    return params_info, return_annotation, doc

def parse_python_file(file_path: str) -> Dict[str, CallableInfo]:
    parsed_ops: Dict[str, CallableInfo] = {}
    module_name = f"dynamic_module_{inspect.safe_join('', file_path).replace('.', '_').replace('/', '_').replace('-', '_')}"

    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            print(f"[DynamicPyUtils] Error: Could not create module spec for {file_path}")
            return parsed_ops

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except FileNotFoundError:
        print(f"[DynamicPyUtils] Error: File not found {file_path}")
        return parsed_ops
    except SyntaxError as e:
        print(f"[DynamicPyUtils] Error: Syntax error in {file_path}: {e}")
        return parsed_ops
    except Exception as e:
        print(f"[DynamicPyUtils] Error: Could not import module {file_path}: {e}")
        return parsed_ops

    for member_name, member_obj in inspect.getmembers(module):
        if member_name.startswith("_"): # Skip private/protected members generally
            continue

        # Top-level functions
        if inspect.isfunction(member_obj) and member_obj.__module__ == module_name:
            params, ret_ann, doc = _extract_callable_details(member_name, member_obj)
            op_id = member_name
            parsed_ops[op_id] = CallableInfo(
                id_name=op_id,
                display_name=member_name,
                type="function",
                module_name=module_name,
                qual_name=member_name,
                parameters=params,
                return_annotations=ret_ann,
                docstring=doc
            )

        # Classes
        elif inspect.isclass(member_obj) and member_obj.__module__ == module_name:
            class_name = member_name

            # Class constructor (__init__)
            init_method = getattr(member_obj, '__init__', None)
            # We need to inspect member_obj for __init__ signature, not init_method directly if it's a slot wrapper
            # For classes, inspect.signature(member_obj) gives the constructor signature
            try:
                # Add a sentinel to distinguish "no __init__" from "failed to inspect __init__"
                _init_params_sentinel = object()
                _init_ret_ann_sentinel = object()
                _init_doc_sentinel = object()

                init_params, init_ret_ann, init_doc = _init_params_sentinel, _init_ret_ann_sentinel, _init_doc_sentinel

                # Check if __init__ is a user-defined method or object.__init__
                # For object.__init__ (or if no __init__), signature might be tricky or uninformative
                # For user-defined classes, inspect.signature(member_obj) is usually best for constructor
                # Forcing inspect on init_method if it exists and is not object.__init__
                sig_target_for_init = member_obj # By default, inspect the class for constructor signature
                if init_method is not None and init_method is not object.__init__:
                     # If there's a specific __init__, its signature is what we want.
                     sig_target_for_init = init_method

                init_params, init_ret_ann, init_doc = _extract_callable_details(f"{class_name}.__init__", init_method or member_obj, sig_target_for_init)

                # Filter out 'self' from constructor params if present
                if init_params and init_params[0].name == 'self':
                    init_params = init_params[1:]

            except ValueError: # Happens if __init__ is a C function like object.__init__
                init_params = [] # Assume no user-defined params if inspection fails
                init_ret_ann = inspect.Parameter.empty
                init_doc = inspect.getdoc(member_obj) # Get class docstring as fallback

            constructor_op_id = f"{class_name}.__init__"
            parsed_ops[constructor_op_id] = CallableInfo(
                id_name=constructor_op_id,
                display_name=f"{class_name} (Constructor)",
                type="class_constructor",
                module_name=module_name,
                qual_name=class_name, # For constructor, qual_name is the class itself
                class_name=class_name,
                parameters=init_params,
                return_annotations=member_obj, # Constructor "returns" an instance of the class
                docstring=init_doc or inspect.getdoc(member_obj) # Use class doc if __init__ has none
            )

            # Class methods
            for method_name, method_obj in inspect.getmembers(member_obj, predicate=inspect.isfunction):
                if method_name.startswith("_") and method_name != "__call__": # Allow __call__ but skip others like __repr__
                    continue

                # Ensure it's a method defined in this class, not inherited from a different module's base class
                # This check is tricky with complex inheritance. A simpler check might be if method_obj directly belongs to member_obj's dict
                # For now, let's assume methods directly listed are relevant.

                method_params, method_ret_ann, method_doc = _extract_callable_details(f"{class_name}.{method_name}", method_obj)

                # Filter out 'self' from method params if present
                if method_params and method_params[0].name == 'self':
                    method_params = method_params[1:]

                method_op_id = f"{class_name}.{method_name}"
                parsed_ops[method_op_id] = CallableInfo(
                    id_name=method_op_id,
                    display_name=f"{class_name}.{method_name}",
                    type="class_method",
                    module_name=module_name,
                    qual_name=method_name, # For method, qual_name is the method name itself
                    class_name=class_name,
                    parameters=method_params,
                    return_annotations=method_ret_ann,
                    docstring=method_doc
                )
    return parsed_ops

if __name__ == '__main__':
    # Example Usage (for testing this util directly)
    # Create a dummy test_module.py
    test_module_content = """
def greet(name: str = "World") -> str:
    '''Greets the person.'''
    return f"Hello, {name}!"

class Calculator:
    '''A simple calculator class.'''
    def __init__(self, initial_value: int = 0):
        self.current_value = initial_value

    def add(self, amount: int) -> int:
        '''Adds amount to current value.'''
        self.current_value += amount
        return self.current_value

    def get_value(self) -> int:
        '''Returns the current value.'''
        return self.current_value

class EmptyClass:
    pass

def _private_func():
    pass
"""
    with open("test_module.py", "w") as f:
        f.write(test_module_content)

    ops = parse_python_file("test_module.py")
    for op_id, info in ops.items():
        print(f"ID: {op_id}, Display: {info.display_name}, Type: {info.type}")
        print(f"  Doc: {info.docstring}")
        print(f"  Returns: {info.return_annotation_str}")
        print(f"  Params:")
        for p in info.parameters:
            print(f"    - {p.name}: {p.annotation_str}, Default: {'N/A' if not p.default_value_is_set else p.default}, Kind: {p.kind}")
        print("-" * 20)

    import os
    os.remove("test_module.py") # Clean up
