/**
 * AI Features for Grant Management
 * Handles matching, extraction, and narrative generation
 */

// Check if AI is enabled
async function checkAIStatus() {
    try {
        const response = await fetch('/api/ai-v2/status');
        const data = await response.json();
        return data.enabled;
    } catch (error) {
        console.error('Error checking AI status:', error);
        return false;
    }
}

// Match grant with organization
async function matchGrant(grantId) {
    try {
        const response = await fetch('/api/ai-v2/match', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ grant_id: grantId })
        });
        
        const data = await response.json();
        
        if (data.fit_score === null) {
            showAIDisabledMessage();
            return null;
        }
        
        return data;
    } catch (error) {
        console.error('Error matching grant:', error);
        showError('Failed to match grant');
        return null;
    }
}

// Get detailed match explanation
async function explainMatch(grantId) {
    try {
        const response = await fetch('/api/ai-v2/explain-match', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ grant_id: grantId })
        });
        
        const data = await response.json();
        return data.explanation;
    } catch (error) {
        console.error('Error explaining match:', error);
        return null;
    }
}

// Extract grant from URL or text
async function extractGrant(urlOrText, isUrl = true) {
    try {
        const payload = isUrl ? { url: urlOrText } : { text: urlOrText };
        
        const response = await fetch('/api/ai-v2/extract', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        
        if (data.error && data.error.includes('AI extraction disabled')) {
            showAIDisabledMessage();
            return null;
        }
        
        return data;
    } catch (error) {
        console.error('Error extracting grant:', error);
        showError('Failed to extract grant information');
        return null;
    }
}

// Generate narrative for grant
async function generateNarrative(grantId, sections = ['need', 'program', 'outcomes', 'budget_rationale']) {
    try {
        const response = await fetch('/api/ai-v2/narrative', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                grant_id: grantId,
                sections: sections
            })
        });
        
        const data = await response.json();
        
        if (data.error && data.error.includes('AI narrative generation disabled')) {
            showAIDisabledMessage();
            return null;
        }
        
        return data.narrative;
    } catch (error) {
        console.error('Error generating narrative:', error);
        showError('Failed to generate narrative');
        return null;
    }
}

// Batch match multiple grants
async function batchMatchGrants(grantIds) {
    try {
        const response = await fetch('/api/ai-v2/batch-match', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ grant_ids: grantIds })
        });
        
        const data = await response.json();
        return data.results;
    } catch (error) {
        console.error('Error batch matching:', error);
        return [];
    }
}

// UI Functions

// Show AI disabled message with link to settings
function showAIDisabledMessage() {
    const message = `
        <div class="bg-gray-100 border border-gray-300 rounded-lg p-4 text-center">
            <p class="text-gray-600 mb-2">AI features are disabled</p>
            <a href="/settings" class="text-pink-500 hover:text-pink-600 underline">
                Add your OpenAI API key in Settings
            </a>
        </div>
    `;
    
    // Show in modal or alert area
    if (document.getElementById('ai-message-area')) {
        document.getElementById('ai-message-area').innerHTML = message;
    } else {
        alert('AI features are disabled. Please add your OpenAI API key in Settings.');
    }
}

// Display fit score with styling
function displayFitScore(score, reason, elementId) {
    if (!score) {
        document.getElementById(elementId).innerHTML = `
            <span class="text-gray-400">N/A</span>
            <a href="/settings" class="text-xs text-pink-500 hover:underline ml-2">Enable AI</a>
        `;
        return;
    }
    
    const colors = {
        1: 'bg-red-100 text-red-800',
        2: 'bg-orange-100 text-orange-800',
        3: 'bg-yellow-100 text-yellow-800',
        4: 'bg-green-100 text-green-800',
        5: 'bg-green-200 text-green-900'
    };
    
    const html = `
        <div class="inline-flex items-center">
            <span class="px-2 py-1 rounded-full text-sm font-medium ${colors[score]}">
                ${score}/5
            </span>
            <div class="ml-2 group relative">
                <svg class="w-4 h-4 text-gray-400 hover:text-gray-600 cursor-help" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
                </svg>
                <div class="absolute z-10 invisible group-hover:visible bg-gray-800 text-white text-sm rounded-lg p-2 w-64 -top-2 left-6">
                    ${reason}
                </div>
            </div>
        </div>
    `;
    
    document.getElementById(elementId).innerHTML = html;
}

// Show extraction modal
function showExtractionModal() {
    const modal = `
        <div id="extraction-modal" class="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
            <div class="bg-white rounded-lg p-6 w-full max-w-2xl">
                <h2 class="text-xl font-bold mb-4">Extract Grant from URL or Text</h2>
                
                <div class="mb-4">
                    <label class="block text-sm font-medium mb-2">
                        <input type="radio" name="extract-type" value="url" checked class="mr-2">
                        Extract from URL
                    </label>
                    <label class="block text-sm font-medium mb-2">
                        <input type="radio" name="extract-type" value="text" class="mr-2">
                        Extract from Pasted Text
                    </label>
                </div>
                
                <div id="url-input" class="mb-4">
                    <input type="url" id="extract-url" class="w-full border rounded px-3 py-2" 
                           placeholder="https://example.com/grant-opportunity">
                </div>
                
                <div id="text-input" class="mb-4 hidden">
                    <textarea id="extract-text" class="w-full border rounded px-3 py-2 h-32" 
                              placeholder="Paste RFP or grant text here..."></textarea>
                </div>
                
                <div id="ai-message-area" class="mb-4"></div>
                
                <div class="flex justify-end space-x-2">
                    <button onclick="closeExtractionModal()" 
                            class="px-4 py-2 border border-gray-300 rounded hover:bg-gray-100">
                        Cancel
                    </button>
                    <button onclick="performExtraction()" 
                            class="px-4 py-2 bg-pink-500 text-white rounded hover:bg-pink-600">
                        Extract Grant
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modal);
    
    // Toggle input type
    document.querySelectorAll('input[name="extract-type"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            if (e.target.value === 'url') {
                document.getElementById('url-input').classList.remove('hidden');
                document.getElementById('text-input').classList.add('hidden');
            } else {
                document.getElementById('url-input').classList.add('hidden');
                document.getElementById('text-input').classList.remove('hidden');
            }
        });
    });
}

// Close extraction modal
function closeExtractionModal() {
    const modal = document.getElementById('extraction-modal');
    if (modal) modal.remove();
}

// Perform extraction
async function performExtraction() {
    const extractType = document.querySelector('input[name="extract-type"]:checked').value;
    const input = extractType === 'url' 
        ? document.getElementById('extract-url').value
        : document.getElementById('extract-text').value;
    
    if (!input) {
        showError('Please provide a URL or text to extract');
        return;
    }
    
    // Show loading
    const button = event.target;
    button.disabled = true;
    button.textContent = 'Extracting...';
    
    const result = await extractGrant(input, extractType === 'url');
    
    if (result && result.grant) {
        showSuccess(`Grant "${result.grant.title}" extracted and saved successfully!`);
        closeExtractionModal();
        // Refresh grants list if on that page
        if (typeof loadGrants === 'function') {
            loadGrants();
        }
    } else {
        button.disabled = false;
        button.textContent = 'Extract Grant';
    }
}

// Show success message
function showSuccess(message) {
    const alert = `
        <div class="fixed top-4 right-4 bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded z-50">
            ${message}
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', alert);
    setTimeout(() => {
        document.querySelector('.fixed.top-4.right-4').remove();
    }, 3000);
}

// Show error message
function showError(message) {
    const alert = `
        <div class="fixed top-4 right-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded z-50">
            ${message}
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', alert);
    setTimeout(() => {
        document.querySelector('.fixed.top-4.right-4').remove();
    }, 3000);
}

// Initialize AI features on page load
document.addEventListener('DOMContentLoaded', async () => {
    const aiEnabled = await checkAIStatus();
    
    // Update UI based on AI status
    if (!aiEnabled) {
        document.querySelectorAll('.ai-feature').forEach(el => {
            el.classList.add('opacity-50');
            el.title = 'AI features disabled - Add API key in Settings';
        });
    }
});