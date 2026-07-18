import os
import re

path = 'app/templates/index.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(r'\\\`', '`')
text = text.replace(r'\`', '`')
text = text.replace(r'\${', '${')

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
print("Fixed syntax errors in index.html")
