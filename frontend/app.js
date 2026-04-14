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
    const newsTypeFilter = document.getElementById('news-type-filter');
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    
    const manualAssetsSection = document.getElementById('manual-assets-section');
    const manualAssetsCheckbox = document.getElementById('manual-assets-checkbox');
    const manualAssetsContainer = document.getElementById('manual-assets-input-container');
    const manualAssetsTextarea = document.getElementById('manual-assets-textarea');

    let currentTab = 'br-stocks';
    let currentData = [];
    let currentSort = { column: null, asc: true };
    let currentNewsType = '';

    const TAB_CONFIG = {
        'br-stocks': { title: 'BR Stocks', subtitle: 'Focus on Low P/FCF, EPS, low Debt, P/E, and PEG < 1', type: 'stock' },
        'us-stocks': { title: 'US Stocks', subtitle: 'Focus on Low P/FCF, EPS, low Debt, P/E, and PEG < 1', type: 'stock' },
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

        if (newsTypeFilter) {
            newsTypeFilter.addEventListener('change', (e) => {
                currentNewsType = e.target.value.toLowerCase();
                renderTableBody(currentData, TAB_CONFIG[currentTab].type);
            });
        }

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
            if (newsTypeFilter) newsTypeFilter.style.display = 'block';
            if (manualAssetsSection) manualAssetsSection.style.display = 'none';
        } else {
            newsDatePicker.style.display = 'none';
            if (newsTypeFilter) newsTypeFilter.style.display = 'none';
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
        currentSort = { column: null, asc: true };

        try {
            renderTableHeaders(config.type);
            
            const endpoint = getEndpoint(tabId);
            const response = await fetch(`${API_BASE}${endpoint}`);
            if (!response.ok) throw new Error("Network response was not ok");
            
            const data = await response.json();
            currentData = data;
            
            if (currentSort.column) sortData();
            renderTableBody(currentData, config.type);
            tableContainer.style.display = 'block';
        } catch (error) {
            tableBody.innerHTML = `<tr><td colspan="10" class="bad-metric" style="text-align: center;">Error fetching data: ${error.message}</td></tr>`;
            tableContainer.style.display = 'block';
        } finally {
            loader.style.display = 'none';
        }
    }

    function renderTableHeaders(type) {
        const getIcon = (col) => {
            if (currentSort.column !== col) return '';
            return currentSort.asc ? ' <span class="sort-icon">▲</span>' : ' <span class="sort-icon">▼</span>';
        };

        if (type === 'stock') {
            tableHeaderRow.innerHTML = `
                <th data-sort="ticker">Ticker / Name${getIcon('ticker')}</th>
                <th data-sort="price">Price${getIcon('price')}</th>
                <th data-sort="p_fcf">P/FCF${getIcon('p_fcf')}</th>
                <th data-sort="eps">EPS${getIcon('eps')}</th>
                <th data-sort="debt">Debt${getIcon('debt')}</th>
                <th data-sort="pe">P/E${getIcon('pe')}</th>
                <th data-sort="peg">PEG${getIcon('peg')}</th>
            `;
        } else if (type === 'reit') {
            tableHeaderRow.innerHTML = `
                <th data-sort="ticker">Ticker / Name${getIcon('ticker')}</th>
                <th data-sort="price">Price${getIcon('price')}</th>
                <th data-sort="dividend_yield">Div. Yield${getIcon('dividend_yield')}</th>
                <th data-sort="p_vpa">P/VPA${getIcon('p_vpa')}</th>
            `;
        } else if (type === 'news') {
            tableHeaderRow.innerHTML = `
                <th data-sort="published_at">Date${getIcon('published_at')}</th>
                <th data-sort="published_at">Time${getIcon('published_at')}</th>
                <th data-sort="title">Asset${getIcon('title')}</th>
                <th data-sort="title">Headline / Type${getIcon('title')}</th>
            `;
        }
        attachSortListeners();
    }

    function attachSortListeners() {
        const headers = document.querySelectorAll('th[data-sort]');
        headers.forEach(th => {
            th.style.cursor = 'pointer';
            th.addEventListener('click', () => {
                const column = th.dataset.sort;
                if (currentSort.column === column) {
                    currentSort.asc = !currentSort.asc;
                } else {
                    currentSort.column = column;
                    currentSort.asc = true;
                }
                sortData();
                renderTableHeaders(TAB_CONFIG[currentTab].type);
                renderTableBody(currentData, TAB_CONFIG[currentTab].type);
            });
        });
    }

    function sortData() {
        if (!currentSort.column) return;
        currentData.sort((a, b) => {
            let valA = a[currentSort.column];
            let valB = b[currentSort.column];
            
            if (valA === null || valA === undefined) return currentSort.asc ? 1 : -1;
            if (valB === null || valB === undefined) return currentSort.asc ? -1 : 1;
            
            if (typeof valA === 'string') valA = valA.toLowerCase();
            if (typeof valB === 'string') valB = valB.toLowerCase();
            
            if (valA < valB) return currentSort.asc ? -1 : 1;
            if (valA > valB) return currentSort.asc ? 1 : -1;
            return 0;
        });
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
                let datePart = '', timePart = '';
                const pub = item.published_at || '';
                if (pub.includes('T')) {
                    datePart = pub.split('T')[0];
                    timePart = pub.split('T')[1].split('.')[0];
                } else if (pub.includes(' ')) {
                    datePart = pub.split(' ')[0];
                    timePart = pub.split(' ')[1].split('.')[0];
                }
                
                let formattedDate = datePart;
                if (datePart) {
                    const parts = datePart.split('-');
                    if (parts.length === 3) formattedDate = `${parts[2]}/${parts[1]}/${parts[0]}`;
                }

                let asset = '-';
                let headlineStr = item.title || "";
                
                // Advanced parsing for B3 News titles
                // Regex matches (TICKER) capturing TICKER cleanly
                const tickerMatch = headlineStr.match(/\(([A-Z0-9]+)\)/);
                if (tickerMatch) {
                    asset = tickerMatch[1]; // WHGR
                    // Remove the ticker part from the headline
                    headlineStr = headlineStr.replace(tickerMatch[0], '').replace(/\s+/g, ' ').trim();
                }

                // Split by " - " to separate Company Name and News Type/Date
                const dashParts = headlineStr.split(' - ');
                let companyName = dashParts[0].trim();
                let newsType = dashParts.length > 1 ? dashParts.slice(1).join(' - ').trim() : '';

                // Clean trailing date/time from the newsType 
                // Matches patterns like " 12/03/2026", "- 12/03/2026 09:00", etc at the end
                newsType = newsType.replace(/\s*-?\s*\d{2}\/\d{2}\/\d{4}(\s+\d{2}:\d{2})?\s*$/, '').trim();

                // Fallback: if there was no dash, the whole thing might be the company name, or just news
                let finalHeadline = '';
                if (newsType) {
                    finalHeadline = `${companyName} - ${newsType}`;
                } else {
                    finalHeadline = companyName;
                    // Try to guess news type from finalHeadline if needed, or leave it
                    newsType = companyName; // purely for fallback filtering
                }
                
                // Filtering Logic
                if (currentNewsType && currentNewsType !== '') {
                    if (!newsType.toLowerCase().includes(currentNewsType)) {
                        return ''; // Skip this row
                    }
                }

                return `<tr>
                    <td style="white-space:nowrap">${formattedDate}</td>
                    <td style="white-space:nowrap">${timePart}</td>
                    <td style="font-weight:bold; color:var(--text-secondary)">${asset}</td>
                    <td><a href="${item.link}" target="_blank" style="color:var(--text-primary); text-decoration:underline;">${finalHeadline}</a></td>
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
                const fcfClass = (item.p_fcf > 0 && item.p_fcf <= 15) ? 'good-metric' : ((item.p_fcf < 0 || item.p_fcf > 30) ? 'bad-metric' : '');
                const peClass = (item.pe > 0 && item.pe <= 15) ? 'good-metric' : ((item.pe < 0 || item.pe > 25) ? 'bad-metric' : '');
                const pegClass = (item.peg > 0 && item.peg <= 1) ? 'good-metric' : ((item.peg < 0 || item.peg > 2) ? 'bad-metric' : '');
                const debtClass = item.debt < 1 && item.debt !== null ? 'good-metric' : (item.debt > 2 ? 'bad-metric' : '');
                const dyClass = item.dividend_yield > 5 ? 'good-metric' : '';

                rowHTML += `
                    <td class="${fcfClass}">${item.p_fcf !== null && item.p_fcf !== undefined ? item.p_fcf.toFixed(2) : '-'}</td>
                    <td class="${'good-metric'}">${formatNumber(item.eps)}</td>
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
