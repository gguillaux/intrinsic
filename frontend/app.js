document.addEventListener('DOMContentLoaded', () => {
    const API_BASE = "http://localhost:8000/api";
    
    // UI Elements
    const navItems = document.querySelectorAll('.nav-item');
    const pageTitle = document.getElementById('page-title');
    const pageSubtitle = document.getElementById('page-subtitle');
    const tableHeaderRow = document.getElementById('table-header-row');
    const tableFilterRow = document.getElementById('table-filter-row');
    const tableBody = document.getElementById('table-body');
    const loader = document.getElementById('loader');
    const tableContainer = document.getElementById('table-view');
    const refreshBtn = document.getElementById('refresh-btn');
    const exportBtn = document.getElementById('export-btn');
    const searchInput = document.getElementById('search-input');
    const indexSelect = document.getElementById('index-select');
    const configSection = document.getElementById('config-section');
    const dataSection = document.getElementById('data-section');
    const aboutSection = document.getElementById('about-section');
    const aboutContent = document.getElementById('about-content');
    const filtersContainer = document.getElementById('filters-container');
    const newsDatePicker = document.getElementById('news-date-picker');
    const newsTypeFilter = document.getElementById('news-type-filter');
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const viewToggleBtn = document.getElementById('view-toggle-btn');
    const valuationGrid = document.getElementById('valuation-grid');
    
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
    let activeFilters = {};
    let currentViewMode = 'table'; // 'table' or 'grid'
    let donutChartInstances = []; // Track Chart.js instances for cleanup

    const TAB_CONFIG = {
        'br-stocks': { title: 'BR Stocks', subtitle: 'Focus on Low P/FCF, EPS, low Debt, P/E, and PEG < 1', type: 'stock' },
        'us-stocks': { title: 'US Stocks', subtitle: 'Focus on Low P/FCF, EPS, low Debt, P/E, and PEG < 1', type: 'stock' },
        'br-fiis': { title: 'BR FIIs', subtitle: 'Focus on High Dividend Yield and Price to Book (P/VPA)', type: 'reit' },
        'us-reits': { title: 'US REITs', subtitle: 'Focus on Low P/FCF, EPS, low Debt, P/E, and PEG < 1', type: 'stock' },
        'b3-indices': { title: 'B3 Indices Configuration', subtitle: 'Select active index for BR Stocks tab', type: 'config' },
        'market-news': { title: 'Market News Feed', subtitle: 'Latest corporate and economic announcements (B3)', type: 'news' },
        'about-app': { title: 'About Intrinsic', subtitle: 'Architecture, features, and documentation', type: 'about' }
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

    // Sidebar collapse toggle
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');

    if (localStorage.getItem('sidebar_collapsed') === 'true') {
        sidebar.classList.add('collapsed');
        sidebarToggle.textContent = '✕';
    }

    sidebarToggle.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
        const isCollapsed = sidebar.classList.contains('collapsed');
        sidebarToggle.textContent = isCollapsed ? '✕' : '☰';
        localStorage.setItem('sidebar_collapsed', isCollapsed);
    });

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
                renderTableBody(getFilteredData(), TAB_CONFIG[currentTab].type);
            });
        }

        searchInput.addEventListener('input', (e) => {
            renderTableBody(getFilteredData(), TAB_CONFIG[currentTab].type);
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
            const cNtnb = document.getElementById('config-ntnb');
            const cSpread = document.getElementById('config-spread');
            const cIpca = document.getElementById('config-ipca');
            const cSelic = document.getElementById('config-selic');

            settingsBtn.addEventListener('click', () => {
                cBr.value = localStorage.getItem('cfg_br') || '';
                cUs.value = localStorage.getItem('cfg_us') || '';
                cFiis.value = localStorage.getItem('cfg_fiis') || '';
                cReits.value = localStorage.getItem('cfg_reits') || '';
                cCache.value = localStorage.getItem('cfg_cache_hours') || '24';
                cNtnb.value = localStorage.getItem('cfg_ntnb') || '';
                cSpread.value = localStorage.getItem('cfg_spread') || '';
                cIpca.value = localStorage.getItem('cfg_ipca') || '';
                cSelic.value = localStorage.getItem('cfg_selic') || '';
                settingsModal.style.display = 'flex';
            });

            settingsCancel.addEventListener('click', () => settingsModal.style.display = 'none');
            
            settingsSave.addEventListener('click', () => {
                localStorage.setItem('cfg_br', cBr.value.trim());
                localStorage.setItem('cfg_us', cUs.value.trim());
                localStorage.setItem('cfg_fiis', cFiis.value.trim());
                localStorage.setItem('cfg_reits', cReits.value.trim());
                localStorage.setItem('cfg_ntnb', cNtnb.value.trim());
                localStorage.setItem('cfg_spread', cSpread.value.trim());
                localStorage.setItem('cfg_ipca', cIpca.value.trim());
                localStorage.setItem('cfg_selic', cSelic.value.trim());
                
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

        if (viewToggleBtn) {
            viewToggleBtn.addEventListener('click', () => {
                currentViewMode = currentViewMode === 'table' ? 'grid' : 'table';
                applyViewMode();
            });
        }
    }

    function exportDataToCSV(data, type) {
        if (!data || data.length === 0) return;

        let csvContent = "";
        let headers = [];

        if (type === 'stock') {
            headers = ["Rank", "Ticker", "Name", "Price", "PEG", "P/FCF", "P/E", "P/A", "EPS", "Debt/EBIT", "ROIC (%)", "ROE (%)", "Net Margin (%)", "Dividend Yield (%)", "Score"];
        } else if (type === 'reit') {
            if (currentTab === 'br-fiis') {
                headers = ["Rank", "Ticker", "Name", "Price", "Ceiling Price", "Dividend Yield (%)", "P/VP", "DY CAGR (3y) (%)", "Min 52W", "Max 52W", "Val. (12M) (%)", "VP/Cota", "Caixa (%)", "Val. CAGR (3y) (%)", "Cotistas", "Sharpe Ratio", "Score"];
            } else {
                headers = ["Ticker", "Name", "Price", "Dividend Yield (%)", "P/VPA", "P/A"];
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
                row.push(escapeCSV(item.p_a));
                row.push(escapeCSV(item.eps));
                row.push(escapeCSV(item.debt_ebit));
                row.push(escapeCSV(item.roic));
                row.push(escapeCSV(item.roe));
                row.push(escapeCSV(item.net_margin));
                row.push(escapeCSV(item.dividend_yield));
                row.push(escapeCSV(item.rank_score));
            } else if (type === 'reit') {
                if (currentTab === 'br-fiis') {
                    row.push(escapeCSV(item.final_rank));
                }
                row.push(escapeCSV(item.ticker));
                row.push(escapeCSV(nameSub));
                row.push(escapeCSV(item.price));
                if (currentTab === 'br-fiis') {
                    row.push(escapeCSV(item.ceiling_price));
                    row.push(escapeCSV(item.dividend_yield));
                    row.push(escapeCSV(item.p_vpa));
                    row.push(escapeCSV(item.dy_cagr));
                    row.push(escapeCSV(item.min_52w));
                    row.push(escapeCSV(item.max_52w));
                    row.push(escapeCSV(item.val_12m));
                    row.push(escapeCSV(item.vp_cota));
                    row.push(escapeCSV(item.caixa));
                    row.push(escapeCSV(item.val_cagr));
                    row.push(escapeCSV(item.cotistas));
                    row.push(escapeCSV(item.sharpe_ratio));
                    row.push(escapeCSV(item.rank_score));
                } else {
                    row.push(escapeCSV(item.dividend_yield));
                    row.push(escapeCSV(item.p_vpa));
                    row.push(escapeCSV(item.p_a));
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
        if (type !== 'stock' && type !== 'reit') return;
        
        data.forEach(item => { item.rank_score = 0; });
        
        let indicators = [];
        if (type === 'stock') {
            indicators = [
                { key: 'peg', filter: v => v > 0 && v <= 1, sortAsc: true, weight: 1 },
                { key: 'p_fcf', filter: v => v > 0, sortAsc: true, weight: 1 },
                { key: 'pe', filter: v => v > 0, sortAsc: true, weight: 1 },
                { key: 'eps', filter: v => v > 0, sortAsc: false, weight: 1 },
                { key: 'debt_ebit', filter: v => v > 0, sortAsc: true, weight: 1 },
                { key: 'roic', filter: v => v > 0, sortAsc: false, weight: 1 },
                { key: 'roe', filter: v => v > 0, sortAsc: false, weight: 1 },
                { key: 'net_margin', filter: v => v > 0, sortAsc: false, weight: 1 },
                { key: 'dividend_yield', filter: v => v > 0, sortAsc: false, weight: 1 }
            ];
        } else if (type === 'reit') {
            indicators = [
                { key: 'dy_cagr', filter: v => v !== null && v !== undefined && v !== '-', sortAsc: false, weight: 0.35 },
                { key: 'sharpe_ratio', filter: v => v !== null && v !== undefined && v !== '-', sortAsc: false, weight: 0.35 },
                { key: 'dividend_yield', filter: v => v !== null && v !== undefined && v !== '-', sortAsc: false, weight: 0.15 },
                { key: 'p_vpa', filter: v => v !== null && v !== undefined && v !== '-', sortAsc: true, weight: 0.15 }
            ];
        }
        
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
                item.rank_score += (index + 1) * ind.weight;
            });
            
            const invalidPenalty = validItems.length + 1;
            invalidItems.forEach(item => {
                item.rank_score += invalidPenalty * ind.weight;
            });
        });
        
        let sortedByScore = [...data].sort((a, b) => a.rank_score - b.rank_score);
        sortedByScore.forEach((item, index) => {
            item.final_rank = index + 1;
            item.rank_score = parseFloat(item.rank_score.toFixed(2));
        });
    }

    async function loadTabData(tabId) {
        const config = TAB_CONFIG[tabId];
        
        pageTitle.textContent = config.title;
        pageSubtitle.textContent = config.subtitle;
        
        // Handle section visibility
        if (config.type === 'config') {
            configSection.style.display = 'block';
            dataSection.style.display = 'none';
            if (aboutSection) aboutSection.style.display = 'none';
            filtersContainer.style.display = 'none';
            if (manualAssetsSection) manualAssetsSection.style.display = 'none';
            return;
        } else if (config.type === 'about') {
            configSection.style.display = 'none';
            dataSection.style.display = 'none';
            if (aboutSection) aboutSection.style.display = 'block';
            filtersContainer.style.display = 'none';
            if (manualAssetsSection) manualAssetsSection.style.display = 'none';
            loadAboutPage();
            return;
        } else {
            configSection.style.display = 'none';
            dataSection.style.display = 'block';
            if (aboutSection) aboutSection.style.display = 'none';
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
            if (viewToggleBtn) viewToggleBtn.style.display = 'inline-block';
        } else {
            if (manualAssetsSection) manualAssetsSection.style.display = 'none';
            if (viewToggleBtn) viewToggleBtn.style.display = 'none';
            currentViewMode = 'table'; // Reset to table for non-stock tabs
        }

        tableContainer.style.display = 'none';
        if (valuationGrid) valuationGrid.style.display = 'none';
        loader.style.display = 'flex';
        tableBody.innerHTML = '';
        searchInput.value = '';
        activeFilters = {};
        currentSort = { column: null, asc: true };

        try {
            renderTableHeaders(config.type);
            
            const endpoint = getEndpoint(tabId);
            const response = await fetch(`${API_BASE}${endpoint}`);
            if (!response.ok) throw new Error("Network response was not ok");
            
            const data = await response.json();
            
            if (tabId === 'br-fiis') {
                const ntnb = parseFloat(localStorage.getItem('cfg_ntnb')) || 6.00;
                const spread = parseFloat(localStorage.getItem('cfg_spread')) || 4.00;
                const selic = parseFloat(localStorage.getItem('cfg_selic')) || 10.50;
                const denom = ntnb + spread;
                data.forEach(item => {
                    item.ceiling_price = (denom !== 0 && item.price != null && item.dividend_yield != null) 
                        ? ((item.price * item.dividend_yield) / denom) 
                        : null;
                        
                    if (item.min_52w && item.max_52w && item.min_52w > 0 && item.val_cagr !== null) {
                        const lnHL = Math.log(item.max_52w / item.min_52w);
                        const parkinsonVol = (1 / (2 * Math.sqrt(Math.LN2))) * lnHL;
                        const returnDec = item.val_cagr / 100;
                        const selicDec = selic / 100;
                        if (parkinsonVol > 0) {
                            item.sharpe_ratio = (returnDec - selicDec) / parkinsonVol;
                        } else {
                            item.sharpe_ratio = null;
                        }
                    } else {
                        item.sharpe_ratio = null;
                    }
                });
            }
            
            if (tabId === 'market-news') {
                data.forEach(item => {
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
                    
                    const tickerMatch = headlineStr.match(/\(([A-Z0-9]+)\)/);
                    if (tickerMatch) {
                        asset = tickerMatch[1];
                        headlineStr = headlineStr.replace(tickerMatch[0], '').replace(/\s+/g, ' ').trim();
                    }

                    const dashParts = headlineStr.split(' - ');
                    let companyName = dashParts[0].trim();
                    let actualNewsType = '-';
                    
                    if (dashParts.length > 1 && dashParts[1].trim() !== '') {
                        actualNewsType = dashParts[1].trim();
                    }

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
                        
                        const upperHeadline = companyName.toUpperCase();
                        for (const kt of knownTypes) {
                            if (upperHeadline.includes(kt)) {
                                actualNewsType = kt;
                                const regexStr = kt.split(' ').join('\\s+');
                                companyName = companyName.replace(new RegExp(regexStr, 'ig'), '').trim();
                                companyName = companyName.replace(/^[-:\s]+|[-:\s]+$/g, '').trim();
                                if (!companyName) companyName = actualNewsType;
                                break;
                            }
                        }
                    }

                    actualNewsType = actualNewsType.replace(/\s*-?\s*\d{2}\/\d{2}\/\d{4}(\s+\d{2}:\d{2})?\s*$/, '').trim();
                    actualNewsType = actualNewsType.replace(/\s*-?\s*\d{2}\/\d{4}\s*$/, '').trim();

                    item.parsedDate = formattedDate;
                    item.parsedTime = timePart;
                    item.parsedAsset = asset;
                    item.parsedHeadline = companyName;
                    item.parsedType = actualNewsType;
                });
            }
            
            currentData = data;
            
            if (config.type === 'stock' || (config.type === 'reit' && currentTab === 'br-fiis')) {
                calculateRanking(currentData, config.type);
                if (!currentSort.column) {
                    currentSort = { column: 'final_rank', asc: true };
                }
            }
            
            if (currentSort.column) sortData();
            renderTableBody(getFilteredData(), config.type);
            applyViewMode();
        } catch (error) {
            tableBody.innerHTML = `<tr><td colspan="10" class="bad-metric" style="text-align: center;">Error fetching data: ${error.message}</td></tr>`;
            tableContainer.style.display = 'block';
        } finally {
            loader.style.display = 'none';
        }
    }

    function applyViewMode() {
        const isStock = TAB_CONFIG[currentTab]?.type === 'stock';
        if (!isStock || currentViewMode === 'table') {
            tableContainer.style.display = 'block';
            if (valuationGrid) valuationGrid.style.display = 'none';
            if (viewToggleBtn) {
                viewToggleBtn.textContent = '\uD83C\uDF69 GRID';
                viewToggleBtn.classList.remove('active');
            }
        } else {
            tableContainer.style.display = 'none';
            if (valuationGrid) {
                valuationGrid.style.display = 'grid';
                renderValuationGrid(getFilteredData());
            }
            if (viewToggleBtn) {
                viewToggleBtn.textContent = '\uD83D\uDCCA TABLE';
                viewToggleBtn.classList.add('active');
            }
        }
    }

    function renderValuationGrid(data) {
        if (!valuationGrid) return;

        // Destroy previous Chart.js instances
        donutChartInstances.forEach(c => c.destroy());
        donutChartInstances = [];

        // Sort by deep value: lowest positive P/E first (more earnings per market cap)
        const sorted = [...data].sort((a, b) => {
            const peA = (a.pe != null && a.pe > 0) ? a.pe : Infinity;
            const peB = (b.pe != null && b.pe > 0) ? b.pe : Infinity;
            if (peA !== peB) return peA - peB;
            const psA = (a.p_s != null && a.p_s > 0) ? a.p_s : Infinity;
            const psB = (b.p_s != null && b.p_s > 0) ? b.p_s : Infinity;
            return psA - psB;
        });

        const formatMktCap = (val) => {
            if (val == null) return '-';
            if (val >= 1e12) return `${(val / 1e12).toFixed(2)} T`;
            if (val >= 1e9) return `${(val / 1e9).toFixed(2)} B`;
            if (val >= 1e6) return `${(val / 1e6).toFixed(0)} M`;
            return val.toLocaleString();
        };

        valuationGrid.innerHTML = sorted.map((item, idx) => {
            const hasData = item.market_cap && ((item.pe && item.pe > 0) || (item.p_s && item.p_s > 0));
            const isDeepValue = item.pe != null && item.pe > 0 && item.pe <= 10;
            const deepClass = isDeepValue ? 'deep-value-card' : '';
            const peValClass = item.pe != null ? (item.pe > 0 && item.pe <= 10 ? 'deep-value' : (item.pe > 25 || item.pe < 0 ? 'overvalued' : '')) : '';
            const psValClass = item.p_s != null ? (item.p_s > 0 && item.p_s <= 1 ? 'deep-value' : (item.p_s > 5 ? 'overvalued' : '')) : '';

            const peDisplay = item.pe != null ? `${item.pe.toFixed(2)}x` : '-';
            const psDisplay = item.p_s != null ? `${item.p_s.toFixed(2)}x` : '-';
            const name = item.name ? escapeHTML(item.name) : 'Unknown';

            let rankBadge = '';
            if (item.final_rank) {
                let icon = '';
                if (item.final_rank === 1) icon = '\uD83C\uDFC6';
                else if (item.final_rank === 2) icon = '\uD83C\uDFC5';
                else if (item.final_rank === 3) icon = '\uD83E\uDD49';
                rankBadge = `<span class="valuation-card-rank">#${item.final_rank} ${icon}</span>`;
            }

            return `
                <div class="valuation-card ${deepClass}" data-idx="${idx}">
                    <div class="valuation-card-header">
                        <div>
                            <div class="valuation-card-ticker">${item.ticker}</div>
                            <div class="valuation-card-name">${name}</div>
                        </div>
                        ${rankBadge}
                    </div>
                    <div class="valuation-card-body">
                        ${hasData ? `
                            <div class="valuation-donut-container">
                                <canvas id="donut-${idx}" width="130" height="130"></canvas>
                                <div class="valuation-donut-center">${formatMktCap(item.market_cap)}</div>
                            </div>
                        ` : `
                            <div class="valuation-no-data">No valuation data</div>
                        `}
                        <div class="valuation-metrics">
                            <div class="valuation-metric-row">
                                <span class="valuation-metric-label">P/E ratio</span>
                                <span class="valuation-metric-value ${peValClass}">${peDisplay}</span>
                            </div>
                            <div class="valuation-metric-row">
                                <span class="valuation-metric-label">P/S ratio</span>
                                <span class="valuation-metric-value ${psValClass}">${psDisplay}</span>
                            </div>
                            <div class="valuation-metric-row">
                                <span class="valuation-metric-label">P/FCF</span>
                                <span class="valuation-metric-value ${item.p_fcf != null ? (item.p_fcf > 0 && item.p_fcf <= 15 ? 'deep-value' : (item.p_fcf > 30 || item.p_fcf < 0 ? 'overvalued' : '')) : ''}">${item.p_fcf != null ? item.p_fcf.toFixed(2) + 'x' : '-'}</span>
                            </div>
                            <div class="valuation-metric-row">
                                <span class="valuation-metric-label">Price</span>
                                <span class="valuation-metric-value">${item.price != null ? '$' + item.price.toFixed(2) : '-'}</span>
                            </div>
                        </div>
                    </div>
                    <div class="valuation-card-legend">
                        <span class="valuation-legend-item"><span class="valuation-legend-dot" style="background:#3a3a3a"></span> Market Cap</span>
                        <span class="valuation-legend-item"><span class="valuation-legend-dot" style="background:#2ec4b6"></span> Net Income</span>
                        <span class="valuation-legend-item"><span class="valuation-legend-dot" style="background:#5b8bf5"></span> Revenue</span>
                        <span class="valuation-legend-item"><span class="valuation-legend-dot" style="background:#c084fc"></span> FCF</span>
                    </div>
                </div>
            `;
        }).join('');

        // Create Chart.js donut charts — three concentric rings
        // Outer ring: Revenue vs Market Cap (P/S ratio)
        // Middle ring: Net Income vs Market Cap (P/E ratio)
        // Inner ring: Free Cash Flow vs Market Cap (P/FCF ratio)
        sorted.forEach((item, idx) => {
            const canvas = document.getElementById(`donut-${idx}`);
            if (!canvas) return;

            const marketCap = item.market_cap;
            if (!marketCap) return;

            const netIncome = (item.pe && item.pe > 0) ? marketCap / item.pe : 0;
            const revenue = (item.p_s && item.p_s > 0) ? marketCap / item.p_s : 0;
            const fcf = (item.p_fcf && item.p_fcf > 0) ? marketCap / item.p_fcf : 0;

            // Each ring shows its value as a proportion of market cap
            const netIncomeRatio = netIncome > 0 ? Math.min(netIncome / marketCap, 1) : 0;
            const revenueRatio = revenue > 0 ? Math.min(revenue / marketCap, 1) : 0;
            const fcfRatio = fcf > 0 ? Math.min(fcf / marketCap, 1) : 0;

            const chart = new Chart(canvas.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: ['Value', 'Market Cap'],
                    datasets: [
                        {
                            // Outer ring — Revenue (P/S)
                            label: 'Revenue',
                            data: [revenueRatio, 1 - revenueRatio],
                            backgroundColor: ['#5b8bf5', '#3a3a3a'],
                            borderColor: ['#4a7ae0', '#2a2a2a'],
                            borderWidth: 1,
                            hoverBorderWidth: 2,
                            hoverBorderColor: ['#6fa0ff', '#555'],
                            weight: 1,
                        },
                        {
                            // Middle ring — Net Income (P/E)
                            label: 'Net Income',
                            data: [netIncomeRatio, 1 - netIncomeRatio],
                            backgroundColor: ['#2ec4b6', '#3a3a3a'],
                            borderColor: ['#24a89a', '#2a2a2a'],
                            borderWidth: 1,
                            hoverBorderWidth: 2,
                            hoverBorderColor: ['#3ed8c8', '#555'],
                            weight: 1,
                        },
                        {
                            // Inner ring — Free Cash Flow (P/FCF)
                            label: 'FCF',
                            data: [fcfRatio, 1 - fcfRatio],
                            backgroundColor: ['#c084fc', '#3a3a3a'],
                            borderColor: ['#a855f7', '#2a2a2a'],
                            borderWidth: 1,
                            hoverBorderWidth: 2,
                            hoverBorderColor: ['#d8b4fe', '#555'],
                            weight: 1,
                        }
                    ]
                },
                options: {
                    responsive: false,
                    cutout: '40%',
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: '#1a1a1a',
                            titleFont: { family: 'Fira Code', size: 11 },
                            bodyFont: { family: 'Fira Code', size: 11 },
                            borderColor: '#333',
                            borderWidth: 1,
                            callbacks: {
                                title: function(tooltipItems) {
                                    const dsIdx = tooltipItems[0].datasetIndex;
                                    const titles = ['P/S (Revenue)', 'P/E (Net Income)', 'P/FCF (Free Cash Flow)'];
                                    return titles[dsIdx] || '';
                                },
                                label: function(ctx) {
                                    if (ctx.dataIndex === 1) return ' Market Cap (remaining)';
                                    const pct = (ctx.raw * 100).toFixed(1);
                                    const labels = ['Revenue', 'Net Income', 'FCF'];
                                    return ` ${labels[ctx.datasetIndex]}: ${pct}% of Mkt Cap`;
                                }
                            }
                        }
                    },
                    animation: {
                        animateRotate: true,
                        duration: 800
                    }
                }
            });
            donutChartInstances.push(chart);
        });
    }

    function getExternalLinksHTML(ticker) {
        const cleanTicker = ticker.replace('.SA', '');
        const isBR = currentTab === 'br-stocks' || currentTab === 'br-fiis';
        const isUSReit = currentTab === 'us-reits';
        const isUSStock = currentTab === 'us-stocks';

        // Resolve asset type paths per tab
        let assetTypeSI, assetTypeI10;
        if (currentTab === 'br-fiis') { assetTypeSI = 'fundos-imobiliarios'; assetTypeI10 = 'fiis'; }
        else if (isUSReit)            { assetTypeSI = 'reits';               assetTypeI10 = 'reits'; }
        else if (isUSStock)           { assetTypeSI = 'acoes/eua';           assetTypeI10 = 'stocks'; }
        else                          { assetTypeSI = 'acoes';               assetTypeI10 = 'acoes'; }

        // SVG icons
        const siIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20V10"/><path d="M18 20V4"/><path d="M6 20v-4"/></svg>`;
        const i10Icon = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>`;
        const tvIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>`;

        let links = '';
        if (isBR || isUSReit || isUSStock) {
            links += `<a href="https://statusinvest.com.br/${assetTypeSI}/${cleanTicker.toLowerCase()}" target="_blank" rel="noopener" class="ext-link ext-link-si" title="StatusInvest">${siIcon}</a>`;
            links += `<a href="https://investidor10.com.br/${assetTypeI10}/${cleanTicker.toLowerCase()}/" target="_blank" rel="noopener" class="ext-link ext-link-i10" title="Investidor10">${i10Icon}</a>`;
        }
        const tvExchange = isBR ? `BMFBOVESPA-${cleanTicker}` : cleanTicker;
        links += `<a href="https://www.tradingview.com/symbols/${tvExchange}/forecast/" target="_blank" rel="noopener" class="ext-link ext-link-tv" title="TradingView Forecast">${tvIcon}</a>`;
        return `<td class="links-cell">${links}</td>`;
    }

    function escapeHTML(str) {
        if (str == null) return '';
        const div = document.createElement('div');
        div.textContent = String(str);
        return div.innerHTML;
    }

    function getFilteredData() {
        const globalTerm = searchInput.value.trim().toLowerCase();
        
        return currentData.filter(item => {
            // 1. Global Search Filter
            if (globalTerm) {
                let searchStr = '';
                if (TAB_CONFIG[currentTab].type === 'news') {
                    searchStr = `${item.parsedDate} ${item.parsedTime} ${item.parsedAsset} ${item.parsedHeadline} ${item.parsedType}`.toLowerCase();
                } else {
                    searchStr = Object.values(item).join(' ').toLowerCase();
                }
                if (!searchStr.includes(globalTerm)) {
                    return false;
                }
            }

            // 2. Column-specific Header Filters
            for (const [col, filterVal] of Object.entries(activeFilters)) {
                if (!filterVal || filterVal.trim() === '') continue;

                const term = filterVal.trim();
                const termLower = term.toLowerCase();
                
                if (col === 'ticker') {
                    const name = (item.name || '').toLowerCase();
                    const ticker = (item.ticker || '').toLowerCase();
                    if (!ticker.includes(termLower) && !name.includes(termLower)) {
                        return false;
                    }
                    continue;
                }

                const val = item[col];
                if (val === null || val === undefined) {
                    return false;
                }

                // Numeric comparison
                const numVal = parseFloat(val);
                if (!isNaN(numVal)) {
                    const firstChar = term[0];
                    if (firstChar === '>' || firstChar === '<' || firstChar === '=') {
                        let op = '';
                        let targetStr = term;
                        if (term.startsWith('>=') || term.startsWith('<=')) {
                            op = term.substring(0, 2);
                            targetStr = term.substring(2);
                        } else {
                            op = term.substring(0, 1);
                            targetStr = term.substring(1);
                        }

                        const targetNum = parseFloat(targetStr);
                        if (!isNaN(targetNum)) {
                            if (op === '>') { if (numVal <= targetNum) return false; }
                            else if (op === '<') { if (numVal >= targetNum) return false; }
                            else if (op === '>=') { if (numVal < targetNum) return false; }
                            else if (op === '<=') { if (numVal > targetNum) return false; }
                            else if (op === '=') { if (numVal !== targetNum) return false; }
                            continue;
                        }
                    }
                }

                // Default string matching
                const valStr = String(val).toLowerCase();
                if (!valStr.includes(termLower)) {
                    return false;
                }
            }

            return true;
        });
    }

    function attachFilterListeners() {
        const filterInputs = document.querySelectorAll('.header-filter-input');
        filterInputs.forEach(input => {
            input.addEventListener('input', (e) => {
                const col = input.dataset.col;
                activeFilters[col] = input.value;
                renderTableBody(getFilteredData(), TAB_CONFIG[currentTab].type);
            });
            input.addEventListener('click', (e) => e.stopPropagation());
            input.addEventListener('mousedown', (e) => e.stopPropagation());
        });
    }

    function renderTableHeaders(type) {
        const getIcon = (col) => {
            if (currentSort.column !== col) return '';
            return currentSort.asc ? ' <span class="sort-icon">▲</span>' : ' <span class="sort-icon">▼</span>';
        };

        const getFilterInput = (col) => {
            const val = activeFilters[col] || '';
            return `<input type="text" class="header-filter-input" data-col="${col}" value="${escapeHTML(val)}" placeholder="Filter..">`;
        };

        if (type === 'stock') {
            tableHeaderRow.innerHTML = `
                <th data-sort="final_rank">Rank${getIcon('final_rank')}</th>
                <th data-sort="ticker">Ticker / Name${getIcon('ticker')}</th>
                <th data-sort="price">Price${getIcon('price')}</th>
                <th data-sort="peg">PEG${getIcon('peg')}</th>
                <th data-sort="p_fcf">P/FCF${getIcon('p_fcf')}</th>
                <th data-sort="pe">P/E${getIcon('pe')}</th>
                <th data-sort="p_a">P/A${getIcon('p_a')}</th>
                <th data-sort="eps">EPS${getIcon('eps')}</th>
                <th data-sort="debt_ebit">Debt/EBIT${getIcon('debt_ebit')}</th>
                <th data-sort="roic">ROIC${getIcon('roic')}</th>
                <th data-sort="roe">ROE${getIcon('roe')}</th>
                <th data-sort="net_margin">Net Mrg${getIcon('net_margin')}</th>
                <th data-sort="dividend_yield">Div. Yield${getIcon('dividend_yield')}</th>
                <th data-sort="rank_score">Score${getIcon('rank_score')}</th>
                <th>Links</th>
            `;

            tableFilterRow.innerHTML = `
                <th>${getFilterInput('final_rank')}</th>
                <th>${getFilterInput('ticker')}</th>
                <th>${getFilterInput('price')}</th>
                <th>${getFilterInput('peg')}</th>
                <th>${getFilterInput('p_fcf')}</th>
                <th>${getFilterInput('pe')}</th>
                <th>${getFilterInput('p_a')}</th>
                <th>${getFilterInput('eps')}</th>
                <th>${getFilterInput('debt_ebit')}</th>
                <th>${getFilterInput('roic')}</th>
                <th>${getFilterInput('roe')}</th>
                <th>${getFilterInput('net_margin')}</th>
                <th>${getFilterInput('dividend_yield')}</th>
                <th>${getFilterInput('rank_score')}</th>
                <th></th>
            `;
        } else if (type === 'reit') {
            if (currentTab === 'br-fiis') {
                tableHeaderRow.innerHTML = `
                    <th data-sort="final_rank">Rank${getIcon('final_rank')}</th>
                    <th data-sort="ticker">Ticker / Name${getIcon('ticker')}</th>
                    <th data-sort="price">Price${getIcon('price')}</th>
                    <th data-sort="ceiling_price">Ceiling Price${getIcon('ceiling_price')}</th>
                    <th data-sort="dividend_yield">Div. Yield${getIcon('dividend_yield')}</th>
                    <th data-sort="p_vpa">P/VP${getIcon('p_vpa')}</th>
                    <th data-sort="dy_cagr">DY CAGR(3y)${getIcon('dy_cagr')}</th>
                    <th data-sort="min_52w">Min 52W${getIcon('min_52w')}</th>
                    <th data-sort="max_52w">Max 52W${getIcon('max_52w')}</th>
                    <th data-sort="val_12m">Val.(12M)${getIcon('val_12m')}</th>
                    <th data-sort="vp_cota">VP/Cota${getIcon('vp_cota')}</th>
                    <th data-sort="caixa">Caixa${getIcon('caixa')}</th>
                    <th data-sort="val_cagr">Val. CAGR(3y)${getIcon('val_cagr')}</th>
                    <th data-sort="cotistas">Cotistas${getIcon('cotistas')}</th>
                    <th data-sort="sharpe_ratio">Sharpe Ratio${getIcon('sharpe_ratio')}</th>
                    <th data-sort="rank_score">Score${getIcon('rank_score')}</th>
                    <th>Links</th>
                `;

                tableFilterRow.innerHTML = `
                    <th>${getFilterInput('final_rank')}</th>
                    <th>${getFilterInput('ticker')}</th>
                    <th>${getFilterInput('price')}</th>
                    <th>${getFilterInput('ceiling_price')}</th>
                    <th>${getFilterInput('dividend_yield')}</th>
                    <th>${getFilterInput('p_vpa')}</th>
                    <th>${getFilterInput('dy_cagr')}</th>
                    <th>${getFilterInput('min_52w')}</th>
                    <th>${getFilterInput('max_52w')}</th>
                    <th>${getFilterInput('val_12m')}</th>
                    <th>${getFilterInput('vp_cota')}</th>
                    <th>${getFilterInput('caixa')}</th>
                    <th>${getFilterInput('val_cagr')}</th>
                    <th>${getFilterInput('cotistas')}</th>
                    <th>${getFilterInput('sharpe_ratio')}</th>
                    <th>${getFilterInput('rank_score')}</th>
                    <th></th>
                `;
            } else {
                tableHeaderRow.innerHTML = `
                    <th data-sort="ticker">Ticker / Name${getIcon('ticker')}</th>
                    <th data-sort="price">Price${getIcon('price')}</th>
                    <th data-sort="dividend_yield">Div. Yield${getIcon('dividend_yield')}</th>
                    <th data-sort="p_vpa">P/VPA${getIcon('p_vpa')}</th>
                    <th data-sort="p_a">P/A${getIcon('p_a')}</th>
                    <th>Links</th>
                `;

                tableFilterRow.innerHTML = `
                    <th>${getFilterInput('ticker')}</th>
                    <th>${getFilterInput('price')}</th>
                    <th>${getFilterInput('dividend_yield')}</th>
                    <th>${getFilterInput('p_vpa')}</th>
                    <th>${getFilterInput('p_a')}</th>
                    <th></th>
                `;
            }
        } else if (type === 'news') {
            tableHeaderRow.innerHTML = `
                <th data-sort="parsedDate">Date${getIcon('parsedDate')}</th>
                <th data-sort="parsedTime">Time${getIcon('parsedTime')}</th>
                <th data-sort="parsedAsset">Asset${getIcon('parsedAsset')}</th>
                <th data-sort="parsedHeadline">Headline${getIcon('parsedHeadline')}</th>
                <th data-sort="parsedType">Type${getIcon('parsedType')}</th>
            `;

            tableFilterRow.innerHTML = `
                <th>${getFilterInput('parsedDate')}</th>
                <th>${getFilterInput('parsedTime')}</th>
                <th>${getFilterInput('parsedAsset')}</th>
                <th>${getFilterInput('parsedHeadline')}</th>
                <th>${getFilterInput('parsedType')}</th>
            `;
        } else {
            tableHeaderRow.innerHTML = '';
            tableFilterRow.innerHTML = '';
        }
        attachSortListeners();
        attachFilterListeners();
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
                renderTableBody(getFilteredData(), TAB_CONFIG[currentTab].type);
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
                return `<tr>
                    <td style="white-space:nowrap">${item.parsedDate || '-'}</td>
                    <td style="white-space:nowrap">${item.parsedTime || '-'}</td>
                    <td style="color:var(--text-secondary)">${item.parsedAsset || '-'}</td>
                    <td><a href="${item.link}" target="_blank" style="color:var(--text-primary); text-decoration:underline;">${item.parsedHeadline || '-'}</a></td>
                    <td style="white-space:nowrap; color:var(--accent)">${item.parsedType || '-'}</td>
                </tr>`;
            }

            // Normal stock/reit parsing
            const nameSub = escapeHTML(item.name ? item.name : 'Unknown');
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
                    <td style="font-size: 1.1rem; text-align: center;">${item.final_rank || '-'} ${rankIcon}</td>
                    <td class="ticker-cell">
                        ${item.ticker}
                        <span class="name-sub">${nameSub}</span>
                    </td>
                    <td>${formatCurrency(item.price)}</td>
                    <td class="${pegClass}">${formatNumber(item.peg)}</td>
                    <td class="${fcfClass}">${item.p_fcf !== null && item.p_fcf !== undefined ? item.p_fcf.toFixed(2) : '-'}</td>
                    <td class="${peClass}">${formatNumber(item.pe)}</td>
                    <td class="${(item.p_a != null && item.p_a < 1) ? 'good-metric' : (item.p_a != null && item.p_a > 3 ? 'bad-metric' : '')}">${formatNumber(item.p_a)}</td>
                    <td class="${'good-metric'}">${formatNumber(item.eps)}</td>
                    <td class="${debtEbitClass}">${formatNumber(item.debt_ebit)}</td>
                    <td class="${roicClass}">${formatPercent(item.roic)}</td>
                    <td class="${roeClass}">${formatPercent(item.roe)}</td>
                    <td class="${marginClass}">${formatPercent(item.net_margin)}</td>
                    <td class="${dyClass}">${formatPercent(item.dividend_yield)}</td>
                    <td>${item.rank_score}</td>
                    ${getExternalLinksHTML(item.ticker)}
                </tr>`;
            } else if (type === 'reit') {
                let rankIcon = '';
                let rankClass = '';
                if (currentTab === 'br-fiis') {
                    if (item.final_rank === 1) { rankIcon = '🏆'; rankClass = 'rank-1'; }
                    else if (item.final_rank === 2) { rankIcon = '🏅'; rankClass = 'rank-2'; }
                    else if (item.final_rank === 3) { rankIcon = '🥉'; rankClass = 'rank-3'; }
                    else if (item.final_rank === 4) { rankIcon = '🎖️'; rankClass = 'rank-4'; }
                    else if (item.final_rank === 5) { rankIcon = '🌟'; rankClass = 'rank-5'; }
                }

                rowHTML += `<tr class="${rankClass}">`;
                if (currentTab === 'br-fiis') {
                    rowHTML += `<td style="font-size: 1.1rem; text-align: center;">${item.final_rank || '-'} ${rankIcon}</td>`;
                }

                let priceStyle = '';
                if (currentTab === 'br-fiis' && item.ceiling_price && item.price < item.ceiling_price) {
                    priceStyle = 'color: #00FF9F;';
                }

                rowHTML += `
                <td class="ticker-cell">
                    ${item.ticker}
                    <span class="name-sub">${nameSub}</span>
                </td>
                <td style="${priceStyle}">${formatCurrency(item.price)}</td>
                `;
                if (currentTab === 'br-fiis') {
                    const dyClass = (item.dividend_yield > 6) ? 'good-metric' : '';
                    const pVpaClass = (item.p_vpa < 1 && item.p_vpa > 0) ? 'good-metric' : (item.p_vpa > 1.2 ? 'bad-metric' : '');
                    const colorVal12m = item.val_12m > 0 ? "good-metric" : (item.val_12m < 0 ? "bad-metric" : "");

                    rowHTML += `
                        <td>${item.ceiling_price !== null && item.ceiling_price !== undefined ? formatCurrency(item.ceiling_price) : '-'}</td>
                        <td class="${dyClass}">${formatPercent(item.dividend_yield)}</td>
                        <td class="${pVpaClass}">${formatNumber(item.p_vpa)}</td>
                        <td class="${item.dy_cagr > 0 ? 'good-metric' : (item.dy_cagr < 0 ? 'bad-metric' : '')}">${formatPercent(item.dy_cagr)}</td>
                        <td>${item.min_52w !== null && item.min_52w !== undefined ? formatCurrency(item.min_52w) : '-'}</td>
                        <td>${item.max_52w !== null && item.max_52w !== undefined ? formatCurrency(item.max_52w) : '-'}</td>
                        <td class="${colorVal12m}">${formatPercent(item.val_12m)}</td>
                        <td>${item.vp_cota !== null && item.vp_cota !== undefined ? formatCurrency(item.vp_cota) : '-'}</td>
                        <td>${item.caixa !== null && item.caixa !== undefined ? formatPercent(item.caixa) : '-'}</td>
                        <td class="${item.val_cagr > 0 ? 'good-metric' : (item.val_cagr < 0 ? 'bad-metric' : '')}">${formatPercent(item.val_cagr)}</td>
                        <td>${item.cotistas !== null && item.cotistas !== undefined ? item.cotistas.toLocaleString('pt-BR') : '-'}</td>
                        <td class="${item.sharpe_ratio !== null ? (item.sharpe_ratio > 0 ? 'good-metric' : 'bad-metric') : ''}">${item.sharpe_ratio !== null ? formatNumber(item.sharpe_ratio) : '-'}</td>
                        <td>${item.rank_score}</td>
                        ${getExternalLinksHTML(item.ticker)}
                    `;
                } else {
                    const dyClass = (item.dividend_yield > 6) ? 'good-metric' : '';
                    const pVpaClass = (item.p_vpa < 1 && item.p_vpa > 0) ? 'good-metric' : (item.p_vpa > 1.2 ? 'bad-metric' : '');

                    const paClass = (item.p_a != null && item.p_a < 1) ? 'good-metric' : (item.p_a != null && item.p_a > 3 ? 'bad-metric' : '');

                    rowHTML += `
                        <td class="${dyClass}">${formatPercent(item.dividend_yield)}</td>
                        <td class="${pVpaClass}">${formatNumber(item.p_vpa)}</td>
                        <td class="${paClass}">${formatNumber(item.p_a)}</td>
                        ${getExternalLinksHTML(item.ticker)}
                    `;
                }
            }
            return rowHTML + `</tr>`;
        }).join('');

        tableBody.innerHTML = rows;
    }

    // --- About App Page ---
    let aboutLoaded = false;

    async function loadAboutPage() {
        if (aboutLoaded) return; // Only fetch once

        aboutContent.innerHTML = '<div style="text-align: center; padding: 3rem; color: var(--text-secondary);">Loading documentation...</div>';

        try {
            const response = await fetch(`${API_BASE}/readme`);
            if (!response.ok) throw new Error('Failed to fetch README');
            const markdown = await response.text();

            // Configure marked with custom renderer for mermaid blocks
            const renderer = new marked.Renderer();
            const originalCodeRenderer = renderer.code;

            renderer.code = function({ text, lang }) {
                if (lang === 'mermaid') {
                    return `<div class="mermaid">${text}</div>`;
                }
                // Default code block rendering
                const escaped = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                return `<pre><code class="language-${lang || ''}">${escaped}</code></pre>`;
            };

            // Fix image paths: assets/ → ../assets/ (since README is at project root)
            const fixedMarkdown = markdown.replace(/!\[([^\]]*)\]\(assets\//g, '![$1](../assets/');

            marked.setOptions({
                renderer: renderer,
                breaks: true,
                gfm: true,
            });

            aboutContent.innerHTML = marked.parse(fixedMarkdown);

            // Initialize mermaid diagrams
            if (typeof mermaid !== 'undefined') {
                const isDark = document.body.classList.contains('theme-dark');
                mermaid.initialize({
                    startOnLoad: false,
                    theme: isDark ? 'dark' : 'default',
                    securityLevel: 'loose',
                    fontFamily: 'Fira Code, monospace',
                });
                const mermaidElements = aboutContent.querySelectorAll('.mermaid');
                if (mermaidElements.length > 0) {
                    await mermaid.run({ nodes: mermaidElements });
                }
            }

            aboutLoaded = true;
        } catch (error) {
            aboutContent.innerHTML = `<div style="text-align: center; padding: 3rem; color: var(--danger);">Error loading documentation: ${error.message}</div>`;
        }
    }
});
