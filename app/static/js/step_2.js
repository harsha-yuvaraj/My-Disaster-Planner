document.addEventListener('DOMContentLoaded', () => {
    // DOM Element selectors
    const shelterChecklist = document.getElementById('shelterChecklist');
    const recEvacuate = document.getElementById('recEvacuate');
    const recShelterOptional = document.getElementById('recShelterOptional');
    const recShelterNotReady = document.getElementById('recShelterNotReady');
    const finalChoiceQuestion = document.getElementById('finalChoiceQuestion');
    const allRecs = [recEvacuate, recShelterOptional, recShelterNotReady];
    const saveContinueBtn = document.getElementById('saveContinueBtn');
    let shelterIsReady_previous, shelterIsReady;

    // Function to load and apply saved answers from the server
    const loadSavedAnswers = () => {
        // 'planAnswers' is a global variable defined in the HTML script tag
        if (typeof planAnswers === 'undefined' || !planAnswers.step_2) {
            return; // No saved answers found for this step
        }

        const savedData = planAnswers.step_2;

        // Iterate over each saved answer key-value pair
        for (const [key, value] of Object.entries(savedData)) {
            // --- CHANGE: START ---
            // Find the corresponding radio button by its name and value.
            // Added [type="radio"] to the selector to ignore the hidden input with the same name.
            const inputToSelect = document.querySelector(`input[type="radio"][name="${key}"][value="${value}"]`);
            // --- CHANGE: END ---

            if (inputToSelect) {
                inputToSelect.checked = true; // Check the radio button
            }
        }
    };

    // Helper to hide all recommendations and disable their inputs
    const hideAllRecommendations = () => {
        allRecs.forEach(rec => rec.classList.add('d-none'));
        finalChoiceQuestion.classList.add('d-none'); // Also hide the final choice
        // Disable all decision inputs
        document.querySelectorAll('input[name="decision"]').forEach(input => input.disabled = true);
    };

    // --- Main function to update the entire UI state ---
    const updateUIState = () => {
        if (saveContinueBtn) saveContinueBtn.disabled = true;

        // Part 1: Evaluate the "Must Evacuate" checklist
        let mustEvacChecklistCompleted = true;
        for (let i = 1; i <= 5; i++) {
            if (!document.querySelector(`input[name="must_evac_q${i}"]:checked`)) {
                mustEvacChecklistCompleted = false;
                break;
            }
        }
        
        if (!mustEvacChecklistCompleted) {
            hideAllRecommendations();
            shelterChecklist.classList.add('d-none');
            shelterChecklist.querySelectorAll('input').forEach(input => input.disabled = true);
            return;
        }

        let mustEvacuate = Array.from(document.querySelectorAll('input[name^="must_evac_"]:checked')).some(radio => radio.value === 'yes');
        
        if (mustEvacuate) {
            hideAllRecommendations();
            recEvacuate.classList.remove('d-none');
            recEvacuate.querySelector('input[name="decision"]').disabled = false;
            if (saveContinueBtn) saveContinueBtn.disabled = false;
            
            // Hide AND DISABLE the shelter checklist and its inputs
            shelterChecklist.classList.add('d-none');
            shelterChecklist.querySelectorAll('input').forEach(input => {
                input.disabled = true;
            });
            
            return;
        }
        
        // Part 2: Evaluate the "Shelter" checklist
        shelterChecklist.classList.remove('d-none');
        shelterChecklist.querySelectorAll('input').forEach(input => input.disabled = false);

        let shelterChecklistCompleted = true;
        for (let i = 1; i <= 3; i++) {
            if (!document.querySelector(`input[name="shelter_q${i}"]:checked`)) {
                shelterChecklistCompleted = false;
                break;
            }
        }

        if (!shelterChecklistCompleted) {
            hideAllRecommendations();
            return;
        }
        
        // Part 3: Show the final recommendation
        shelterIsReady_previous = shelterIsReady;
        shelterIsReady = Array.from(document.querySelectorAll('input[name^="shelter_"]:checked')).every(radio => radio.value === 'yes');
        if (shelterIsReady) {
            if (shelterIsReady_previous === undefined || shelterIsReady_previous !== shelterIsReady) {
                hideAllRecommendations();
            }
            recShelterOptional.classList.remove('d-none');
            finalChoiceQuestion.classList.remove('d-none');
            finalChoiceQuestion.querySelectorAll('input[name="decision"]').forEach(input => input.disabled = false);
            
            const finalChoiceMade = document.querySelector('#finalChoiceQuestion input[name="decision"]:checked');
            if(saveContinueBtn) saveContinueBtn.disabled = !finalChoiceMade;
        } else {
            hideAllRecommendations();
            recShelterNotReady.classList.remove('d-none');
            recShelterNotReady.querySelector('input[name="decision"]').disabled = false;
            if (saveContinueBtn) saveContinueBtn.disabled = false;
        }
    };

    // Add a single event listener to the form to handle all changes
    document.getElementById('decisionForm').addEventListener('change', updateUIState);

    // Initial calls on page load
    loadSavedAnswers(); // First, load the saved state from the server
    updateUIState();    // Then, update the UI to reflect the loaded state
});