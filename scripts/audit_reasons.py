import json
import re
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(root_dir / "backend"))

strings_path = Path('shared/strings.json')
with open(strings_path, encoding='utf-8') as f:
    strings = json.load(f)
defined_reasons = strings.get('reasons', {})
print(f"Total defined in shared/strings.json: {len(defined_reasons)}")

found_reasons = set()
for p in Path('.').rglob('*.py'):
    if 'node_modules' in str(p) or '.venv' in str(p):
        continue
    content = p.read_text(encoding='utf-8', errors='ignore')
    for m in re.finditer(r'_reason_entry\(["\']([a-zA-Z0-9_]+)["\']', content):
        found_reasons.add(m.group(1))
    for m in re.finditer(r'reasons\.append\(["\']([a-zA-Z0-9_]+)["\']', content):
        found_reasons.add(m.group(1))

from ml.config import VALID_REASONS
for r in VALID_REASONS:
    found_reasons.add(r)

print(f"Total found in backend and ML: {len(found_reasons)}")
missing = sorted(list(found_reasons - set(defined_reasons.keys())))
print(f"Missing in strings.json: {missing}")

for k in sorted(defined_reasons.keys()):
    v = defined_reasons[k]
    en = v.get('en', '')
    hi = v.get('hi', '')
    status = "OK" if en and hi else "INCOMPLETE"
    print(f"  {k:24} | {status} | EN: {en[:35]}... | HI: {hi[:35]}...")
