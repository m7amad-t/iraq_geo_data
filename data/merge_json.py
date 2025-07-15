import json
from collections import defaultdict
import os

def load_json(filename):
    with open(filename, encoding='utf-8') as f:
        return json.load(f)

def save_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def normalize_name(d, key):
    # Prefer krdName, fallback to krdName
    if 'krdName' in d:
        d['krdName'] = d['krdName']
    elif 'krdName' in d:
        d['krdName'] = d['krdName']
    elif 'krdName' in d:
        d['krdName'] = d['krdName']
    elif 'krdName' in d:
        d['krdName'] = d['krdName']
    else:
        d['krdName'] = ''
    if 'krdName' in d:
        del d['krdName']
    return d

def merge_lists(list1, list2, key_fields):
    merged = {tuple(item[k] for k in key_fields): item for item in list1}
    for item in list2:
        k = tuple(item.get(k, '') for k in key_fields)
        if k in merged:
            # Merge subfields recursively if present
            for subkey in ['subdistricts', 'sub_districts', 'villages']:
                if subkey in item and subkey in merged[k]:
                    merged[k][subkey] = merge_lists(
                        merged[k][subkey], item[subkey], ['engName'])
                elif subkey in item:
                    merged[k][subkey] = item[subkey]
        else:
            merged[k] = item
    return list(merged.values())

def clean_province(prov):
    # Standardize krdName/krdName
    prov = normalize_name(prov, 'krdName')
    # Merge sub_districts into districts if present
    if 'sub_districts' in prov:
        if 'districts' not in prov:
            prov['districts'] = []
        for subd in prov['sub_districts']:
            prov['districts'].append({
                'engName': subd.get('engName', ''),
                'krdName': subd.get('krdName', ''),
                'arbName': subd.get('arbName', ''),
                'subdistricts': [],
                'villages': subd.get('villages', [])
            })
        del prov['sub_districts']
    # Clean districts
    if 'districts' in prov:
        new_districts = []
        for d in prov['districts']:
            d = normalize_name(d, 'krdName')
            # Standardize subdistricts
            if 'subdistricts' in d:
                d['subdistricts'] = [normalize_name(sd, 'krdName') for sd in d['subdistricts']]
            elif 'sub_districts' in d:
                d['subdistricts'] = [normalize_name(sd, 'krdName') for sd in d['sub_districts']]
                del d['sub_districts']
            else:
                d['subdistricts'] = []
            new_districts.append(d)
        prov['districts'] = new_districts
    return prov

def main():
    kfile = 'kurdistan.json'
    sfile = 'source2.json'
    ofile = 'output.json'
    kdata = load_json(kfile)
    sdata = load_json(sfile)
    kprovs = kdata['provinces'] if 'provinces' in kdata else kdata.get('country', [])
    sprovs = sdata['provinces']
    # Clean and normalize
    kprovs = [clean_province(p) for p in kprovs]
    sprovs = [clean_province(p) for p in sprovs]
    # Merge provinces by engName
    merged = merge_lists(kprovs, sprovs, ['engName'])
    # Remove empty/duplicate fields
    for prov in merged:
        if 'districts' in prov:
            prov['districts'] = merge_lists(prov['districts'], [], ['engName'])
            for d in prov['districts']:
                if 'subdistricts' in d:
                    d['subdistricts'] = merge_lists(d['subdistricts'], [], ['engName'])
    save_json({'provinces': merged}, ofile)

if __name__ == '__main__':
    main() 