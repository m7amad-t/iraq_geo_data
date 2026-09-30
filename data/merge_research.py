#!/usr/bin/env python3
"""Merge researched governorate/district/subdistrict data into data/output.json.

Matching strategy: Arabic name first (strong signal), then normalized English,
then an explicit alias map. Old entries that match nothing are retried as
subdistricts (Kirkuk/Sulaymaniyah had nahiyas listed as districts); Baghdad's
municipal districts are kept with a provenance note; wrong-governorate entries
(e.g. Muthanna's Afak) are merged into their correct governorate.
"""
import json, re, unicodedata, copy, os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def norm_en(s):
    if not s: return '', None
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    s = s.lower()
    m = re.match(r'^(.*?)\((.*?)\)\s*$', s)  # "Tooz (Tuz Khurmatu)" -> try inner too
    cands = [s]
    if m:
        cands = [m.group(1), m.group(2)]
    out = []
    for c in cands:
        c = re.sub(r"^(al|ar|as|ad|at|an|ash|az)-", "", c)   # Al-, Ar- ...
        c = re.sub(r"^(al|ar|as|ad|at|an|ash|az) ", "", c)   # Al ...
        c = re.sub(r"^(nahiyat|nahiat|nahiya)[ -]?", "", c)  # Nahiyat X
        c = re.sub(r'[^a-z0-9]', '', c)
        out.append(c)
    return out[0], (out[1] if len(out) > 1 else None)

def norm_ar(s):
    if not s: return ''
    s = re.sub(r'[\u064B-\u0652\u0670]', '', s)
    s = s.replace('\u0640', '')
    s = re.sub(r'[أإآٱ]', 'ا', s)
    s = s.replace('ة', 'ه').replace('ى', 'ي')
    # Sorani Kurdish letters -> Arabic equivalents for matching
    for a, b in [('ێ', 'ي'), ('ۆ', 'و'), ('ڕ', 'ر'), ('ڵ', 'ل'), ('گ', 'ك'),
                 ('چ', 'ج'), ('پ', 'ب'), ('ژ', 'ز'), ('ڤ', 'ف'), ('ک', 'ك'),
                 ('ە', 'ه'), ('ھ', 'ه')]:
        s = s.replace(a, b)
    s = re.sub(r'[^\u0600-\u06FF]', '', s)
    s = s.replace('قضاء', '').replace('ناحيه', '').replace('ناحية', '')
    if s.startswith('ال') and len(s) > 3:
        s = s[2:]
    return s

# normalized-old-english -> normalized-research-english
ALIASES = {
    'dubz': 'dibis',
    'baladrooz': 'baladruz',
    'mejaralkabi': 'majaralkabir',
    'dayr': 'dair',
    'suqalshuykh': 'suqalshuyukh',
    'dashtihawler': 'binaslawa',
    'khoramal': 'khurmal',
    'semel': 'sumel',
    'penjwen': 'penjween',
    'sharazur': 'sharazoor',
    'darbendikhan': 'darbandikhan',
    'biyara': 'biyare',
    'sadrcity': 'sadrcity1',
    'hamza': 'hamzaalsharqi',
    'afak': 'afaq',
    'tuwayrij': 'hindiya',
    'tooz': 'tuzkhurmatu',
    # subdistrict transliteration variants
    'tazehkormatoo': 'tazakhurmatu',
    'yachii': 'yayji',
    'qerehnejir': 'qarahhanjir',
    'isiwa': 'esewa',
    'zharawa': 'jarawa',
    'halsho': 'helsho',
    'mangeshk': 'mankishki',
    'mankish': 'mankishki',
    'dartu': 'darato',
    'daratu': 'darato',
    'rya': 'riyadh',
    'abeasi': 'abbasi',
    'sarsang': 'sarsing',
    'faidie': 'faida',
    'salahuddinpiramam': 'salahaldin',
    'basirma': 'basarma',
    'diyanan': 'diyana',
    'saidkan': 'sidakan',
    'mazna': 'mazne',
    'shirawamazin': 'sherwanmazin',
    'shorsh': 'shorish',
    'sektan': 'siktan',
    'segirdkan': 'segrdkan',
    'dareshkeran': 'darashakran',
}

def en_key(s):
    k, inner = norm_en(s)
    return ALIASES.get(k, k), (ALIASES.get(inner, inner) if inner else None)

def match_score(old, new):
    """Return match strength: 2 = arabic, 1 = english, 0 = none."""
    oa, na = norm_ar(old.get('arbName', '')), norm_ar(new.get('arb', ''))
    if oa and na and oa == na:
        return 2
    ok, oinner = en_key(old.get('engName', ''))
    nk, _ = en_key(new.get('eng', ''))
    if ok and nk and ok == nk:
        return 1
    if oinner and oinner == nk:
        return 1
    return 0

def merge_names(old, new):
    for f in ('krdName', 'arbName'):
        if not old.get(f) and new.get(f if f != 'krdName' else 'kur', ''):
            old[f] = new[f if f != 'krdName' else 'kur']
    if new.get('notes'):
        old['notes'] = (old.get('notes', '') + ' ' + new['notes']).strip()
    return old

def merge_subdistricts(old_list, new_list):
    out = list(old_list)
    for ns in new_list:
        best, bs = None, 0
        for os in out:
            sc = match_score(
                {'engName': os.get('engName', ''), 'arbName': os.get('arbName', '')},
                {'eng': ns.get('eng', ''), 'arb': ns.get('arb', '')})
            if sc > bs:
                best, bs = os, sc
        if best:
            merge_names(best, ns)
        else:
            out.append({'engName': ns.get('eng', ''), 'krdName': ns.get('kur', ''),
                        'arbName': ns.get('arb', '')} |
                       ({'notes': ns['notes']} if ns.get('notes') else {}))
    return out

def place_subdistrict_govwide(districts, sub):
    """Place an old-format entry into the best district of the governorate.
    Tries subdistrict-level match first, then district-level (as center)."""
    skey = {'engName': sub.get('engName', ''), 'arbName': sub.get('arbName', '')}
    best, bs = None, 0
    for nd in districts:
        for es in nd.get('subdistricts', []):
            sc = match_score(skey, {'eng': es.get('engName', ''), 'arb': es.get('arbName', '')})
            if sc > bs:
                best, bs = es, sc
    if best:
        merge_names(best, {'kur': sub.get('krdName', ''), 'arb': sub.get('arbName', ''),
                           'eng': sub.get('engName', ''), 'notes': sub.get('notes', '')})
        return True
    for nd in districts:
        if match_score(skey, {'eng': nd['engName'], 'arb': nd.get('arbName', '')}):
            entry = {'engName': sub.get('engName', ''), 'krdName': sub.get('krdName', ''),
                     'arbName': sub.get('arbName', '')}
            if sub.get('notes'):
                entry['notes'] = sub['notes']
            nd['subdistricts'] = merge_subdistricts(nd.get('subdistricts', []), [entry])
            return True
    return False


# (governorate-label, old-name) -> target district eng for manual placement as subdistrict
MANUAL_SUB_PLACE = {
    ('Kirkuk', 'Mela Abdulla'): ('Kirkuk', 'Nahiya from the original dataset; possibly renamed Al-Multaqa.'),
    ('Sulaymaniyah', 'Qaladze'): ('Pshdar', 'Town; district center of Pshdar (Qaladze). Its former nahiyas were merged into Pshdar district.'),
    ('Halabja (prov-level)', 'Sirwan'): ('Sirwan', ''),
    ('Halabja (prov-level)', 'Biyara'): ('Biyare', ''),
    ('Halabja (prov-level)', 'Bamo'): ('Bamo', ''),
}

# (governorate, district-after-rename, subdistrict-key, target-district) for known misplacements
MANUAL_MOVES = [
    ('Kirkuk', 'Dibis', 'rya', 'Hawija'),
    ('Kirkuk', 'Dibis', 'abeasi', 'Hawija'),
    ('Kirkuk', 'Dibis', 'zab', 'Hawija'),
]
def main():
    data = json.load(open(f'{REPO}/data/output.json', encoding='utf-8'))
    research = []
    for f in ['north', 'central', 'south', 'mid_euphrates', 'kurdistan']:
        research.extend(json.load(open(f'{REPO}/research/{f}.json', encoding='utf-8'))['governorates'])

    # move province-level subdistrict lists into their districts first
    prov_level_moves = {
        'Erbil': 'Erbil',   # Ankawa, Baharka, Shamamk -> Erbil district
        'Duhok': 'Duhok',   # Zawita, Mangeshk -> Duhok district
    }
    unmatched_old_districts = []   # (gov_eng, district) for report
    dropped = []

    for gov in data['provinces']:
        rgov = next((r for r in research if r['eng'] == gov['engName']), None)
        if not rgov:
            print('NO RESEARCH for', gov['engName'])
            continue
        if rgov.get('notes'):
            gov['notes'] = (gov.get('notes', '') + ' ' + rgov['notes']).strip()

        # collect prov-level subdistricts to relocate
        extra_subs = gov.pop('subdistricts', [])

        new_districts = []
        used_old = set()
        for rd in rgov['districts']:
            best, bs, bi = None, 0, -1
            for i, od in enumerate(gov.get('districts', [])):
                if i in used_old:
                    continue
                sc = match_score(od, rd)
                if sc > bs:
                    best, bs, bi = od, sc, i
            if best:
                used_old.add(bi)
                merge_names(best, rd)
                # adopt researched official English name as canonical
                if best['engName'] != rd['eng']:
                    best.setdefault('altNames', [])
                    if best['engName'] not in best['altNames']:
                        best['altNames'].append(best['engName'])
                    best['engName'] = rd['eng']
                best['subdistricts'] = merge_subdistricts(best.get('subdistricts', []), rd.get('subdistricts', []))
                if 'villages' not in best:
                    best['villages'] = []
                new_districts.append(best)
            else:
                nd = {'engName': rd.get('eng', ''), 'krdName': rd.get('kur', ''),
                      'arbName': rd.get('arb', ''), 'subdistricts': [], 'villages': []}
                if rd.get('notes'):
                    nd['notes'] = rd['notes']
                nd['subdistricts'] = merge_subdistricts([], rd.get('subdistricts', []))
                new_districts.append(nd)

        # leftover old districts: place their subdistricts individually, then the district itself
        leftovers = [od for i, od in enumerate(gov.get('districts', [])) if i not in used_old]
        for od in leftovers:
            # Baghdad municipal districts: keep with provenance note
            if gov['engName'] == 'Baghdad':
                od['notes'] = ((od.get('notes', '') + " Amanat Baghdad municipal district (kati'), not an official qada'a.").strip())
                new_districts.append(od)
                continue
            mkey = (gov['engName'], od['engName'])
            if mkey in MANUAL_SUB_PLACE:
                target, note = MANUAL_SUB_PLACE[mkey]
                td = next((d for d in new_districts
                           if en_key(d['engName'])[0] == en_key(target)[0]), None)
                if td:
                    entry = {'engName': od['engName'], 'krdName': od.get('krdName', ''),
                             'arbName': od.get('arbName', '')}
                    if note:
                        entry['notes'] = note
                    td['subdistricts'] = merge_subdistricts(td.get('subdistricts', []), [entry])
                    for sub in od.get('subdistricts', []):
                        place_subdistrict_govwide(new_districts, sub)
                    continue
            for sub in od.get('subdistricts', []):
                place_subdistrict_govwide(new_districts, sub)
            placed = False
            for nd in new_districts:
                if match_score(od, {'eng': nd['engName'], 'arb': nd.get('arbName', '')}):
                    merge_names(nd, {'kur': od.get('krdName', ''), 'arb': od.get('arbName', ''),
                                     'eng': od.get('engName', ''), 'notes': od.get('notes', '')})
                    if od['engName'] != nd['engName'] and od['engName'] not in nd.get('altNames', []):
                        nd.setdefault('altNames', []).append(od['engName'])
                    placed = True
                    break
            if placed:
                continue
            if place_subdistrict_govwide(new_districts, od):
                continue
            unmatched_old_districts.append((gov['engName'], od))

        gov['districts'] = new_districts

        # relocate former province-level subdistricts
        for es in extra_subs:
            tgt_name = prov_level_moves.get(gov['engName'])
            mkey = (gov['engName'] + ' (prov-level)', es.get('engName', ''))
            if mkey in MANUAL_SUB_PLACE:
                target, note = MANUAL_SUB_PLACE[mkey]
                td = next((d for d in gov['districts']
                           if en_key(d['engName'])[0] == en_key(target)[0]), None)
                if td:
                    entry = {'engName': es.get('engName', ''), 'krdName': es.get('krdName', ''),
                             'arbName': es.get('arbName', '')}
                    if note:
                        entry['notes'] = note
                    td['subdistricts'] = merge_subdistricts(td.get('subdistricts', []), [entry])
                    continue
            tgt = next((d for d in gov['districts']
                        if en_key(d['engName'])[0] == en_key(es.get('engName', ''))[0]), None)
            if tgt and tgt_name:  # name matches a district -> it belongs there as subdistrict? no: skip, research covers
                continue
            if tgt_name:
                td = next((d for d in gov['districts'] if en_key(d['engName'])[0] == en_key(tgt_name)[0]), None)
                if td:
                    td['subdistricts'] = merge_subdistricts(td['subdistricts'], [es])
                    continue
            unmatched_old_districts.append((gov['engName'] + ' (prov-level)', es))

    # cross-governorate rescue for unmatched old districts (e.g. Muthanna's Afak -> Qadisiyyah)
    still = []
    for govname, od in unmatched_old_districts:
        if '(prov-level)' in govname:
            still.append((govname, od))
            continue
        placed = False
        for gov in data['provinces']:
            for nd in gov['districts']:
                if match_score(od, {'eng': nd['engName'], 'arb': nd.get('arbName', '')}) == 2:
                    nd['subdistricts'] = merge_subdistricts(nd.get('subdistricts', []), od.get('subdistricts', []))
                    merge_names(nd, {'kur': od.get('krdName', ''), 'arb': '', 'notes': ''})
                    placed = True
                    break
            if placed:
                break
        if not placed:
            still.append((govname, od))

    print('\nUnmatched old entries (dropped or needs review):')
    for govname, od in still:
        print(f'  {govname}: {od.get("engName")} / {od.get("arbName")} subs={len(od.get("subdistricts", []))}')

    # known misplacements: move subdistrict from one district to another
    for govname, from_d, sub_key, to_d in MANUAL_MOVES:
        gov = next((g for g in data['provinces'] if g['engName'] == govname), None)
        if not gov:
            continue
        fd = next((d for d in gov['districts'] if en_key(d['engName'])[0] == en_key(from_d)[0]), None)
        td = next((d for d in gov['districts'] if en_key(d['engName'])[0] == en_key(to_d)[0]), None)
        if not fd or not td:
            continue
        moving = [s for s in fd.get('subdistricts', []) if en_key(s.get('engName', ''))[0] == sub_key]
        if moving:
            fd['subdistricts'] = [s for s in fd['subdistricts'] if s not in moving]
            for m in moving:
                place_subdistrict_govwide([td], m)

    # final cleanup: drop empty-name subdistricts, drop empty villages arrays
    for gov in data['provinces']:
        for d in gov.get('districts', []):
            d['subdistricts'] = [s for s in d.get('subdistricts', [])
                                 if s.get('engName') or s.get('arbName')]
            if not d.get('villages'):
                d.pop('villages', None)
            for s in d['subdistricts']:
                if not s.get('villages'):
                    s.pop('villages', None)

    json.dump(data, open(f'{REPO}/data/output.json', 'w', encoding='utf-8'),
              ensure_ascii=False, separators=(',', ':'))
    print('\nsaved.')

if __name__ == '__main__':
    main()
