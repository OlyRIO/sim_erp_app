// SIM Inventory Management
(function() {
    'use strict';

    let currentPage = 1;
    let currentFilters = {
        status: '',
        iccid: '',
        msisdn: ''
    };

    // Status color mapping
    const statusColors = {
        'active': '#00b8a9',
        'inactive': '#6b6b6b',
        'suspended': '#ff9500',
        'available': '#e20074',
        'provisioning': '#3498db',
        'unknown': '#9b9b9b'
    };

    // DOM elements
    const tableBody = document.getElementById('sim-table-body');
    const totalSimsEl = document.getElementById('total-sims');
    const paginationControls = document.getElementById('pagination-controls');
    const filterIccid = document.getElementById('filter-iccid');
    const filterMsisdn = document.getElementById('filter-msisdn');
    const filterStatus = document.getElementById('filter-status');
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

    // Fetch SIM data from API
    async function fetchSims(page = 1) {
        const params = new URLSearchParams({
            page: page,
            per_page: 50
        });

        if (currentFilters.status) params.append('status', currentFilters.status);
        if (currentFilters.iccid) params.append('iccid', currentFilters.iccid);
        if (currentFilters.msisdn) params.append('msisdn', currentFilters.msisdn);

        try {
            const response = await fetch(`/api/sims?${params.toString()}`);
            if (!response.ok) throw new Error('Failed to fetch SIM data');
            
            const data = await response.json();
            renderTable(data.sims);
            renderPagination(data);
            updateStats(data.total);
        } catch (error) {
            console.error('Error fetching SIMs:', error);
            tableBody.innerHTML = `
                <tr class="error-row">
                    <td colspan="5" class="error-cell">Failed to load SIM data. Please try again.</td>
                </tr>
            `;
        }
    }

    // Render table rows
    function renderTable(sims) {
        if (!sims || sims.length === 0) {
            tableBody.innerHTML = `
                <tr class="empty-row">
                    <td colspan="5" class="empty-cell">No SIM cards found matching your filters.</td>
                </tr>
            `;
            return;
        }

        tableBody.innerHTML = sims.map(sim => `
            <tr class="sim-row">
                <td class="iccid-cell">${escapeHtml(sim.iccid)}</td>
                <td class="msisdn-cell">${escapeHtml(sim.msisdn)}</td>
                <td class="status-cell">
                    <span class="status-badge" style="background-color: ${statusColors[sim.status] || statusColors.unknown}">
                        ${escapeHtml(sim.status)}
                    </span>
                </td>
                <td class="carrier-cell">${escapeHtml(sim.carrier)}</td>
                <td class="date-cell">${escapeHtml(sim.created_at)}</td>
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
                    onclick="window.simInventory.goToPage(${data.current_page - 1})">
                ‹ Previous
            </button>
        `;

        // First page
        if (startPage > 1) {
            html += `<button class="pagination-btn" onclick="window.simInventory.goToPage(1)">1</button>`;
            if (startPage > 2) html += `<span class="pagination-ellipsis">...</span>`;
        }

        // Page numbers
        for (let i = startPage; i <= endPage; i++) {
            html += `
                <button class="pagination-btn ${i === data.current_page ? 'active' : ''}" 
                        onclick="window.simInventory.goToPage(${i})">
                    ${i}
                </button>
            `;
        }

        // Last page
        if (endPage < data.pages) {
            if (endPage < data.pages - 1) html += `<span class="pagination-ellipsis">...</span>`;
            html += `<button class="pagination-btn" onclick="window.simInventory.goToPage(${data.pages})">${data.pages}</button>`;
        }

        // Next button
        html += `
            <button class="pagination-btn" ${!data.has_next ? 'disabled' : ''} 
                    onclick="window.simInventory.goToPage(${data.current_page + 1})">
                Next ›
            </button>
        `;

        html += '</div>';
        paginationControls.innerHTML = html;
    }

    // Update statistics
    function updateStats(total) {
        totalSimsEl.textContent = total.toLocaleString();
    }

    // Escape HTML to prevent XSS
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Event handlers
    function handleFilterChange() {
        currentFilters.iccid = filterIccid.value.trim();
        currentFilters.msisdn = filterMsisdn.value.trim();
        currentFilters.status = filterStatus.value;
        currentPage = 1;
        fetchSims(currentPage);
    }

    // Debounced filter handlers
    const debouncedFilterChange = debounce(handleFilterChange, 500);

    filterIccid.addEventListener('input', debouncedFilterChange);
    filterMsisdn.addEventListener('input', debouncedFilterChange);
    filterStatus.addEventListener('change', handleFilterChange);

    clearFiltersBtn.addEventListener('click', () => {
        filterIccid.value = '';
        filterMsisdn.value = '';
        filterStatus.value = '';
        handleFilterChange();
    });

    // Public API
    window.simInventory = {
        goToPage: (page) => {
            currentPage = page;
            fetchSims(currentPage);
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    };

    // Initial load
    fetchSims(currentPage);
})();
