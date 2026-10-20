#!/usr/bin/env python3
"""Filter fmz200 Surge module without modifying unrelated rules or MITM.

This approximates QX #out=music\\.126 for rewrite lines, and additionally
excludes standalone [Rule] DOMAIN/DOMAIN-SUFFIX entries for music.126.net.
"""
import argparse
import difflib
import json
import re
import urllib.request
from pathlib import Path

SOURCE = 'https://raw.githubusercontent.com/fmz200/wool_scripts/main/Surge/module/blockAds.module'
REWRITE_SECTIONS = {'URL Rewrite'}
DOMAIN_TYPES = {'DOMAIN', 'DOMAIN-SUFFIX'}


def normalized(text: str) -> str:
    return text.replace(r'\.', '.')


def matches_rewrite(line: str, keyword: str) -> bool:
    """Match either regex-escaped or literal music.126 spelling."""
    candidate = normalized(line)
    return (normalized(keyword) in candidate or 'music.126.net' in candidate)


def matches_rule(line: str) -> bool:
    """Only target standalone domain entries; never touch shared rules."""
    fields = [part.strip() for part in line.split(',')]
    if len(fields) < 3 or fields[0] not in DOMAIN_TYPES:
        return False
    host = fields[1].lower().rstrip('.')
    return host == 'music.126.net' or host.endswith('.music.126.net')


def transform(source: str, keyword: str = r'music\.126'):
    section = ''
    kept, removed = [], []
    for index, line in enumerate(source.splitlines(keepends=True), 1):
        stripped = line.strip()
        header = re.fullmatch(r'\[([^\]]+)\]', stripped)
        if header:
            section = header.group(1)
        if not stripped or stripped.startswith(('#', ';')):
            kept.append(line)
            continue
        if section == 'Script' and matches_rewrite(line, keyword):
            raise ValueError(f'Matched [Script] at line {index}; manual review required: {stripped[:200]}')
        remove = ((section in REWRITE_SECTIONS and matches_rewrite(line, keyword))
                  or (section == 'Rule' and matches_rule(line)))
        if remove:
            removed.append({'line': index, 'section': section, 'content': stripped})
        else:
            kept.append(line)
    if '[URL Rewrite]' not in source or '[MITM]' not in source:
        raise ValueError('Missing expected Surge sections')
    if not removed:
        raise ValueError('No matching entries; upstream may have changed')
    result = ''.join(kept)
    if not result.strip() or len(result) < len(source) * .5:
        raise ValueError('Unexpectedly large removal')
    return result, removed


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', help='Use local source for testing')
    p.add_argument('--output', default='blockAds-filtered.sgmodule')
    p.add_argument('--keyword', default=r'music\.126')
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()
    if args.input:
        original = Path(args.input).read_text(encoding='utf-8-sig')
    else:
        request = urllib.request.Request(SOURCE, headers={'User-Agent': 'Surge-Filter/1.1'})
        with urllib.request.urlopen(request, timeout=40) as response:
            original = response.read().decode('utf-8-sig')
    result, removed = transform(original, args.keyword)
    report = {
        'source': SOURCE,
        'rewrite_keyword': args.keyword,
        'additional_exclusion': 'music.126.net (rewrite + standalone DOMAIN/DOMAIN-SUFFIX)',
        'removed_count': len(removed),
        'removed': removed,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.dry_run:
        print(''.join(difflib.unified_diff(original.splitlines(True), result.splitlines(True), fromfile='upstream', tofile='filtered')))
    else:
        Path(args.output).write_text(result, encoding='utf-8')
        Path('filter-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
