document.addEventListener('DOMContentLoaded', () => {

    // --- DOM ELEMENT SELECTORS ---
    const form = document.getElementById('step3Form');
    const saveContinueBtn = document.getElementById('saveContinueBtn');
    
    const isEvacPlan = planAnswers?.step_2?.decision === 'evacuate';
    // Added a check for the shelter-in-place plan
    const isShelterPlan = planAnswers?.step_2?.decision === 'shelter';
    // --- NEW CHANGE END ---

    // Evacuation-specific elements
    const specialNeedsShelterInfo = document.getElementById('specialNeedsShelterInfo');
    const primaryOtherDetails = document.getElementById('primary_other_details');
    const primaryOtherDetailsLabel = document.getElementById('primary_other_details_label');
    const countySelectEl = document.getElementById('county_select');
    const countyLinkContainer = document.getElementById('county_link_container');
    
    // --- Generic function to select an element; helps keep code DRY ---
    const getEl = (id) => document.getElementById(id);

    /**
     * Initializes a Tom Select instance on a given element.
     * @param {string} elementId - The ID of the select element.
     * @param {string} placeholder - The placeholder text for the select input.
     * @returns {TomSelect} The created Tom Select instance.
     */
    const initializeTomSelect = (elementId, placeholder) => {
        const el = getEl(elementId);
        if (el) {
            // This function now correctly returns the new TomSelect instance
            return new TomSelect(el, {
                plugins: ['remove_button'],
                placeholder: placeholder,
                create: true, // Allows users to create new options
                sortField: {
                    field: "text",
                    direction: "asc"
                }
            });
        }
        return null;
    };


    /**
     * Loads saved answers from the planAnswers object into the form fields.
     */
    const loadSavedAnswers = () => {
        const savedData = planAnswers.step_3;
        if (!savedData) return;

        for (const [key, value] of Object.entries(savedData)) {
            const multiSelectKeys = ['gokit_docs', 'gokit_medical', 'gokit_supplies', 'gokit_comfort', 'secure_home_items', 'staykit_items', 'power_comfort_items'];
            if (multiSelectKeys.includes(key)) {
                continue;
            }
            
            const radio = document.querySelector(`input[type="radio"][name="${key}"][value="${value}"]`);
            if (radio) {
                radio.checked = true;
                continue; 
            }
            
            if (value === 'true' || value === true) {
                const checkbox = document.querySelector(`input[type="checkbox"][name="${key}"]`);
                if (checkbox) checkbox.checked = true;
                continue; 
            }
            
            if (key === 'fl_county' && countySelectEl) {
                // Storing the value in a data attribute is a good way to pass it
                // to the Tom Select initializer later.
                countySelectEl.setAttribute('data-saved-value', value);
                continue;
            }

            const input = document.querySelector(`[name="${key}"]`);
            if (input) {
                input.value = value;
            }
        }
    };

    /**
     * Manages the UI for a destination section (primary or backup).
     * @param {string} type - 'primary' or 'backup'
     */
    const manageDestinationUI = (type) => {
        const knowsAddress = document.querySelector(`input[name="${type}_knows_address"]:checked`);
        const addressContainer = getEl(`${type}_address_container`);
        const noAddressInfo = getEl(`${type}_no_address_info`);
        const knows = knowsAddress?.value === 'yes';

        if (addressContainer && noAddressInfo) {
            addressContainer.classList.toggle('d-none', !knows);
            noAddressInfo.classList.toggle('d-none', knowsAddress?.value !== 'no');
        }

        if (type === 'primary') {
            const primaryAddressInput = getEl('primary_address');
            const primaryAddressLabel = getEl('primary_address_label');
            if (primaryAddressInput && primaryAddressLabel) {
                primaryAddressInput.required = knows;
                primaryAddressLabel.classList.toggle('is-required', knows);
            }
            const transport = document.querySelector(`input[name="primary_transport"]:checked`);
            ['car', 'bus', 'air'].forEach(method => {
                const adviceEl = getEl(`primary_transport_advice_${method}`);
                if (adviceEl) {
                    adviceEl.classList.toggle('d-none', transport?.value !== method);
                }
            });
        } 
        else if (type === 'backup') {
            const backupAddressInput = getEl('backup_address');
            const backupAddressLabel = getEl('backup_address_label');
            if (backupAddressInput && backupAddressLabel) {
                backupAddressInput.required = knows;
                backupAddressLabel.classList.toggle('is-required', knows);
            }
        }
    };

    /**
     * Toggles the visibility of the special needs shelter information.
     */
    const updateShelterInfoVisibility = () => {
        if (!specialNeedsShelterInfo) return; 
        const selectedDestination = document.querySelector('input[name="evac_primary_destination_type"]:checked');
        specialNeedsShelterInfo.classList.toggle('d-none', selectedDestination?.value !== 'public_shelter');
    };
    
    /**
     * Checks if the "Other Details" for the primary destination should be required
     * and shows a tip.
     */
    const updateConditionalRequiredFields = () => {
        if (!isEvacPlan || !primaryOtherDetails || !primaryOtherDetailsLabel) return;
        
        const selectedDestinationType = document.querySelector('input[name="evac_primary_destination_type"]:checked');
        const isOther = selectedDestinationType?.value === 'other';
        
        primaryOtherDetails.required = isOther;
        primaryOtherDetailsLabel.classList.toggle('is-is-required', isOther);
    };

    /**
     * Checks if the form is valid enough to proceed.
     */
    const validateForm = () => {
        if (!saveContinueBtn) return;
        
        let isValid = true; 
        
        if (isEvacPlan) {
            const selectedDestinationType = document.querySelector('input[name="evac_primary_destination_type"]:checked');
            
            if (!selectedDestinationType) {
                isValid = false;
            } else if (selectedDestinationType.value === 'other' && primaryOtherDetails.value.trim() === '') {
                isValid = false;
            }
        }
        
        saveContinueBtn.disabled = !isValid;
    };

    const handleCountyChange = (selectedValue) => {
        if (!countyLinkContainer) return;
        const countyUrl = flCounties[selectedValue];
    
        if (selectedValue && countyUrl) {
            countyLinkContainer.innerHTML = `
                <p class="mb-0 text-start">
                    <i class="bi bi-link-45deg"></i> 
                    Here is the direct link for <strong>${selectedValue} County</strong>: 
                    <a href="${countyUrl}" target="_blank" rel="noopener noreferrer">Visit Website</a>.
                </p>
            `;
            countyLinkContainer.classList.remove('d-none');
        } else {
            countyLinkContainer.innerHTML = '';
            countyLinkContainer.classList.add('d-none');
        }
    };

    // --- NEW FUNCTION START ---
    /**
     * Initializes all Tom Select multi-select fields based on the current plan type
     * and loads any saved data into them. This function replaces the previous,
     * evacuation-only logic.
     */
    const initializeAndLoadMultiSelects = () => {
        const multiSelectConfigs = {
            evacuate: [
                { id: 'gokit_docs_select', placeholder: 'Select or add documents...', dataKey: 'gokit_docs' },
                { id: 'gokit_medical_select', placeholder: 'Select or add medical items...', dataKey: 'gokit_medical' },
                { id: 'gokit_supplies_select', placeholder: 'Select or add supplies...', dataKey: 'gokit_supplies' },
                { id: 'gokit_comfort_select', placeholder: 'Select or add comfort items...', dataKey: 'gokit_comfort' }
            ],
            shelter: [
                { id: 'secure_home_select', placeholder: 'Select or add tasks...', dataKey: 'secure_home_items' },
                { id: 'staykit_select', placeholder: 'Select or add supplies...', dataKey: 'staykit_items' },
                { id: 'power_comfort_select', placeholder: 'Select or add items...', dataKey: 'power_comfort_items' }
            ]
        };

        const planType = isEvacPlan ? 'evacuate' : (isShelterPlan ? 'shelter' : null);
        if (!planType) return;

        const selectsToInit = multiSelectConfigs[planType];
        const savedData = planAnswers.step_3 || {};

        selectsToInit.forEach(config => {
            const tomSelectInstance = initializeTomSelect(config.id, config.placeholder);
            if (tomSelectInstance) {
                const savedValues = savedData[config.dataKey];
                if (savedValues && Array.isArray(savedValues)) {
                    // Add any user-created options that aren't in the original <option> list
                    savedValues.forEach(item => {
                        if (!tomSelectInstance.getOption(item)) {
                            tomSelectInstance.addOption({ value: item, text: item });
                        }
                    });
                    // Set the selected values
                    tomSelectInstance.setValue(savedValues);
                }
            }
        });
    };
    // --- NEW FUNCTION END ---


    // --- INITIALIZATION ---

    loadSavedAnswers();

    if (countySelectEl) {
        new TomSelect(countySelectEl, {
            create: false,
            sortField: { field: "text", direction: "asc" },
            onChange: function(value) { handleCountyChange(value); }
        });
        const savedValue = countySelectEl.getAttribute('data-saved-value');
        if (savedValue) countySelectEl.tomselect.setValue(savedValue);
    }
    

    // This new function handles both cases correctly. - eval and shelter plans
    initializeAndLoadMultiSelects();

    
    // UI updates that are specific to the evacuation plan
    if (isEvacPlan) {
        updateShelterInfoVisibility();
        manageDestinationUI('primary');
        manageDestinationUI('backup');
        updateConditionalRequiredFields();
    }

    validateForm(); 

    if (form) {
        form.addEventListener('input', (event) => {
            if (event.target.id === 'primary_other_details') {
                validateForm();
            }
        });

        form.addEventListener('change', () => {
             if (isEvacPlan) {
                updateShelterInfoVisibility();
                manageDestinationUI('primary');
                manageDestinationUI('backup');
                updateConditionalRequiredFields();
            }
            validateForm();
        });
    }
});