import re
import sys

def main():
    file_path = "app/templates/index.html"
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Change grid to flex
    content = content.replace(
        '<div class="grid grid-cols-1 lg:grid-cols-12 gap-8">',
        '<div class="flex flex-col lg:flex-row gap-8 items-start min-h-[calc(100vh-10rem)]">'
    )

    # 2. Extract and remove old Mode Selector Tab
    tab_regex = re.compile(r'<!-- Mode Selector Tab -->\s*<div class="flex bg-slate-100.*?</div>', re.DOTALL)
    content = tab_regex.sub('', content)

    # 3. Add Sidebar Navigation before setupPanel
    sidebar_html = """
            <!-- Sidebar Navigation -->
            <aside class="w-full lg:w-64 shrink-0 flex flex-col gap-2 bg-white/80 dark:bg-[#121B3A]/90 backdrop-blur-xl rounded-3xl p-4 shadow-xl border border-slate-100 dark:border-[#1E2954]">
                <h3 class="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-3 px-3 mt-2">Navigation</h3>
                <button id="tabSingle" class="w-full text-left flex items-center px-4 py-3 text-sm font-bold rounded-xl bg-blue-50 dark:bg-[#1E2954] text-blue-600 dark:text-white transition-colors">
                    <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                    Single Eval
                </button>
                <button id="tabBatch" class="w-full text-left flex items-center px-4 py-3 text-sm font-bold rounded-xl text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-[#1E2954]/50 transition-colors">
                    <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
                    Batch Eval
                </button>
                <button id="tabAnalytics" class="w-full text-left flex items-center px-4 py-3 text-sm font-bold rounded-xl text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-[#1E2954]/50 transition-colors">
                    <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>
                    Analytics
                </button>
                <button id="tabTriage" class="w-full text-left flex items-center px-4 py-3 text-sm font-bold rounded-xl text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-[#1E2954]/50 transition-colors">
                    <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                    Triage
                </button>
            </aside>
            
            <!-- Main Content Area -->
            <main class="flex-1 flex flex-col min-w-0">
    """
    
    content = content.replace(
        '<!-- Left Panel -->\n            <div id="setupPanel" class="lg:col-span-4 flex flex-col space-y-6 transition-all duration-300">',
        sidebar_html + '\n                <div id="setupPanel" class="w-full flex flex-col space-y-6 transition-all duration-300">'
    )

    # Wrap the end of reportPanel with closing main tag
    # reportPanel ends at line ~359, which is 2 lines before "<!-- OCR Modal -->"
    content = content.replace(
        '        </div>\n    </div>\n\n    <!-- OCR Modal -->',
        '        </main>\n        </div>\n    </div>\n\n    <!-- OCR Modal -->'
    )

    # 4. Modify reportPanel class to not be col-span-8 and start hidden by default, taking full width
    content = content.replace(
        '<div id="reportPanel" class="lg:col-span-8 bg-white/80',
        '<div id="reportPanel" class="hidden w-full bg-white/80'
    )

    # 5. Modifying JavaScript logic
    
    # We will replace the entire tab event listener section
    
    old_js = """        tabSingle.addEventListener('click', () => {
            currentMode = 'single';
            tabSingle.className = "flex-1 min-w-[70px] text-center py-2 text-xs font-bold rounded-lg bg-white dark:bg-[#1E2954] text-blue-600 dark:text-white shadow-sm transition";
            tabBatch.className = "flex-1 min-w-[70px] text-center py-2 text-xs font-bold rounded-lg text-slate-500 dark:text-slate-400 hover:text-slate-700 transition";
            tabAnalytics.className = "flex-1 min-w-[70px] flex items-center justify-center py-2 text-xs font-bold rounded-lg text-slate-500 dark:text-slate-400 hover:text-slate-700 transition";
            tabTriage.className = "flex-1 min-w-[70px] flex items-center justify-center py-2 text-xs font-bold rounded-lg text-slate-500 dark:text-slate-400 hover:text-slate-700 transition";
            
            dropZonePdf.classList.remove('hidden');
            usnContainer.classList.remove('hidden');
            dropZoneFolder.classList.add('hidden');
            btnRun.classList.remove('hidden');
            
            document.getElementById('reportContent').classList.add('hidden');
            document.getElementById('batchReportContent').classList.add('hidden');
            document.getElementById('analyticsContent').classList.add('hidden');
            document.getElementById('triageContent').classList.add('hidden');
            document.getElementById('emptyResults').classList.remove('hidden');
            showCompactView();
        });

        tabBatch.addEventListener('click', () => {
            currentMode = 'batch';
            tabBatch.className = "flex-1 min-w-[70px] text-center py-2 text-xs font-bold rounded-lg bg-white dark:bg-[#1E2954] text-blue-600 dark:text-white shadow-sm transition";
            tabSingle.className = "flex-1 min-w-[70px] text-center py-2 text-xs font-bold rounded-lg text-slate-500 dark:text-slate-400 hover:text-slate-700 transition";
            tabAnalytics.className = "flex-1 min-w-[70px] flex items-center justify-center py-2 text-xs font-bold rounded-lg text-slate-500 dark:text-slate-400 hover:text-slate-700 transition";
            tabTriage.className = "flex-1 min-w-[70px] flex items-center justify-center py-2 text-xs font-bold rounded-lg text-slate-500 dark:text-slate-400 hover:text-slate-700 transition";
            
            dropZoneFolder.classList.remove('hidden');
            dropZonePdf.classList.add('hidden');
            usnContainer.classList.add('hidden');
            btnRun.classList.remove('hidden');
            
            document.getElementById('reportContent').classList.add('hidden');
            document.getElementById('batchReportContent').classList.add('hidden');
            document.getElementById('analyticsContent').classList.add('hidden');
            document.getElementById('triageContent').classList.add('hidden');
            document.getElementById('emptyResults').classList.remove('hidden');
            showCompactView();
        });

        tabAnalytics.addEventListener('click', () => {
            currentMode = 'analytics';
            tabAnalytics.className = "flex-1 min-w-[70px] flex items-center justify-center py-2 text-xs font-bold rounded-lg bg-white dark:bg-[#1E2954] text-blue-600 dark:text-white shadow-sm transition";
            tabSingle.className = "flex-1 min-w-[70px] text-center py-2 text-xs font-bold rounded-lg text-slate-500 dark:text-slate-400 hover:text-slate-700 transition";
            tabBatch.className = "flex-1 min-w-[70px] text-center py-2 text-xs font-bold rounded-lg text-slate-500 dark:text-slate-400 hover:text-slate-700 transition";
            tabTriage.className = "flex-1 min-w-[70px] flex items-center justify-center py-2 text-xs font-bold rounded-lg text-slate-500 dark:text-slate-400 hover:text-slate-700 transition";
            
            showCompactView();
            setupPanel.classList.add('hidden');
            reportPanel.classList.remove('lg:col-span-8');
            reportPanel.classList.add('lg:col-span-12');
            
            document.getElementById('reportContent').classList.add('hidden');
            document.getElementById('batchReportContent').classList.add('hidden');
            document.getElementById('emptyResults').classList.add('hidden');
            document.getElementById('triageContent').classList.add('hidden');
            document.getElementById('analyticsContent').classList.remove('hidden');
            btnBackToSetup.classList.remove('hidden');
            
            loadAnalytics();
        });

        tabTriage.addEventListener('click', () => {
            currentMode = 'triage';
            tabTriage.className = "flex-1 min-w-[70px] flex items-center justify-center py-2 text-xs font-bold rounded-lg bg-white dark:bg-[#1E2954] text-blue-600 dark:text-white shadow-sm transition";
            tabSingle.className = "flex-1 min-w-[70px] text-center py-2 text-xs font-bold rounded-lg text-slate-500 dark:text-slate-400 hover:text-slate-700 transition";
            tabBatch.className = "flex-1 min-w-[70px] text-center py-2 text-xs font-bold rounded-lg text-slate-500 dark:text-slate-400 hover:text-slate-700 transition";
            tabAnalytics.className = "flex-1 min-w-[70px] flex items-center justify-center py-2 text-xs font-bold rounded-lg text-slate-500 dark:text-slate-400 hover:text-slate-700 transition";
            
            showCompactView();
            setupPanel.classList.add('hidden');
            reportPanel.classList.remove('lg:col-span-8');
            reportPanel.classList.add('lg:col-span-12');
            
            document.getElementById('reportContent').classList.add('hidden');
            document.getElementById('batchReportContent').classList.add('hidden');
            document.getElementById('emptyResults').classList.add('hidden');
            document.getElementById('analyticsContent').classList.add('hidden');
            document.getElementById('triageContent').classList.remove('hidden');
            btnBackToSetup.classList.remove('hidden');
            
            loadFlaggedReviews();
        });"""

    new_js = """
        const activeClass = "w-full text-left flex items-center px-4 py-3 text-sm font-bold rounded-xl bg-blue-50 dark:bg-[#1E2954] text-blue-600 dark:text-white transition-colors";
        const inactiveClass = "w-full text-left flex items-center px-4 py-3 text-sm font-bold rounded-xl text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-[#1E2954]/50 transition-colors";

        function updateTabStyles(activeTab) {
            tabSingle.className = (activeTab === 'single') ? activeClass : inactiveClass;
            tabBatch.className = (activeTab === 'batch') ? activeClass : inactiveClass;
            tabAnalytics.className = (activeTab === 'analytics') ? activeClass : inactiveClass;
            tabTriage.className = (activeTab === 'triage') ? activeClass : inactiveClass;
        }

        tabSingle.addEventListener('click', () => {
            currentMode = 'single';
            updateTabStyles('single');
            
            dropZonePdf.classList.remove('hidden');
            usnContainer.classList.remove('hidden');
            dropZoneFolder.classList.add('hidden');
            btnRun.classList.remove('hidden');
            
            setupPanel.classList.remove('hidden');
            reportPanel.classList.add('hidden');
            
            document.getElementById('reportContent').classList.add('hidden');
            document.getElementById('batchReportContent').classList.add('hidden');
            document.getElementById('analyticsContent').classList.add('hidden');
            document.getElementById('triageContent').classList.add('hidden');
            document.getElementById('emptyResults').classList.remove('hidden');
        });

        tabBatch.addEventListener('click', () => {
            currentMode = 'batch';
            updateTabStyles('batch');
            
            dropZoneFolder.classList.remove('hidden');
            dropZonePdf.classList.add('hidden');
            usnContainer.classList.add('hidden');
            btnRun.classList.remove('hidden');
            
            setupPanel.classList.remove('hidden');
            reportPanel.classList.add('hidden');
            
            document.getElementById('reportContent').classList.add('hidden');
            document.getElementById('batchReportContent').classList.add('hidden');
            document.getElementById('analyticsContent').classList.add('hidden');
            document.getElementById('triageContent').classList.add('hidden');
            document.getElementById('emptyResults').classList.remove('hidden');
        });

        tabAnalytics.addEventListener('click', () => {
            currentMode = 'analytics';
            updateTabStyles('analytics');
            
            setupPanel.classList.add('hidden');
            reportPanel.classList.remove('hidden');
            
            document.getElementById('reportContent').classList.add('hidden');
            document.getElementById('batchReportContent').classList.add('hidden');
            document.getElementById('emptyResults').classList.add('hidden');
            document.getElementById('triageContent').classList.add('hidden');
            document.getElementById('analyticsContent').classList.remove('hidden');
            btnBackToSetup.classList.add('hidden');
            
            loadAnalytics();
        });

        tabTriage.addEventListener('click', () => {
            currentMode = 'triage';
            updateTabStyles('triage');
            
            setupPanel.classList.add('hidden');
            reportPanel.classList.remove('hidden');
            
            document.getElementById('reportContent').classList.add('hidden');
            document.getElementById('batchReportContent').classList.add('hidden');
            document.getElementById('emptyResults').classList.add('hidden');
            document.getElementById('analyticsContent').classList.add('hidden');
            document.getElementById('triageContent').classList.remove('hidden');
            btnBackToSetup.classList.add('hidden');
            
            loadFlaggedReviews();
        });
    """

    content = content.replace(old_js, new_js)

    # We also need to fix `showCompactView()` and `showDetailedView()`
    # because they manipulate `lg:col-span-8` and `lg:col-span-12` which we removed.
    
    old_compact_detailed = """        function showDetailedView() {
            setupPanel.classList.add('hidden');
            reportPanel.classList.remove('lg:col-span-8');
            reportPanel.classList.add('lg:col-span-12');
            btnBackToSetup.classList.remove('hidden');
            btnViewDetails.classList.add('hidden');
            document.querySelectorAll('.details-section').forEach(el => el.classList.remove('hidden'));
        }

        function showCompactView() {
            if (currentMode === 'batch') {
                if (viewState === 'report') {
                    // Go back to the Gradebook table view (keep it full screen for clarity)
                    viewState = 'gradebook';
                    document.getElementById('reportContent').classList.add('hidden');
                    document.getElementById('batchReportContent').classList.remove('hidden');
                    btnBackToSetup.classList.remove('hidden'); // Remains to let them go back to setup
                } else {
                    // Go back to Setup from Gradebook
                    viewState = 'setup';
                    document.getElementById('batchReportContent').classList.add('hidden');
                    document.getElementById('emptyResults').classList.remove('hidden');
                    
                    setupPanel.classList.remove('hidden');
                    reportPanel.classList.remove('lg:col-span-12');
                    reportPanel.classList.add('lg:col-span-8');
                    btnBackToSetup.classList.add('hidden');
                }
                btnViewDetails.classList.add('hidden');
            } else {
                viewState = 'setup';
                setupPanel.classList.remove('hidden');
                reportPanel.classList.remove('lg:col-span-12');
                reportPanel.classList.add('lg:col-span-8');
                btnBackToSetup.classList.add('hidden');
                btnViewDetails.classList.remove('hidden');
                document.querySelectorAll('.details-section').forEach(el => el.classList.add('hidden'));
            }
        }"""
        
    new_compact_detailed = """        function showDetailedView() {
            setupPanel.classList.add('hidden');
            reportPanel.classList.remove('hidden');
            btnBackToSetup.classList.remove('hidden');
            btnViewDetails.classList.add('hidden');
            document.querySelectorAll('.details-section').forEach(el => el.classList.remove('hidden'));
        }

        function showCompactView() {
            if (currentMode === 'batch') {
                if (viewState === 'report') {
                    // Go back to the Gradebook table view
                    viewState = 'gradebook';
                    document.getElementById('reportContent').classList.add('hidden');
                    document.getElementById('batchReportContent').classList.remove('hidden');
                    btnBackToSetup.classList.remove('hidden');
                } else {
                    // Go back to Setup from Gradebook
                    viewState = 'setup';
                    document.getElementById('batchReportContent').classList.add('hidden');
                    document.getElementById('emptyResults').classList.remove('hidden');
                    
                    setupPanel.classList.remove('hidden');
                    reportPanel.classList.add('hidden');
                    btnBackToSetup.classList.add('hidden');
                }
                btnViewDetails.classList.add('hidden');
            } else {
                viewState = 'setup';
                setupPanel.classList.remove('hidden');
                reportPanel.classList.add('hidden');
                btnBackToSetup.classList.add('hidden');
                btnViewDetails.classList.remove('hidden');
                document.querySelectorAll('.details-section').forEach(el => el.classList.add('hidden'));
            }
        }"""
        
    content = content.replace(old_compact_detailed, new_compact_detailed)
    
    # We also need to fix `btnRun.addEventListener` behavior for switching views when run is clicked.
    # Luckily, `showDetailedView` is called or `viewState` is changed, but we also want to show `reportPanel`.
    # Let's replace instances of reportPanel.classList.remove('lg:col-span-8') with nothing if they exist outside.

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("Refactoring done.")

if __name__ == "__main__":
    main()
