# FILE: modules/tokenizer_victor.py
# VERSION: v1.0.0-TOKENIZER-CORTEX
# NAME: VictorModule (Tokenizer)
# AUTHOR: Jules @ Dev (for Bando)
# PURPOSE: Simple text tokenizer for Comfy Cortex. Demonstrates string input and list of strings output.
# LICENSE: Proprietary - Massive Magnetics / Ethica AI / BHeard Network

import re

class VictorModule:
    VERSION = "v1.0.0-TOKENIZER-CORTEX"
    FUNCTION = "tokenize_text" # Method to execute
    CATEGORY = "VictorModules/Text Processing" # Category in ComfyUI menu

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": ("STRING", {"multiline": True, "default": "Hello world, this is Comfy Cortex!"}),
                "delimiter_type": (["whitespace", "comma", "custom_regex"], {"default": "whitespace"}),
            },
            "optional": {
                "custom_delimiter_regex": ("STRING", {"multiline": False, "default": "\\s+"}),
                "to_lowercase": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("LIST_STRING",) # Custom type to indicate a list of strings
    RETURN_NAMES = ("tokens",)

    def __init__(self, **kwargs):
        self.name = "TokenizerVictorModule"

    def tokenize_text(self, text, delimiter_type, custom_delimiter_regex="\\s+", to_lowercase=False):
        """
        Tokenizes the input text based on the specified delimiter.
        Outputs a list of string tokens.
        """
        if to_lowercase:
            text = text.lower()

        tokens = []
        if delimiter_type == "whitespace":
            tokens = re.split(r'\s+', text.strip())
        elif delimiter_type == "comma":
            tokens = [t.strip() for t in text.split(',')]
        elif delimiter_type == "custom_regex":
            try:
                tokens = re.split(custom_delimiter_regex, text.strip())
            except re.error as e:
                print(f"[ERROR] Invalid regex for Tokenizer: {e}")
                # Fallback to whitespace on regex error to prevent crash, or could raise error
                tokens = re.split(r'\s+', text.strip())

        # Filter out empty strings that can result from splitting
        tokens = [token for token in tokens if token]

        print(f"[{self.get_metadata().get('display_name', self.name)}] Text: '{text[:50]}...' -> Tokens ({len(tokens)}): {tokens[:10]}")

        # The custom type "LIST_STRING" needs to be handled carefully.
        # ComfyUI's core types are basic (STRING, INT, FLOAT, IMAGE, LATENT, MASK, CONDITIONING, CLIP, VAE, MODEL, CONTROL_NET etc.).
        # For complex types like lists or dicts, they are often passed as Python objects if the next node can handle it.
        # If we want it to be generally connectable, it might need to be serialized (e.g., JSON string)
        # or we define how "LIST_STRING" is treated.
        # For now, returning a Python list. Nodes consuming this will need to expect a Python list.
        # Alternatively, ComfyUI uses "*" as a wildcard type that can accept anything.
        # Let's assume for now that downstream VictorModules can handle a Python list of strings.
        return (tokens,)

    def get_metadata(self):
        return {
            "node_name": "TokenizerVictorNode",
            "display_name": "Tokenizer (Victor)",
            "version": self.VERSION,
            "category": self.CATEGORY,
            "description": "Splits input text into a list of tokens based on a delimiter. Supports whitespace, comma, or custom regex delimiters and optional lowercasing.",
            "author": "Jules @ Dev for Bando"
        }

# We need to define how "LIST_STRING" is handled or if it's a valid ComfyUI type.
# For now, we'll assume it's a Python list passed as is.
# If this type is not recognized by LiteGraph for connection, we might need to change RETURN_TYPES to ("*",)
# or serialize the list into a STRING (e.g., JSON).
# To make it more ComfyUI-native for simple display or connection to string inputs,
# we might output a single string with tokens joined by newline, or just the first token.
# For true list passing, the receiving node must be designed to accept a Python list.
# For now, this is a proof-of-concept.
# Let's adjust RETURN_TYPES to be more standard for now, e.g. output a string representation.
# Or, if we want to keep it as a list for other VictorModules, we should ensure this is clear.
# The `*` type (meaning ANY) is often used for passing complex Python objects.
# Let's change RETURN_TYPES to ("*",) to indicate it's a Python object (list of strings).
# And update RETURN_NAMES for clarity.

# Re-evaluation: For nodes to connect visually in LiteGraph, types must match or be compatible.
# Standard ComfyUI doesn't have a "LIST_STRING" visual type.
# Outputting as "*" (ANY) is the most flexible for Python objects.
VictorModule.RETURN_TYPES = ("*",)
VictorModule.RETURN_NAMES = ("token_list_obj",)
