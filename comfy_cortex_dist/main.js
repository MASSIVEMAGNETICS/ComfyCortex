// main.js (or main.ts) - Entry point for the Vue application

// In a real Vue application, you would import Vue, the root App component,
// and potentially routers, state management (Pinia), etc.
// e.g.:
// import { createApp } from 'vue'
// import App from './App.vue' // Assuming App.vue is in the same directory for this simulation
// import './style.css' // Import global styles

console.log("Comfy Cortex Frontend Initializing...");

// Placeholder for Vue app creation and mounting
// const app = createApp(App)
// app.mount('#app')

// Simple DOM manipulation for placeholder content if Vue isn't fully set up:
document.addEventListener('DOMContentLoaded', () => {
  const appDiv = document.getElementById('app');
  if (appDiv) {
    const header = document.createElement('h1');
    header.textContent = 'Comfy Cortex (JavaScript Initialized)';
    header.classList.add('neon-text'); // Example of using a neon style

    const existingHeader = appDiv.querySelector('h1');
    if (existingHeader) {
      appDiv.replaceChild(header, existingHeader);
    } else {
      appDiv.prepend(header);
    }

    console.log('Comfy Cortex placeholder UI updated by main.js');
  } else {
    console.error('#app element not found');
  }
});

// Later, this file will be responsible for:
// 1. Importing and setting up Vue.
// 2. Importing the root Vue component (App.vue).
// 3. Importing global styles (like style.css which includes Tailwind).
// 4. Mounting the Vue application to the #app div in index.html.
// 5. Setting up PrimeVue, Pinia, vue-i18n if used directly.

// For now, this is a simple script to show the JS is linked.

// --- "RUN BRAIN" Button Logic ---
async function handleRunBrain() {
  const runBrainButton = document.getElementById('run-brain-button');
  if (!runBrainButton) {
    console.error('RUN BRAIN button not found.');
    return;
  }

  console.log('RUN BRAIN button clicked.');
  runBrainButton.disabled = true;
  runBrainButton.textContent = 'EXECUTING...';

  // Simulate getting the current workflow/graph
  // In a real ComfyUI app, this would be something like:
  // const graph = window.app.graph; // Access to the LiteGraph instance
  // const workflow = graph.serialize();
  // For now, create a dummy workflow that uses our BasicAGINode
  const dummyWorkflow = {
    "last_node_id": 2,
    "last_link_id": 1,
    "nodes": [
      {
        "id": 1,
        "type": "BasicAGINode", // Matches NODE_CLASS_MAPPINGS key
        "pos": [100, 100],
        "size": {"0":180,"1":58}, // Example size
        "flags": {},
        "order": 0,
        "mode": 0, // LiteGraph.ALWAYS
        "inputs": [], // No inputs connected for this example node instance
        "outputs": [
          {"name": "output_string", "type": "STRING", "links": [1]}
        ],
        "properties": {}, // Could hold serialized widget values
        "widgets_values": [
          "Initial Brain Wave" // Value for "input_string"
        ]
      },
      {
        "id": 2,
        "type": "PreviewImage", // Using a standard node to see output conceptually
                                // A real AGI brain might output to a custom display node or save data.
                                // This node expects an IMAGE, so this specific workflow isn't runnable as-is.
                                // This is just a placeholder for graph structure.
                                // For an actual test, we'd need a node that accepts STRING.
                                // Let's imagine a "LogStringNode" for demonstration.
        // "type": "LogStringNode", // If such a node existed
        "pos": [400, 100],
        "size": {"0":210,"1":58},
        "flags": {},
        "order": 1,
        "mode": 0,
        "inputs": [
          {"name": "text_input", "type": "STRING", "link": 1} // "text_input" is hypothetical
        ],
        "properties": {}
      }
    ],
    "links": [
      [1, 1, 0, 2, 0, "STRING"] // Link ID, from_node_id, from_slot_idx, to_node_id, to_slot_idx, type
    ],
    "groups": [],
    "config": {},
    "extra": {}, // Could include client_id if needed by backend
    "version": 0.4 // Example version
  };

  // For a real test with BasicAGINode, we need a node that accepts a string.
  // Let's simplify the dummy workflow to just the BasicAGINode for the API call.
  // The backend doesn't strictly require a fully connected graph to queue,
  // it validates based on what `outputs_to_execute` are determined.
  const simplifiedWorkflowForRunBrain = {
    "1": { // Node ID as key
      "inputs": { "input_string": "Test Brain Input via API" },
      "class_type": "BasicAGINode"
    }
    // We'd typically specify which outputs to execute, or the backend determines this.
    // For now, sending this simplified format similar to what /prompt expects.
  };


  try {
    const response = await fetch('/run_brain', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      // The /prompt endpoint expects a structure like:
      // { prompt: workflow_object, number: ..., client_id: ... (optional) }
      // We will mimic this for /run_brain
      body: JSON.stringify({ prompt: dummyWorkflow }), // Using the more complete dummyWorkflow
    });

    const result = await response.json();

    if (response.ok) {
      console.log('Brain execution request successful:', result);
      if (result.prompt_id) {
        alert(`Brain queued for execution! Prompt ID: ${result.prompt_id}`);
      }
      // TODO: Handle UI updates, e.g., display prompt ID, status, etc.
    } else {
      console.error('Brain execution request failed:', result);
      alert(`Error queuing brain: ${result.error?.message || 'Unknown error'}`);
    }
  } catch (error) {
    console.error('Error sending run_brain request:', error);
    alert(`Network error or server unavailable: ${error.message}`);
  } finally {
    runBrainButton.disabled = false;
    runBrainButton.textContent = 'RUN BRAIN';
  }
}


document.addEventListener('DOMContentLoaded', () => {
  const appDiv = document.getElementById('app');
  if (appDiv) {
    const header = appDiv.querySelector('h1') || document.createElement('h1');
    header.textContent = 'Comfy Cortex (JavaScript Initialized)';
    if (!header.parentElement) appDiv.prepend(header);

    console.log('Comfy Cortex placeholder UI updated by main.js');
  } else {
    console.error('#app element not found');
  }

  const runBrainButton = document.getElementById('run-brain-button');
  if (runBrainButton) {
    runBrainButton.addEventListener('click', handleRunBrain);
  } else {
    console.error('RUN BRAIN button not found for event listener setup.');
  }
});
