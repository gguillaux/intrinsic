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
    const indexSelect = document.getElementById('index-select');

    let currentTab = 'br-stocks';
    let currentData = [];

    const TAB_CONFIG = {
        'br-stocks': { title: 'BR Stocks (Ações)', subtitle: 'Focus on High FCF, EPS, low Debt, P/E, and PEG < 1', endpoint: '/stocks/br', type: 'stock' },
        'us-stocks': { title: 'US Stocks', subtitle: 'Focus on High FCF, EPS, low Debt, P/E, and PEG < 1', endpoint: '/stocks/us', type: 'stock' },
        'br-fiis': { title: 'BR FIIs', subtitle: 'Focus on High Dividend Yield and Price to Book (P/VPA)', endpoint: '/fiis/br', type: 'reit' },
        'us-reits': { title: 'US REITs', subtitle: 'Focus on High Dividend Yield and Price to Book (P/VPA)', endpoint: '/reits/us', type: 'reit' },
        'b3-indices': { title: 'B3 Indices Composition', subtitle: 'Tracker for all major Brazilian Indices', endpoint: '/indices/IBOV', type: 'index' },
        'market-news': { title: 'Market News Feed', subtitle: 'Latest corporate and economic announcements (B3)', endpoint: '/news', type: 'news' }
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
                
                // Show/hide Index Select dropdown
                if (currentTab === 'b3-indices') {
                    indexSelect.style.display = 'block';
                    TAB_CONFIG['b3-indices'].endpoint = `/indices/${indexSelect.value}`;
                } else {
                    indexSelect.style.display = 'none';
                }
                
                loadTabData(currentTab);
            });
        });

        indexSelect.addEventListener('change', (e) => {
            TAB_CONFIG['b3-indices'].endpoint = `/indices/${e.target.value}`;
            loadTabData('b3-indices');
        });

        refreshBtn.addEventListener('click', () => {
            loadTabData(currentTab);
        });

        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            const filtered = currentData.filter(item => {
                const searchStr = Object.values(item).join(' ').toLowerCase();
                return searchStr.includes(term);
            });
            renderTableBody(filtered, TAB_CONFIG[currentTab].type);
        });
    }

    async function loadTabData(tabId) {
        const config = TAB_CONFIG[tabId];
        
        pageTitle.textContent = config.title;
        pageSubtitle.textContent = config.subtitle;
        
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
            tableHeaderRow.innerHTML = `<th>Ticker / Name</th><th>Price</th><th>FCF</th><th>EPS</th><th>Debt</th><th>P/E</th><th>PEG</th>`;
        } else if (type === 'reit') {
            tableHeaderRow.innerHTML = `<th>Ticker / Name</th><th>Price</th><th>Div. Yield</th><th>P/VPA</th>`;
        } else if (type === 'index') {
            tableHeaderRow.innerHTML = `<th>Component Ticker</th><th>Weight (%)</th><th>Last Updated</th>`;
        } else if (type === 'news') {
            tableHeaderRow.innerHTML = `<th>Published At</th><th>Source</th><th>Headline</th><th>Link</th>`;
        }
    }

    function renderTableBody(data, type) {
        if (!data || data.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="10" style="text-align:center; color: var(--text-secondary)">NO DATA FOUND_</td></tr>`;
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
            if (type === 'news') {
                return `<tr>
                    <td style="white-space:nowrap">${item.published_at.split('.')[0]}</td>
                    <td style="color:var(--accent-hover)">[${item.source}]</td>
                    <td style="font-weight:bold">${item.title}</td>
                    <td><a href="${item.link}" target="_blank" style="color:var(--success); text-decoration:underline;">READ_</a></td>
                </tr>`;
            }

            if (type === 'index') {
                return `<tr>
                    <td class="ticker-cell" style="color:var(--success)">${item.ticker}</td>
                    <td style="font-weight:bold">${formatNumber(item.weight, 3)}%</td>
                    <td style="color:var(--text-secondary)">${item.last_updated}</td>
                </tr>`;
            }

            // Normal stock/reit parsing
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
            return rowHTML + `</tr>`;
        }).join('');

        tableBody.innerHTML = rows;
    }
});
