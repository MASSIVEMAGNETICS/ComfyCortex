class BasicAGINode:
    """
    A basic example of an AGI component for Comfy Cortex.
    It takes a string, appends a suffix, and returns it.
    """
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "input_string": ("STRING", {"multiline": False, "default": "Hello"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_string",)
    FUNCTION = "process"
    CATEGORY = "AGI_Components"

    def process(self, input_string):
        output_string = input_string + " - from AGI Node!"
        return (output_string,)

# A dictionary that ComfyUI will use to load nodes.
# Ensuring NODE_CLASS_MAPPINGS and NODE_DISPLAY_NAME_MAPPINGS are present in the module.
NODE_CLASS_MAPPINGS = {
    "BasicAGINode": BasicAGINode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BasicAGINode": "Basic AGI String Processor"
}
