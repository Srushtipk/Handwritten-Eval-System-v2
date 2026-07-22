import re

def refactor_html():
    file_path = "app/templates/index.html"
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update body class
    content = re.sub(
        r'<body class=".*?">',
        '<body class="bg-slate-50 text-slate-800 dark:bg-[#0B0B2A] dark:text-slate-200 h-screen w-screen overflow-hidden flex transition-colors duration-300 relative">',
        content
    )

    # 2. Remove the container div and header
    container_start = content.find('<div class="container mx-auto px-6 py-10 max-w-7xl relative z-10">')
    if container_start == -1:
        print("Could not find container div")
        return
        
    main_content_area_idx = content.find('<!-- Main Content Area -->', container_start)
    if main_content_area_idx == -1:
        print("Could not find main content area")
        return
        
    main_start = content.find('<main', main_content_area_idx)
    main_end = content.find('>', main_start) + 1
    
    # We will replace from container_start up to main_end
    
    new_sidebar_and_main = """    <!-- Sidebar Navigation -->
    <aside id="sidebarNav" class="w-64 h-full shrink-0 flex flex-col justify-between bg-white/80 dark:bg-[#121B3A]/90 backdrop-blur-xl shadow-[4px_0_24px_rgb(0,0,0,0.02)] dark:shadow-[4px_0_24px_rgb(0,0,0,0.2)] border-r border-slate-100 dark:border-[#1E2954] z-20 transition-all duration-300">
        <div>
            <!-- Logo Area -->
            <div class="p-6 border-b border-slate-100 dark:border-[#1E2954]">
                <div class="flex items-center space-x-3 mb-2">
                    <div class="w-10 h-10 rounded-2xl bg-blue-600 dark:bg-orange-500 flex items-center justify-center shadow-[0_4px_12px_rgb(37,99,235,0.3)] dark:shadow-[0_4px_12px_rgb(249,115,22,0.3)]">
                        <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path></svg>
                    </div>
                    <div>
                        <h1 class="text-xl font-extrabold text-slate-900 dark:text-white leading-tight">EduEval</h1>
                        <p class="text-blue-600 dark:text-orange-400 text-[9px] font-bold tracking-widest uppercase">AI Engine</p>
                    </div>
                </div>
            </div>
            
            <div class="p-4">
                <h3 class="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-3 px-3 mt-2">Navigation</h3>
                <div class="flex flex-col gap-1.5">
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
                </div>
            </div>
        </div>
        
        <div class="p-4">
            <button id="themeToggle" class="w-full mb-4 h-10 flex items-center justify-center rounded-xl bg-slate-50 dark:bg-[#1E2954] hover:bg-slate-100 dark:hover:bg-[#2A3768] transition-colors focus:outline-none border border-slate-100 dark:border-transparent">
                <div id="themeToggleDarkIcon" class="hidden text-[11px] font-bold text-blue-600 flex items-center gap-2 uppercase tracking-wider">
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z"></path></svg> Dark Mode
                </div>
                <div id="themeToggleLightIcon" class="hidden text-[11px] font-bold text-orange-400 flex items-center gap-2 uppercase tracking-wider">
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4.22 2.366a1 1 0 011.415 0l.708.707a1 1 0 01-1.414 1.415l-.707-.708a1 1 0 010-1.414zm3.78 4.634a1 1 0 110 2h-1a1 1 0 110-2h1zm-2.366 4.22a1 1 0 010 1.415l-.708.707a1 1 0 01-1.414-1.414l.707-.708a1 1 0 011.415 0zM10 16a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zm-4.22-2.366a1 1 0 010-1.415l-.708-.707a1 1 0 011.414-1.414l.708.707a1 1 0 01-1.415 1.415zM4 10a1 1 0 11-2 0 1 1 0 012 0zm2.366-4.22a1 1 0 011.415-1.415l.707.708a1 1 0 01-1.414 1.415l-.708-.707z" clip-rule="evenodd"></path></svg Light Mode
                </div>
            </button>
            <div class="p-4 bg-slate-50 dark:bg-[#0B0B2A] rounded-2xl border border-slate-100 dark:border-[#1E2954]">
                <div class="flex items-center gap-3 mb-2">
                    <div class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                    <span class="text-xs font-bold text-slate-700 dark:text-slate-300">System Online</span>
                </div>
                <p class="text-[10px] text-slate-500 dark:text-slate-400">EduEval is ready to process submissions.</p>
            </div>
        </div>
    </aside>

    <!-- Main Content Area -->
    <main class="flex-1 h-full overflow-y-auto p-6 lg:p-10 relative z-10 min-w-0">"""
    
    content = content[:container_start] + new_sidebar_and_main + content[main_end:]
    
    closing_main_idx = content.find('</main>')
    if closing_main_idx != -1:
        post_main = content[closing_main_idx:]
        post_main = re.sub(r'</main>\s*</div>\s*</div>', '</main>', post_main)
        content = content[:closing_main_idx] + post_main

    content = content.replace(
        "if(sidebarNav) sidebarNav.classList.add('hidden');",
        "if(sidebarNav) sidebarNav.classList.add('-ml-64');"
    )
    content = content.replace(
        "if(sidebarNav) sidebarNav.classList.remove('hidden');",
        "if(sidebarNav) sidebarNav.classList.remove('-ml-64');"
    )

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    refactor_html()
