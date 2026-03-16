document.addEventListener('DOMContentLoaded', () => {
    const API_BASE = "http://localhost:8000/api";
    
    // UI Elements
    const navItems = document.querySelectorAll('.nav-item');
    const pageTitle = document.getElementById('page-title');
    const pageSubtitle = document.getElementById('page-subtitle');
    const tableHeaderRow = document.getElementById('table-header-row');
    const tableBody = document.getElementById('table-body');
    const loader = document.getElementById('loader');
    const tableContainer = document.querySelector('.table-container');
    const refreshBtn = document.getElementById('refresh-btn');
    const searchInput = document.getElementById('search-input');

    let currentTab = 'br-stocks';
    let currentData = [];

    const TAB_CONFIG = {
        'br-stocks': {
            title: 'BR Stocks (Ações)',
            subtitle: 'Focus on High FCF, EPS, low Debt, P/E, and PEG < 1',
            endpoint: '/stocks/br',
            type: 'stock'
        },
        'us-stocks': {
            title: 'US Stocks',
            subtitle: 'Focus on High FCF, EPS, low Debt, P/E, and PEG < 1',
            endpoint: '/stocks/us',
            type: 'stock'
        },
        'br-fiis': {
            title: 'BR Real Estate Funds (FIIs)',
            subtitle: 'Focus on High Dividend Yield and Price to Book (P/VPA)',
            endpoint: '/fiis/br',
            type: 'reit'
        },
        'us-reits': {
            title: 'US Real Estate Funds (REITs)',
            subtitle: 'Focus on High Dividend Yield and Price to Book (P/VPA)',
            endpoint: '/reits/us',
            type: 'reit'
        }
    };

    // Initialize
    bindEvents();
    loadTabData(currentTab);

    function bindEvents() {
        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                navItems.forEach(nav => nav.classList.remove('active'));
                e.currentTarget.classList.add('active');
                
                currentTab = e.currentTarget.dataset.tab;
                loadTabData(currentTab);
            });
        });

        refreshBtn.addEventListener('click', () => {
            loadTabData(currentTab);
        });

        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            const filtered = currentData.filter(item => 
                item.ticker.toLowerCase().includes(term) || 
                (item.name && item.name.toLowerCase().includes(term))
            );
            renderTableBody(filtered, TAB_CONFIG[currentTab].type);
        });
    }

    async function loadTabData(tabId) {
        const config = TAB_CONFIG[tabId];
        
        // Update Headers
        pageTitle.textContent = config.title;
        pageSubtitle.textContent = config.subtitle;
        
        // Clear old data
        tableContainer.style.display = 'none';
        loader.style.display = 'flex';
        tableBody.innerHTML = '';
        searchInput.value = '';

        try {
            renderTableHeaders(config.type);
            
            const response = await fetch(`${API_BASE}${config.endpoint}`);
            if (!response.ok) throw new Error("Network response was not ok");
            
            const data = await response.json();
            currentData = data;
            
            renderTableBody(data, config.type);
            tableContainer.style.display = 'block';
        } catch (error) {
            tableBody.innerHTML = `<tr><td colspan="10" class="bad-metric" style="text-align: center;">Error fetching data: ${error.message}</td></tr>`;
            tableContainer.style.display = 'block';
        } finally {
            loader.style.display = 'none';
        }
    }

    function renderTableHeaders(type) {
        if (type === 'stock') {
            tableHeaderRow.innerHTML = `
                <th>Ticker / Name</th>
                <th>Price</th>
                <th>FCF</th>
                <th>EPS</th>
                <th>Debt</th>
                <th>P/E</th>
                <th>PEG</th>
            `;
        } else if (type === 'reit') {
            tableHeaderRow.innerHTML = `
                <th>Ticker / Name</th>
                <th>Price</th>
                <th>Div. Yield</th>
                <th>P/VPA</th>
            `;
        }
    }

    function renderTableBody(data, type) {
        if (data.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="10" style="text-align:center; color: var(--text-secondary)">No records found.</td></tr>`;
            return;
        }

        const formatCurrency = (val) => val != null ? val.toLocaleString('en-US', { style: 'currency', currency: 'USD' }) : '-';
        const formatNumber = (val, dec=2) => val != null ? val.toLocaleString('en-US', { minimumFractionDigits: dec, maximumFractionDigits: dec }) : '-';
        const formatPercent = (val) => val != null ? `${val.toFixed(2)}%` : '-';
        const formatLarge = (val) => {
            if (val == null) return '-';
            if (val >= 1e9) return `$${(val / 1e9).toFixed(2)}B`;
            if (val >= 1e6) return `$${(val / 1e6).toFixed(2)}M`;
            return formatCurrency(val);
        };

        const rows = data.map(item => {
            const nameSub = item.name ? item.name : 'Unknown';
            let rowHTML = `<tr>
                <td class="ticker-cell">
                    ${item.ticker}
                    <span class="name-sub">${nameSub}</span>
                </td>
                <td>${formatCurrency(item.price)}</td>
            `;

            if (type === 'stock') {
                const fcfClass = item.fcf > 0 ? 'good-metric' : (item.fcf < 0 ? 'bad-metric' : '');
                const epsClass = item.eps > 0 ? 'good-metric' : (item.eps < 0 ? 'bad-metric' : '');
                const peClass = (item.pe != null && item.pe < 15 && item.pe > 0) ? 'good-metric' : ((item.pe > 30 || item.pe < 0) ? 'bad-metric' : '');
                const pegClass = (item.peg != null && item.peg < 1 && item.peg > 0) ? 'good-metric' : (item.peg > 2 ? 'bad-metric' : '');

                rowHTML += `
                    <td class="${fcfClass}">${formatLarge(item.fcf)}</td>
                    <td class="${epsClass}">${formatNumber(item.eps)}</td>
                    <td>${formatLarge(item.debt)}</td>
                    <td class="${peClass}">${formatNumber(item.pe)}</td>
                    <td class="${pegClass}">${formatNumber(item.peg)}</td>
                `;
            } else if (type === 'reit') {
                const dyClass = (item.dividend_yield > 6) ? 'good-metric' : '';
                const pVpaClass = (item.p_vpa < 1 && item.p_vpa > 0) ? 'good-metric' : (item.p_vpa > 1.2 ? 'bad-metric' : '');

                rowHTML += `
                    <td class="${dyClass}">${formatPercent(item.dividend_yield)}</td>
                    <td class="${pVpaClass}">${formatNumber(item.p_vpa)}</td>
                `;
            }

            rowHTML += `</tr>`;
            return rowHTML;
        }).join('');

        tableBody.innerHTML = rows;
    }
});
