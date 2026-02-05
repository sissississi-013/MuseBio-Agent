/**
 * Muse Bio Chat Interface
 * Frontend JavaScript for the AI assistant
 */

// Configuration
const API_BASE_URL = window.location.origin;
let sessionId = null;
let isLoading = false;

// DOM Elements
const chatMessages = document.getElementById('chatMessages');
const chatContainer = document.getElementById('chatContainer');
const chatForm = document.getElementById('chatForm');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const pdfList = document.getElementById('pdfList');
const sessionIndicator = document.getElementById('sessionIndicator');
const userTypeIndicator = document.getElementById('userTypeIndicator');
const pdfModal = document.getElementById('pdfModal');
const pdfViewer = document.getElementById('pdfViewer');
const pdfModalTitle = document.getElementById('pdfModalTitle');
const pdfDownloadLink = document.getElementById('pdfDownloadLink');
const closePdfModal = document.getElementById('closePdfModal');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

async function initializeApp() {
    // Configure marked for markdown parsing
    marked.setOptions({
        breaks: true,
        gfm: true,
        headerIds: false,
        mangle: false
    });

    // Load PDFs
    await loadPdfList();

    // Set up event listeners
    setupEventListeners();

    // Auto-resize textarea
    setupTextareaAutoResize();
}

function setupEventListeners() {
    // Chat form submission
    chatForm.addEventListener('submit', handleSubmit);

    // Enter key to send (Shift+Enter for new line)
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
        }
    });

    // Quick start buttons
    document.querySelectorAll('.quick-btn').forEach(btn => {
        btn.addEventListener('click', () => handleQuickStart(btn.dataset.type));
    });

    // New chat button
    document.querySelector('[data-action="new-chat"]').addEventListener('click', resetChat);

    // PDF modal close
    closePdfModal.addEventListener('click', () => {
        pdfModal.classList.remove('active');
    });

    // Close modal on backdrop click
    pdfModal.addEventListener('click', (e) => {
        if (e.target === pdfModal) {
            pdfModal.classList.remove('active');
        }
    });

    // Close modal on Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && pdfModal.classList.contains('active')) {
            pdfModal.classList.remove('active');
        }
    });
}

function setupTextareaAutoResize() {
    messageInput.addEventListener('input', () => {
        messageInput.style.height = 'auto';
        messageInput.style.height = Math.min(messageInput.scrollHeight, 150) + 'px';
    });
}

async function loadPdfList() {
    try {
        const response = await fetch(`${API_BASE_URL}/pdfs`);
        if (!response.ok) throw new Error('Failed to load PDFs');

        const data = await response.json();
        renderPdfList(data.pdfs);
    } catch (error) {
        console.error('Error loading PDFs:', error);
    }
}

function renderPdfList(pdfs) {
    pdfList.innerHTML = pdfs.map(pdf => `
        <div class="pdf-item" data-key="${pdf.key}" data-file="${pdf.file}" data-description="${pdf.description}">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
                <polyline points="10 9 9 9 8 9"></polyline>
            </svg>
            <span class="pdf-item-text">${pdf.description}</span>
        </div>
    `).join('');

    // Add click handlers
    pdfList.querySelectorAll('.pdf-item').forEach(item => {
        item.addEventListener('click', () => {
            openPdfModal(item.dataset.key, item.dataset.description);
        });
    });
}

async function handleSubmit(e) {
    e.preventDefault();

    const message = messageInput.value.trim();
    if (!message || isLoading) return;

    // Clear input and reset height
    messageInput.value = '';
    messageInput.style.height = 'auto';

    // Add user message
    addMessage(message, 'user');

    // Show loading
    const loadingId = showLoading();

    try {
        const response = await sendMessage(message);

        // Remove loading
        removeLoading(loadingId);

        // Update session info
        if (response.session_id) {
            sessionId = response.session_id;
            sessionIndicator.textContent = `Session: ${sessionId.slice(0, 8)}...`;
        }

        if (response.detected_user_type) {
            const typeLabels = {
                donor: 'Potential Donor',
                investor: 'Investor Inquiry',
                partner: 'Partnership Inquiry'
            };
            userTypeIndicator.textContent = typeLabels[response.detected_user_type] || response.detected_user_type;
        }

        // Add assistant message with PDFs
        addMessage(response.response, 'assistant', response.suggested_pdfs);

    } catch (error) {
        removeLoading(loadingId);
        showError(error.message || 'Failed to send message. Please try again.');
    }
}

async function sendMessage(message) {
    isLoading = true;
    sendBtn.disabled = true;

    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                session_id: sessionId
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to send message');
        }

        return await response.json();
    } finally {
        isLoading = false;
        sendBtn.disabled = false;
    }
}

async function handleQuickStart(type) {
    const prompts = {
        donor: "Hi! I'm interested in learning about donating to Muse Bio. Can you tell me about your programs?",
        investor: "Hello, I'm interested in learning about investment opportunities at Muse Bio.",
        partner: "Hi there! I represent a company and I'm interested in exploring partnership opportunities with Muse Bio."
    };

    const message = prompts[type];
    if (message) {
        messageInput.value = message;
        handleSubmit(new Event('submit'));
    }
}

function addMessage(content, role, suggestedPdfs = []) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    const avatarImg = document.createElement('img');
    avatarImg.src = role === 'assistant' ? '/static/avatar-muse.png' : '/static/avatar-user.png';
    avatarImg.alt = role === 'assistant' ? 'Muse Bio' : 'You';
    avatar.appendChild(avatarImg);

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';

    if (role === 'assistant') {
        // Parse markdown for assistant messages
        // Remove emoji patterns and clean up
        let cleanContent = content
            .replace(/[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]/gu, '')
            .replace(/:\)|:\(|:D|;\)|:P/g, '');

        textDiv.innerHTML = marked.parse(cleanContent);
    } else {
        // Plain text for user messages
        textDiv.textContent = content;
    }

    contentDiv.appendChild(textDiv);

    // Add PDF previews if suggested
    if (suggestedPdfs && suggestedPdfs.length > 0) {
        suggestedPdfs.forEach(pdf => {
            const pdfPreview = createPdfPreview(pdf);
            contentDiv.appendChild(pdfPreview);
        });
    }

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);

    // Scroll to bottom
    scrollToBottom();
}

function createPdfPreview(pdf) {
    const container = document.createElement('div');
    container.className = 'pdf-preview';

    container.innerHTML = `
        <div class="pdf-preview-header">
            <div class="pdf-preview-title">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                </svg>
                ${pdf.description}
            </div>
            <div class="pdf-preview-actions">
                <button class="pdf-action-btn toggle-preview" data-expanded="false">Show Preview</button>
                <button class="pdf-action-btn primary view-full" data-key="${pdf.key}" data-description="${pdf.description}">Open</button>
            </div>
        </div>
        <div class="pdf-preview-body" style="display: none;">
            <object class="pdf-preview-frame" data="${API_BASE_URL}/pdfs/${pdf.key}" type="application/pdf">
                <p>PDF preview not available. <a href="${API_BASE_URL}/pdfs/${pdf.key}" target="_blank">Click here to view</a></p>
            </object>
        </div>
    `;

    // Toggle preview
    const toggleBtn = container.querySelector('.toggle-preview');
    const previewBody = container.querySelector('.pdf-preview-body');

    toggleBtn.addEventListener('click', () => {
        const expanded = toggleBtn.dataset.expanded === 'true';
        toggleBtn.dataset.expanded = !expanded;
        toggleBtn.textContent = expanded ? 'Show Preview' : 'Hide Preview';
        previewBody.style.display = expanded ? 'none' : 'block';

        if (!expanded) {
            scrollToBottom();
        }
    });

    // Open full view
    container.querySelector('.view-full').addEventListener('click', (e) => {
        openPdfModal(e.target.dataset.key, e.target.dataset.description);
    });

    return container;
}

function openPdfModal(pdfKey, title) {
    pdfModalTitle.textContent = title;
    const pdfUrl = `${API_BASE_URL}/pdfs/${pdfKey}`;
    // Replace iframe with object for better PDF rendering
    const container = document.querySelector('.pdf-viewer-container');
    container.innerHTML = `<object class="pdf-viewer" data="${pdfUrl}" type="application/pdf">
        <p>PDF cannot be displayed. <a href="${pdfUrl}" target="_blank">Click here to open in new tab</a></p>
    </object>`;
    pdfDownloadLink.href = pdfUrl;
    pdfModal.classList.add('active');
}

function showLoading() {
    const id = 'loading-' + Date.now();
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message assistant-message loading-message';
    loadingDiv.id = id;

    loadingDiv.innerHTML = `
        <div class="message-avatar"><img src="/static/avatar-muse.png" alt="Muse Bio"></div>
        <div class="message-content">
            <div class="message-text">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        </div>
    `;

    chatMessages.appendChild(loadingDiv);
    scrollToBottom();
    return id;
}

function removeLoading(id) {
    const loadingEl = document.getElementById(id);
    if (loadingEl) {
        loadingEl.remove();
    }
}

function showError(message) {
    const toast = document.createElement('div');
    toast.className = 'error-toast';
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 5000);
}

function resetChat() {
    // Clear messages except welcome
    chatMessages.innerHTML = `
        <div class="message assistant-message">
            <div class="message-avatar"><img src="/static/avatar-muse.png" alt="Muse Bio"></div>
            <div class="message-content">
                <div class="message-text">
                    <p>Welcome to Muse Bio! I'm here to help you learn about our menstrual blood stem cell programs.</p>
                    <p>I can assist with:</p>
                    <ul>
                        <li><strong>Potential Donors</strong> - Learn about our Research Study and Commercial Donation programs</li>
                        <li><strong>Investors</strong> - Get information about investment opportunities</li>
                        <li><strong>Partners</strong> - Explore partnership possibilities</li>
                    </ul>
                    <p>How can I help you today?</p>
                </div>
            </div>
        </div>
    `;

    // Reset session
    sessionId = null;
    sessionIndicator.textContent = 'New Session';
    userTypeIndicator.textContent = 'Ask about donations, partnerships, or investments';

    // Clear input
    messageInput.value = '';
    messageInput.style.height = 'auto';
}

function scrollToBottom() {
    chatContainer.scrollTo({
        top: chatContainer.scrollHeight,
        behavior: 'smooth'
    });
}
