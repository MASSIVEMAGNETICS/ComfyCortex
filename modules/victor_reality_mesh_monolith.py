# FILE: modules/victor_reality_mesh_monolith.py
# VERSION: v5.0.0-REALITY-MESH-GODCORE-VM
# NAME: VictorModule (RealityMeshMonolithVictorModule Wrapper)
# AUTHOR: Brandon "iambandobandz" Emery x Victor (Core Logic) / Jules @ Dev (VM Wrapper)
# PURPOSE: 3D Fractal Flower-of-Life Mesh — AGI Cortex Monolith Node for Comfy Cortex.
# LICENSE: Proprietary – Massive Magnetics / Ethica AI / BHeard Network

import numpy as np
import json
import random
import logging
import sys
import os

# Ensure bando_reality_mesh_core is discoverable
try:
    from bando_reality_mesh_core.mesh_definitions import BandoRealityMeshMonolith
except ImportError as e:
    comfy_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if comfy_root not in sys.path:
        sys.path.append(comfy_root)
    try:
        from bando_reality_mesh_core.mesh_definitions import BandoRealityMeshMonolith
    except ImportError:
        logging.critical(f"[VM_RealityMesh] CRITICAL ERROR: Could not import BandoRealityMeshMonolith from bando_reality_mesh_core.mesh_definitions. Error: {e}", exc_info=True)
        class BandoRealityMeshMonolith: # Dummy for registration
            def __init__(self, *args, **kwargs): raise RuntimeError("BandoRealityMeshMonolith core logic not loaded!")
            def propagate(self, *args, **kwargs): raise RuntimeError("BandoRealityMeshMonolith core logic not loaded!")
            def summary(self): return {"error": "BandoRealityMeshMonolith core logic not loaded"}
            @property
            def history(self): return [{"error": "BandoRealityMeshMonolith core logic not loaded"}]
            @property
            def dim(self): return 0
            @property
            def mesh(self): return type('dummy_mesh', (object,), {'depth': 0, 'nodes': {}})()


class VictorModule: # Standard class name for victor_loader.py
    """
    VictorModule: Wraps BandoRealityMeshMonolith as a pluggable node for Comfy Cortex.
    Enables 3D mesh-based neural propagation, introspection, and real-time mutation.
    """
    # ComfyUI Node Attributes
    CATEGORY = "Victor/AGI/Mesh"
    FUNCTION = "run_monolith_node" # Explicitly named function for clarity
    RETURN_TYPES = ("*", "STRING", "STRING") # Numpy array, JSON string, JSON string
    RETURN_NAMES = ("mesh_embedding_obj", "summary_json", "mesh_history_json")

    # VictorModule Standard Attributes
    VERSION = "v5.0.0-REALITY-MESH-GODCORE-VM"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_signal": ("*", {"tooltip": "NumPy array signal. Can be from another VictorModule or a converter."}),
                "start_node_id": ("STRING", {"default": "random", "tooltip": "ID of mesh node or 'random'"}),
                "propagation_steps": ("INT", {"default": 3, "min":0, "max":100, "tooltip": "Number of propagation steps"}),
                "mesh_dim": ("INT", {"default": 64, "min":4, "max":1024, "step":4, "tooltip": "Dimension of mesh vectors. Re-initializes mesh if changed."}),
                "mesh_depth": ("INT", {"default": 2, "min":1, "max":5, "tooltip": "Fractal depth of the mesh. Re-initializes mesh if changed."}),
            }
        }

    def __init__(self):
        self.monolith_instance: BandoRealityMeshMonolith | None = None
        self.last_config: dict = {}
        # Use the display name from get_metadata for logging prefix if available early
        # For now, using a generic logger name or the class name.
        self.logger = logging.getLogger(f"ComfyCortex.VM.{self.__class__.__name__}")
        self.logger.info(f"Instance created.")


    def run_monolith_node(self, input_signal: np.ndarray, start_node_id: str, propagation_steps: int, mesh_dim: int, mesh_depth: int):
        self.logger.info(f"Running mesh: dim={mesh_dim}, depth={mesh_depth}, steps={propagation_steps}, start_node='{start_node_id}'")

        if not isinstance(input_signal, np.ndarray):
            error_msg = f"Invalid input_signal type: {type(input_signal)}. Expected numpy.ndarray."
            self.logger.error(error_msg)
            # Try to get a summary if monolith exists, otherwise empty dict
            summary_on_fail = self.monolith_instance.summary() if self.monolith_instance else {"error": "Monolith not initialized due to input error."}
            return (None, json.dumps({"error": error_msg, "summary": summary_on_fail}, default=str), "[]")

        needs_init = (
            self.monolith_instance is None
            or self.last_config.get("dim") != mesh_dim
            or self.last_config.get("mesh_depth") != mesh_depth
        )
        if needs_init:
            self.logger.info(f"Initializing/Re-initializing BandoRealityMeshMonolith: dim={mesh_dim}, depth={mesh_depth}")
            try:
                self.monolith_instance = BandoRealityMeshMonolith(dim=mesh_dim, mesh_depth=mesh_depth)
                self.last_config = {"dim": mesh_dim, "mesh_depth": mesh_depth}
            except Exception as e:
                self.logger.error(f"Failed to init BandoRealityMeshMonolith: {e}", exc_info=True)
                error_summary = json.dumps({"error": f"Monolith init failed: {str(e)}"})
                return (None, error_summary, "[]")

        final_start_node_id = start_node_id
        if start_node_id.lower() == "random":
            if self.monolith_instance and self.monolith_instance.mesh.nodes:
                final_start_node_id = random.choice(list(self.monolith_instance.mesh.nodes.keys()))
                self.logger.info(f"Random start_node selected: {final_start_node_id}")
            else:
                self.logger.error("Cannot select random start_node, mesh has no nodes or monolith not initialized.")
                error_summary = json.dumps({"error": "Cannot select random start_node, mesh/monolith issue."})
                return (None, error_summary, "[]")

        if input_signal.shape[-1] != self.monolith_instance.dim:
            err_msg = f"Input_signal final dimension ({input_signal.shape[-1]}) does not match monolith dimension ({self.monolith_instance.dim})."
            self.logger.error(err_msg)
            current_summary = self.monolith_instance.summary() if self.monolith_instance else {}
            current_history_list = self.monolith_instance.history if self.monolith_instance else []
            serializable_hist_on_err = [ {nid: state.tolist() for nid, state in step.items()} for step in current_history_list[-5:] ]
            return (None, json.dumps({"error": err_msg, "summary": current_summary}, default=str), json.dumps(serializable_hist_on_err, default=str) )

        try:
            mesh_embedding = self.monolith_instance.propagate(final_start_node_id, input_signal, steps=propagation_steps)
            summary = self.monolith_instance.summary()
            history_serializable = [
                {nid: state.tolist() for nid, state in step_snapshot.items()}
                for step_snapshot in self.monolith_instance.history
            ]
        except Exception as e:
            self.logger.error(f"Error during monolith propagation: {e}", exc_info=True)
            error_summary = json.dumps({"error": f"Propagation error: {str(e)}"})
            current_summary_on_err = self.monolith_instance.summary() if self.monolith_instance else {}
            current_history_on_err = self.monolith_instance.history if self.monolith_instance else []
            serializable_hist_on_err_prop = [ {nid: state.tolist() for nid, state in step.items()} for step in current_history_on_err[-5:] ]
            return (None, json.dumps(current_summary_on_err, indent=2, default=str), json.dumps(serializable_hist_on_err_prop, default=str) )

        self.logger.info(f"Mesh run complete. Embedding shape: {mesh_embedding.shape if mesh_embedding is not None else 'None'}")
        return (
            mesh_embedding,
            json.dumps(summary, indent=2, default=str),
            json.dumps(history_serializable, default=str)
        )

    def get_metadata(self): # No longer a classmethod if it might use self (though here it doesn't strictly need to)
        return {
            "node_name": "RealityMeshMonolithNode",
            "display_name": "Bando Reality Mesh Monolith (VM)",
            "version": self.VERSION,
            "category": self.CATEGORY,
            "description": (
                "3D Fractal Flower-of-Life Reality Mesh Monolith by Bando. "
                "AGI Core Block Mesh Engine. Inject signal, propagate in 3D geometry, mutate brain."
            ),
            "author": "Brandon 'iambandobandz' Emery x Victor (Core Logic) / Jules @ Dev (VM Wrapper)"
        }

NODE_CLASS_MAPPINGS = {
    "RealityMeshMonolithNode": VictorModule
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RealityMeshMonolithNode": "Bando Reality Mesh Monolith (VM)"
}
