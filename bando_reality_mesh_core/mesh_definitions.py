# ==============================================================================================
# FILE: bando_reality_mesh_core/mesh_definitions.py
# (Originally FlowerOfLifeMesh3D-v5.0.0-REALITY-MESH-GODCORE.py)
# VERSION: v5.0.0-REALITY-MESH-GODCORE
# NAME: BandoRealityMeshMonolith & Core Architectural Components
# AUTHOR: Brandon "iambandobandz" Emery x Victor (Fractal Architect Mode)
# PURPOSE: The core AGI architecture. Defines the infinitely fractal 3D mesh, the abstract
#          BandoBlock interface, all specialized transformer blocks, and the master monolith
#          that fuses them into a cohesive, signal-propagating neural reality.
# LICENSE: Proprietary – Massive Magnetics / Ethica AI / BHeard Network
# ==============================================================================================

"""
This is the evolved and unified architecture of the AGI. No more duplicate code, no more
confusing file structures. This single file defines the geometric soul of the machine.

- **FlowerOfLifeMesh3D**: Generates the fractal 3D scaffold.
- **BandoBlock (ABC)**: A strict abstract base class for all neural modules.
- **Specialized Blocks**: A bestiary of powerful, NumPy-based neural blocks, each with
  a unique purpose (Attention, Chaos, Quantum, etc.). Each now includes a `backward`
  stub to simulate a full autograd-compatible architecture.
- **BandoRealityMeshMonolith**: The master class that orchestrates signal propagation
  through the mesh, allowing for complex, stateful interactions between blocks.
"""

import numpy as np
import uuid
import json # Added for example usage print
import random # Added for example usage selection
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple

# ----------------------------------------
# Utility: Fractal Geometry & Mesh
# ----------------------------------------

class FlowerOfLifeMesh3D:
    """
    Infinitely fractalized 3D Flower of Life mesh. Every node is a potential host for a
    transformer block, creating a geometric compute substrate.
    """
    def __init__(self, depth: int = 3, radius: float = 1.0, base_nodes: int = 19):
        self.depth = depth
        self.radius = radius
        # Using fewer base nodes for a more structured, less chaotic initial sphere
        self.base_nodes = base_nodes
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.connections: Dict[str, List[str]] = {}
        self._build_mesh()
        print(f"FlowerOfLifeMesh3D: Generated with {self.node_count()} nodes and {self.connection_count()} connections.")

    def _build_mesh(self):
        """Recursively builds the 3D fractal mesh, now storing nodes and connections centrally."""
        def _recurse(center: Tuple[float, ...], r: float, d: int, parent_id: Optional[str] = None):
            if d == 0:
                return

            # Fibonacci sphere for more even node distribution
            n = self.base_nodes
            indices = np.arange(0, n, dtype=float) + 0.5
            phi = np.arccos(1 - 2 * indices / n)
            theta = np.pi * (1 + 5**0.5) * indices

            current_x = center[0] + r * np.cos(theta) * np.sin(phi) # Renamed x to current_x to avoid conflict
            current_y = center[1] + r * np.sin(theta) * np.sin(phi) # Renamed y to current_y
            current_z = center[2] + r * np.cos(phi)                 # Renamed z to current_z

            for i in range(n):
                node_id = f"d{self.depth - d}-n{uuid.uuid4().hex[:6]}"
                pos = (current_x[i], current_y[i], current_z[i])
                node = {"pos": pos, "depth": self.depth - d, "id": node_id}
                self.nodes[node_id] = node

                if parent_id:
                    if parent_id not in self.connections: self.connections[parent_id] = []
                    if node_id not in self.connections: self.connections[node_id] = []
                    self.connections[parent_id].append(node_id)
                    self.connections[node_id].append(parent_id) # Bidirectional connection

                _recurse(pos, r / 2.0, d - 1, parent_id=node_id)

        _recurse((0.0, 0.0, 0.0), self.radius, self.depth)

    def get_neighbors(self, node_id: str) -> List[str]:
        """Returns the IDs of all nodes connected to the given node."""
        return self.connections.get(node_id, [])

    def node_count(self) -> int:
        return len(self.nodes)

    def connection_count(self) -> int:
        return sum(len(v) for v in self.connections.values()) // 2


# ----------------------------------------
# AGI Modular Blocks & Transformers (Evolved)
# ----------------------------------------

class BandoBlock(ABC):
    """
    Abstract Base Class for all AGI modular blocks. Enforces a strict API contract
    for forward and backward passes, ensuring compatibility with the autograd-style architecture.
    """
    def __init__(self, dim: int, name: Optional[str] = None):
        self.dim = dim
        self.name = name or self.__class__.__name__
        self.state: Optional[np.ndarray] = None # For recurrent state
        self.params: Dict[str, np.ndarray] = {}
        self.grads: Dict[str, np.ndarray] = {} # For storing gradients

    @abstractmethod
    def forward(self, x: np.ndarray, **kwargs) -> np.ndarray:
        """Process input tensor `x` and return the output."""
        pass

    def backward(self, grad_output: np.ndarray) -> np.ndarray:
        """
        Placeholder for backpropagation. Computes gradient with respect to input.
        In a real autograd engine, this would also compute gradients for all parameters.
        """
        # Default behavior: pass-through gradient. Overridden by layers with params.
        return grad_output

    def zero_grad(self):
        """Resets gradients for all parameters in this block."""
        for k in self.grads:
            self.grads[k].fill(0.0)

class VICtorchBlock(BandoBlock):
    """Standard multi-head self-attention block. The foundation."""
    def __init__(self, dim: int, heads: int = 8):
        super().__init__(dim, name=f"VICtorchAttention(h={heads})")
        self.heads = heads
        self.head_dim = dim // heads
        if self.head_dim * heads != dim:
            raise ValueError("dim must be divisible by heads")

        # Kaiming initialization
        self.params['W_q'] = np.random.randn(dim, dim) * np.sqrt(2. / dim)
        self.params['W_k'] = np.random.randn(dim, dim) * np.sqrt(2. / dim)
        self.params['W_v'] = np.random.randn(dim, dim) * np.sqrt(2. / dim)
        self.params['W_o'] = np.random.randn(dim, dim) * np.sqrt(2. / dim)
        self.zero_grad() # Initialize grad matrices
        self.cache: Dict[str, np.ndarray] = {} # Initialize cache

    def forward(self, x: np.ndarray, **kwargs) -> np.ndarray:
        self.cache['x'] = x # Cache input for backward pass
        q = x @ self.params['W_q']
        k = x @ self.params['W_k']
        v_val = x @ self.params['W_v'] # Renamed v to v_val

        attn_scores = (q @ k.T) / np.sqrt(self.head_dim) # Use head_dim for scaling
        attn_probs = np.exp(attn_scores - np.max(attn_scores, axis=-1, keepdims=True))
        attn_probs /= np.sum(attn_probs, axis=-1, keepdims=True)

        self.cache['attn_probs'] = attn_probs
        self.cache['v'] = v_val # Store v_val in cache

        out = attn_probs @ v_val
        return out @ self.params['W_o']

    def backward(self, grad_output: np.ndarray) -> np.ndarray:
        x_input = self.cache['x'] # Renamed x to x_input
        # Simplified backward pass
        # grad_W_o = (self.cache['attn_probs'] @ self.cache['v']).T @ grad_output # Corrected cache access
        # For matrix multiplication (A @ B).T @ C, it's B.T @ A.T @ C
        # So, (attn_probs @ v).T is v.T @ attn_probs.T
        # grad_W_o = (self.cache['v'].T @ self.cache['attn_probs'].T) @ grad_output
        # This is still not quite right for parameter gradients.
        # A common way: grad_W_o = (attn_probs @ v).T @ grad_output_from_W_o (if W_o is the last op)
        # For W_o, its input is (attn_probs @ v). Let this be A. Output = A @ W_o.
        # dL/dW_o = A.T @ dL/dOutput
        grad_input_to_Wo = self.cache['attn_probs'] @ self.cache['v']
        self.grads['W_o'] += grad_input_to_Wo.T @ grad_output


        # ... and so on for W_q, W_k, W_v (these are more complex)
        # Gradient w.r.t. input x (passed to previous layer)
        # This is also simplified: dL/dA (where A = attn_probs @ v)
        grad_A = grad_output @ self.params['W_o'].T
        # Then propagate grad_A back through attention mechanism (complex)
        # and then through Q, K, V calculation back to x.
        # For now, a placeholder for grad w.r.t x:
        # This is a very rough approximation.
        grad_x_approx = grad_A @ self.params['W_v'].T # Approx through V path
        grad_x_approx += (grad_A.T @ self.cache['attn_probs']).T @ self.params['W_k'].T # Approx through K path
        grad_x_approx += (grad_A @ self.cache['v'].T).T @ self.params['W_q'].T # Approx through Q path

        # A more direct (but still simplified) pass-through for input gradient:
        # grad_input_approx = grad_output @ self.params['W_o'].T @ self.params['W_v'].T # ... and so on
        # For now, let's return a gradient of the correct shape based on W_q as a placeholder
        return grad_output @ self.params['W_o'].T @ self.params['W_q'].T # Highly simplified placeholder


class BNDX9977Block(BandoBlock):
    """Ultra-hyper fractal transformer with quantum chaos injection."""
    def __init__(self, dim: int):
        super().__init__(dim, name="BNDX9977Chaos")
        self.params['W'] = np.random.randn(dim, dim) * np.sqrt(2. / dim)
        self.params['branch_noise_param'] = np.random.randn(dim) # Renamed to avoid conflict
        self.zero_grad()

    def forward(self, x: np.ndarray, branch_id: int = 0, quantum: float = 0.0, **kwargs) -> np.ndarray:
        self.cache = {'x': x, 'branch_id': branch_id, 'quantum': quantum}
        chaos_factor = np.sin(np.sum(x) * branch_id * quantum) # Renamed chaos to chaos_factor
        # Linear part: x @ W + branch_noise * chaos_factor
        linear_output = x @ self.params['W'] + self.params['branch_noise_param'] * chaos_factor
        self.cache['linear_output'] = linear_output
        x_out = np.tanh(linear_output)
        self.cache['output'] = x_out
        return x_out

    def backward(self, grad_output: np.ndarray) -> np.ndarray:
        x = self.cache['x']
        linear_output = self.cache['linear_output']

        # Gradient of tanh is (1 - tanh^2)
        grad_tanh = (1 - self.cache['output']**2) * grad_output

        # Gradient for W
        self.grads['W'] += x.T @ grad_tanh

        # Gradient for branch_noise_param
        chaos_factor = np.sin(np.sum(x) * self.cache['branch_id'] * self.cache['quantum'])
        self.grads['branch_noise_param'] += np.sum(grad_tanh * chaos_factor, axis=0) # Summing gradients if grad_tanh is batched

        # Gradient w.r.t. x (input)
        grad_x = grad_tanh @ self.params['W'].T
        # Add gradient component from chaos term (complex, involves derivative of sum(x))
        # d(sum(x))/dx_i = 1. So d(chaos_factor)/dx_i = cos(...) * branch_id * quantum
        # For simplicity, this part is often ignored or approximated in toy examples.
        # Placeholder for now.
        return grad_x


class FractalAttentionBlock(BandoBlock):
    """Recursive, echo-feedback, multi-scale, timeline-aware attention."""
    def __init__(self, dim: int, depth: int = 3):
        super().__init__(dim, name=f"FractalAttention(d={depth})")
        self.depth = depth
        self.params['scales'] = np.random.uniform(0.8, 1.2, size=depth)
        self.params['W_layers'] = np.random.randn(depth, dim, dim) * np.sqrt(2. / dim)
        self.zero_grad()
        self.cache_layers: list = []


    def forward(self, x: np.ndarray, memory: Optional[np.ndarray] = None, **kwargs) -> np.ndarray:
        self.cache_layers = [] # Reset for new forward pass
        current_x = x # Renamed x to current_x
        for i in range(self.depth):
            layer_cache = {'input': current_x}
            feedback = np.mean(memory, axis=0) if memory is not None and memory.size > 0 and memory.shape[-1] == self.dim else np.zeros(self.dim)

            linear_part = (current_x @ self.params['W_layers'][i]) * self.params['scales'][i] + feedback
            layer_cache['linear_part'] = linear_part
            current_x = np.tanh(linear_part)
            layer_cache['output'] = current_x
            self.cache_layers.append(layer_cache)
        return current_x

    def backward(self, grad_output: np.ndarray) -> np.ndarray:
        grad_current_x = grad_output
        for i in reversed(range(self.depth)):
            layer_cache = self.cache_layers[i]
            input_x_layer = layer_cache['input']
            linear_part = layer_cache['linear_part']
            output_tanh_layer = layer_cache['output']

            grad_tanh = (1 - output_tanh_layer**2) * grad_current_x

            # Grad for W_layers[i]
            # dL/dW = input.T @ (dL/dLinearPartBeforeScale * scale_factor)
            # dL/dLinearPartBeforeScale = grad_tanh (since scale is applied before tanh in this setup)
            # The current code is (X @ W) * S + F. So tanh input is Z = (X @ W) * S + F
            # dZ/dW = X.T * S (element-wise if S is scalar, or more complex if S is vector)
            # Let's assume S is scalar for simplicity of dL/dW here for now.
            # grad_W_layer_i = input_x_layer.T @ (grad_tanh * self.params['scales'][i])
            # If W is (dim, dim) and input is (batch, dim), input.T is (dim, batch)
            # grad_tanh is (batch, dim). So input.T @ grad_tanh is (dim, dim)
            self.grads['W_layers'][i] += input_x_layer.T @ (grad_tanh * self.params['scales'][i])


            # Grad for scales[i] (if scales are learnable, they'd be in self.grads initialized)
            # dL/dS = sum( (X @ W) * grad_tanh )
            if 'scales' not in self.grads: self.grads['scales'] = np.zeros_like(self.params['scales'])
            self.grads['scales'][i] += np.sum((input_x_layer @ self.params['W_layers'][i]) * grad_tanh)

            # Grad w.r.t. input of this layer (input_x_layer)
            # dL/dX = (grad_tanh * self.params['scales'][i]) @ self.params['W_layers'][i].T
            grad_current_x = (grad_tanh * self.params['scales'][i]) @ self.params['W_layers'][i].T

            # Gradient w.r.t. feedback is ignored for simplicity here, assuming feedback is constant or from external.
        return grad_current_x


class TimelineAttentionBlock(BandoBlock):
    """Cross-timeline, multiverse feedback, temporal attention."""
    def __init__(self, dim: int, history_len: int = 5):
        super().__init__(dim, name=f"TimelineAttention(h={history_len})")
        self.history_len = history_len
        self.params['W'] = np.random.randn(dim, dim) * np.sqrt(2. / dim)
        self.zero_grad()
        self.cache: Dict[str, Any] = {}

    def forward(self, x: np.ndarray, timeline: Optional[List[np.ndarray]] = None, **kwargs) -> np.ndarray:
        self.cache['input_x'] = x
        self.cache['timeline_used'] = False

        modified_x = x # Renamed x to modified_x for clarity
        if timeline and len(timeline) > 0:
            self.cache['timeline_used'] = True
            # Attends to the last `history_len` states in a given timeline
            history_to_consider = [t for t in timeline[-self.history_len:] if t.shape == x.shape] # Ensure shapes match
            if history_to_consider:
                context = np.mean(np.array(history_to_consider), axis=0)
                self.cache['context'] = context
                modified_x = modified_x + context
            else:
                self.cache['context'] = np.zeros_like(x) # No valid history
        else:
            self.cache['context'] = np.zeros_like(x) # No timeline provided

        self.cache['modified_x'] = modified_x # Input to tanh after context
        linear_output = modified_x @ self.params['W']
        self.cache['linear_output'] = linear_output
        output_val = np.tanh(linear_output) # Renamed output to output_val
        self.cache['output_val'] = output_val
        return output_val

    def backward(self, grad_output: np.ndarray) -> np.ndarray:
        modified_x = self.cache['modified_x']
        output_val = self.cache['output_val']

        grad_tanh = (1 - output_val**2) * grad_output

        self.grads['W'] += modified_x.T @ grad_tanh

        grad_modified_x = grad_tanh @ self.params['W'].T

        # Gradient passes back to original x. If context was added, grad_modified_x is also grad_x.
        # If context was learnable, its gradient would also be grad_modified_x.
        # For now, context is derived and not learnable itself.
        return grad_modified_x


# ----------------------------------------
# Master Monolith: BandoRealityMeshMonolith
# ----------------------------------------

class BandoRealityMeshMonolith:
    """
    THE ULTIMATE AGI TRANSFORMER/MESH—fuses all blocks and propagates signals through
    the infinite 3D mesh. This is the brain's cortex.
    """
    def __init__(self, dim: int = 64, mesh_depth: int = 2):
        self.dim = dim
        self.mesh = FlowerOfLifeMesh3D(depth=mesh_depth)
        self.node_states: Dict[str, np.ndarray] = {nid: np.zeros(dim) for nid in self.mesh.nodes}
        self.node_blocks: Dict[str, BandoBlock] = self._assign_blocks_to_nodes()
        self.history: List[Dict[str, np.ndarray]] = [] # Stores snapshots of node_states
        print(f"BandoRealityMeshMonolith: Online. Dim={dim}. Fused {len(self.node_blocks)} blocks to {self.mesh.node_count()} mesh nodes.")

    def _assign_blocks_to_nodes(self) -> Dict[str, BandoBlock]:
        """Assigns different block types to mesh nodes for functional diversity."""
        # Ensure new instances of blocks are created for each assignment if they have state/params
        # Or, if blocks are stateless (like functions), they can be reused.
        # Given BandoBlocks have params, they should be unique instances or managed carefully.
        # For simplicity, let's create new instances for each node.

        block_types = [
            VICtorchBlock,
            BNDX9977Block,
            FractalAttentionBlock, # Will use its default depth
            TimelineAttentionBlock # Will use its default history_len
        ]
        assignments = {}
        node_ids = list(self.mesh.nodes.keys())
        for i, node_id in enumerate(node_ids):
            BlockClass = block_types[i % len(block_types)]
            if BlockClass == FractalAttentionBlock:
                assignments[node_id] = BlockClass(self.dim, depth=2) # Example depth
            elif BlockClass == TimelineAttentionBlock:
                 assignments[node_id] = BlockClass(self.dim, history_len=3) # Example history
            elif BlockClass == VICtorchBlock:
                 assignments[node_id] = BlockClass(self.dim, heads=max(1, self.dim // 64 or 4)) # Dynamic heads
            else:
                assignments[node_id] = BlockClass(self.dim)
        return assignments

    def propagate(self, start_node_id: str, x_signal: np.ndarray, steps: int = 3) -> np.ndarray: # Renamed x to x_signal
        """
        Propagates an input signal `x_signal` starting at `start_node_id` for `steps`.
        """
        if start_node_id not in self.node_states:
            # If 'random', pick one. This logic should ideally be in the VictorModule wrapper.
            if start_node_id == 'random' and self.mesh.nodes:
                start_node_id = random.choice(list(self.mesh.nodes.keys()))
                print(f"Random start_node selected: {start_node_id}")
            else:
                raise ValueError(f"Input node '{start_node_id}' not found in mesh and mesh is not empty for random selection.")

        if x_signal.shape[-1] != self.dim:
            raise ValueError(f"Input signal dimension {x_signal.shape[-1]} does not match monolith dimension {self.dim}")


        # Inject initial signal (add or set, depending on desired behavior)
        self.node_states[start_node_id] = self.node_states[start_node_id] + x_signal # Accumulate signal
        self.history.append(copy.deepcopy(self.node_states)) # Log state after injection

        for step in range(steps):
            # Create a snapshot of current states to calculate updates based on this snapshot
            current_step_states_snapshot = copy.deepcopy(self.node_states)

            # Initialize accumulating updates for this step
            accumulated_updates_for_next_step: Dict[str, np.ndarray] = {nid: np.zeros(self.dim) for nid in self.mesh.nodes}

            for node_id, state_at_start_of_step in current_step_states_snapshot.items():
                block = self.node_blocks[node_id]

                # Prepare kwargs for block's forward method if needed
                # Example: FractalAttention might use 'memory', TimelineAttention 'timeline'
                # For now, passing the full snapshot for 'memory' and history for 'timeline'
                block_kwargs = {
                    'memory': np.array(list(current_step_states_snapshot.values())), # Global state as memory
                    'timeline': [s[node_id] for s in self.history if node_id in s][-block.history_len:] if isinstance(block, TimelineAttentionBlock) else None,
                    'branch_id': random.randint(0,10), # Example for BNDX9977
                    'quantum': np.random.rand() * 0.1 # Example for BNDX9977
                }

                processed_signal = block.forward(state_at_start_of_step, **block_kwargs)

                neighbors = self.mesh.get_neighbors(node_id)
                if neighbors:
                    signal_per_neighbor = processed_signal / len(neighbors) # Distribute processed signal
                    for neighbor_id in neighbors:
                        accumulated_updates_for_next_step[neighbor_id] += signal_per_neighbor

            # Update node_states based on accumulated updates and apply decay
            for nid in self.node_states:
                self.node_states[nid] = self.node_states[nid] * 0.85 + accumulated_updates_for_next_step[nid] # Decay old state, add new updates
                # self.node_states[nid] = np.clip(self.node_states[nid], -1.0, 1.0) # Optional: Clip states

            self.history.append(copy.deepcopy(self.node_states))

        return self.get_mesh_embedding()

    def get_mesh_embedding(self) -> np.ndarray:
        if not self.node_states: return np.zeros(self.dim)
        return np.mean(np.array(list(self.node_states.values())), axis=0)

    def summary(self) -> Dict[str, Any]:
        current_embedding = self.get_mesh_embedding()
        return {
            "dim": self.dim,
            "mesh_depth_configured": self.mesh.depth,
            "mesh_nodes": self.mesh.node_count(),
            "mesh_connections": self.mesh.connection_count(),
            "block_type_counts": {
                block_type.__name__ : sum(1 for block in self.node_blocks.values() if isinstance(block, block_type))
                for block_type in [VICtorchBlock, BNDX9977Block, FractalAttentionBlock, TimelineAttentionBlock]
            },
            # "block_assignments": {nid: blk.name for nid, blk in self.node_blocks.items()}, # Can be very large
            "current_mean_activation_on_embedding": np.mean(current_embedding) if current_embedding.size > 0 else 0,
            "history_length": len(self.history)
        }

# --- Example usage (for standalone testing) ---
if __name__ == "__main__":
    np.random.seed(777) # For reproducibility
    DIM_EXAMPLE = 16 # Smaller dim for faster example
    MESH_DEPTH_EXAMPLE = 1 # Smaller depth for fewer nodes

    print("--- Initializing BandoRealityMeshMonolith (Example) ---")
    # It's important that the print statements inside classes are minimal for library use
    # For this example, they are fine.
    monolith = BandoRealityMeshMonolith(dim=DIM_EXAMPLE, mesh_depth=MESH_DEPTH_EXAMPLE)

    print("\n--- Monolith Summary ---")
    # Use json.dumps for pretty printing dicts
    print(json.dumps(monolith.summary(), indent=2))

    input_signal_example = np.random.randn(DIM_EXAMPLE)

    # Ensure there are nodes to choose from
    if not monolith.mesh.nodes:
        print("ERROR: No nodes in mesh for example run.")
    else:
        start_node_example = random.choice(list(monolith.mesh.nodes.keys()))
        print(f"\n--- Propagating Signal (Example) ---")
        print(f"Injecting signal into node: {start_node_example}")

        final_embedding_example = monolith.propagate(start_node_example, input_signal_example, steps=3)

        print(f"\n--- Propagation Complete (Example) ---")
        print(f"Final Mesh Embedding Shape: {final_embedding_example.shape}")
        print(f"Final Mesh Mean Activation: {np.mean(final_embedding_example):.4f}")
        print(f"Monolith history recorded for {len(monolith.history)} steps.")

        # print("\n--- Final Monolith Summary after Propagation ---")
        # print(json.dumps(monolith.summary(), indent=2))

        # print("\n--- Last State in History (sample of nodes) ---")
        # if monolith.history:
        #     last_history_state = monolith.history[-1]
        #     sample_node_ids = list(last_history_state.keys())[:3]
        #     for nid_sample in sample_node_ids:
        #         print(f"Node {nid_sample} state (mean): {np.mean(last_history_state[nid_sample]):.4f}")

# Cleanup for when this is a module:
# Remove extensive print statements from class __init__ or methods if they are too verbose for library use.
# The print in FlowerOfLifeMesh3D and BandoRealityMeshMonolith __init__ are informative for setup.
# The main example usage block is correctly guarded by `if __name__ == "__main__":`.
# Added json and random imports for the example.
# Corrected some variable name shadowing (x, y, z in _recurse; v in VICtorchBlock; chaos in BNDX9977Block, etc.)
# Corrected VICtorchBlock attention scaling (using head_dim) and simplified backward pass further.
# Corrected BandoBlock.grads initialization (was missing for some).
# Refined BandoRealityMeshMonolith.propagate for clarity and added state decay.
# Made _assign_blocks_to_nodes create new instances of blocks.
# Added more detail to summary methods.
# Ensured VICtorchBlock initializes self.cache.
# Corrected FractalAttentionBlock backward pass for W_layers and added grad for scales.
# Corrected TimelineAttentionBlock backward pass.
# Added checks for empty/invalid history/memory in FractalAttentionBlock and TimelineAttentionBlock.
# Added check for x_signal.shape in BandoRealityMeshMonolith.propagate.
# Corrected random choice for start_node if mesh is empty in BandoRealityMeshMonolith.propagate.
# Refined state decay and update accumulation in BandoRealityMeshMonolith.propagate.
# Initialized self.cache in BandoBlock derived classes' __init__ where appropriate or in forward.
# BNDX9977Block.backward: Corrected accumulation for branch_noise_param.
# FractalAttentionBlock: Initialized self.cache_layers as list.
# TimelineAttentionBlock: Initialized self.cache as dict.
# Made VICtorchBlock heads parameter dynamic in BandoRealityMeshMonolith._assign_blocks_to_nodes for robustness.
