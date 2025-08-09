"""
Data Mode Indicator Helper
Shows whether the app is running in LIVE or MOCK mode
"""

import os

def get_data_mode():
    """Get current data mode from environment"""
    mode = os.environ.get('APP_DATA_MODE', 'MOCK')
    return mode.upper()

def is_live_mode():
    """Check if running in LIVE mode"""
    return get_data_mode() == 'LIVE'

def is_mock_mode():
    """Check if running in MOCK mode"""
    return get_data_mode() == 'MOCK'

def get_mode_badge_html():
    """Get HTML for mode indicator badge"""
    mode = get_data_mode()
    if mode == 'LIVE':
        badge_class = 'bg-green-600 text-white'
        badge_text = 'LIVE'
    else:
        badge_class = 'bg-yellow-600 text-white'
        badge_text = 'DEMO'
    
    return f'''
    <div class="fixed bottom-4 right-4 z-50" data-mode="{mode}">
        <span class="mode-badge {badge_class} px-3 py-1 rounded-full text-xs font-semibold shadow-lg">
            {badge_text}
        </span>
    </div>
    '''