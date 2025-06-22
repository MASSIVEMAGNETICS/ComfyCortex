# FILE: modules/echo_victor.py
# VERSION: v1.0.0-ECHO-GODCORE
# NAME: VictorModule (Echo)
# AUTHOR: Brandon "iambandobandz" Emery x Victor (Fractal Architect Mode)
# PURPOSE: Returns whatever input is given, for pipeline debugging.
# LICENSE: Proprietary - Massive Magnetics / Ethica AI / BHeard Network

class VictorModule:
    VERSION = "v1.0.0-ECHO-GODCORE"

    @classmethod
    def INPUT_TYPES(s):
        """
        Defines the input types for this node, used by ComfyUI.
        """
        return {
            "required": {
                "input_data": ("STRING", {"multiline": True, "default": "Hello Victor"}),
                # Using STRING type for broad compatibility, could be ANY or specific types.
            },
            "optional": {
                "prefix": ("STRING", {"multiline": False, "default": ""}),
            }
        }

    RETURN_TYPES = ("STRING",) # Output type
    RETURN_NAMES = ("output_echo",) # Name of the output slot
    FUNCTION = "forward"        # Method to execute
    CATEGORY = "VictorModules/Debug" # Category in ComfyUI menu

    def __init__(self, **kwargs):
        """
        Standard __init__. kwargs are not directly used by ComfyUI node instantiation
        but good practice for a generic class.
        """
        self.name = "EchoVictorModule" # Internal name
        # ComfyUI doesn't pass kwargs to __init__ for node instances.
        # Widget values are passed directly to the FUNCTION method.
        # If params were needed for init, they'd come from class-level configs or fixed values.

    def forward(self, input_data, prefix=""):
        """
        The main execution method called by ComfyUI.
        Matches the FUNCTION specified above.
        Input arguments must match keys in INPUT_TYPES.
        """
        echoed_data = f"{prefix}{input_data}"
        print(f"[{self.get_metadata().get('display_name', self.name)}] Input: {input_data}, Prefix: {prefix}, Output: {echoed_data}")
        return (echoed_data,) # Must return a tuple

    def get_metadata(self):
        """
        Provides metadata about the module.
        Used by the VictorModule loader and potentially by the UI.
        """
        return {
            "node_name": "EchoVictorNode", # Suggested unique key for NODE_CLASS_MAPPINGS
            "display_name": "Echo Victor (Debug)", # UI friendly name
            "version": self.VERSION,
            "category": self.CATEGORY, # Ensures consistency
            "description": "Echoes the input_data, optionally prepended with a prefix. For Victor pipeline debugging."
            # Add other relevant metadata like author, license, etc.
        }

# Note: ComfyUI's system for custom nodes usually expects NODE_CLASS_MAPPINGS
# and NODE_DISPLAY_NAME_MAPPINGS at the module level.
# Our victor_loader.py handles this registration dynamically by inspecting VictorModule classes.
# So, these explicit mappings are not strictly needed in *this file* if victor_loader.py does its job.
# However, if a module had multiple node classes, it would define them here.
# For a single VictorModule per file, the loader handles it.
