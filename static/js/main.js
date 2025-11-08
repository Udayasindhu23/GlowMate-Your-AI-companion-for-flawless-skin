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
let captureBtn = document.getElementById('captureBtn');
const captureBtnFallback = document.getElementById('captureBtnFallback');
const cancelWebcam = document.getElementById('cancelWebcam');
const flipCameraBtn = document.getElementById('flipCameraBtn');
const flashBtn = document.getElementById('flashBtn');
const countdown = document.getElementById('countdown');
const countdownNumber = document.getElementById('countdownNumber');
const captureFlash = document.getElementById('captureFlash');
const capturedThumbnail = document.getElementById('capturedThumbnail');
const thumbnailImg = document.getElementById('thumbnailImg');
const closeThumbnail = document.getElementById('closeThumbnail');
let stream = null;
let currentFacingMode = 'user'; // Always default to front camera
let isCapturing = false;
let videoTrack = null;

// Debug: Check if capture button exists
console.log('Capture button element:', captureBtn);
console.log('Capture button exists:', !!captureBtn);
if (captureBtn) {
    console.log('Capture button visible:', captureBtn.offsetParent !== null);
    console.log('Capture button display style:', window.getComputedStyle(captureBtn).display);
    console.log('Capture button visibility:', window.getComputedStyle(captureBtn).visibility);
    console.log('Capture button disabled:', captureBtn.disabled);
    console.log('Capture button z-index:', window.getComputedStyle(captureBtn).zIndex);
    console.log('Capture button position:', window.getComputedStyle(captureBtn).position);
    console.log('Capture button pointer-events:', window.getComputedStyle(captureBtn).pointerEvents);
} else {
    console.error('CRITICAL: Capture button element not found!');
}

// Check if cameras are available
async function checkAvailableCameras() {
    try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            return false;
        }
        
        // Try to enumerate devices
        const devices = await navigator.mediaDevices.enumerateDevices();
        const videoDevices = devices.filter(device => device.kind === 'videoinput');
        return videoDevices.length > 0;
    } catch (error) {
        console.error('Error checking cameras:', error);
        // If enumeration fails, still try to access camera
        return true;
    }
}

// Capture button click handler
function handleCaptureClick() {
    if (isCapturing) return;
    
    // Ensure video is ready
    if (!video || video.readyState !== video.HAVE_ENOUGH_DATA) {
        alert('Please wait for the camera to be ready.');
        return;
    }
    
    // Start countdown
    startCountdown();
}

webcamBtn.addEventListener('click', async () => {
    // Check if cameras are available first
    try {
        const camerasAvailable = await checkAvailableCameras();
        if (!camerasAvailable) {
            alert('No cameras found on this device. Please upload an image instead.');
            return;
        }
    } catch (error) {
        console.warn('Could not check cameras, proceeding anyway:', error);
    }
    
    webcamModal.style.display = 'block';
    isCapturing = false;
    
    // Ensure capture button is enabled and visible
    if (captureBtn) {
        captureBtn.disabled = false;
        captureBtn.style.display = 'flex';
        captureBtn.style.visibility = 'visible';
        captureBtn.style.opacity = '1';
        captureBtn.style.pointerEvents = 'auto';
        captureBtn.style.cursor = 'pointer';
        
        // Remove old listeners by cloning and replacing
        const oldBtn = captureBtn;
        const newCaptureBtn = oldBtn.cloneNode(true);
        oldBtn.parentNode.replaceChild(newCaptureBtn, oldBtn);
        captureBtn = newCaptureBtn;
        
        // Add fresh event listener
        captureBtn.addEventListener('click', handleCaptureClick);
    } else {
        // Try to get button again if it wasn't found initially
        captureBtn = document.getElementById('captureBtn');
        if (captureBtn) {
            captureBtn.disabled = false;
            captureBtn.style.display = 'flex';
            captureBtn.style.visibility = 'visible';
            captureBtn.style.opacity = '1';
            captureBtn.style.pointerEvents = 'auto';
            captureBtn.style.cursor = 'pointer';
            captureBtn.addEventListener('click', handleCaptureClick);
        }
    }
    
    // Hide fallback button
    if (captureBtnFallback) {
        captureBtnFallback.style.display = 'none';
    }
    
    // Always start with front camera
    currentFacingMode = 'user';
    startWebcam();
});

// Prevent clicks on modal backdrop from going through
webcamModal.addEventListener('click', (e) => {
    if (e.target === webcamModal) {
        // Clicked on backdrop, close modal
        stopWebcam();
        isCapturing = false;
        if (captureBtn) {
            captureBtn.disabled = false;
        }
        webcamModal.style.display = 'none';
    }
});

// Prevent clicks inside modal content from closing the modal
const modalContent = webcamModal.querySelector('.modal-content');
if (modalContent) {
    modalContent.addEventListener('click', (e) => {
        e.stopPropagation();
    });
}

document.querySelector('#webcamModal .close').addEventListener('click', () => {
    stopWebcam();
    isCapturing = false;
    if (captureBtn) {
        captureBtn.disabled = false;
    }
    if (captureBtnFallback) {
        captureBtnFallback.disabled = false;
    }
    webcamModal.style.display = 'none';
});

cancelWebcam.addEventListener('click', () => {
    stopWebcam();
    isCapturing = false;
    if (captureBtn) {
        captureBtn.disabled = false;
    }
    if (captureBtnFallback) {
        captureBtnFallback.disabled = false;
    }
    webcamModal.style.display = 'none';
});

function startWebcam() {
    // Request high-quality video with constraints - prefer front camera first
    const constraints = {
        video: {
            width: { ideal: 1280, min: 640 },
            height: { ideal: 720, min: 480 },
            facingMode: currentFacingMode, // Use preferred instead of exact for better compatibility
            aspectRatio: { ideal: 16/9 }
        }
    };
    
    navigator.mediaDevices.getUserMedia(constraints)
        .then((mediaStream) => {
            stream = mediaStream;
            video.srcObject = mediaStream;
            
            // Get the video track for additional control
            videoTrack = mediaStream.getVideoTracks()[0];
            if (videoTrack) {
                console.log('Camera started with facing mode:', currentFacingMode);
                console.log('Camera capabilities:', videoTrack.getCapabilities());
            }
            
            // Apply mirror effect only for front camera
            if (currentFacingMode === 'user') {
                video.classList.add('mirror');
            } else {
                video.classList.remove('mirror');
            }
            
            // Wait for video to be ready
            video.onloadedmetadata = () => {
                video.play().catch(err => {
                    console.error('Error playing video:', err);
                });
                
                // Update camera button to reflect current state
                updateCameraButton();
                
                // Show notification about which camera is active
                const cameraName = currentFacingMode === 'user' ? 'Front Camera' : 'Rear Camera';
                showNotification(`${cameraName} is now active`, 'info');
            };
        })
        .catch((error) => {
            console.error('Error accessing webcam with exact constraints:', error);
            
            // Try with basic constraints if exact ones fail
            const fallbackConstraints = {
                video: {
                    facingMode: currentFacingMode,
                    width: { min: 640 },
                    height: { min: 480 }
                }
            };
            
            navigator.mediaDevices.getUserMedia(fallbackConstraints)
                .then((mediaStream) => {
                    stream = mediaStream;
                    video.srcObject = mediaStream;
                    
                    // Get the video track
                    videoTrack = mediaStream.getVideoTracks()[0];
                    if (videoTrack) {
                        console.log('Camera started with fallback constraints, facing mode:', currentFacingMode);
                    }
                    
                    // Apply mirror effect only for front camera
                    if (currentFacingMode === 'user') {
                        video.classList.add('mirror');
                    } else {
                        video.classList.remove('mirror');
                    }
                    
                    video.onloadedmetadata = () => {
                        video.play().catch(err => {
                            console.error('Error playing video:', err);
                        });
                        
                        // Update camera button to reflect current state
                        updateCameraButton();
                        
                        // Show notification about which camera is active
                        const cameraName = currentFacingMode === 'user' ? 'Front Camera' : 'Rear Camera';
                        showNotification(`${cameraName} is now active`, 'info');
                    };
                })
                .catch((fallbackError) => {
                    console.error('Fallback webcam access failed:', fallbackError);
                    alert('Unable to access webcam. Please check permissions and ensure your camera is connected.\n\nTip: Make sure you grant camera permissions and that no other app is using the camera.');
                });
        });
}

// Update camera button appearance based on current camera
function updateCameraButton() {
    if (flipCameraBtn) {
        if (currentFacingMode === 'user') {
            flipCameraBtn.innerHTML = '📱'; // Front camera icon
            flipCameraBtn.title = 'Switch to Rear Camera';
        } else {
            flipCameraBtn.innerHTML = '📷'; // Rear camera icon
            flipCameraBtn.title = 'Switch to Front Camera';
        }
    }
}

// Flip camera functionality
if (flipCameraBtn) {
    flipCameraBtn.addEventListener('click', () => {
        if (isCapturing) return;
        
        // Toggle between front and back camera
        currentFacingMode = currentFacingMode === 'user' ? 'environment' : 'user';
        console.log('Switching to camera:', currentFacingMode);
        
        // Update button appearance
        updateCameraButton();
        
        // Stop current camera and restart with new facing mode
        stopWebcam();
        setTimeout(() => {
            startWebcam();
        }, 200); // Slightly longer delay for camera switching
    });
}

function stopWebcam() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
    }
    if (videoTrack) {
        videoTrack.stop();
        videoTrack = null;
    }
    video.srcObject = null;
}

// Initialize capture button on page load as backup
document.addEventListener('DOMContentLoaded', () => {
    // Re-get the button reference after DOM is loaded
    const btn = document.getElementById('captureBtn');
    if (btn && btn !== captureBtn) {
        captureBtn = btn;
        btn.addEventListener('click', handleCaptureClick);
    }
});

function startCountdown() {
    console.log('🎯 StartCountdown function called!');
    isCapturing = true;
    if (captureBtn) {
        captureBtn.disabled = true;
        console.log('✅ Primary capture button disabled for countdown');
    }
    if (captureBtnFallback) {
        captureBtnFallback.disabled = true;
        console.log('✅ Fallback capture button disabled for countdown');
    }
    if (!captureBtn && !captureBtnFallback) {
        console.error('❌ No capture button found in startCountdown!');
    }
    let count = 3;
    
    countdown.style.display = 'flex';
    countdownNumber.textContent = count;
    console.log('⏰ Countdown started:', count);
    
    const countdownInterval = setInterval(() => {
        count--;
        if (count > 0) {
            countdownNumber.textContent = count;
            console.log('⏰ Countdown:', count);
        } else {
            clearInterval(countdownInterval);
            countdown.style.display = 'none';
            console.log('🎯 Countdown complete, starting capture');
            performCapture();
        }
    }, 1000);
}

function performCapture() {
    // Flash effect
    captureFlash.style.display = 'block';
    setTimeout(() => {
        captureFlash.style.display = 'none';
    }, 200);
    
    // Ensure video has enough data before capturing
    if (video.readyState < video.HAVE_CURRENT_DATA) {
        alert('Camera not ready. Please wait a moment and try again.');
        isCapturing = false;
        if (captureBtn) {
            captureBtn.disabled = false;
        }
        return;
    }
    
    // Set canvas dimensions to match video
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    
    // Draw video frame to canvas with proper orientation
    const ctx = canvas.getContext('2d');
    ctx.save();
    
    // For front camera, we need to flip horizontally to show the correct orientation
    // This matches what users expect to see (like a mirror)
    if (currentFacingMode === 'user') {
        ctx.translate(canvas.width, 0);
        ctx.scale(-1, 1);
        console.log('Applying front camera mirror correction');
    }
    
    // Draw the video frame
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    ctx.restore();
    
    // Capture with high quality (0.95 quality for JPEG)
    canvas.toBlob((blob) => {
        if (!blob) {
            alert('Failed to capture image. Please try again.');
            isCapturing = false;
            if (captureBtn) {
                captureBtn.disabled = false;
            }
            return;
        }
        
        const file = new File([blob], 'webcam-capture.jpg', { type: 'image/jpeg' });
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        imageUpload.files = dataTransfer.files;
        
        // Get the captured image data URL
        const capturedImageData = canvas.toDataURL('image/jpeg', 0.95);
        
        // Show preview in main area
        previewImg.src = capturedImageData;
        imagePreview.style.display = 'block';
        
        // Show thumbnail in top right corner
        showCapturedThumbnail(capturedImageData);
        
        console.log('Image captured successfully with camera mode:', currentFacingMode);
        
        // Reset UI state
        isCapturing = false;
        if (captureBtn) {
            captureBtn.disabled = false;
        }
        if (captureBtnFallback) {
            captureBtnFallback.disabled = false;
        }
        stopWebcam();
        webcamModal.style.display = 'none';
        
        // Show success message
        showNotification('Photo captured successfully!', 'success');
        
    }, 'image/jpeg', 0.95);
}

// Show captured thumbnail in top right corner
function showCapturedThumbnail(imageData) {
    if (thumbnailImg && capturedThumbnail) {
        thumbnailImg.src = imageData;
        capturedThumbnail.style.display = 'block';
        
        // Animate in
        setTimeout(() => {
            capturedThumbnail.style.opacity = '1';
            capturedThumbnail.style.transform = 'scale(1)';
        }, 10);
    }
}

// Close thumbnail handler
if (closeThumbnail) {
    closeThumbnail.addEventListener('click', (e) => {
        e.stopPropagation();
        if (capturedThumbnail) {
            capturedThumbnail.style.opacity = '0';
            capturedThumbnail.style.transform = 'scale(0.8)';
            setTimeout(() => {
                capturedThumbnail.style.display = 'none';
            }, 300);
        }
    });
}

// Make thumbnail clickable to view full image
if (thumbnailImg) {
    thumbnailImg.addEventListener('click', () => {
        // Scroll to the main preview
        if (imagePreview) {
            imagePreview.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    });
}

// Notification function for user feedback
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Style the notification
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#4CAF50' : type === 'error' ? '#f44336' : '#2196F3'};
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        font-weight: 500;
        transform: translateX(100%);
        transition: transform 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

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

