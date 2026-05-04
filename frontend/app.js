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
    const exportBtn = document.getElementById('export-btn');
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

    if (newsDatePicker) {
        flatpickr(newsDatePicker, {
            dateFormat: "d/m/Y",
            allowInput: true
        });
    }

    let currentTab = 'br-stocks';
    let currentData = [];
    let currentSort = { column: null, asc: true };
    let currentNewsType = '';

    const TAB_CONFIG = {
        'br-stocks': { title: 'BR Stocks', subtitle: 'Focus on Low P/FCF, EPS, low Debt, P/E, and PEG < 1', type: 'stock' },
        'us-stocks': { title: 'US Stocks', subtitle: 'Focus on Low P/FCF, EPS, low Debt, P/E, and PEG < 1', type: 'stock' },
        'br-fiis': { title: 'BR FIIs', subtitle: 'Focus on High Dividend Yield and Price to Book (P/VPA)', type: 'reit' },
        'us-reits': { title: 'US REITs', subtitle: 'Focus on Low P/FCF, EPS, low Debt, P/E, and PEG < 1', type: 'stock' },
        'b3-indices': { title: 'B3 Indices Configuration', subtitle: 'Select active index for BR Stocks tab', type: 'config' },
        'market-news': { title: 'Market News Feed', subtitle: 'Latest corporate and economic announcements (B3)', type: 'news' }
    };

    function getEndpoint(tabId) {
        let manualTickers = '';
        if ((tabId === 'br-stocks' || tabId === 'us-stocks') && manualAssetsCheckbox && manualAssetsCheckbox.checked) {
            manualTickers = manualAssetsTextarea.value.trim().split(/[\\s,]+/).filter(x => x).join(',');
        }

        if (tabId === 'br-stocks') {
            if (manualTickers) return `/stocks/br?tickers=${manualTickers}`;
            const devConf = localStorage.getItem('cfg_br');
            return devConf ? `/stocks/br?tickers=${devConf}` : `/stocks/br?index=${indexSelect.value}`;
        }
        if (tabId === 'us-stocks') {
            if (manualTickers) return `/stocks/us?tickers=${manualTickers}`;
            const devConf = localStorage.getItem('cfg_us');
            return devConf ? `/stocks/us?tickers=${devConf}` : `/stocks/us`;
        }
        if (tabId === 'br-fiis') {
            const devConf = localStorage.getItem('cfg_fiis');
            return devConf ? `/fiis/br?tickers=${devConf}` : `/fiis/br`;
        }
        if (tabId === 'us-reits') {
            const devConf = localStorage.getItem('cfg_reits');
            return devConf ? `/stocks/us?tickers=${devConf}` : `/reits/us`;
        }
        if (tabId === 'market-news') {
            const dateVal = newsDatePicker.value.trim();
            if (dateVal) {
                if (dateVal.includes('-')) {
                    return `/news?date=${dateVal}`;
                }
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
    
    // Sync cache config on boot
    const initCacheHours = localStorage.getItem('cfg_cache_hours');
    if (initCacheHours) {
        fetch(`${API_BASE}/cache/config`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ hours: parseInt(initCacheHours, 10) || 24 })
        }).catch(err => console.error("Failed to sync cache config on boot", err));
    }

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
            // Settings Modal UI bindings
            const settingsBtn = document.getElementById('settings-btn');
            const settingsModal = document.getElementById('settings-modal');
            const settingsSave = document.getElementById('settings-save');
            const settingsCancel = document.getElementById('settings-cancel');
            const clearCacheBtn = document.getElementById('clear-cache-btn');
            const cBr = document.getElementById('config-br-stocks');
            const cUs = document.getElementById('config-us-stocks');
            const cFiis = document.getElementById('config-br-fiis');
            const cReits = document.getElementById('config-us-reits');
            const cCache = document.getElementById('config-cache-hours');

            settingsBtn.addEventListener('click', () => {
                cBr.value = localStorage.getItem('cfg_br') || '';
                cUs.value = localStorage.getItem('cfg_us') || '';
                cFiis.value = localStorage.getItem('cfg_fiis') || '';
                cReits.value = localStorage.getItem('cfg_reits') || '';
                cCache.value = localStorage.getItem('cfg_cache_hours') || '24';
                settingsModal.style.display = 'flex';
            });

            settingsCancel.addEventListener('click', () => settingsModal.style.display = 'none');
            
            settingsSave.addEventListener('click', () => {
                localStorage.setItem('cfg_br', cBr.value.trim());
                localStorage.setItem('cfg_us', cUs.value.trim());
                localStorage.setItem('cfg_fiis', cFiis.value.trim());
                localStorage.setItem('cfg_reits', cReits.value.trim());
                
                const cacheHours = parseInt(cCache.value.trim(), 10) || 24;
                localStorage.setItem('cfg_cache_hours', cacheHours);
                
                fetch(`${API_BASE}/cache/config`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ hours: cacheHours })
                }).catch(err => console.error("Failed to update cache config", err));

                settingsModal.style.display = 'none';
                loadTabData(currentTab);
            });

            clearCacheBtn.addEventListener('click', async () => {
                clearCacheBtn.textContent = 'PURGING...';
                try {
                    await fetch(`${API_BASE}/cache/clear`, { method: 'POST' });
                    clearCacheBtn.textContent = 'CLEARED!';
                    setTimeout(() => { clearCacheBtn.textContent = '[ PURGE CACHE ]'; }, 2000);
                } catch (err) {
                    clearCacheBtn.textContent = 'ERROR';
                }
            });

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

        if (exportBtn) {
            exportBtn.addEventListener('click', () => {
                if (!currentData || currentData.length === 0) {
                    alert('No data to export.');
                    return;
                }
                exportDataToCSV(currentData, TAB_CONFIG[currentTab].type);
            });
        }
    }

    function exportDataToCSV(data, type) {
        if (!data || data.length === 0) return;

        let csvContent = "";
        let headers = [];

        if (type === 'stock') {
            headers = ["Rank", "Ticker", "Name", "Price", "PEG", "P/FCF", "P/E", "EPS", "Debt/EBIT", "ROIC (%)", "ROE (%)", "Net Margin (%)", "Dividend Yield (%)", "Score"];
        } else if (type === 'reit') {
            if (currentTab === 'br-fiis') {
                headers = ["Ticker", "Name", "Price", "Min 52W", "Max 52W", "Dividend Yield (%)", "Val. (12M) (%)", "P/VP", "VP/Cota", "Caixa (%)", "DY CAGR (3y) (%)", "Val. CAGR (3y) (%)", "Cotistas"];
            } else {
                headers = ["Ticker", "Name", "Price", "Dividend Yield (%)", "P/VPA"];
            }
        } else {
            return;
        }

        csvContent += headers.join(";") + "\n";

        const escapeCSV = (val) => {
            if (val === null || val === undefined) return '';
            let str = String(val);
            if (str.includes(';') || str.includes('"') || str.includes('\n')) {
                str = '"' + str.replace(/"/g, '""') + '"';
            }
            return str;
        };

        data.forEach(item => {
            let row = [];
            let nameSub = item.name ? item.name : 'Unknown';

            if (type === 'stock') {
                row.push(escapeCSV(item.final_rank));
                row.push(escapeCSV(item.ticker));
                row.push(escapeCSV(nameSub));
                row.push(escapeCSV(item.price));
                row.push(escapeCSV(item.peg));
                row.push(escapeCSV(item.p_fcf));
                row.push(escapeCSV(item.pe));
                row.push(escapeCSV(item.eps));
                row.push(escapeCSV(item.debt_ebit));
                row.push(escapeCSV(item.roic));
                row.push(escapeCSV(item.roe));
                row.push(escapeCSV(item.net_margin));
                row.push(escapeCSV(item.dividend_yield));
                row.push(escapeCSV(item.rank_score));
            } else if (type === 'reit') {
                row.push(escapeCSV(item.ticker));
                row.push(escapeCSV(nameSub));
                row.push(escapeCSV(item.price));
                if (currentTab === 'br-fiis') {
                    row.push(escapeCSV(item.min_52w));
                    row.push(escapeCSV(item.max_52w));
                    row.push(escapeCSV(item.dividend_yield));
                    row.push(escapeCSV(item.val_12m));
                    row.push(escapeCSV(item.p_vpa));
                    row.push(escapeCSV(item.vp_cota));
                    row.push(escapeCSV(item.caixa));
                    row.push(escapeCSV(item.dy_cagr));
                    row.push(escapeCSV(item.val_cagr));
                    row.push(escapeCSV(item.cotistas));
                } else {
                    row.push(escapeCSV(item.dividend_yield));
                    row.push(escapeCSV(item.p_vpa));
                }
            }
            csvContent += row.join(";") + "\n";
        });

        const blob = new Blob(["\uFEFF" + csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.setAttribute("href", url);
        const filename = `${currentTab}_export_${new Date().toISOString().split('T')[0]}.csv`;
        link.setAttribute("download", filename);
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }

    function calculateRanking(data, type) {
        if (type !== 'stock') return;
        
        data.forEach(item => { item.rank_score = 0; });
        
        const indicators = [
            { key: 'peg', filter: v => v > 0 && v <= 1, sortAsc: true },
            { key: 'p_fcf', filter: v => v > 0, sortAsc: true },
            { key: 'pe', filter: v => v > 0, sortAsc: true },
            { key: 'eps', filter: v => v > 0, sortAsc: false },
            { key: 'debt_ebit', filter: v => v > 0, sortAsc: true },
            { key: 'roic', filter: v => v > 0, sortAsc: false },
            { key: 'roe', filter: v => v > 0, sortAsc: false },
            { key: 'net_margin', filter: v => v > 0, sortAsc: false },
            { key: 'dividend_yield', filter: v => v > 0, sortAsc: false }
        ];
        
        indicators.forEach(ind => {
            let validItems = [];
            let invalidItems = [];
            
            data.forEach(item => {
                const val = item[ind.key];
                if (val !== null && val !== undefined && ind.filter(val)) {
                    validItems.push(item);
                } else {
                    invalidItems.push(item);
                }
            });
            
            validItems.sort((a, b) => {
                let va = a[ind.key];
                let vb = b[ind.key];
                return ind.sortAsc ? (va - vb) : (vb - va);
            });
            
            validItems.forEach((item, index) => {
                item.rank_score += (index + 1);
            });
            
            const invalidPenalty = validItems.length + 1;
            invalidItems.forEach(item => {
                item.rank_score += invalidPenalty;
            });
        });
        
        let sortedByScore = [...data].sort((a, b) => a.rank_score - b.rank_score);
        sortedByScore.forEach((item, index) => {
            item.final_rank = index + 1;
        });
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
            if (exportBtn) exportBtn.style.display = 'none';
        } else {
            newsDatePicker.style.display = 'none';
            if (newsTypeFilter) newsTypeFilter.style.display = 'none';
            if (exportBtn) {
                if (config.type === 'config') {
                    exportBtn.style.display = 'none';
                } else {
                    exportBtn.style.display = 'block';
                }
            }
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
            
            if (config.type === 'stock') {
                calculateRanking(currentData, config.type);
                if (!currentSort.column) {
                    currentSort = { column: 'final_rank', asc: true };
                }
            }
            
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
                <th data-sort="final_rank">Rank${getIcon('final_rank')}</th>
                <th data-sort="ticker">Ticker / Name${getIcon('ticker')}</th>
                <th data-sort="price">Price${getIcon('price')}</th>
                <th data-sort="peg">PEG${getIcon('peg')}</th>
                <th data-sort="p_fcf">P/FCF${getIcon('p_fcf')}</th>
                <th data-sort="pe">P/E${getIcon('pe')}</th>
                <th data-sort="eps">EPS${getIcon('eps')}</th>
                <th data-sort="debt_ebit">Debt/EBIT${getIcon('debt_ebit')}</th>
                <th data-sort="roic">ROIC${getIcon('roic')}</th>
                <th data-sort="roe">ROE${getIcon('roe')}</th>
                <th data-sort="net_margin">Net Mrg${getIcon('net_margin')}</th>
                <th data-sort="dividend_yield">Div. Yield${getIcon('dividend_yield')}</th>
                <th data-sort="rank_score">Score${getIcon('rank_score')}</th>
            `;
        } else if (type === 'reit') {
            if (currentTab === 'br-fiis') {
                tableHeaderRow.innerHTML = `
                    <th data-sort="ticker">Ticker / Name${getIcon('ticker')}</th>
                    <th data-sort="price">Price${getIcon('price')}</th>
                    <th data-sort="min_52w">Min 52W${getIcon('min_52w')}</th>
                    <th data-sort="max_52w">Max 52W${getIcon('max_52w')}</th>
                    <th data-sort="dividend_yield">Div. Yield${getIcon('dividend_yield')}</th>
                    <th data-sort="val_12m">Val.(12M)${getIcon('val_12m')}</th>
                    <th data-sort="p_vpa">P/VP${getIcon('p_vpa')}</th>
                    <th data-sort="vp_cota">VP/Cota${getIcon('vp_cota')}</th>
                    <th data-sort="caixa">Caixa${getIcon('caixa')}</th>
                    <th data-sort="dy_cagr">DY CAGR(3y)${getIcon('dy_cagr')}</th>
                    <th data-sort="val_cagr">Val. CAGR(3y)${getIcon('val_cagr')}</th>
                    <th data-sort="cotistas">Cotistas${getIcon('cotistas')}</th>
                `;
            } else {
                tableHeaderRow.innerHTML = `
                    <th data-sort="ticker">Ticker / Name${getIcon('ticker')}</th>
                    <th data-sort="price">Price${getIcon('price')}</th>
                    <th data-sort="dividend_yield">Div. Yield${getIcon('dividend_yield')}</th>
                    <th data-sort="p_vpa">P/VPA${getIcon('p_vpa')}</th>
                `;
            }
        } else if (type === 'news') {
            tableHeaderRow.innerHTML = `
                <th data-sort="published_at">Date${getIcon('published_at')}</th>
                <th data-sort="published_at">Time${getIcon('published_at')}</th>
                <th data-sort="title">Asset${getIcon('title')}</th>
                <th data-sort="title">Headline${getIcon('title')}</th>
                <th data-sort="title">Type${getIcon('title')}</th>
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
                let actualNewsType = '-';
                
                if (dashParts.length > 1 && dashParts[1].trim() !== '') {
                    actualNewsType = dashParts[1].trim();
                }

                // Smart fallback for unstructured B3 streams if type wasn't found
                if (actualNewsType === '-') {
                    const knownTypes = [
                        'SUMARIO DE DECISOES', 'SUMARIO AGE', 'SUMARIO AGOE', 'SUMARIO AGO',
                        'PROPOSTA DA ADMINISTRACAO', 'PROPOSTA AGE', 'PROPOSTA AGOE', 'PROPOSTA AGO',
                        'EDITAL DE CONVOCACAO', 'EDITAL AGE', 'EDITAL AGOE', 'EDITAL AGO',
                        'ATA DE REUNIAO', 'ATA AGE', 'ATA AGOE', 'ATA AGO', 'ATA RCA', 'ATA',
                        'DEMONSTRACOES FINANCEIRAS', 'DEMONST. FINANC.', 'DEMONSTRACAO FINANCEIRA',
                        'AVISO AOS ACIONISTAS', 'AVISO AOS DEBENTURISTAS', 'AVISO AOS COTISTAS',
                        'FATO RELEVANTE', 'COMUNICADO AO MERCADO', 
                        'INFORME MENSAL', 'INFORME TRIMESTRAL', 'RELATORIO GERENCIAL', 
                        'PROVENTOS'
                    ];
                    
                    // Normalize all spaces, newlines, and tabs into a single space for robust matching
                    const normalizedHeadline = companyName.replace(/\s+/g, ' ');
                    const upperHeadline = normalizedHeadline.toUpperCase();
                    
                    for (const kt of knownTypes) {
                        if (upperHeadline.includes(kt)) {
                            actualNewsType = kt;
                            // Replace keyword in companyName even if it spans across newlines
                            const regexStr = kt.split(' ').join('\\s+');
                            companyName = companyName.replace(new RegExp(regexStr, 'ig'), '').trim();
                            // Clean up dangling dashes, spaces or separators at the end
                            companyName = companyName.replace(/^[-:\s]+|[-:\s]+$/g, '').trim();
                            // Failsafe in case the entire headline was just the Type keyword
                            if (!companyName) companyName = actualNewsType;
                            break;
                        }
                    }
                }

                // Clean trailing dates from news type (like 03/2026 or 12/03/2026)
                actualNewsType = actualNewsType.replace(/\s*-?\s*\d{2}\/\d{2}\/\d{4}(\s+\d{2}:\d{2})?\s*$/, '').trim();
                actualNewsType = actualNewsType.replace(/\s*-?\s*\d{2}\/\d{4}\s*$/, '').trim();
                
                // Fallback filtering check
                let filterStr = (actualNewsType !== '-') ? actualNewsType : companyName;
                if (currentNewsType && currentNewsType !== '') {
                    if (!filterStr.toLowerCase().includes(currentNewsType)) {
                        return ''; // Skip this row
                    }
                }
                
                let finalHeadline = companyName;

                return `<tr>
                    <td style="white-space:nowrap">${formattedDate}</td>
                    <td style="white-space:nowrap">${timePart}</td>
                    <td style="font-weight:bold; color:var(--text-secondary)">${asset}</td>
                    <td><a href="${item.link}" target="_blank" style="color:var(--text-primary); text-decoration:underline;">${finalHeadline}</a></td>
                    <td style="white-space:nowrap; color:var(--accent)">${actualNewsType}</td>
                </tr>`;
            }

            // Normal stock/reit parsing
            const nameSub = item.name ? item.name : 'Unknown';
            let rowHTML = "";

            if (type === 'stock') {
                const fcfClass = (item.p_fcf > 0 && item.p_fcf <= 15) ? 'good-metric' : ((item.p_fcf < 0 || item.p_fcf > 30) ? 'bad-metric' : '');
                const peClass = (item.pe > 0 && item.pe <= 15) ? 'good-metric' : ((item.pe < 0 || item.pe > 25) ? 'bad-metric' : '');
                const pegClass = (item.peg > 0 && item.peg <= 1) ? 'good-metric' : ((item.peg < 0 || item.peg > 2) ? 'bad-metric' : '');
                const dyClass = (item.dividend_yield > 5) ? 'good-metric' : '';
                const debtEbitClass = item.debt_ebit < 3 && item.debt_ebit !== null ? 'good-metric' : (item.debt_ebit > 5 ? 'bad-metric' : '');
                const roicClass = item.roic > 10 ? 'good-metric' : '';
                const roeClass = item.roe > 15 ? 'good-metric' : '';
                const marginClass = item.net_margin > 10 ? 'good-metric' : '';

                let rankIcon = '';
                let rankClass = '';
                if (item.final_rank === 1) { rankIcon = '🏆'; rankClass = 'rank-1'; }
                else if (item.final_rank === 2) { rankIcon = '🏅'; rankClass = 'rank-2'; }
                else if (item.final_rank === 3) { rankIcon = '🥉'; rankClass = 'rank-3'; }
                else if (item.final_rank === 4) { rankIcon = '🎖️'; rankClass = 'rank-4'; }
                else if (item.final_rank === 5) { rankIcon = '🌟'; rankClass = 'rank-5'; }

                rowHTML += `<tr class="${rankClass}">
                    <td style="font-size: 1.1rem; text-align: center; font-weight: bold;">${item.final_rank || '-'} ${rankIcon}</td>
                    <td class="ticker-cell">
                        ${item.ticker}
                        <span class="name-sub">${nameSub}</span>
                    </td>
                    <td>${formatCurrency(item.price)}</td>
                    <td class="${pegClass}">${formatNumber(item.peg)}</td>
                    <td class="${fcfClass}">${item.p_fcf !== null && item.p_fcf !== undefined ? item.p_fcf.toFixed(2) : '-'}</td>
                    <td class="${peClass}">${formatNumber(item.pe)}</td>
                    <td class="${'good-metric'}">${formatNumber(item.eps)}</td>
                    <td class="${debtEbitClass}">${formatNumber(item.debt_ebit)}</td>
                    <td class="${roicClass}">${formatPercent(item.roic)}</td>
                    <td class="${roeClass}">${formatPercent(item.roe)}</td>
                    <td class="${marginClass}">${formatPercent(item.net_margin)}</td>
                    <td class="${dyClass}">${formatPercent(item.dividend_yield)}</td>
                    <td style="font-weight: bold;">${item.rank_score}</td>
                </tr>`;
            } else if (type === 'reit') {
                rowHTML += `<tr>
                <td class="ticker-cell">
                    ${item.ticker}
                    <span class="name-sub">${nameSub}</span>
                </td>
                <td>${formatCurrency(item.price)}</td>
                `;
                if (currentTab === 'br-fiis') {
                    const dyClass = (item.dividend_yield > 6) ? 'good-metric' : '';
                    const pVpaClass = (item.p_vpa < 1 && item.p_vpa > 0) ? 'good-metric' : (item.p_vpa > 1.2 ? 'bad-metric' : '');
                    const colorVal12m = item.val_12m > 0 ? "good-metric" : (item.val_12m < 0 ? "bad-metric" : "");

                    rowHTML += `
                        <td>${item.min_52w !== null && item.min_52w !== undefined ? formatCurrency(item.min_52w) : '-'}</td>
                        <td>${item.max_52w !== null && item.max_52w !== undefined ? formatCurrency(item.max_52w) : '-'}</td>
                        <td class="${dyClass}">${formatPercent(item.dividend_yield)}</td>
                        <td class="${colorVal12m}">${formatPercent(item.val_12m)}</td>
                        <td class="${pVpaClass}">${formatNumber(item.p_vpa)}</td>
                        <td>${item.vp_cota !== null && item.vp_cota !== undefined ? formatCurrency(item.vp_cota) : '-'}</td>
                        <td>${item.caixa !== null && item.caixa !== undefined ? formatPercent(item.caixa) : '-'}</td>
                        <td class="${item.dy_cagr > 0 ? 'good-metric' : ''}">${formatPercent(item.dy_cagr)}</td>
                        <td class="${item.val_cagr > 0 ? 'good-metric' : ''}">${formatPercent(item.val_cagr)}</td>
                        <td>${item.cotistas !== null && item.cotistas !== undefined ? item.cotistas.toLocaleString('pt-BR') : '-'}</td>
                    `;
                } else {
                    const dyClass = (item.dividend_yield > 6) ? 'good-metric' : '';
                    const pVpaClass = (item.p_vpa < 1 && item.p_vpa > 0) ? 'good-metric' : (item.p_vpa > 1.2 ? 'bad-metric' : '');

                    rowHTML += `
                        <td class="${dyClass}">${formatPercent(item.dividend_yield)}</td>
                        <td class="${pVpaClass}">${formatNumber(item.p_vpa)}</td>
                    `;
                }
            }
            return rowHTML + `</tr>`;
        }).join('');

        tableBody.innerHTML = rows;
    }
});
