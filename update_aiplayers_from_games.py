import re
import json
from pathlib import Path

GAMES = Path('games.txt')
AIJSON = Path('AIplayers.json')
BACKUP = Path('AIplayers.json.bak2')

# Canonical race list/order
CANON_RACES = [
    'Space Marines', 'Imperial Guard', 'Sisters of Battle', 'Orks',
    'Necrons', 'Chaos Marines', 'Eldar', 'Dark Eldar', 'Tau'
]

# Map loose race names -> canonical
RACE_CANON = {
    'sisters': 'Sisters of Battle',
    'sisters of battle': 'Sisters of Battle',
    'chaos': 'Chaos Marines',
    'chaos marines': 'Chaos Marines',
    'dark eldar': 'Dark Eldar',
    'necrons': 'Necrons',
    'imperial guard': 'Imperial Guard',
    'imperialguard': 'Imperial Guard',
    'orks': 'Orks',
    'ork': 'Orks',
    'space marines': 'Space Marines',
    'spacemarines': 'Space Marines',
    'eldar': 'Eldar',
    'tau': 'Tau'
}

# Normalization and fuzzy match helpers
def normalize_name(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())

# Levenshtein
def levenshtein(a, b):
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            add = prev[j] + 1
            delete = cur[j-1] + 1
            change = prev[j-1] + (0 if ca == cb else 1)
            cur.append(min(add, delete, change))
        prev = cur
    return prev[-1]

# Parse games.txt
stats = {}  # normalized player -> {canon_race: {'win':x,'loss':y}}
raw_names = {}  # normalized -> original name (first seen)

with GAMES.open() as f:
    for line in f:
        line = line.strip('\n')
        if not line:
            continue
        # split by tabs or multiple spaces
        cells = re.split(r'\t|\s{2,}', line)
        for cell in cells:
            cell = cell.strip()
            if not cell:
                continue
            # match e.g. 'Will-win-Necrons' or 'Circuit board-loss-Orks'
            m = re.match(r'^(.*?)-(win|loss)-(.*)$', cell, re.I)
            if not m:
                # skip entries like 'Jezz--' or 'Greg--'
                continue
            raw_player = m.group(1).strip()
            res = m.group(2).lower()
            race_raw = m.group(3).strip()
            n = normalize_name(raw_player)
            raw_names.setdefault(n, raw_player)
            # normalize race
            rc = RACE_CANON.get(race_raw.lower(), None)
            if rc is None:
                key = race_raw.lower().strip()
                if key in RACE_CANON:
                    rc = RACE_CANON[key]
                else:
                    # try removing trailing s
                    if key.endswith('s') and key[:-1] in RACE_CANON:
                        rc = RACE_CANON[key[:-1]]
                    else:
                        # as a fallback, try fuzzy match against canonical race names
                        best = None
                        bestd = None
                        for c in CANON_RACES:
                            d = levenshtein(key, c.lower())
                            if bestd is None or d < bestd:
                                bestd = d
                                best = c
                        if bestd is not None and bestd <= 5:
                            rc = best
                        else:
                            # unknown race; skip
                            continue
            player_stats = stats.setdefault(n, {})
            rct = player_stats.setdefault(rc, {'win': 0, 'loss': 0})
            rct[res] += 1

# Backup AIplayers.json
if AIJSON.exists():
    BACKUP.write_text(AIJSON.read_text())

ai = json.loads(AIJSON.read_text())
# map normalized ai names to index
ai_name_map = {normalize_name(r.get('name','')): idx for idx, r in enumerate(ai)}

added = []
updated = []

for n, s in stats.items():
    # find ai index
    if n in ai_name_map:
        idx = ai_name_map[n]
        rec = ai[idx]
    else:
        # fuzzy match
        best_idx = None
        bestd = None
        for an, idx in ai_name_map.items():
            d = levenshtein(n, an)
            if bestd is None or d < bestd:
                bestd = d
                best_idx = idx
        if bestd is not None and bestd <= 4:
            idx = best_idx
            rec = ai[idx]
        else:
            # create new record
            rec = {
                'scores': [[r,0,0] for r in CANON_RACES],
                'name': raw_names.get(n, n),
                'lastRaces': [0,0,0],
                'raceNumber': 0
            }
            ai.append(rec)
            idx = len(ai)-1
            ai_name_map[normalize_name(rec['name'])] = idx
            added.append(rec['name'])
    # apply counts: overwrite scores for canonical races
    for sc in rec.get('scores', []):
        race_name = sc[0]
        counts = s.get(race_name, {'win':0, 'loss':0})
        sc[1] = counts.get('win', 0)
        sc[2] = counts.get('loss', 0)
    updated.append(rec.get('name',''))

# write back
AIJSON.write_text(json.dumps(ai, indent=2))

print('Backup written to', BACKUP)
print('Players updated:', ', '.join(sorted(set(updated))))
if added:
    print('Players added:', ', '.join(added))

# Print stats summary
print('\nDerived stats:')
for n, s in stats.items():
    print(raw_names.get(n, n))
    for r, ct in s.items():
        print(f"  {r}: win={ct['win']}, loss={ct['loss']}")
