// Theme Toggle
const themeToggle = document.getElementById('themeToggle');
const body = document.body;

themeToggle.addEventListener('click', () => {
    const currentTheme = body.getAttribute('data-theme');
    if (currentTheme === 'dark') {
        body.removeAttribute('data-theme');
        themeToggle.textContent = '🌙 Dark Mode';
        localStorage.setItem('theme', 'light');
    } else {
        body.setAttribute('data-theme', 'dark');
        themeToggle.textContent = '☀️ Light Mode';
        localStorage.setItem('theme', 'dark');
    }
});

// Load saved theme
const savedTheme = localStorage.getItem('theme');
if (savedTheme === 'dark') {
    body.setAttribute('data-theme', 'dark');
    themeToggle.textContent = '☀️ Light Mode';
}

// Set session ID
if (!document.cookie.includes('session_id')) {
    document.cookie = `session_id=${generateUUID()}; path=/`;
}

function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// Image Upload
const imageUpload = document.getElementById('imageUpload');
const imagePreview = document.getElementById('imagePreview');
const previewImg = document.getElementById('previewImg');
const analyzeBtn = document.getElementById('analyzeBtn');
const loading = document.getElementById('loading');
const resultsSection = document.getElementById('resultsSection');

imageUpload.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (event) => {
            previewImg.src = event.target.result;
            imagePreview.style.display = 'block';
        };
        reader.readAsDataURL(file);
    }
});

// Webcam
const webcamBtn = document.getElementById('webcamBtn');
const webcamModal = document.getElementById('webcamModal');
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const captureBtn = document.getElementById('captureBtn');
const cancelWebcam = document.getElementById('cancelWebcam');
let stream = null;

webcamBtn.addEventListener('click', () => {
    webcamModal.style.display = 'block';
    startWebcam();
});

document.querySelector('#webcamModal .close').addEventListener('click', () => {
    stopWebcam();
    webcamModal.style.display = 'none';
});

cancelWebcam.addEventListener('click', () => {
    stopWebcam();
    webcamModal.style.display = 'none';
});

function startWebcam() {
    navigator.mediaDevices.getUserMedia({ video: true })
        .then((mediaStream) => {
            stream = mediaStream;
            video.srcObject = mediaStream;
        })
        .catch((error) => {
            console.error('Error accessing webcam:', error);
            alert('Unable to access webcam. Please check permissions.');
        });
}

function stopWebcam() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
    }
}

captureBtn.addEventListener('click', () => {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    
    canvas.toBlob((blob) => {
        const file = new File([blob], 'webcam-capture.jpg', { type: 'image/jpeg' });
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        imageUpload.files = dataTransfer.files;
        
        previewImg.src = canvas.toDataURL();
        imagePreview.style.display = 'block';
        
        stopWebcam();
        webcamModal.style.display = 'none';
    }, 'image/jpeg');
});

// Analyze Skin
analyzeBtn.addEventListener('click', async () => {
    const file = imageUpload.files[0];
    if (!file) {
        alert('Please select an image first');
        return;
    }
    
    loading.style.display = 'block';
    imagePreview.style.display = 'none';
    resultsSection.style.display = 'none';
    
    const formData = new FormData();
    formData.append('image', file);
    
    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayResults(data);
            loadHistory();
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred during analysis');
    } finally {
        loading.style.display = 'none';
    }
});

function displayResults(data) {
    // Display health score
    document.getElementById('healthScore').textContent = Math.round(data.health_score);
    document.getElementById('skinType').textContent = data.skin_type;
    
    // Display analysis details
    const analysisGrid = document.getElementById('analysisGrid');
    analysisGrid.innerHTML = '';
    
    const analysis = data.analysis;
    const items = [
        { title: 'Acne Spots', value: analysis.acne_spots?.severity || 0, level: analysis.acne_spots?.level || 'low' },
        { title: 'Dark Circles', value: analysis.dark_circles?.severity || 0, level: analysis.dark_circles?.level || 'low' },
        { title: 'Redness', value: analysis.redness?.severity || 0, level: analysis.redness?.level || 'low' },
        { title: 'Oiliness', value: analysis.oiliness?.score || 0, level: analysis.oiliness?.level || 'low' },
        { title: 'Dryness', value: analysis.dryness?.score || 0, level: analysis.dryness?.level || 'low' },
        { title: 'Uneven Tone', value: analysis.uneven_tone?.score || 0, level: analysis.uneven_tone?.level || 'low' }
    ];
    
    items.forEach(item => {
        const div = document.createElement('div');
        div.className = 'analysis-item';
        div.innerHTML = `
            <h4>${item.title}</h4>
            <div class="value">${item.value.toFixed(1)}</div>
            <div class="level ${item.level}">${item.level}</div>
        `;
        analysisGrid.appendChild(div);
    });
    
    // Display recommendations
    displayRecommendations(data.recommendations);
    
    // Store report ID
    analyzeBtn.setAttribute('data-report-id', data.report_id);
    
    // Show results section
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function displayRecommendations(recommendations) {
    const tabContent = document.getElementById('tabContent');
    
    const tabs = {
        products: recommendations.products || [],
        morning: recommendations.morning_routine || [],
        night: recommendations.night_routine || [],
        tips: [...(recommendations.diet_tips || []), ...(recommendations.general_tips || [])]
    };
    
    // Tab buttons
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            tabButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            showTabContent(btn.dataset.tab, tabs);
        });
    });
    
    // Show default tab
    showTabContent('products', tabs);
}

function showTabContent(tab, tabs) {
    const tabContent = document.getElementById('tabContent');
    const items = tabs[tab] || [];
    
    const ul = document.createElement('ul');
    items.forEach(item => {
        const li = document.createElement('li');
        li.textContent = item;
        ul.appendChild(li);
    });
    
    tabContent.innerHTML = '';
    tabContent.appendChild(ul);
}

// Download PDF
const downloadPdfBtn = document.getElementById('downloadPdfBtn');
downloadPdfBtn.addEventListener('click', async () => {
    const reportId = analyzeBtn.getAttribute('data-report-id');
    if (reportId) {
        try {
            // Fetch the PDF as blob
            const response = await fetch(`/generate_pdf/${reportId}`);
            if (!response.ok) {
                const error = await response.json();
                alert(`Error: ${error.error || 'Failed to download PDF'}`);
                return;
            }
            
            // Get blob from response
            const blob = await response.blob();
            
            // Create download link
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `report_${reportId}.pdf`;
            document.body.appendChild(link);
            link.click();
            
            // Cleanup
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('PDF download error:', error);
            alert('Failed to download PDF. Please try again.');
        }
    } else {
        alert('Please analyze an image first');
    }
});

// Compare Modal
const compareBtn = document.getElementById('compareBtn');
const compareModal = document.getElementById('compareModal');
const beforeImage = document.getElementById('beforeImage');
const afterImage = document.getElementById('afterImage');
const beforePreview = document.getElementById('beforePreview');
const afterPreview = document.getElementById('afterPreview');
const compareAnalyzeBtn = document.getElementById('compareAnalyzeBtn');

compareBtn.addEventListener('click', () => {
    compareModal.style.display = 'block';
});

document.querySelector('#compareModal .close').addEventListener('click', () => {
    compareModal.style.display = 'none';
});

beforeImage.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (event) => {
            beforePreview.innerHTML = `<img src="${event.target.result}" alt="Before">`;
        };
        reader.readAsDataURL(file);
    }
});

afterImage.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (event) => {
            afterPreview.innerHTML = `<img src="${event.target.result}" alt="After">`;
        };
        reader.readAsDataURL(file);
    }
});

compareAnalyzeBtn.addEventListener('click', async () => {
    const beforeFile = beforeImage.files[0];
    const afterFile = afterImage.files[0];
    
    if (!beforeFile || !afterFile) {
        alert('Please select both before and after images');
        return;
    }
    
    compareAnalyzeBtn.disabled = true;
    compareAnalyzeBtn.textContent = 'Analyzing...';
    
    const formData = new FormData();
    formData.append('before', beforeFile);
    formData.append('after', afterFile);
    
    try {
        const response = await fetch('/compare', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('beforeScore').textContent = `Score: ${Math.round(data.before.score)}/100`;
            document.getElementById('afterScore').textContent = `Score: ${Math.round(data.after.score)}/100`;
            
            const improvement = document.getElementById('improvement');
            const improvementPercent = data.improvement_percentage.toFixed(1);
            if (data.improvement > 0) {
                improvement.innerHTML = `✨ Improvement: +${improvementPercent}%`;
                improvement.style.color = 'green';
            } else {
                improvement.innerHTML = `⚠️ Change: ${improvementPercent}%`;
                improvement.style.color = 'orange';
            }
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred during comparison');
    } finally {
        compareAnalyzeBtn.disabled = false;
        compareAnalyzeBtn.textContent = 'Compare';
    }
});

// Chatbot
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
const chatMessages = document.getElementById('chatMessages');

sendBtn.addEventListener('click', sendMessage);
chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// Quick question buttons
document.querySelectorAll('.quick-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const question = btn.getAttribute('data-question');
        chatInput.value = question;
        sendMessage();
    });
});

async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message) return;
    
    // Disable input while processing
    chatInput.disabled = true;
    sendBtn.disabled = true;
    
    // Display user message
    addMessage(message, 'user');
    chatInput.value = '';
    
    // Show typing indicator
    const typingId = 'typing-' + Date.now();
    const typingDiv = document.createElement('div');
    typingDiv.id = typingId;
    typingDiv.className = 'message bot-message typing-indicator';
    typingDiv.innerHTML = '<p>Thinking...</p>';
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Get bot response
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({ message: message }),
            credentials: 'same-origin'
        });
        
        // Remove typing indicator
        const typingElement = document.getElementById(typingId);
        if (typingElement) {
            typingElement.remove();
        }
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success && data.response) {
            addMessage(data.response, 'bot');
        } else {
            const errorMsg = data.error || 'Sorry, I encountered an error. Please try again.';
            addMessage(errorMsg, 'bot');
            console.error('Chatbot error:', data);
        }
    } catch (error) {
        // Remove typing indicator
        const typingElement = document.getElementById(typingId);
        if (typingElement) {
            typingElement.remove();
        }
        
        console.error('Error sending message:', error);
        addMessage('Sorry, I encountered an error connecting to the server. Please check your connection and try again.', 'bot');
    } finally {
        // Re-enable input
        chatInput.disabled = false;
        sendBtn.disabled = false;
        chatInput.focus();
    }
}

function addMessage(text, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    // Escape HTML to prevent XSS, but allow basic formatting
    const escapedText = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\n/g, '<br>');
    messageDiv.innerHTML = `<p>${escapedText}</p>`;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Add smooth scroll animation
    messageDiv.style.opacity = '0';
    messageDiv.style.transform = 'translateY(10px)';
    setTimeout(() => {
        messageDiv.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        messageDiv.style.opacity = '1';
        messageDiv.style.transform = 'translateY(0)';
    }, 10);
}

// Load History
async function loadHistory() {
    try {
        const response = await fetch('/history');
        const data = await response.json();
        
        if (data.success && data.reports.length > 0) {
            const historyList = document.getElementById('historyList');
            historyList.innerHTML = '';
            
            data.reports.forEach(report => {
                const div = document.createElement('div');
                div.className = 'history-item';
                div.innerHTML = `
                    <img src="${report.image_path}" alt="History">
                    <p><strong>${report.skin_type}</strong></p>
                    <p>Score: ${Math.round(report.health_score)}/100</p>
                    <p style="font-size: 0.8rem; color: var(--text-light);">${new Date(report.created_at).toLocaleDateString()}</p>
                `;
                div.addEventListener('click', () => {
                    window.location.href = `#report-${report.id}`;
                });
                historyList.appendChild(div);
            });
        }
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

// Load history on page load
loadHistory();

