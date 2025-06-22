# FILE: generate_docs.py
# PURPOSE: Auto-generates documentation for VictorModules found in the 'modules/' directory.
# USAGE: Run from the ComfyUI root directory: python generate_docs.py

import inspect
import os
import sys
import logging

# Ensure the script can find victor_loader and ComfyUI's nodes module
# This assumes the script is run from the ComfyUI root directory.
sys.path.append(os.getcwd())

try:
    import victor_loader
    import nodes # Needed by victor_loader.load_victor_modules() to map nodes
except ImportError as e:
    print(f"Error: Could not import necessary modules. Make sure you are running this script from the ComfyUI root directory.")
    print(f"Details: {e}")
    sys.exit(1)

OUTPUT_FILENAME = "MODULES_DOCUMENTATION.md"

# Configure basic logging for the script, similar to how victor_loader might log
logging.basicConfig(level=logging.INFO, format='[DocGenerator] %(levelname)s: %(message)s')

def get_method_docstring(cls, method_name):
    """Safely retrieves a method's docstring."""
    if hasattr(cls, method_name):
        method = getattr(cls, method_name)
        if inspect.isfunction(method) or inspect.ismethod(method):
            doc = inspect.getdoc(method)
            return doc if doc else "No docstring available."
    return "Method not found or not a function/method."

def format_input_types(input_types_method):
    """Formats INPUT_TYPES for display."""
    try:
        types_data = input_types_method()
        md_string = ""
        if types_data.get("required"):
            md_string += "    *   **Required Inputs:**\n"
            for name, details in types_data["required"].items():
                type_info = details[0]
                config = details[1] if len(details) > 1 else {}
                md_string += f"        *   `{name}` (`{type_info}`): Default = `{config.get('default', 'N/A')}`. {config.get('tooltip', '')}\n"

        if types_data.get("optional"):
            md_string += "    *   **Optional Inputs:**\n"
            for name, details in types_data["optional"].items():
                type_info = details[0]
                config = details[1] if len(details) > 1 else {}
                md_string += f"        *   `{name}` (`{type_info}`): Default = `{config.get('default', 'N/A')}`. {config.get('tooltip', '')}\n"
        return md_string if md_string else "    *   No inputs defined."
    except Exception as e:
        return f"    *   Error formatting inputs: {e}"

def format_return_types(return_types_tuple, return_names_tuple):
    """Formats RETURN_TYPES and RETURN_NAMES for display."""
    try:
        if not return_types_tuple:
            return "    *   No outputs defined."
        md_string = "    *   **Outputs:**\n"
        names = return_names_tuple if return_names_tuple and len(return_names_tuple) == len(return_types_tuple) else [f"output_{i+1}" for i in range(len(return_types_tuple))]
        for i, r_type in enumerate(return_types_tuple):
            md_string += f"        *   `{names[i]}` (`{r_type}`)\n"
        return md_string
    except Exception as e:
        return f"    *   Error formatting outputs: {e}"


def main():
    logging.info("Starting VictorModule documentation generation...")

    # Step 1: Load the VictorModules. This populates victor_loader.loaded_modules
    # and also registers them with ComfyUI's node system (though that part isn't strictly needed for doc gen,
    # load_victor_modules does both).
    try:
        logging.info(f"Scanning for VictorModules in '{victor_loader.MODULES_DIR}'...")
        victor_loader.load_victor_modules()
    except Exception as e:
        logging.error(f"Failed during module loading phase: {e}", exc_info=True)
        print(f"Critical error: Could not load VictorModules. Documentation cannot be generated.")
        sys.exit(1)

    # Step 2: Get the structured info
    modules_info = victor_loader.get_loaded_modules_info()

    if not modules_info:
        logging.warning("No VictorModules were loaded. Documentation file will be empty or indicate this.")
        doc_content = "# VictorModules Documentation\n\nNo VictorModules found or loaded.\n"
    else:
        logging.info(f"Found {len(modules_info)} VictorModules to document.")
        doc_content = "# VictorModules Documentation\n\n"
        doc_content += "This document provides details for all loaded VictorModules in Comfy Cortex.\n\n"

        # Sort modules by display name for consistent ordering
        modules_info.sort(key=lambda x: x.get("display_name", x.get("node_name", "")))

        for module_data in modules_info:
            node_name = module_data.get("node_name", "UnknownNode")
            display_name = module_data.get("display_name", node_name)

            doc_content += f"## {display_name}\n\n"
            doc_content += f"-   **Node Name (Key)**: `{node_name}`\n"
            doc_content += f"-   **File**: `{module_data.get('filename', 'N/A')}`\n"
            doc_content += f"-   **Version**: `{module_data.get('version', 'N/A')}`\n"
            doc_content += f"-   **Category**: `{module_data.get('category', 'N/A')}`\n"
            doc_content += f"-   **Hash**: `{module_data.get('file_hash', 'N/A')}`\n"

            metadata = module_data.get("metadata", {})
            description = metadata.get("description", "No description provided in metadata.")
            doc_content += f"-   **Description (from metadata)**: {description}\n"

            # Attempt to get the class object for more detailed inspection
            victor_module_instance_info = victor_loader.loaded_modules.get(node_name)
            if victor_module_instance_info:
                cls = victor_module_instance_info.get("class_obj")
                if cls:
                    class_doc = inspect.getdoc(cls)
                    if class_doc:
                        doc_content += f"\n### Class Docstring:\n```\n{class_doc}\n```\n"

                    # Document INPUT_TYPES
                    if hasattr(cls, "INPUT_TYPES") and inspect.ismethod(cls.INPUT_TYPES):
                        doc_content += f"\n### Inputs:\n{format_input_types(cls.INPUT_TYPES)}\n"

                    # Document RETURN_TYPES and RETURN_NAMES
                    return_types = getattr(cls, "RETURN_TYPES", tuple())
                    return_names = getattr(cls, "RETURN_NAMES", tuple())
                    doc_content += f"\n### Outputs:\n{format_return_types(return_types, return_names)}\n"

                    # Document the main FUNCTION method
                    function_name = getattr(cls, "FUNCTION", "forward") # Default to 'forward' if not specified
                    doc_content += f"\n### Main Function (`{function_name}`):\n"
                    method_doc = get_method_docstring(cls, function_name)
                    doc_content += f"```\n{method_doc}\n```\n"
                else:
                    doc_content += "\n*Note: Class object not found in loader's registry for detailed inspection.*\n"
            else:
                 doc_content += "\n*Note: Module details not found in loader's internal registry for detailed inspection.*\n"

            doc_content += "\n---\n\n"

    try:
        with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
            f.write(doc_content)
        logging.info(f"Documentation successfully written to {OUTPUT_FILENAME}")
        print(f"Documentation generated: {OUTPUT_FILENAME}")
    except IOError as e:
        logging.error(f"Failed to write documentation file: {e}", exc_info=True)
        print(f"Error: Could not write {OUTPUT_FILENAME}.")

if __name__ == "__main__":
    main()
