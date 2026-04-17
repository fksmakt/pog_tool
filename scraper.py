import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_URL = 'https://tep.sakura.ne.jp/pog'
USER_ID = '8'
PASSWORD = 'sika'
YEAR = 2026
CACHE_DIR = Path(__file__).parent / 'cache'
CACHE_DIR.mkdir(exist_ok=True)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': f'{BASE_URL}/index.php?year={YEAR}',
    'Origin': 'https://tep.sakura.ne.jp',
}


def get_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    s.cookies.set('lovepogid', USER_ID, domain='tep.sakura.ne.jp')
    s.cookies.set('lovepogpass', PASSWORD, domain='tep.sakura.ne.jp')
    return s


def _parse_advice_html(html: bytes) -> list[dict]:
    """
    Parse advice.php HTML (bytes) and return list of horse dicts.

    The page uses uppercase HTML tags (TR/TD/TABLE) which confuse html.parser,
    so lxml is required for correct parsing.

    Structure per horse (100 horses, each maps to one echo div by position):
      <TD class='cen'>No.X</TD>          — rank
      <A class='horse'>馬名</A>          — horse name (sibling in same TR)
      <TD class='ts'>父：... 母：...</TD> — sire/dam (sibling in same TR)
      <TD class='zaikyu'>厩舎 name (stable)...</TD> — trainer (next TR)
      <DIV class='echo'><UL><LI>...</LI></UL></DIV> — connections (paired by index)
    """
    soup = BeautifulSoup(html, 'lxml', from_encoding='utf-8')
    main = soup.find('div', id='NoColumn')
    if not main:
        return []

    # rank cells and echo divs appear in the same order (1:1 pairing by index)
    rank_cells = main.find_all('td', class_='cen')
    echo_divs = main.find_all('div', class_='echo')

    results = []

    for i, rank_cell in enumerate(rank_cells):
        rank_text = rank_cell.get_text(strip=True)
        rank_m = re.match(r'No\.(\d+)', rank_text)
        if not rank_m:
            continue
        rank = int(rank_m.group(1))

        # Horse name: <a class="horse"> in the same <tr>
        parent_tr = rank_cell.find_parent('tr')
        if not parent_tr:
            continue

        horse_link = parent_tr.find('a', class_='horse')
        horse_name = horse_link.get_text(strip=True) if horse_link else ''

        # Sire/dam: <td class="ts"> in the same <tr>
        ts_td = parent_tr.find('td', class_='ts')
        sire = ''
        dam = ''
        if ts_td:
            ts_text = ts_td.get_text(' ', strip=True)
            sire_m = re.search(r'父[：:]\s*(\S+)', ts_text)
            dam_m = re.search(r'母[：:]\s*(\S+)', ts_text)
            if sire_m:
                sire = sire_m.group(1)
            if dam_m:
                dam = dam_m.group(1)

        # Trainer/stable: <td class="zaikyu"> in the next sibling <tr>
        trainer = ''
        stable = ''
        next_tr = parent_tr.find_next_sibling('tr')
        if next_tr:
            zaikyu_td = next_tr.find('td', class_='zaikyu')
            if zaikyu_td:
                z_text = zaikyu_td.get_text(' ', strip=True)
                trainer_m = re.search(r'厩舎\s+(.+?)\s+\(([^)]+)\)', z_text)
                if trainer_m:
                    trainer = trainer_m.group(1).strip()
                    stable = trainer_m.group(2).strip()

        # Connections: paired echo div at same index
        connections = []
        if i < len(echo_divs):
            for li in echo_divs[i].find_all('li'):
                connections.append(li.get_text(' ', strip=True))

        results.append({
            'rank': rank,
            'horse_name': horse_name,
            'sire': sire,
            'dam': dam,
            'trainer': trainer,
            'stable': stable,
            'connections': connections,
        })

    return results


def fetch_advice(sex: int, use_cache: bool = True) -> list[dict]:
    """sex=1:牡, sex=2:牝"""
    cache_file = CACHE_DIR / f'advice_{"male" if sex == 1 else "female"}.json'
    if use_cache and cache_file.exists():
        age = time.time() - cache_file.stat().st_mtime
        if age < 3600:  # 1時間キャッシュ
            return json.loads(cache_file.read_text(encoding='utf-8'))

    s = get_session()
    url = f'{BASE_URL}/advice.php?UserId={USER_ID}&year={YEAR}&sex={sex}'
    r = s.get(url, timeout=30)
    r.raise_for_status()
    data = _parse_advice_html(r.content)
    if not data:
        raise ValueError(f"0頭しか取得できませんでした: {url} — 認証またはHTMLの構造を確認してください")
    cache_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    return data


def build_draft_payload(male_ids: list[str], female_ids: list[str]) -> dict:
    return {
        'draftEntry1': '\n'.join(male_ids[:50]),
        'draftEntry2': '\n'.join(female_ids[:50]),
        'draftEntry': 'この内容で登録する',
    }


def submit_draft(male_ids: list[str], female_ids: list[str]) -> dict:
    """ぽぐ！にリストを送信する。戻り値: {'success': bool, 'message': str}"""
    s = get_session()
    payload = build_draft_payload(male_ids, female_ids)
    url = f'{BASE_URL}/draftEntry.php?year={YEAR}'
    r = s.post(url, data=payload, timeout=30)
    r.raise_for_status()

    soup = BeautifulSoup(r.content, 'lxml', from_encoding='utf-8')
    main = soup.find('div', id='NoColumn') or soup.find('body')
    text = main.get_text(' ', strip=True) if main else r.text[:200]

    if '登録' in text and ('完了' in text or '受付' in text or 'リスト順' in text):
        return {'success': True, 'message': '登録完了しました！'}
    elif 'エラー' in text or 'error' in text.lower():
        return {'success': False, 'message': f'エラー: {text[:200]}'}
    else:
        return {'success': True, 'message': f'送信完了（応答: {text[:100]}）'}
