/**
 * Shared Navigation Loader
 * Dynamically loads navigation bar and handles mobile menu functionality
 * 
 * This script runs synchronously to ensure the nav exists before
 * page translation scripts run.
 */

(function() {
    'use strict';
    
    // Get stored language for initial render
    const storedLang = localStorage.getItem('lang') || 'en';

    // Determine base path based on current page location
    function getBasePath() {
        const path = window.location.pathname;
        // If we're in a subdirectory (like docs/), go up one level
        if (path.includes('/docs/')) {
            return '../';
        }
        return '';
    }

    // Determine if current page is index.html (home page)
    function isHomePage() {
        const path = window.location.pathname;
        return path.endsWith('/') || path.endsWith('/index.html') || path.endsWith('/website_temp/') || path.endsWith('/website_temp/index.html');
    }

    // Determine current page for active state
    function getCurrentPage() {
        const path = window.location.pathname;
        if (path.includes('/docs/')) {
            const filename = path.split('/').pop();
            return filename.replace('.html', '');
        }
        if (path.includes('team.html')) return 'team';
        if (path.includes('how-it-works.html')) return 'overview';
        return 'home';
    }

    // Generate navigation HTML
    function generateNavHTML() {
        const basePath = getBasePath();
        const currentPage = getCurrentPage();
        const isHome = isHomePage();

        // Determine active states
        const featuresActive = isHome ? '' : '';
        const docsActive = currentPage === 'overview' || currentPage === 'execution' || 
                          currentPage === 'compilation' || currentPage === 'syntax' || 
                          currentPage === 'examples' ? 'active' : '';
        const teamActive = currentPage === 'team' ? 'active' : '';
        
        // Determine which doc item is active
        let overviewActive = currentPage === 'overview' ? 'active' : '';
        let executionActive = currentPage === 'execution' ? 'active' : '';
        let compilationActive = currentPage === 'compilation' ? 'active' : '';
        let syntaxActive = currentPage === 'syntax' ? 'active' : '';
        let examplesActive = currentPage === 'examples' ? 'active' : '';

        // Home link - use #features for home page, index.html for others
        const homeLink = isHome ? '#features' : (basePath + 'index.html');

        return `
            <nav>
                <div class="nav-content">
                    <a href="${basePath}index.html" class="nav-brand">
                        <img src="${basePath}Psylensai_log_raw.png" alt="Psylens.AI" class="logo-small">
                        <span class="company-name" data-i18n="nav.companyName">Psylens.AI</span>
                    </a>
                    <button class="menu-toggle" aria-label="Toggle navigation menu">
                        <span></span>
                        <span></span>
                        <span></span>
                    </button>
                    <div class="nav-links">
                        ${isHome ? 
                            '<a href="#features" data-i18n="nav.features">Features</a>' :
                            `<a href="${homeLink}" data-i18n="nav.home">Home</a>`
                        }
                        <div class="nav-dropdown">
                            <button class="nav-dropdown-trigger ${docsActive}" data-i18n="nav.docs">
                                Documentation
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <polyline points="6 9 12 15 18 9"></polyline>
                                </svg>
                            </button>
                            <div class="nav-dropdown-menu">
                                <a href="${basePath}how-it-works.html" class="${overviewActive}" data-i18n="nav.overview">Overview</a>
                                <a href="${basePath}docs/execution.html" class="${executionActive}" data-i18n="nav.execution">Execution Model</a>
                                <a href="${basePath}docs/compilation.html" class="${compilationActive}" data-i18n="nav.compilation">Compilation</a>
                                <a href="${basePath}docs/syntax.html" class="${syntaxActive}" data-i18n="nav.syntax">Syntax Reference</a>
                                <a href="${basePath}docs/examples.html" class="${examplesActive}" data-i18n="nav.examples">Examples</a>
                            </div>
                        </div>
                        <a href="${basePath}team.html" class="${teamActive}" data-i18n="nav.team">Team</a>
                        <div class="lang-switcher">
                            <button class="lang-btn${storedLang === 'en' ? ' active' : ''}" data-lang="en">EN</button>
                            <button class="lang-btn${storedLang === 'zh' ? ' active' : ''}" data-lang="zh">中文</button>
                        </div>
                    </div>
                </div>
            </nav>
        `;
    }

    // Initialize navigation
    function initNavigation() {
        // Create menu overlay if it doesn't exist
        let menuOverlay = document.querySelector('.menu-overlay');
        if (!menuOverlay) {
            menuOverlay = document.createElement('div');
            menuOverlay.className = 'menu-overlay';
            document.body.insertBefore(menuOverlay, document.body.firstChild);
        }

        // Find or create nav container
        let navContainer = document.querySelector('nav');
        if (!navContainer) {
            // Create nav container
            navContainer = document.createElement('div');
            navContainer.innerHTML = generateNavHTML();
            navContainer = navContainer.querySelector('nav');
            document.body.insertBefore(navContainer, document.body.firstChild);
        } else {
            // Replace existing nav
            navContainer.outerHTML = generateNavHTML();
            navContainer = document.querySelector('nav');
        }

        // Setup mobile menu toggle
        const menuToggle = navContainer.querySelector('.menu-toggle');
        const navLinks = navContainer.querySelector('.nav-links');

        function toggleMenu(open) {
            const isOpen = open !== undefined ? open : !navLinks.classList.contains('active');
            menuToggle.classList.toggle('active', isOpen);
            navLinks.classList.toggle('active', isOpen);
            menuOverlay.classList.toggle('active', isOpen);
            document.body.style.overflow = isOpen ? 'hidden' : '';
        }

        if (menuToggle) {
            menuToggle.addEventListener('click', () => toggleMenu());
        }
        if (menuOverlay) {
            menuOverlay.addEventListener('click', () => toggleMenu(false));
        }

        // Smooth scroll for anchor links
        navContainer.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                const href = this.getAttribute('href');
                if (href === '#') return;
                
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
                toggleMenu(false);
            });
        });

        // Setup language switcher
        setupLanguageSwitcher(navContainer);
    }

    // Setup language switcher functionality
    function setupLanguageSwitcher(navContainer) {
        const langButtons = navContainer.querySelectorAll('.lang-btn');
        
        // Active state is already set in the HTML based on storedLang
        
        // Attach click handlers that work with page's translation system
        langButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                const lang = this.getAttribute('data-lang');
                
                // Update localStorage and document lang
                localStorage.setItem('lang', lang);
                document.documentElement.lang = lang;
                
                // Update active state on all lang buttons (including any duplicates)
                document.querySelectorAll('.lang-btn').forEach(b => {
                    b.classList.toggle('active', b.getAttribute('data-lang') === lang);
                });
                
                // Call the page's setLanguage function to update translations
                if (typeof window.setLanguage === 'function') {
                    window.setLanguage(lang);
                }
            });
        });
    }

    // Initialize immediately - script is at end of body so DOM is ready
    // This ensures nav exists before page translation scripts run
    initNavigation();
    
    // Also set document lang attribute based on stored preference
    document.documentElement.lang = storedLang;
})();

