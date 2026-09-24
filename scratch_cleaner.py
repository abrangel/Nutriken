import re

with open('scripts/build_overlays.py', 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.split('\n')
pattern = re.compile(r'\b\d+(?:[-–—\s]|â€“|â€”|\xc3\xa2\xe2\x82\xac\xe2\x80\x9c|\?"|\?"){1,3}\[DOSIS_CLINICA_REMOVIDA\]')
pattern2 = re.compile(r'\b\d+\.?\d*\s*[-–—]\s*\[DOSIS_CLINICA_REMOVIDA\]')

for i, line in enumerate(lines):
    if 'hsa04930' in line: continue
    line = pattern.sub('[DOSIS_CLINICA_REMOVIDA]', line)
    line = pattern2.sub('[DOSIS_CLINICA_REMOVIDA]', line)
    lines[i] = line

with open('scripts/build_overlays.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
