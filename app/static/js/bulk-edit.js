// Bulk Edit Interface for SIMs and Customers
(function() {
    'use strict';

    // DOM Elements
    const tabs = document.querySelectorAll('.edit-tab');
    const sections = document.querySelectorAll('.edit-section');
    const simSearch = document.getElementById('sim-search');
    const simSearchBtn = document.getElementById('sim-search-btn');
    const simResults = document.getElementById('sim-results');
    const customerSearch = document.getElementById('customer-search');
    const customerSearchBtn = document.getElementById('customer-search-btn');
    const customerResults = document.getElementById('customer-results');
    const modal = document.getElementById('edit-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');
    const modalClose = document.getElementById('modal-close');
    const modalCancel = document.getElementById('modal-cancel');
    const modalSave = document.getElementById('modal-save');

    let currentEditType = null;
    let currentEditId = null;

    // Tab switching
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetTab = tab.dataset.tab;
            
            tabs.forEach(t => t.classList.remove('active'));
            sections.forEach(s => s.classList.remove('active'));
            
            tab.classList.add('active');
            document.getElementById(`${targetTab}-edit`).classList.add('active');
        });
    });

    // Search SIMs
    simSearchBtn.addEventListener('click', searchSims);
    simSearch.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchSims();
    });

    async function searchSims() {
        const query = simSearch.value.trim();
        if (!query) {
            showMessage(simResults, 'Please enter an ICCID or MSISDN', 'error');
            return;
        }

        showMessage(simResults, 'Searching...', 'loading');

        try {
            const response = await fetch(`/api/search/sims?q=${encodeURIComponent(query)}`);
            const data = await response.json();

            if (!response.ok) {
                showMessage(simResults, data.error || 'Search failed', 'error');
                return;
            }

            if (data.length === 0) {
                showMessage(simResults, 'No SIMs found matching your search', 'empty');
                return;
            }

            renderSimResults(data);
        } catch (error) {
            console.error('Search error:', error);
            showMessage(simResults, 'Failed to search. Please try again.', 'error');
        }
    }

    function renderSimResults(sims) {
        simResults.innerHTML = `
            <div class="results-grid">
                ${sims.map(sim => `
                    <div class="result-card" data-id="${sim.id}">
                        <div class="card-header">
                            <span class="status-badge" style="background: ${getStatusColor(sim.status)}">${sim.status}</span>
                            <button class="btn-edit" onclick="window.editSim(${sim.id})">Edit</button>
                        </div>
                        <div class="card-body">
                            <div class="card-row">
                                <span class="label">ICCID:</span>
                                <span class="value">${escapeHtml(sim.iccid)}</span>
                            </div>
                            <div class="card-row">
                                <span class="label">MSISDN:</span>
                                <span class="value">${escapeHtml(sim.msisdn)}</span>
                            </div>
                            <div class="card-row">
                                <span class="label">Carrier:</span>
                                <span class="value">${escapeHtml(sim.carrier)}</span>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    // Search Customers
    customerSearchBtn.addEventListener('click', searchCustomers);
    customerSearch.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchCustomers();
    });

    async function searchCustomers() {
        const query = customerSearch.value.trim();
        if (!query) {
            showMessage(customerResults, 'Please enter a name or OIB', 'error');
            return;
        }

        showMessage(customerResults, 'Searching...', 'loading');

        try {
            const response = await fetch(`/api/search/customers?q=${encodeURIComponent(query)}`);
            const data = await response.json();

            if (!response.ok) {
                showMessage(customerResults, data.error || 'Search failed', 'error');
                return;
            }

            if (data.length === 0) {
                showMessage(customerResults, 'No customers found matching your search', 'empty');
                return;
            }

            renderCustomerResults(data);
        } catch (error) {
            console.error('Search error:', error);
            showMessage(customerResults, 'Failed to search. Please try again.', 'error');
        }
    }

    function renderCustomerResults(customers) {
        customerResults.innerHTML = `
            <div class="results-grid">
                ${customers.map(customer => `
                    <div class="result-card" data-id="${customer.id}">
                        <div class="card-header">
                            <strong>${escapeHtml(customer.name)}</strong>
                            <button class="btn-edit" onclick="window.editCustomer(${customer.id})">Edit</button>
                        </div>
                        <div class="card-body">
                            <div class="card-row">
                                <span class="label">Email:</span>
                                <span class="value">${escapeHtml(customer.email || 'N/A')}</span>
                            </div>
                            <div class="card-row">
                                <span class="label">OIB:</span>
                                <span class="value">${escapeHtml(customer.oib)}</span>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    // Edit SIM Modal
    window.editSim = function(simId) {
        currentEditType = 'sim';
        currentEditId = simId;

        const card = document.querySelector(`.result-card[data-id="${simId}"]`);
        const statusBadge = card.querySelector('.status-badge');
        const currentStatus = statusBadge.textContent.trim();

        modalTitle.textContent = 'Edit SIM Status';
        modalBody.innerHTML = `
            <div class="form-group">
                <label for="sim-status">Status</label>
                <select id="sim-status" class="form-select">
                    <option value="active" ${currentStatus === 'active' ? 'selected' : ''}>Active</option>
                    <option value="inactive" ${currentStatus === 'inactive' ? 'selected' : ''}>Inactive</option>
                    <option value="suspended" ${currentStatus === 'suspended' ? 'selected' : ''}>Suspended</option>
                    <option value="available" ${currentStatus === 'available' ? 'selected' : ''}>Available</option>
                    <option value="provisioning" ${currentStatus === 'provisioning' ? 'selected' : ''}>Provisioning</option>
                </select>
            </div>
        `;

        modal.classList.remove('hidden');
    };

    // Edit Customer Modal
    window.editCustomer = function(customerId) {
        currentEditType = 'customer';
        currentEditId = customerId;

        const card = document.querySelector(`.result-card[data-id="${customerId}"]`);
        const name = card.querySelector('.card-header strong').textContent;
        const email = card.querySelectorAll('.value')[0].textContent;
        const oib = card.querySelectorAll('.value')[1].textContent;

        modalTitle.textContent = 'Edit Customer Information';
        modalBody.innerHTML = `
            <div class="form-group">
                <label for="customer-name">Name</label>
                <input type="text" id="customer-name" class="form-input" value="${escapeHtml(name)}">
            </div>
            <div class="form-group">
                <label for="customer-email">Email</label>
                <input type="email" id="customer-email" class="form-input" value="${email === 'N/A' ? '' : escapeHtml(email)}">
            </div>
            <div class="form-group">
                <label for="customer-oib">OIB</label>
                <input type="text" id="customer-oib" class="form-input" value="${oib === 'N/A' ? '' : escapeHtml(oib)}" maxlength="11">
            </div>
        `;

        modal.classList.remove('hidden');
    };

    // Save changes
    modalSave.addEventListener('click', async () => {
        modalSave.disabled = true;
        modalSave.textContent = 'Saving...';

        try {
            if (currentEditType === 'sim') {
                await saveSim();
            } else if (currentEditType === 'customer') {
                await saveCustomer();
            }
        } finally {
            modalSave.disabled = false;
            modalSave.textContent = 'Save Changes';
        }
    });

    async function saveSim() {
        const status = document.getElementById('sim-status').value;

        try {
            const response = await fetch(`/api/sims/${currentEditId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status })
            });

            const data = await response.json();

            if (!response.ok) {
                alert('Error: ' + (data.error || 'Failed to update'));
                return;
            }

            // Update UI
            const card = document.querySelector(`.result-card[data-id="${currentEditId}"]`);
            const statusBadge = card.querySelector('.status-badge');
            statusBadge.textContent = status;
            statusBadge.style.background = getStatusColor(status);

            modal.classList.add('hidden');
            showNotification('SIM status updated successfully', 'success');
        } catch (error) {
            console.error('Save error:', error);
            alert('Failed to save. Please try again.');
        }
    }

    async function saveCustomer() {
        const name = document.getElementById('customer-name').value.trim();
        const email = document.getElementById('customer-email').value.trim();
        const oib = document.getElementById('customer-oib').value.trim();

        if (!name) {
            alert('Name is required');
            return;
        }

        try {
            const response = await fetch(`/api/customers/${currentEditId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, oib })
            });

            const data = await response.json();

            if (!response.ok) {
                alert('Error: ' + (data.error || 'Failed to update'));
                return;
            }

            // Update UI
            const card = document.querySelector(`.result-card[data-id="${currentEditId}"]`);
            card.querySelector('.card-header strong').textContent = name;
            card.querySelectorAll('.value')[0].textContent = email || 'N/A';
            card.querySelectorAll('.value')[1].textContent = oib || 'N/A';

            modal.classList.add('hidden');
            showNotification('Customer information updated successfully', 'success');
        } catch (error) {
            console.error('Save error:', error);
            alert('Failed to save. Please try again.');
        }
    }

    // Modal close handlers
    modalClose.addEventListener('click', () => modal.classList.add('hidden'));
    modalCancel.addEventListener('click', () => modal.classList.add('hidden'));
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.classList.add('hidden');
    });

    // Utility functions
    function showMessage(container, message, type) {
        const className = type === 'error' ? 'error-message' : 
                         type === 'loading' ? 'loading-message' : 
                         type === 'empty' ? 'empty-message' : 'placeholder-text';
        container.innerHTML = `<p class="${className}">${message}</p>`;
    }

    function showNotification(message, type) {
        const notif = document.createElement('div');
        notif.className = `notification ${type}`;
        notif.textContent = message;
        document.body.appendChild(notif);

        setTimeout(() => {
            notif.style.opacity = '0';
            setTimeout(() => notif.remove(), 300);
        }, 3000);
    }

    function getStatusColor(status) {
        const colors = {
            'active': '#00b8a9',
            'inactive': '#6b6b6b',
            'suspended': '#ff9500',
            'available': '#e20074',
            'provisioning': '#3498db',
            'unknown': '#9b9b9b'
        };
        return colors[status] || colors.unknown;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
})();
