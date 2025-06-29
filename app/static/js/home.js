document.addEventListener('DOMContentLoaded', function () {
    const deleteModal = document.getElementById('deleteConfirmationModal');
    if (deleteModal) {
        deleteModal.addEventListener('show.bs.modal', function (event) {
            // Button that triggered the modal
            const button = event.relatedTarget;
            
            // Extract info from data-* attributes
            const planId = button.getAttribute('data-plan-id');
            const planName = button.getAttribute('data-plan-name');

            // Update the modal's content
            const planNameElement = deleteModal.querySelector('#planNameToDelete');
            const deleteForm = deleteModal.querySelector('#deletePlanForm');

            if (planNameElement && deleteForm) {
                planNameElement.textContent = planName;
                // Dynamically create the correct action URL for the form
                deleteForm.action = `plan/delete/${planId}`;
            }
        });
    }

    // edit confirmation modal
    const editModal = document.getElementById('editConfirmationModal');
    if (editModal) {
        editModal.addEventListener('show.bs.modal', function (event) {
            // Button that triggered the modal
            const button = event.relatedTarget;
            
            // Extract info from data-* attributes
            const planId = button.getAttribute('data-plan-id');
            const planName = button.getAttribute('data-plan-name');
        
            // Update the modal's content
            const planNameElement = editModal.querySelector('#planNameToEdit');
            const editForm = editModal.querySelector('#editPlanForm');
        
            if (planNameElement && editForm) {
                planNameElement.textContent = planName;
                // Dynamically create the correct action URL for the form
                editForm.action = `plan/edit/${planId}`; 
            }
        });
    }

    // Search & Filter logic
    const forWhomFilter = document.getElementById('plan-for-filter');
    const nameSearchInput = document.getElementById('plan-name-search');
    const allPlanItems = document.querySelectorAll('.list-group-item');
    const tabPanes = document.querySelectorAll('.tab-pane');
    const inProgressBadge = document.getElementById('inprogress-count-badge');
    const completedBadge = document.getElementById('completed-count-badge');

    function filterAndSortPlans() {
        const forWhomValue = forWhomFilter.value;
        const searchTerm = nameSearchInput.value.toLowerCase();

        allPlanItems.forEach(item => {
            const isForSelf = item.dataset.isForSelf === 'true';
            const planName = item.dataset.planName;
            const forWhomMatch = (forWhomValue === 'all') || (forWhomValue === 'self' && isForSelf) || (forWhomValue === 'others' && !isForSelf);

            // Split the search term into individual keywords and remove any empty ones
            const keywords = searchTerm.split(' ').filter(k => k);
            // Check if EVERY keyword is included in the plan name
            const nameMatch = keywords.every(keyword => planName.includes(keyword));

            if (forWhomMatch && nameMatch) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });

        updateEmptyTabMessages();
        updateTabCounts(); // Update the counts after filtering
    }

    function updateEmptyTabMessages() {
        tabPanes.forEach(pane => {
            const messageEl = pane.querySelector('.text-center.p-4');
            const visibleItems = pane.querySelectorAll('.list-group-item:not([style*="display: none"])');
            if (messageEl) {
                messageEl.style.display = visibleItems.length === 0 ? 'block' : 'none';
            }
        });
    }

    function updateTabCounts() {
        const visibleInProgress = document.querySelectorAll('#inprogress-pane .list-group-item:not([style*="display: none"])');
        if (inProgressBadge) {
            inProgressBadge.textContent = visibleInProgress.length;
        }

        const visibleCompleted = document.querySelectorAll('#completed-pane .list-group-item:not([style*="display: none"])');
        if (completedBadge) {
            completedBadge.textContent = visibleCompleted.length;
        }
    }

    // Attach event listeners
    if (forWhomFilter && nameSearchInput) {
        forWhomFilter.addEventListener('change', filterAndSortPlans);
        nameSearchInput.addEventListener('input', filterAndSortPlans);
    }

    // Initial check
    updateEmptyTabMessages();
});