    // --- CDN URLs ---
    const PDFJS_URL = `//unpkg.com/pdfjs-dist@4.4.168/build/pdf.mjs`;
    const WORKER_URL = `//unpkg.com/pdfjs-dist@4.4.168/build/pdf.worker.mjs`;

    // --- DOM Elements ---
    const pageNumEl = document.getElementById('page-num');
    const pageCountEl = document.getElementById('page-count');
    const viewerArea = document.getElementById('viewer-area');
    const loadingSpinner = document.getElementById('loading-spinner');

    // --- Configuration and State ---
    const pdfUrl = viewerArea.dataset.pdfUrl;; 
    let pdfDoc = null;
    let currentScale = 1.0; 
    let isRendering = false;
    const zoomStep = 0.25;


    // --- PDF.js Initialization ---
    const pdfjsLib = await import(PDFJS_URL);
    pdfjsLib.GlobalWorkerOptions.workerSrc = WORKER_URL;

    // --- Core Rendering Function ---
    async function renderPage(page, canvas) {
        const devicePixelRatio = window.devicePixelRatio || 1;
        const viewport = page.getViewport({ scale: currentScale });
        
        const ctx = canvas.getContext('2d');
        canvas.width = Math.floor(viewport.width * devicePixelRatio);
        canvas.height = Math.floor(viewport.height * devicePixelRatio);
        canvas.style.width = `${Math.floor(viewport.width)}px`;
        canvas.style.height = `${Math.floor(viewport.height)}px`;

        const renderContext = {
            canvasContext: ctx,
            viewport: viewport,
            transform: devicePixelRatio !== 1 ? [devicePixelRatio, 0, 0, devicePixelRatio, 0, 0] : null,
        };
        await page.render(renderContext).promise;
    }

    // --- UI Control Functions ---
    async function renderAllPages() {
        if (isRendering) return;
        isRendering = true;
        
        loadingSpinner.style.display = 'block';
        try {
            const pages = await Promise.all(
                Array.from({ length: pdfDoc.numPages }, (_, i) => pdfDoc.getPage(i + 1))
            );
            const canvases = viewerArea.querySelectorAll('.pdf-page-canvas');
            await Promise.all(pages.map((page, i) => renderPage(page, canvases[i])));
        } catch (err) {
            console.error("Error during page rendering:", err);
        } finally {
            loadingSpinner.style.display = 'none';
            isRendering = false;
        }
    }

    const onZoomIn = () => { currentScale += zoomStep; renderAllPages(); };
    const onZoomOut = () => { if (currentScale - zoomStep > 0.25) { currentScale -= zoomStep; renderAllPages(); }};

    // --- Event Listeners ---
    document.getElementById('zoom-in').addEventListener('click', onZoomIn);
    document.getElementById('zoom-out').addEventListener('click', onZoomOut);
    document.getElementById('fit-to-page').addEventListener('click', () => fitToPage().then(renderAllPages));
    document.getElementById('fit-to-width').addEventListener('click', () => fitToWidth().then(renderAllPages));

    // --- Page Number Tracking via Intersection Observer ---
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const pageNum = entry.target.dataset.pageNum;
                pageNumEl.textContent = pageNum;
            }
        });
    }, { root: viewerArea, threshold: 0.5 });

    // --- SCALING & INITIAL LOAD LOGIC ---
    async function fitToWidth() {
        if (!pdfDoc) return;
        const page = await pdfDoc.getPage(1);
        const containerWidth = viewerArea.clientWidth;
        const scale = (containerWidth - 48) / page.getViewport({ scale: 1.0 }).width;
        currentScale = scale;
    }

    async function fitToPage() {
        if (!pdfDoc) return;
        const page = await pdfDoc.getPage(1);
        const containerWidth = viewerArea.clientWidth;
        const containerHeight = viewerArea.clientHeight;
        const viewport = page.getViewport({ scale: 1.0 });
        const scaleX = (containerWidth - 48) / viewport.width;
        const scaleY = (containerHeight - 48) / viewport.height;
        currentScale = Math.min(scaleX, scaleY);
    }
    
    async function loadPdf() {
        loadingSpinner.style.display = 'block';
        try {
            const loadingTask = pdfjsLib.getDocument({ url: pdfUrl });
            pdfDoc = await loadingTask.promise;
            pageCountEl.textContent = pdfDoc.numPages;
            
            viewerArea.innerHTML = ''; 
            for (let i = 1; i <= pdfDoc.numPages; i++) {
                const canvas = document.createElement('canvas');
                canvas.className = 'pdf-page-canvas';
                canvas.dataset.pageNum = i;
                viewerArea.appendChild(canvas);
                observer.observe(canvas);
            }

            await fitToPage(); 
            await renderAllPages();

        } catch (err) {
            console.error('Error loading PDF:', err);
            loadingSpinner.style.display = 'none';
            viewerArea.innerHTML = `<div class="alert alert-danger">Failed to load the PDF document. Please try opening in a new tab.</div>`;
        }
    }

    function debounce(func, timeout = 250){
        let timer;
        return (...args) => {
            clearTimeout(timer);
            timer = setTimeout(() => { func.apply(this, args); }, timeout);
        };
    }

    const handleResize = debounce(() => {
        if (pdfDoc) {
            fitToWidth().then(() => renderAllPages());
        }
    });

    window.addEventListener('resize', handleResize);
    
    // --- PAN-ON-DRAG LOGIC ---
    let pos = { top: 0, left: 0, x: 0, y: 0 };
    let isDown = false;

    const mouseDownHandler = function (e) {
        if (e.button !== 0) return;
        isDown = true;
        viewerArea.classList.add('grabbing');
        viewerArea.classList.remove('grab');
        pos = {
            left: viewerArea.scrollLeft,
            top: viewerArea.scrollTop,
            x: e.clientX,
            y: e.clientY,
        };
    };

    const mouseMoveHandler = function (e) {
        if (!isDown) return;
        e.preventDefault();
        const dx = e.clientX - pos.x;
        const dy = e.clientY - pos.y;
        viewerArea.scrollTop = pos.top - dy;
        viewerArea.scrollLeft = pos.left - dx;
    };

    const mouseUpHandler = function () {
        isDown = false;
        viewerArea.classList.remove('grabbing');
        viewerArea.classList.add('grab');
    };

    viewerArea.addEventListener('mousedown', mouseDownHandler);
    viewerArea.addEventListener('mousemove', mouseMoveHandler);
    viewerArea.addEventListener('mouseup', mouseUpHandler);
    viewerArea.addEventListener('mouseleave', mouseUpHandler);
    
/* 
    const downloadBtn = document.getElementById('download-btn');
    downloadBtn.addEventListener('click', async (e) => {
        e.preventDefault(); // Stop the link from navigating
        
        // Show a temporary loading state on the button
        const originalText = downloadBtn.innerHTML;
        downloadBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Downloading...`;
        downloadBtn.disabled = true;

        try {
            // Fetch the PDF data
            const response = await fetch(pdfUrl);
            if (!response.ok) throw new Error('Network response was not ok.');
            const blob = await response.blob();

            // Create a temporary link to download the blob
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            // Set a default filename for the download
            a.download = "{{name}}"; 
            document.body.appendChild(a);
            a.click();
            
            // Clean up the temporary URL and link
            window.URL.revokeObjectURL(url);
            a.remove();

        } catch (err) {
            console.error('Download failed:', err);
            alert('Could not download the file.');
        } finally {
            // Restore the button to its original state
            downloadBtn.innerHTML = originalText;
            downloadBtn.disabled = false;
        }
    });
    */

    // EMAIL SHARING MODAL LOGIC 

    // --- Modal DOM Elements ---
    const shareEmailBtn = document.getElementById('share-email-btn');
    const shareModalEl = document.getElementById('shareEmailModal');
    const shareModal = new bootstrap.Modal(shareModalEl);
    const emailInput = document.getElementById('email-share-input');
    const sendEmailSubmitBtn = document.getElementById('send-email-submit-btn');
    const shareEmailForm = document.getElementById('share-email-form');
    const planId = document.getElementById('plan-id-holder').value;
    const sendBtnText = document.getElementById('send-btn-text');
    const sendBtnSpinner = document.getElementById('send-btn-spinner');
    const shareErrorMessage = document.getElementById('share-error-message');
    const shareSuccessMessage = document.getElementById('share-success-message');

    // --- Initialize Tom Select ---
    const emailLimitMessage = document.getElementById('email-limit-message');
    const maxEmails = 5; 

    const tomSelect = new TomSelect(emailInput, {
        create: true,
        persist: false,
        maxItems: maxEmails, 
        plugins: ['remove_button'],
        createFilter: function(input) {
            const emailRegex = new RegExp(/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/);
            return emailRegex.test(input);
        },
        // Add event listeners to show/hide the limit message
        onItemAdd: function() {
            if (this.items.length >= maxEmails) {
                emailLimitMessage.style.display = 'block';
            }
        },
        onItemRemove: function() {
            if (this.items.length < maxEmails) {
                emailLimitMessage.style.display = 'none';
            }
        }
    });

    // --- Event Listeners ---
    shareEmailBtn.addEventListener('click', () => {
        // Reset modal state before showing
        tomSelect.clear();
        shareErrorMessage.textContent = '';
        shareSuccessMessage.textContent = '';
        shareModal.show();
    });

    sendEmailSubmitBtn.addEventListener('click', async () => {
        const emails = tomSelect.getValue();
        
        // Clear previous messages
        shareErrorMessage.textContent = '';
        shareSuccessMessage.textContent = '';

        if (emails.length === 0) {
            shareErrorMessage.textContent = 'Please enter at least one email address.';
            return;
        }

        // Set loading state
        sendBtnText.textContent = 'Sending...';
        sendBtnSpinner.style.display = 'inline-block';
        sendEmailSubmitBtn.disabled = true;

        try {

            const csrfToken = document.getElementById('csrf_token').value;
            const shareUrl = shareEmailForm.dataset.shareUrl;
            const response = await fetch(shareUrl, { 
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'X-CSRFToken': csrfToken
                                },
                                body: JSON.stringify({
                                    emails: emails 
                                })
                            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'An unknown error occurred.');
            }
            
            // Handle success
            shareSuccessMessage.textContent = 'Your plan has been shared successfully!';
            tomSelect.clear(); // Clear the input on success
            setTimeout(() => shareModal.hide(), 2000); // Close modal after 2 seconds

        } catch (err) {
            shareErrorMessage.textContent = err.message;
        } finally {
            // Reset button state
            sendBtnText.textContent = 'Send Email';
            sendBtnSpinner.style.display = 'none';
            sendEmailSubmitBtn.disabled = false;
        }
    });

    // Reset messages when modal is closed
    shareModalEl.addEventListener('hidden.bs.modal', function () {
        shareErrorMessage.textContent = '';
        shareSuccessMessage.textContent = '';
    });
    
    loadPdf();