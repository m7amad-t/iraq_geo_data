#!/usr/bin/env python3
"""Dedup subdistricts within each district (and districts within each
governorate) in data/output.json, merging transliteration variants."""
import json, sys, re
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from merge_research import match_score, en_key

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def has_article(name):
    return bool(re.match(r'^(al|ar|as|ad|at|an|ash|az)[ -]', name or '', re.I))

def better_name(a, b, parent_key):
    """True if engName a is preferable to b."""
    ka, kb = en_key(a)[0], en_key(b)[0]
    if parent_key:
        if ka == parent_key and kb != parent_key:
            return True
        if kb == parent_key and ka != parent_key:
            return False
    aa, ab = has_article(a), has_article(b)
    if aa and not ab:
        return True
    if ab and not aa:
        return False
    return False

def dedup_list(entries, parent_name=None):
    out = []
    parent_key = en_key(parent_name)[0] if parent_name else None
    for e in entries:
        target = None
        for o in out:
            if match_score({'engName': e.get('engName', ''), 'arbName': e.get('arbName', '')},
                           {'eng': o.get('engName', ''), 'arb': o.get('arbName', '')}) >= 1:
                target = o
                break
        if target is None:
            out.append(e)
            continue
        for f in ('krdName', 'arbName'):
            if not target.get(f) and e.get(f):
                target[f] = e[f]
        if e.get('notes'):
            target['notes'] = (target.get('notes', '') + ' ' + e['notes']).strip()
        en, tn = e.get('engName', ''), target.get('engName', '')
        if en and tn and en != tn:
            if better_name(en, tn, parent_key):
                keep, alt = en, tn
            else:
                keep, alt = tn, en
            target['engName'] = keep
            target.setdefault('altNames', [])
            if alt not in target['altNames']:
                target['altNames'].append(alt)
        for a in e.get('altNames', []):
            target.setdefault('altNames', [])
            if a not in target['altNames'] and a != target.get('engName'):
                target['altNames'].append(a)
    return out

def main():
    d = json.load(open(f'{REPO}/data/output.json', encoding='utf-8'))
    for p in d['provinces']:
        for x in p['districts']:
            x['subdistricts'] = dedup_list(x.get('subdistricts', []), x.get('engName'))
            for e in [x] + x['subdistricts']:
                # krdName must hold Kurdish (Arabic-script) text; ASCII fillers came
                # from source data that duplicated the English name
                k = e.get('krdName', '')
                if k and not re.search(r'[\u0600-\u06FF]', k):
                    if k != e.get('engName') and k not in e.get('altNames', []):
                        e.setdefault('altNames', []).append(k)
                    e['krdName'] = ''
        p['districts'] = dedup_list(p['districts'])
    json.dump(d, open(f'{REPO}/data/output.json', 'w', encoding='utf-8'),
              ensure_ascii=False, separators=(',', ':'))
    print('deduped.')

if __name__ == '__main__':
    main()
