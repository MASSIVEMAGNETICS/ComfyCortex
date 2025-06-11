# Recursive and Stateful Operations in ComfyCortex

ComfyUI executes workflows as a directed acyclic graph (DAG). This means that direct cycles (e.g., a node's output connected to its own input, or a small loop of nodes) are generally disallowed and will result in a `DependencyCycleError`.

ComfyCortex, while aiming for more brain-like cognitive flows, operates within this ComfyUI framework. Therefore, implementing recursion and persistent state requires specific patterns.

## 1. Stateful Nodes

Stateful nodes are the primary way to manage persistent information across multiple executions or iterations of a part of the graph.

**Concept:**
A node maintains its state in its instance variables (e.g., `self.my_data = ...`). When the node executes, it can read from and write to this internal state.

**Example (`SimpleTextMemoryNode` from `example_cognitive_nodes.py`):**
```python
class SimpleTextMemoryNode(GenericCognitiveNode):
    # ... (INPUT_TYPES, RETURN_TYPES etc.) ...

    def __init__(self):
        super().__init__()
        self.instance_memories: dict[str, str] = {} # State stored here

    def access_memory(self, memory_id: str, store_value: str, write_trigger: bool, read_trigger: bool, clear_trigger: bool = False) -> Tuple[str]:
        if write_trigger:
            self.instance_memories[memory_id] = store_value

        if read_trigger:
            return (self.instance_memories.get(memory_id, ""),)
        return ("",) # Default output
```

**Characteristics:**
- **Persistence:** The state (`self.instance_memories`) persists as long as the ComfyUI server process is running and the workflow/graph object containing the node instance remains in memory.
- **Scope:** State is typically scoped to the specific instance of the node in the graph. If you need memory shared across different memory nodes, you'd use class-level variables (though this can have its own complexities with parallel execution if not handled carefully).
- **Activation:** The node's state is read or updated *when the node executes*. Triggers for execution come from changes in its inputs or by being part of an execution chain.

**Use Cases for State:**
- Short-term, medium-term, long-term memory stores.
- Accumulators (e.g., aggregating data over time).
- Emotional state representation.
- Beliefs, world models.
- Current goals or directives being processed.

## 2. Iterative Execution (Simulating Loops/Recursion)

True recursion in the sense of a node calling itself or a direct graph cycle isn't directly supported. Loops and recursive-like processes are achieved by re-triggering execution of a part of the graph.

**Patterns:**

### a. External Control / Re-Queueing Prompts
- An external script or another system (or even a complex "Controller Node" within ComfyUI) can repeatedly queue new prompts.
- In each new prompt, inputs to the "looping" section of the graph can be modified based on the outputs from the previous execution.
- Stateful nodes are essential here to carry over information (the "state" of the loop/recursion) from one iteration to the next.

**Example Flow:**
1. **Graph:** `InputNode` -> `ProcessingLogicNode` -> `StatefulMemoryNode` -> `OutputNode`
2. **Iteration 1:**
   - External script sends `data_1` to `InputNode`.
   - `ProcessingLogicNode` processes it, result is `processed_1`.
   - `StatefulMemoryNode` stores `processed_1` (and maybe its previous state `S0` becomes `S1`).
3. **Iteration 2:**
   - External script gets `OutputNode`'s result from Iteration 1.
   - It decides new input `data_2` (perhaps based on previous output or `S1` if `StatefulMemoryNode` also outputs its state).
   - Sends `data_2` to `InputNode`.
   - `StatefulMemoryNode` now updates its state from `S1` to `S2`.
   - ...and so on.

### b. Conditional Execution and Branching (within a single run)
- Nodes like the `TextDirectiveRouterNode` can direct data flow.
- You can create graph structures that process data, then based on a condition (e.g., output of a "DecisionNode"), route the data back to an earlier-style processing stage *but with different parameters or by enabling different parts of the graph*.
- This isn't a true loop in terms of re-executing the *same instance* of a node with its *exact same inputs* in one go, but rather a conditional path that might re-use similar *types* of processing.
- "Looping" a fixed number of times can be achieved by chaining N copies of a processing sub-graph, with state passed between them.

### c. "Tick" or "Step" Based Execution
- Introduce a global or regional "tick" or "step" input.
- Many cognitive nodes could take this "tick" as an input.
- Each time the "tick" changes (e.g., an integer incrementing), nodes re-evaluate.
- This is a form of iterative execution driven by an external pacer.

## 3. Dynamic Graph Alteration (Advanced - Conceptual)

- ComfyUI's `comfy_execution.graph.DynamicPrompt` object suggests capabilities for nodes to modify the graph structure at runtime (e.g., by adding "ephemeral nodes").
- This is an advanced feature of ComfyUI itself.
- If a cognitive node could, as part of its execution, add new instances of itself or other nodes to the graph and wire them up, this could enable more complex recursive structures.
- **Challenges:** This would require careful management of:
    - Termination conditions (to prevent infinite loops).
    - State propagation to new instances.
    - Namespacing and ID management for dynamically added nodes.
- This is currently more of a theoretical possibility for ComfyCortex to explore within ComfyUI's existing advanced capabilities, rather than a straightforward pattern.

## 4. CortexCluster/MetaNode Recursion

- If a `CortexClusterNode` (MetaNode) can contain other `CortexClusterNodes`, including instances of itself or its own type, then recursion at the cluster level becomes possible.
- This is a powerful concept but inherits all the challenges of standard recursion:
    - **Base Cases:** The subgraph within the cluster must have logic to determine when recursion should stop.
    - **State Modification:** Each recursive call would likely operate on a modified version of the state or problem.
    - **Stack Depth:** Deeply nested cluster calls could have performance implications or hit limits.
- The `CortexClusterNode` would need to manage the execution and state of its contained subgraph carefully, especially if that subgraph makes a "recursive call" by including another instance of the same cluster type.

## Summary of Best Practices for ComfyCortex:

- **Embrace Stateful Nodes:** Use them extensively to manage context, memory, and ongoing processes.
- **Design for Iteration:** Think about how your cognitive processes unfold over discrete steps or iterations.
- **Use External Control for Complex Loops:** For sophisticated looping or recursive algorithms that exceed simple graph re-triggering, an external script managing prompt queuing is often the most robust approach.
- **Clearly Define Triggers:** Ensure stateful nodes have clear input conditions (e.g., `write_trigger`, `read_trigger`, `process_tick`) that define when they should update or output their state.
- **Be Wary of Direct Cycles:** Understand that ComfyUI will prevent direct graph cycles. Design your flows accordingly.

By using these patterns, ComfyCortex can achieve complex, dynamic, and seemingly recursive behaviors even within ComfyUI's DAG-based execution model.
