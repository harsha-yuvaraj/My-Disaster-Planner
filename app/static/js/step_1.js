document.addEventListener('DOMContentLoaded', () => {

    // --- Section 1: Initialize Tom Select for the Health Conditions Dropdown ---
    const healthSelect = document.getElementById('health-conditions-select');
    if (healthSelect) {
        // Initialize TomSelect on the dropdown element
        const tomInstance = new TomSelect(healthSelect, {
            plugins: ['remove_button'], // Adds a small 'x' to remove selected items
            placeholder: 'Select all that apply...',
        });
    }


    // --- Section 2: Contact Management Logic ---
    const contactsContainer = document.getElementById('supportContactsContainer');
    const addContactBtn = document.getElementById('addContactBtn');
    const contactTemplate = document.getElementById('contact-template');
    const contactLimitMessage = document.getElementById('contactLimitMessage');
    const MAX_CONTACTS = 4;
    let contactIndex = 0;
    
    // Safely parse existing contact data from the server
    const existingContactsJSON = contactsContainer ? contactsContainer.dataset.existingContacts : '[]';
    let existingContacts = [];
    try {
        let parsedData = JSON.parse(existingContactsJSON);
        if (typeof parsedData === 'string') {
            existingContacts = JSON.parse(parsedData);
        } else {
            existingContacts = parsedData;
        }
        if (!Array.isArray(existingContacts)) {
             existingContacts = [];
        }
    } catch (e) {
        console.error("Could not parse existing contacts JSON.", e);
        existingContacts = [];
    }
    
    /**
     * Updates the UI to show/hide the "Add" button and limit message.
     */
    function updateAddContactButtonState() {
        if (!contactsContainer) return; // Exit if the container doesn't exist
        const currentContactCount = contactsContainer.querySelectorAll('.contact-row').length;
        
        const isLimitReached = currentContactCount >= MAX_CONTACTS;
        
        if(addContactBtn) addContactBtn.disabled = isLimitReached;
        if(contactLimitMessage) contactLimitMessage.classList.toggle('d-none', !isLimitReached);
    }

    /**
     * Creates and adds a new contact input row to the form.
     * @param {object} contact - Optional data to pre-fill the row.
     */
    function addContact(contact = {}) {
        if (!contactsContainer || contactsContainer.querySelectorAll('.contact-row').length >= MAX_CONTACTS) {
            return;
        }

        const newContactRow = contactTemplate.content.cloneNode(true);
        const nameInput = newContactRow.querySelector('.contact-name');
        const phoneInput = newContactRow.querySelector('.contact-phone');
        const relationshipInput = newContactRow.querySelector('.contact-relationship');
        const removeBtn = newContactRow.querySelector('.remove-contact-btn');
        const mainDiv = newContactRow.querySelector('.contact-row');

        nameInput.name = `contacts[${contactIndex}][name]`;
        phoneInput.name = `contacts[${contactIndex}][phone]`;
        relationshipInput.name = `contacts[${contactIndex}][relationship]`;
        nameInput.value = contact.name || '';
        phoneInput.value = contact.phone || '';
        relationshipInput.value = contact.relationship || '';

        removeBtn.addEventListener('click', () => {
            mainDiv.remove();
            updateAddContactButtonState();
        });
        
        contactsContainer.appendChild(newContactRow);
        contactIndex++;
        updateAddContactButtonState();
    }

    // Initialize contact section event listeners and state
    if (addContactBtn) {
        addContactBtn.addEventListener('click', () => addContact());

        if (existingContacts && existingContacts.length > 0) {
            const contactsToLoad = existingContacts.slice(0, MAX_CONTACTS);
            contactsToLoad.forEach(contact => addContact(contact));
        } else {
            addContact(); 
        }
        updateAddContactButtonState();
    }
});
