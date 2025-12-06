// Customer Inventory Management
(function() {
    'use strict';

    let currentPage = 1;
    let currentFilters = {
        name: '',
        oib: '',
        msisdn: ''
    };

    // DOM elements
    const tableBody = document.getElementById('customer-table-body');
    const totalCustomersEl = document.getElementById('total-customers');
    const paginationControls = document.getElementById('pagination-controls');
    const filterName = document.getElementById('filter-name');
    const filterOib = document.getElementById('filter-oib');
    const filterMsisdn = document.getElementById('filter-msisdn');
    const clearFiltersBtn = document.getElementById('clear-filters');

    // Debounce function for input filters
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Fetch Customer data from API
    async function fetchCustomers(page = 1) {
        const params = new URLSearchParams({
            page: page,
            per_page: 50
        });

        if (currentFilters.name) params.append('name', currentFilters.name);
        if (currentFilters.oib) params.append('oib', currentFilters.oib);
        if (currentFilters.msisdn) params.append('msisdn', currentFilters.msisdn);

        try {
            const response = await fetch(`/api/customers?${params.toString()}`);
            if (!response.ok) throw new Error('Failed to fetch customer data');
            
            const data = await response.json();
            renderTable(data.customers);
            renderPagination(data);
            updateStats(data.total);
        } catch (error) {
            console.error('Error fetching customers:', error);
            tableBody.innerHTML = `
                <tr class="error-row">
                    <td colspan="6" class="error-cell">Failed to load customer data. Please try again.</td>
                </tr>
            `;
        }
    }

    // Render table rows
    function renderTable(customers) {
        if (!customers || customers.length === 0) {
            tableBody.innerHTML = `
                <tr class="empty-row">
                    <td colspan="6" class="empty-cell">No customers found matching your filters.</td>
                </tr>
            `;
            return;
        }

        tableBody.innerHTML = customers.map(customer => `
            <tr class="sim-row">
                <td class="name-cell" data-label="Name"><strong>${escapeHtml(customer.name)}</strong></td>
                <td class="email-cell" data-label="Email">${escapeHtml(customer.email)}</td>
                <td class="oib-cell" data-label="OIB">${escapeHtml(customer.oib)}</td>
                <td class="ba-cell" data-label="Billing Account">${escapeHtml(customer.billing_account)}</td>
                <td class="sim-count-cell" data-label="SIM Count">${customer.sim_count}</td>
                <td class="date-cell" data-label="Created At">${escapeHtml(customer.created_at)}</td>
            </tr>
        `).join('');
    }

    // Render pagination controls
    function renderPagination(data) {
        if (data.pages <= 1) {
            paginationControls.innerHTML = '';
            return;
        }

        const maxButtons = 5;
        let startPage = Math.max(1, data.current_page - Math.floor(maxButtons / 2));
        let endPage = Math.min(data.pages, startPage + maxButtons - 1);

        if (endPage - startPage < maxButtons - 1) {
            startPage = Math.max(1, endPage - maxButtons + 1);
        }

        let html = '<div class="pagination">';

        // Previous button
        html += `
            <button class="pagination-btn" ${!data.has_prev ? 'disabled' : ''} 
                    onclick="window.customerInventory.goToPage(${data.current_page - 1})">
                < Previous
            </button>
        `;

        // First page
        if (startPage > 1) {
            html += `<button class="pagination-btn" onclick="window.customerInventory.goToPage(1)">1</button>`;
            if (startPage > 2) html += `<span class="pagination-ellipsis">...</span>`;
        }

        // Page numbers
        for (let i = startPage; i <= endPage; i++) {
            html += `
                <button class="pagination-btn ${i === data.current_page ? 'active' : ''}" 
                        onclick="window.customerInventory.goToPage(${i})">
                    ${i}
                </button>
            `;
        }

        // Last page
        if (endPage < data.pages) {
            if (endPage < data.pages - 1) html += `<span class="pagination-ellipsis">...</span>`;
            html += `<button class="pagination-btn" onclick="window.customerInventory.goToPage(${data.pages})">${data.pages}</button>`;
        }

        // Next button
        html += `
            <button class="pagination-btn" ${!data.has_next ? 'disabled' : ''} 
                    onclick="window.customerInventory.goToPage(${data.current_page + 1})">
                Next >
            </button>
        `;

        html += '</div>';
        paginationControls.innerHTML = html;
    }

    // Update statistics
    function updateStats(total) {
        totalCustomersEl.textContent = total.toLocaleString();
    }

    // Escape HTML to prevent XSS
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Event handlers
    function handleFilterChange() {
        currentFilters.name = filterName.value.trim();
        currentFilters.oib = filterOib.value.trim();
        currentFilters.msisdn = filterMsisdn.value.trim();
        currentPage = 1;
        fetchCustomers(currentPage);
    }

    // Debounced filter handlers
    const debouncedFilterChange = debounce(handleFilterChange, 500);

    filterName.addEventListener('input', debouncedFilterChange);
    filterOib.addEventListener('input', debouncedFilterChange);
    filterMsisdn.addEventListener('input', debouncedFilterChange);

    clearFiltersBtn.addEventListener('click', () => {
        filterName.value = '';
        filterOib.value = '';
        filterMsisdn.value = '';
        handleFilterChange();
    });

    // Public API
    window.customerInventory = {
        goToPage: (page) => {
            currentPage = page;
            fetchCustomers(currentPage);
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    };

    // Initial load
    fetchCustomers(currentPage);
})();
