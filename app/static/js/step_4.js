document.addEventListener('DOMContentLoaded', function() {
    const finalizeForm = document.getElementById('finalizeForm');
    
    if (finalizeForm) {
        const loaderOverlay = document.getElementById('loader-overlay');
        const generatePlanBtn = document.getElementById('generatePlanBtn');

        // This event listener activates the loader when you submit the form
        finalizeForm.addEventListener('submit', function() {
            if (generatePlanBtn) {
                generatePlanBtn.disabled = true;
            }
            if (loaderOverlay) {
                loaderOverlay.classList.add('is-active');
            }
        });

        // This event listener handles the user navigating back to the page
        window.addEventListener('pageshow', function(event) {
            // The 'persisted' property is true if the page was loaded from the bfcache
            if (event.persisted) {
                if (loaderOverlay) {
                    // Hide the loader overlay
                    loaderOverlay.classList.remove('is-active');
                }
                if (generatePlanBtn) {
                    // Re-enable the submit button
                    generatePlanBtn.disabled = false;
                }
            }
        });
    }
});