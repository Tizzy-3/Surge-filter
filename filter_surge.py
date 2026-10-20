#!/usr/bin/env python3
"""Conservative Surge rewrite filter; does not modify [Rule] or [MITM]."""
import argparse
import difflib
import json
import re
import urllib.request
from pathlib import Path

SOURCE = 'https://raw.githubusercontent.com/fmz200/wool_scripts/main/Surge/module/blockAds.module'
SECTIONS = {'URL Rewrite', 'Script'}


def matches(line: str, keyword: str) -> bool:
    # KOP-XIAO documents escaped dot in keyword parameters; this is a
    # conservative approximation, NOT execution of the QX parser.
    return keyword.replace(r'\.', '.') in line.replace(r'\.', '.')


def transform(source: str, keyword: str):
    section = ''
    kept, removed = [], []
    for index, line in enumerate(source.splitlines(keepends=True), 1):
        stripped = line.strip()
        match = re.fullmatch(r'\[([^\]]+)\]', stripped)
        if match:
            section = match.group(1)
        if section in SECTIONS and stripped and not stripped.startswith(('#', ';')) and matches(line, keyword):
            # Script entries can have coupled MITM requirements; fail rather than silently remove.
            if section == 'Script':
                raise ValueError(f'Matched a [Script] line {index}; requires manual review: {stripped[:200]}')
            removed.append({'line': index, 'section': section, 'content': stripped})
        else:
            kept.append(line)
    if '[URL Rewrite]' not in source or '[MITM]' not in source:
        raise ValueError('Missing expected Surge sections')
    if not removed:
        raise ValueError('No matching rewrite entries: upstream may have changed')
    result = ''.join(kept)
    # Preserve MITM, Rule and all other content by construction.
    if not result.strip() or len(result) < len(source) * .5:
        raise ValueError('Unexpectedly large removal')
    return result, removed


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', help='Use a local source for testing')
    p.add_argument('--output', default='blockAds-filtered.sgmodule')
    p.add_argument('--keyword', default=r'music\.126')
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()
    if args.input:
        original = Path(args.input).read_text(encoding='utf-8-sig')
    else:
        request = urllib.request.Request(SOURCE, headers={'User-Agent': 'Surge-Filter/1.0'})
        with urllib.request.urlopen(request, timeout=40) as response:
            original = response.read().decode('utf-8-sig')
    result, removed = transform(original, args.keyword)
    report = {'source': SOURCE, 'keyword': args.keyword, 'removed_count': len(removed), 'removed': removed}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.dry_run:
        print(''.join(difflib.unified_diff(original.splitlines(True), result.splitlines(True), fromfile='upstream', tofile='filtered')))
    else:
        Path(args.output).write_text(result, encoding='utf-8')
        Path('filter-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

if __name__ == '__main__':
    main()
