const repoSetSelector = document.getElementById('repo-set-selector');
const newRepoBtn = document.getElementById('new-repo-btn');
const loadRepoBtn = document.getElementById('load-repo-btn');
const saveRepoBtn = document.getElementById('save-repo-btn');
const deleteRepoBtn = document.getElementById('delete-repo-btn');
const runRepoBtn = document.getElementById('run-repo-btn');
const logOutput = document.getElementById('log-output');

let editor = null; // JSONEditor instance
let currentRepoSetName = null;
let currentLogFilename = null;
let logPollingInterval = null;

const API_BASE_URL = 'http://127.0.0.1:8001/api/repositories';

// --- JSON Editor Setup ---
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById("json-editor");
    const options = {
        mode: 'code', // or 'tree', 'form', 'text', 'view'
        modes: ['code', 'tree', 'form', 'text', 'view'],
        onError: function (err) {
            alert(err.toString());
        },
        onModeChange: function (newMode, oldMode) {
            console.log('Mode switched from ', oldMode, 'to', newMode);
        }
    };
    editor = new JSONEditor(container, options);

    // Initial load of repository sets
    fetchRepositorySets();
});

// --- API Functions ---
async function fetchRepositorySets() {
    try {
        const response = await fetch(API_BASE_URL);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        repoSetSelector.innerHTML = data.repository_set_names.map(name => 
            `<option value="${name}">${name}</option>`
        ).join('');
    } catch (error) {
        console.error("Error fetching repository sets:", error);
        alert("Failed to fetch repository sets. Is the backend running?");
    }
}

async function loadRepositorySet(name) {
    try {
        const response = await fetch(`${API_BASE_URL}/${name}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        editor.set(data.repository_set);
        currentRepoSetName = name;
        logOutput.textContent = `Loaded repository set: ${name}.`;
        stopLogPolling();
        currentLogFilename = null;
    } catch (error) {
        console.error(`Error loading repository set ${name}:`, error);
        alert(`Failed to load repository set ${name}.`);
    }
}

async function saveRepositorySet() {
    if (!editor) return;

    let repoSetData;
    try {
        repoSetData = editor.get();
    } catch (e) {
        alert("Invalid JSON in editor: " + e.message);
        return;
    }

    if (!repoSetData || !repoSetData.name) {
        alert("Repository Set must have a 'name' field.");
        return;
    }

    try {
        const response = await fetch(API_BASE_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(repoSetData)
        });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const result = await response.json();
        alert(`Repository set '${result.name}' saved!`);
        fetchRepositorySets(); // Refresh the list
        currentRepoSetName = result.name;
    } catch (error) {
        console.error("Error saving repository set:", error);
        alert("Failed to save repository set.");
    }
}

async function deleteRepositorySet(name) {
    if (!confirm(`Are you sure you want to delete repository set '${name}'?`)) return;
    try {
        const response = await fetch(`${API_BASE_URL}/${name}`, {
            method: 'DELETE',
        });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        alert(`Repository set '${name}' deleted!`);
        fetchRepositorySets();
        if (currentRepoSetName === name) {
            editor.set({}); // Clear editor if deleted
            currentRepoSetName = null;
            logOutput.textContent = "";
            stopLogPolling();
        }
    } catch (error) {
        console.error(`Error deleting repository set ${name}:`, error);
        alert(`Failed to delete repository set ${name}.`);
    }
}

async function runRepositorySet(name) {
    if (!name) {
        alert("Please load a repository set first.");
        return;
    }
    logOutput.textContent = `Running repository set: ${name}...\n`;
    stopLogPolling(); // Stop any previous polling

    try {
        const response = await fetch(`${API_BASE_URL}/run`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ repository_set_name: name })
        });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const result = await response.json();
        currentLogFilename = result.log_file;
        startLogPolling();
    } catch (error) {
        console.error(`Error running repository set ${name}:`, error);
        alert(`Failed to run repository set ${name}.`);
        logOutput.textContent += `Error: ${error.message}\n`;
    }
}

async function getLogContent(logFilename) {
    try {
        const response = await fetch(`${API_BASE_URL}/logs/${logFilename}`);
        if (!response.ok) {
            // If log file not found, it might still be generating or an error occurred.
            // Don't stop polling immediately, give it a few tries.
            console.warn(`Log file ${logFilename} not yet available or error: ${response.status}`);
            return;
        }
        const data = await response.json();
        logOutput.textContent = data.content;
        logOutput.scrollTop = logOutput.scrollHeight; // Scroll to bottom

        // Check if execution has completed (look for a specific string in the log)
        if (data.content.includes("--- Normcode Execution Completed ---") ||
            data.content.includes("--- Normcode Execution Failed:")) {
            stopLogPolling();
        }

    } catch (error) {
        console.error(`Error fetching log content for ${logFilename}:`, error);
        stopLogPolling();
    }
}

function startLogPolling() {
    if (logPollingInterval) clearInterval(logPollingInterval);
    if (currentLogFilename) {
        logPollingInterval = setInterval(() => getLogContent(currentLogFilename), 2000); // Poll every 2 seconds
    }
}

function stopLogPolling() {
    if (logPollingInterval) {
        clearInterval(logPollingInterval);
        logPollingInterval = null;
    }
}

// --- Event Listeners ---
repoSetSelector.addEventListener('change', (e) => loadRepositorySet(e.target.value));
newRepoBtn.addEventListener('click', () => {
    editor.set({
        name: "new_repository_set",
        concepts: [],
        inferences: []
    });
    currentRepoSetName = null; // No currently loaded repo until saved
    logOutput.textContent = "Create a new repository set. Remember to save it!";
    stopLogPolling();
});
loadRepoBtn.addEventListener('click', () => {
    if (repoSetSelector.value) {
        loadRepositorySet(repoSetSelector.value);
    } else {
        alert("Please select a repository set to load.");
    }
});
saveRepoBtn.addEventListener('click', saveRepositorySet);
deleteRepoBtn.addEventListener('click', () => {
    if (repoSetSelector.value) {
        deleteRepositorySet(repoSetSelector.value);
    } else {
        alert("Please select a repository set to delete.");
    }
});
runRepoBtn.addEventListener('click', () => {
    if (currentRepoSetName) {
        runRepositorySet(currentRepoSetName);
    } else if (repoSetSelector.value) {
        runRepositorySet(repoSetSelector.value);
    } else {
        alert("Please load or select a repository set to run.");
    }
});
