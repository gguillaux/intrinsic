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
    const configSection = document.getElementById('config-section');
    const dataSection = document.getElementById('data-section');
    const filtersContainer = document.getElementById('filters-container');
    const newsDatePicker = document.getElementById('news-date-picker');
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    
    const manualAssetsSection = document.getElementById('manual-assets-section');
    const manualAssetsCheckbox = document.getElementById('manual-assets-checkbox');
    const manualAssetsContainer = document.getElementById('manual-assets-input-container');
    const manualAssetsTextarea = document.getElementById('manual-assets-textarea');

    let currentTab = 'br-stocks';
    let currentData = [];

    const TAB_CONFIG = {
        'br-stocks': { title: 'BR Stocks', subtitle: 'Focus on High FCF, EPS, low Debt, P/E, and PEG < 1', type: 'stock' },
        'us-stocks': { title: 'US Stocks', subtitle: 'Focus on High FCF, EPS, low Debt, P/E, and PEG < 1', type: 'stock' },
        'br-fiis': { title: 'BR FIIs', subtitle: 'Focus on High Dividend Yield and Price to Book (P/VPA)', type: 'reit' },
        'us-reits': { title: 'US REITs', subtitle: 'Focus on High Dividend Yield and Price to Book (P/VPA)', type: 'reit' },
        'b3-indices': { title: 'B3 Indices Configuration', subtitle: 'Select active index for BR Stocks tab', type: 'config' },
        'market-news': { title: 'Market News Feed', subtitle: 'Latest corporate and economic announcements (B3)', type: 'news' }
    };

    function getEndpoint(tabId) {
        let manualTickers = '';
        if ((tabId === 'br-stocks' || tabId === 'us-stocks') && manualAssetsCheckbox && manualAssetsCheckbox.checked) {
            manualTickers = manualAssetsTextarea.value.trim().split(/[\s,]+/).filter(x => x).join(',');
        }

        if (tabId === 'br-stocks') {
            return manualTickers ? `/stocks/br?tickers=${manualTickers}` : `/stocks/br?index=${indexSelect.value}`;
        }
        if (tabId === 'us-stocks') {
            return manualTickers ? `/stocks/us?tickers=${manualTickers}` : `/stocks/us`;
        }
        if (tabId === 'br-fiis') return `/fiis/br`;
        if (tabId === 'us-reits') return `/reits/us`;
        if (tabId === 'market-news') {
            const dateVal = newsDatePicker.value.trim();
            if (dateVal) {
                const parts = dateVal.split('/');
                if (parts.length === 3) {
                    const formattedDate = `${parts[2]}-${parts[1]}-${parts[0]}`;
                    return `/news?date=${formattedDate}`;
                }
            }
            return `/news`;
        }
        return null;
    }

    // Initialize
    document.body.classList.add('theme-dark'); // set default theme
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

        indexSelect.addEventListener('change', () => {
            // Automatically switch back to BR Stocks when a new index is selected
            navItems.forEach(nav => {
                nav.classList.remove('active');
                if (nav.dataset.tab === 'br-stocks') nav.classList.add('active');
            });
            currentTab = 'br-stocks';
            loadTabData(currentTab);
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

        if (themeToggleBtn) {
            themeToggleBtn.addEventListener('click', () => {
                if (document.body.classList.contains('theme-dark')) {
                    document.body.classList.remove('theme-dark');
                    document.body.classList.add('theme-light');
                } else {
                    document.body.classList.remove('theme-light');
                    document.body.classList.add('theme-dark');
                }
            });
        }

        if (manualAssetsCheckbox) {
            manualAssetsCheckbox.addEventListener('change', (e) => {
                if (manualAssetsContainer) {
                    manualAssetsContainer.style.display = e.target.checked ? 'block' : 'none';
                }
            });
        }
    }

    async function loadTabData(tabId) {
        const config = TAB_CONFIG[tabId];
        
        pageTitle.textContent = config.title;
        pageSubtitle.textContent = config.subtitle;
        
        // Handle config tab vs data tabs
        if (config.type === 'config') {
            configSection.style.display = 'block';
            dataSection.style.display = 'none';
            filtersContainer.style.display = 'none';
            if (manualAssetsSection) manualAssetsSection.style.display = 'none';
            return;
        } else {
            configSection.style.display = 'none';
            dataSection.style.display = 'block';
            filtersContainer.style.display = 'flex';
        }

        if (tabId === 'market-news') {
            newsDatePicker.style.display = 'block';
            if (manualAssetsSection) manualAssetsSection.style.display = 'none';
        } else {
            newsDatePicker.style.display = 'none';
        }

        if (tabId === 'br-stocks' || tabId === 'us-stocks') {
            if (manualAssetsSection) manualAssetsSection.style.display = 'block';
        } else {
            if (manualAssetsSection) manualAssetsSection.style.display = 'none';
        }

        tableContainer.style.display = 'none';
        loader.style.display = 'flex';
        tableBody.innerHTML = '';
        searchInput.value = '';

        try {
            renderTableHeaders(config.type);
            
            const endpoint = getEndpoint(tabId);
            const response = await fetch(`${API_BASE}${endpoint}`);
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
