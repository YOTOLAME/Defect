#!/usr/bin/env python3
"""Build a report draft (tepa-report-draft JSON) from a Field Capture ZIP and a mapping file.

Usage:
  python3 gen_draft.py CAPTURE.zip MAPPING.json FORMS_DIR OUT.json

MAPPING.json:
{
  "inspector": "PEIGNIER Loic",
  "items": [
    {"obs": 1, "form": "INSPECTARE-PSV-MOBILE.html", "q": "4.12",
     "comment": "Factual OVID-style comment, past tense.", "photos": [1],
     "subject": "Liquid Bulk Manifold Condition",
     "action": "CTR to label the manifold and provide evidence of completion."}
  ],
  "synergi": {"INSPECTARE-PSV-MOBILE.html": {"type": "Marine Inspection"}}   (optional overrides)
}
"photos" = 1-based indexes of the observation's photos (omit = all photos of that observation).
Answers (YES/NO/N/A) are left blank for the inspector; the Observation box is ticked.
"""
import base64
import html
import json
import os
import re
import sys
import zipfile


def load_form(path):
    s = open(path, encoding='utf-8').read()
    key = re.search(r'var STORAGE_KEY = "([^"]+)"', s).group(1)
    nums = json.loads(re.search(r'var Q_NUMS = (\{.*?\});', s, re.S).group(1))
    title = html.unescape(re.search(r'<title>(.*?)</title>', s, re.S).group(1)).strip()
    return {'key': key, 'num2qid': {v: k for k, v in nums.items()}, 'title': title}


DP_FORMS = ('OVID-DP-OPERATIONS-MOBILE.html', 'INSPECTARE-500M-MOBILE.html', 'INSPECTARE-500M-ASSET-MOBILE.html')


def synergi_label(title):
    if title.startswith('OVID -- '):
        return title.replace(' -- ', ' - ', 1)
    return title.replace(' -- ', ' ', 1)


def main(zpath, mpath, forms_dir, out):
    z = zipfile.ZipFile(zpath)
    insp = json.loads(z.read('inspection.json').decode('utf-8'))
    mapping = json.load(open(mpath, encoding='utf-8'))
    obs_by_no = {o['no']: o for o in insp['observations']}

    forms = {}
    for f in insp['forms']:
        info = load_form(os.path.join(forms_dir, f))
        forms[f] = {
            'file': f, 'storageKey': info['key'], 'title': info['title'],
            'meta': {'vessel': insp['vesselName'], 'insp_date': insp['inspectionDate'],
                     'inspector': mapping.get('inspector', ''), 'port': insp.get('location', ''),
                     'status': 'In Progress'},
            'answers': {}, 'obs': {}, 'comments': {}, 'photos': {}, '_num2qid': info['num2qid'],
            'synergi': dict({'type': 'DP Inspection' if f in DP_FORMS else 'Marine Inspection',
                             'label': synergi_label(info['title']), 'items': {}},
                            **mapping.get('synergi', {}).get(f, {})),
        }

    errors = []
    used_obs = set()
    for it in mapping['items']:
        fm = forms.get(it['form'])
        if not fm:
            errors.append('form not in inspection: %s' % it['form']); continue
        qid = fm['_num2qid'].get(it['q'])
        if not qid:
            errors.append('question %s not in %s' % (it['q'], it['form'])); continue
        o = obs_by_no.get(it['obs'])
        if not o:
            errors.append('observation %s not found' % it['obs']); continue
        used_obs.add(it['obs'])
        if not it.get('subject'):
            errors.append('missing subject for %s %s' % (it['form'], it['q'])); continue
        fm['synergi']['items'][qid] = {'subject': it['subject'].strip(), 'action': it.get('action', '').strip()}
        fm['obs'][qid] = True
        prev = fm['comments'].get(qid)
        fm['comments'][qid] = (prev + '\n' if prev else '') + it['comment'].strip()
        idx = it.get('photos')
        sel = o['photos'] if idx is None else [o['photos'][i - 1] for i in idx]
        for p in sel:
            fm['photos'].setdefault(qid, []).append(
                'data:image/jpeg;base64,' + base64.b64encode(z.read(p)).decode('ascii'))

    if errors:
        sys.exit('ERRORS:\n' + '\n'.join(errors))

    for fm in forms.values():
        del fm['_num2qid']
    draft = {
        'format': 'tepa-report-draft', 'version': 1,
        'id': '%s|%s|%s' % (insp['vesselName'], insp['inspectionDate'], insp['checklist']),
        'vesselName': insp['vesselName'], 'checklist': insp['checklist'],
        'inspectionDate': insp['inspectionDate'],
        'forms': [forms[f] for f in insp['forms']],
    }
    json.dump(draft, open(out, 'w', encoding='utf-8'), ensure_ascii=False)
    unmapped = sorted(set(obs_by_no) - used_obs)
    print('forms: %d, items: %d, unmapped observations: %s'
          % (len(forms), len(mapping['items']), unmapped or 'none'))


if __name__ == '__main__':
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    main(*sys.argv[1:])
