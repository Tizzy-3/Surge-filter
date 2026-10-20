#!/usr/bin/env python3
"""Conservative cover-image exception for fmz200 Surge module.

Preserve NetEase Music ad blocking, scripts, MITM, and unrelated apps.
Only remove image reject/tiny-gif rules for the NetEase cover CDN.
"""
import argparse
import difflib
import json
import re
import urllib.request
from pathlib import Path

SOURCE = 'https://raw.githubusercontent.com/fmz200/wool_scripts/main/Surge/module/blockAds.module'



def is_cover_rule(section: str, line: str) -> bool:
    """Match only image-blocking rules for p*.music.126.net cover hosts.

    The source uses escaped regex patterns; normalize only escaped dots and slashes.
    Never remove ad-specific iadmusicmat/admusicpic hosts.
    """
    if section not in {'URL Rewrite', 'Map Local'}:
        return False
    flat = line.replace(r'\.', '.').replace(r'\/', '/')
    # Covers p.c.music.126.net, p1.music.126.net, p\d.music.126.net,
    # and p[^4](c)?.music.126.net; does not cover iadmusicmat.music.126.net.
    cover_host = re.search(r'(?i)//p[^/\s]*?\.music\.126\.net', flat)
    if not cover_host:
        return False
    if section == 'URL Rewrite':
        return bool(re.search(r'(?i)\s-\sreject(?:\s|$)', line))
    return bool(re.search(r'(?i)\bdata-type=tiny-gif\b', line))


def transform(source: str, keyword: str = r'music\.126'):
    """Return filtered module and report; keyword retained for CLI compatibility."""
    section = ''
    kept, removed = [], []
    for number, line in enumerate(source.splitlines(keepends=True), 1):
        stripped = line.strip()
        header = re.fullmatch(r'\[([^\]]+)\]', stripped)
        if header:
            section = header.group(1)
        if stripped and not stripped.startswith(('#', ';')) and is_cover_rule(section, stripped):
            removed.append({'line': number, 'section': section, 'content': stripped})
        else:
            kept.append(line)
    if '[URL Rewrite]' not in source or '[MITM]' not in source:
        raise ValueError('Missing expected Surge sections')
    if not removed:
        raise ValueError('No cover-image rules matched; upstream may have changed')
    result = ''.join(kept)
    if len(result) < len(source) * .5:
        raise ValueError('Unexpectedly large removal')
    return result, removed


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', help='Use local source for testing')
    p.add_argument('--output', default='blockAds-filtered.sgmodule')
    p.add_argument('--keyword', default=r'music\.126', help='Legacy argument; V3 uses cover-image matching')
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()
    if args.input:
        original = Path(args.input).read_text(encoding='utf-8-sig')
    else:
        request = urllib.request.Request(SOURCE, headers={'User-Agent': 'Surge-Filter/1.2'})
        with urllib.request.urlopen(request, timeout=40) as response:
            original = response.read().decode('utf-8-sig')
    result, removed = transform(original, args.keyword)
    report = {'source': SOURCE, 'strategy': 'cover-image-only-v3',
              'preserved': ['Rule', 'Script', 'MITM', 'other Map Local'],
              'removed_count': len(removed), 'removed': removed}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.dry_run:
        print(''.join(difflib.unified_diff(original.splitlines(True), result.splitlines(True), fromfile='upstream', tofile='filtered')))
    else:
        Path(args.output).write_text(result, encoding='utf-8')
        Path('filter-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
