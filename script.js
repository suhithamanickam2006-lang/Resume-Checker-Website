/**
 * Automated Resume Reviewer for College Placement Cells
 * Client-side Interactivity & UI Controller
 */

document.addEventListener('DOMContentLoaded', () => {
    initMobileNav();
    initFileUploadDropzone();
    initFormSubmission();
    initScoreGaugeAnimation();
});

/**
 * 1. Mobile Navigation Toggle
 */
function initMobileNav() {
    const navToggle = document.getElementById('navToggle');
    const navMenu = document.getElementById('navMenu');

    if (navToggle && navMenu) {
        navToggle.addEventListener('click', () => {
            navMenu.classList.toggle('show');
            const icon = navToggle.querySelector('i');
            if (icon) {
                if (navMenu.classList.contains('show')) {
                    icon.classList.remove('fa-bars');
                    icon.classList.add('fa-xmark');
                } else {
                    icon.classList.remove('fa-xmark');
                    icon.classList.add('fa-bars');
                }
            }
        });
    }
}

/**
 * 2. Drag & Drop File Upload Handler
 */
function initFileUploadDropzone() {
    const dropzoneArea = document.getElementById('dropzoneArea');
    const dropzoneInner = document.getElementById('dropzoneInner');
    const fileInput = document.getElementById('resume_file');
    const selectedFileBox = document.getElementById('selectedFileBox');
    const selectedFileName = document.getElementById('selectedFileName');
    const selectedFileSize = document.getElementById('selectedFileSize');
    const btnRemoveFile = document.getElementById('btnRemoveFile');

    if (!dropzoneArea || !fileInput) return;

    // Click to open file dialog
    dropzoneArea.addEventListener('click', (e) => {
        if (e.target.closest('#btnRemoveFile')) return;
        fileInput.click();
    });

    // Drag and Drop Events
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzoneArea.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzoneArea.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzoneArea.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzoneArea.classList.remove('dragover');
        });
    });

    dropzoneArea.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files && files.length > 0) {
            handleFileSelection(files[0]);
        }
    });

    // File Input change event
    fileInput.addEventListener('change', (e) => {
        if (fileInput.files && fileInput.files.length > 0) {
            handleFileSelection(fileInput.files[0]);
        }
    });

    // Remove File button
    if (btnRemoveFile) {
        btnRemoveFile.addEventListener('click', (e) => {
            e.stopPropagation();
            fileInput.value = '';
            dropzoneInner.classList.remove('d-none');
            selectedFileBox.classList.add('d-none');
        });
    }

    function handleFileSelection(file) {
        if (!file) return;

        // Check file extension
        const isPdf = file.name.toLowerCase().endsWith('.pdf') || file.type === 'application/pdf';
        if (!isPdf) {
            alert('Please select a valid PDF file format (.pdf).');
            fileInput.value = '';
            return;
        }

        // Check file size (16MB max)
        const maxBytes = 16 * 1024 * 1024;
        if (file.size > maxBytes) {
            alert('File size exceeds the 16MB limit. Please upload a smaller PDF resume.');
            fileInput.value = '';
            return;
        }

        // Update UI
        if (selectedFileName) selectedFileName.textContent = file.name;
        if (selectedFileSize) selectedFileSize.textContent = formatBytes(file.size);

        if (dropzoneInner) dropzoneInner.classList.add('d-none');
        if (selectedFileBox) selectedFileBox.classList.remove('d-none');
    }

    function formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

/**
 * 3. Form Submission & Animated Loading Stepper
 */
function initFormSubmission() {
    const form = document.getElementById('resumeUploadForm');
    const overlay = document.getElementById('loadingOverlay');

    if (!form || !overlay) return;

    form.addEventListener('submit', (e) => {
        const fileInput = document.getElementById('resume_file');
        if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
            alert('Please select a PDF resume file to proceed.');
            e.preventDefault();
            return;
        }

        // Show loading overlay
        overlay.classList.remove('d-none');

        // Simulate multi-step diagnostic animation
        const steps = [
            { id: 'step1', text: 'Extracting PDF text with PyMuPDF...', delay: 100 },
            { id: 'step2', text: 'Identifying contact info & key sections...', delay: 800 },
            { id: 'step3', text: 'Detecting technical skills & action verbs...', delay: 1600 },
            { id: 'step4', text: 'Running LanguageTool grammar diagnostics...', delay: 2400 },
            { id: 'step5', text: 'Storing records to MySQL database...', delay: 3200 }
        ];

        steps.forEach((step, index) => {
            setTimeout(() => {
                const currentEl = document.getElementById(step.id);
                if (currentEl) {
                    currentEl.classList.add('active');
                    currentEl.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i> ${step.text}`;
                }

                // Mark previous step as done
                if (index > 0) {
                    const prevEl = document.getElementById(steps[index - 1].id);
                    if (prevEl) {
                        prevEl.classList.remove('active');
                        prevEl.classList.add('done');
                        prevEl.innerHTML = `<i class="fa-solid fa-circle-check text-success"></i> ${steps[index - 1].text}`;
                    }
                }
            }, step.delay);
        });
    });
}

/**
 * 4. Circular Progress Score Gauge on Result Page
 */
function initScoreGaugeAnimation() {
    const scoreCircle = document.getElementById('scoreCircle');
    if (!scoreCircle) return;

    const targetScore = parseFloat(scoreCircle.getAttribute('data-score')) || 0;
    
    // Choose theme color based on score
    let scoreColor = '#ef4444'; // Red (<60)
    if (targetScore >= 80) {
        scoreColor = '#10b981'; // Green (>=80)
    } else if (targetScore >= 60) {
        scoreColor = '#f59e0b'; // Amber (60-79)
    }

    // Animate conic gradient from 0 to targetScore
    let currentScore = 0;
    const duration = 1200; // ms
    const startTime = performance.now();

    function animate(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        // Ease-out curve
        const easeOut = 1 - Math.pow(1 - progress, 3);
        currentScore = easeOut * targetScore;

        scoreCircle.style.background = `conic-gradient(${scoreColor} ${currentScore * 3.6}deg, #e2e8f0 0deg)`;

        if (progress < 1) {
            requestAnimationFrame(animate);
        } else {
            scoreCircle.style.background = `conic-gradient(${scoreColor} ${targetScore * 3.6}deg, #e2e8f0 0deg)`;
        }
    }

    requestAnimationFrame(animate);
}
