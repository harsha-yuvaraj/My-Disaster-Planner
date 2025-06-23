document.addEventListener('DOMContentLoaded', () => {
    // DOM Element selectors
    const shelterChecklist = document.getElementById('shelterChecklist');
    const recEvacuate = document.getElementById('recEvacuate');
    const recShelterOptional = document.getElementById('recShelterOptional');
    const recShelterNotReady = document.getElementById('recShelterNotReady');
    const finalChoiceQuestion = document.getElementById('finalChoiceQuestion'); // New selector
    const allRecs = [recEvacuate, recShelterOptional, recShelterNotReady];
    const saveContinueBtn = document.getElementById('saveContinueBtn');
    let shelterIsReady_previous, shelterIsReady; 

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
            return;
        }

        let mustEvacuate = Array.from(document.querySelectorAll('input[name^="must_evac_"]:checked')).some(radio => radio.value === 'yes');
        
        if (mustEvacuate) {
            hideAllRecommendations();
            recEvacuate.classList.remove('d-none');
            recEvacuate.querySelector('input[name="decision"]').disabled = false;
            if (saveContinueBtn) saveContinueBtn.disabled = false;
            shelterChecklist.classList.add('d-none');
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
        shelterIsReady_previous = shelterIsReady; // Store previous state for comparison
        console.log('Previous shelterIsReady:', shelterIsReady_previous);
        shelterIsReady = Array.from(document.querySelectorAll('input[name^="shelter_"]:checked')).every(radio => radio.value === 'yes');
        console.log('Shelter is ready:', shelterIsReady);
        if (shelterIsReady) {
            if (shelterIsReady_previous === undefined || shelterIsReady_previous !== shelterIsReady) {
                hideAllRecommendations();
            }
            recShelterOptional.classList.remove('d-none');
            finalChoiceQuestion.classList.remove('d-none'); // Show the separate choice div
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

    // Initial call on page load
    updateUIState();
});
