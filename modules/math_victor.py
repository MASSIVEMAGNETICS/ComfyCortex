# FILE: modules/math_victor.py
# VERSION: v1.0.0-MATH-CORTEX
# NAME: VictorModule (Math)
# AUTHOR: Jules @ Dev (for Bando)
# PURPOSE: Performs basic arithmetic operations. Demonstrates multiple number inputs and a selection widget.
# LICENSE: Proprietary - Massive Magnetics / Ethica AI / BHeard Network

import math

class VictorModule:
    VERSION = "v1.0.0-MATH-CORTEX"
    FUNCTION = "perform_operation"
    CATEGORY = "VictorModules/Logic"

    OPERATIONS = ["add", "subtract", "multiply", "divide", "power", "log", "sqrt"]

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "operation": (s.OPERATIONS, {"default": "add"}),
                "a": ("FLOAT", {"default": 0.0, "step": 0.01}),
            },
            "optional": { # 'b' is optional for unary operations like sqrt, log (if base is fixed)
                "b": ("FLOAT", {"default": 1.0, "step": 0.01}),
                "log_base": ("FLOAT", {"default": 10.0, "min": 0.001, "step": 0.01, "display": "slider"}),
            }
        }

    RETURN_TYPES = ("FLOAT", "STRING") # Output value and a string description/error
    RETURN_NAMES = ("result", "status_message")

    def __init__(self, **kwargs):
        self.name = "MathVictorModule"

    def perform_operation(self, operation, a, b=1.0, log_base=10.0):
        result = 0.0
        status = "OK"

        try:
            if operation == "add":
                result = a + b
            elif operation == "subtract":
                result = a - b
            elif operation == "multiply":
                result = a * b
            elif operation == "divide":
                if b == 0:
                    status = "Error: Division by zero."
                    result = float('nan') # Not a Number
                else:
                    result = a / b
            elif operation == "power":
                result = a ** b
            elif operation == "log":
                if a <= 0:
                    status = f"Error: Log input 'a' ({a}) must be positive."
                    result = float('nan')
                elif log_base <= 0 or log_base == 1:
                    status = f"Error: Log base ({log_base}) must be positive and not equal to 1."
                    result = float('nan')
                else:
                    result = math.log(a, log_base)
            elif operation == "sqrt":
                if a < 0:
                    status = f"Error: Sqrt input 'a' ({a}) must be non-negative."
                    result = float('nan')
                else:
                    result = math.sqrt(a)
            else:
                status = f"Error: Unknown operation '{operation}'."
                result = float('nan')
        except Exception as e:
            status = f"Error: {str(e)}"
            result = float('nan')

        if status == "OK":
            status_message = f"Performed {operation} on {a}"
            if operation not in ["sqrt"]: # Unary ops don't always use b
                 if operation == "log":
                     status_message += f" with base {log_base}"
                 else:
                     status_message += f" and {b}"
            status_message += f". Result: {result}"
        else:
            status_message = status

        print(f"[{self.get_metadata().get('display_name', self.name)}] Op: {operation}, A: {a}, B: {b}, Base: {log_base} -> Result: {result}, Status: {status}")
        return (result, status_message)

    def get_metadata(self):
        return {
            "node_name": "MathVictorNode",
            "display_name": "Math Operation (Victor)",
            "version": self.VERSION,
            "category": self.CATEGORY,
            "description": "Performs various mathematical operations like add, subtract, multiply, divide, power, log, sqrt. Outputs result and status.",
            "author": "Jules @ Dev for Bando"
        }
