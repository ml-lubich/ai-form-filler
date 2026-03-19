"""Shared JavaScript for extracting form fields (Playwright + Selenium)."""

# Inner logic: runs in browser, returns array of field objects.
# Use normal (non-raw) string so '\\"' becomes correct JS escape for id.replace.
_FORM_FIELDS_INNER = """
        const fields = [];
        const seen = new Set();

        const inputs = document.querySelectorAll('input, textarea, select');
        for (const el of inputs) {
            const tag = el.tagName.toLowerCase();
            const name = el.name || null;
            const id = el.id || null;
            const type = (el.type || 'text').toLowerCase();
            if (tag === 'select') {
                const options = [];
                for (const o of el.options) {
                    if (o.value !== undefined) options.push([o.value, (o.text || o.value).trim()]);
                }
                const key = name || id || 'select_' + fields.length;
                if (!seen.has(key)) { seen.add(key); fields.push({
                    key, tag: 'select', input_type: 'select', name, id,
                    placeholder: null, label_text: null, options
                }); }
                continue;
            }
            if (['button', 'submit', 'image', 'hidden'].includes(type)) continue;
            let label_text = null;
            if (id) {
                const label = document.querySelector('label[for="' + id.replace(/"/g, '\\"') + '"]');
                if (label) label_text = (label.textContent || '').trim().replace(/\\s+/g, ' ');
            }
            if (!label_text && el.closest('label')) {
                const label = el.closest('label');
                if (label) label_text = (label.textContent || '').trim().replace(/\\s+/g, ' ');
            }
            const placeholder = (el.placeholder || null);
            const key = name || id || 'field_' + fields.length;
            if (!seen.has(key)) {
                seen.add(key);
                fields.push({
                    key, tag, input_type: type, name, id, placeholder, label_text,
                    options: type === 'radio' ? [] : []
                });
            }
        }
        return fields;
"""

# Playwright: page.evaluate expects a function string.
PLAYWRIGHT_EXTRACT_JS = "() => {\n" + _FORM_FIELDS_INNER + "\n}"

# Selenium: execute_script needs explicit return.
SELENIUM_EXTRACT_JS = "return (function() {\n" + _FORM_FIELDS_INNER + "\n})();"
