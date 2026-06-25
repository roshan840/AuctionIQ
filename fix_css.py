import re

with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix CSS styling error outputted on the top of the interface
# `shadow: 0...` text is showing on the UI.
text = text.replace('shadow: 0 4px 6px rgba(0,0,0,0.05); --ring-bg: #f1f5f9; --ring-border: #e2e8f0; }', '')

# Remove double {root_css} injection that might be bleeding into the frontend text view
start_idx = text.find('MAIN_CSS = f"""')
end_idx = text.find('<style>', start_idx)

# Clean out raw {root_css} var before <style>. Put it firmly *inside* <style>
new_main_css = text[start_idx:end_idx]
new_main_css = new_main_css.replace('{root_css}', '')

text = text[:start_idx] + new_main_css + text[end_idx:]

text = text.replace('<style>', '<style>\n{root_css}')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("CSS Bleed fixed")
