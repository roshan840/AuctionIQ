import re

with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update Imports
text = text.replace('import math', 'import math\nfrom typing import Optional')

# 2. Inject Theme Configuration after Page Config
theme_injection = """
# ─── Theme Configuration ─────────────────────────────────────────────────────
if 'theme_mode' not in st.session_state:
    st.session_state.theme_mode = 'System'

# Render theme selector in sidebar early so styles apply instantly
st.sidebar.markdown("**🎨 Appearance**")
theme_mode = st.sidebar.radio("Theme", ["System", "Light", "Dark"], horizontal=True, label_visibility="collapsed")
st.session_state.theme_mode = theme_mode
st.sidebar.markdown('<hr style="border:none;border-top:1px solid rgba(255,56,92,0.15);margin:12px 0;">', unsafe_allow_html=True)

if theme_mode == "Dark":
    root_css = \"\"\"
    :root {
        --bg-main: #111111;
        --bg-card: #1a1a1a;
        --text-main: #ffffff;
        --text-muted: #888888;
        --border-alpha: rgba(255, 56, 92, 0.2);
        --border-light: rgba(255, 56, 92, 0.15);
        --card-shadow: 0 4px 6px rgba(0,0,0,0.3);
        --ring-bg: #1e293b;
        --ring-border: #334155;
    }
    \"\"\"
    plotly_template = "plotly_dark"
elif theme_mode == "Light":
    root_css = \"\"\"
    :root {
        --bg-main: #f8fafc;
        --bg-card: #ffffff;
        --text-main: #0f172a;
        --text-muted: #64748b;
        --border-alpha: rgba(255, 56, 92, 0.3);
        --border-light: rgba(255, 56, 92, 0.15);
        --card-shadow: 0 4px 6px rgba(0,0,0,0.05);
        --ring-bg: #f1f5f9;
        --ring-border: #e2e8f0;
    }
    \"\"\"
    plotly_template = "plotly_white"
else:
    root_css = \"\"\"
    :root {
        --bg-main: #f8fafc;
        --bg-card: #ffffff;
        --text-main: #0f172a;
        --text-muted: #64748b;
        --border-alpha: rgba(255, 56, 92, 0.3);
        --border-light: rgba(255, 56, 92, 0.15);
        --card-shadow: 0 4px 6px rgba(0,0,0,0.05);
        --ring-bg: #f1f5f9;
        --ring-border: #e2e8f0;
    }
    @media (prefers-color-scheme: dark) {
        :root {
            --bg-main: #111111;
            --bg-card: #1a1a1a;
            --text-main: #ffffff;
            --text-muted: #888888;
            --border-alpha: rgba(255, 56, 92, 0.2);
            --border-light: rgba(255, 56, 92, 0.15);
            --card-shadow: 0 4px 6px rgba(0,0,0,0.3);
            --ring-bg: #1e293b;
            --ring-border: #334155;
        }
    }
    \"\"\"
    plotly_template = None

def render_plotly(col, fig):
    if theme_mode == "System":
        col.plotly_chart(fig, theme="streamlit", width="stretch")
    else:
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        col.plotly_chart(fig, theme=None, width="stretch")

# ─── Premium CSS Injection ───────────────────────────────────────────────────
"""
text = text.replace('# ─── Premium CSS Injection ───────────────────────────────────────────────────', theme_injection)

# 3. Setup MAIN_CSS F-String with proper brackets
start_idx = text.find('MAIN_CSS = """')
end_idx = text.find('"""\nst.markdown(MAIN_CSS', start_idx + 14) + 3
main_css_block = text[start_idx:end_idx]

# Fix brackets inside the CSS so it works as an f-string
new_main_css_block = main_css_block.replace('{', '{{').replace('}', '}}')

# Add the variable evaluation for root_css and text replacement
new_main_css_block = new_main_css_block.replace('MAIN_CSS = ""\"', 'MAIN_CSS = f""\"\n{root_css}')

text = text[:start_idx] + new_main_css_block + text[end_idx:]

# Handle string text replacements for HTML hardcoded colors
text = re.sub(r'#111111', 'var(--bg-main)', text)
text = re.sub(r'#1a1a1a', 'var(--bg-card)', text)
text = re.sub(r'#ffffff', 'var(--text-main)', text)
text = re.sub(r'#888888', 'var(--text-muted)', text)
text = re.sub(r'rgba\(255,56,92,0\.2\)', 'var(--border-alpha)', text)
text = re.sub(r'rgba\(255,56,92,0\.15\)', 'var(--border-light)', text)
text = re.sub(r'box-shadow:0 4px 20px rgba\(0,0,0,0\.3\)', 'box-shadow:var(--card-shadow)', text)
text = re.sub(r'#1e293b', 'var(--ring-bg)', text)
text = re.sub(r'#334155', 'var(--ring-border)', text)

# For plotly `template='plotly_dark'` -> `template=plotly_template`
text = text.replace("template='plotly_dark'", "template=plotly_template")

# Cleanup background settings from plotly update_layout
# plot_bgcolor='#111111' -> plot_bgcolor='var(--bg-main)' (which is invalid for python plotly so we regex it out)
text = re.sub(r"plot_bgcolor='var\(--bg-main\)',paper_bgcolor='var\(--bg-card\)',?\s*font_color='var\(--text-main\)',?", "", text)
text = re.sub(r"plot_bgcolor='var\(--bg-main\)',\s*paper_bgcolor='var\(--bg-card\)',?\s*font_color='var\(--text-main\)',?", "", text)
text = re.sub(r"paper_bgcolor='var\(--bg-card\)',?\s*font_color='var\(--text-main\)',?", "", text)

# Fix commas for empty params in update_layout
text = text.replace("update_layout( )", "update_layout()")
text = text.replace("update_layout( ,", "update_layout(")

# Update `st.plotly_chart` calls to `render_plotly(col, fig)` wrapper
text = re.sub(r'(\w+)\.plotly_chart\((fig_[\w]+),\s*width=\'stretch\'\)', r'render_plotly(\1, \2)', text)

# Write modified text to app.py
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Replacement complete")
