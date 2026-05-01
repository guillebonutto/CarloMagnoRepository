import re

with open('templates/base.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the split template tag - Django tag was split across two lines by formatter
fixed = re.sub(
    r'\{\{\s*\r?\n\s*user\.first_name\|default:user\.username\s*\}\}',
    '{{ user.first_name|default:user.username }}',
    content
)

if fixed != content:
    with open('templates/base.html', 'w', encoding='utf-8') as f:
        f.write(fixed)
    print('Fixed username template tag!')
else:
    print('Pattern not found - no change made')
