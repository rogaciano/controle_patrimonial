"""
Script to fix encoding issues in ALL Django template files.
Re-reads each file and writes it back as clean UTF-8 without BOM.
"""
import os
import glob

TEMPLATE_DIR = r"E:\projetos\patrimonial_lucivaldo\apps\patrimonio\templates"
GLOBAL_TEMPLATE_DIR = r"E:\projetos\patrimonial_lucivaldo\templates"

fixed = []
skipped = []

def fix_file(filepath):
    """Read file trying multiple encodings, write back as clean UTF-8."""
    for encoding in ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                content = f.read()
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    else:
        return False, "Could not decode"

    # Remove BOM if present
    if content.startswith('\ufeff'):
        content = content[1:]

    # Check for problematic invisible characters around {{ }} and {% %}
    # Replace any zero-width spaces, non-breaking spaces, etc.
    import unicodedata
    cleaned = []
    changes = 0
    for char in content:
        cat = unicodedata.category(char)
        # Keep normal chars, but replace invisible format chars (Cf category)
        # except for normal whitespace
        if cat == 'Cf':  # Format characters (zero-width space, BOM, etc.)
            changes += 1
            continue  # Skip invisible chars
        cleaned.append(char)
    
    content = ''.join(cleaned)

    # Write back as clean UTF-8 with Unix line endings
    with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    
    return True, f"OK ({changes} invisible chars removed)"

# Process all HTML files in patrimonio templates
for dirpath, dirnames, filenames in os.walk(TEMPLATE_DIR):
    for fname in filenames:
        if fname.endswith('.html'):
            fpath = os.path.join(dirpath, fname)
            ok, msg = fix_file(fpath)
            if ok:
                fixed.append((fpath, msg))
            else:
                skipped.append((fpath, msg))

# Process global templates too
for dirpath, dirnames, filenames in os.walk(GLOBAL_TEMPLATE_DIR):
    for fname in filenames:
        if fname.endswith('.html'):
            fpath = os.path.join(dirpath, fname)
            ok, msg = fix_file(fpath)
            if ok:
                fixed.append((fpath, msg))
            else:
                skipped.append((fpath, msg))

print(f"\n{'='*60}")
print(f"Fixed {len(fixed)} files:")
for path, msg in fixed:
    short = path.replace(r"E:\projetos\patrimonial_lucivaldo\\", "")
    print(f"  ✓ {short} -> {msg}")

if skipped:
    print(f"\nSkipped {len(skipped)} files:")
    for path, msg in skipped:
        print(f"  ✗ {path} -> {msg}")

print(f"{'='*60}")
