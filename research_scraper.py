import json
import re
import time
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

CACHE_DIR = Path(__file__).parent / 'cache'
CACHE_DIR.mkdir(exist_ok=True)

CACHE_REIDEOURO = CACHE_DIR / 'research_reideouro.json'
CACHE_PAST_MARES = CACHE_DIR / 'research_past_mares.json'

HISTORY_PATH = Path(__file__).parent / 'cache' / 'history.json'

_HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}


def load_research_cache(cache_file: Path, ttl_hours: float = 24) -> list | None:
    if not cache_file.exists():
        return None
    age = time.time() - cache_file.stat().st_mtime
    if age > ttl_hours * 3600:
        return None
    return json.loads(cache_file.read_text(encoding='utf-8'))


def save_research_cache(cache_file: Path, data: list) -> None:
    cache_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def _row_to_research_item(row: pd.Series, dam_nominated_year: int | None) -> dict:
    reg_no = str(row.get('血統登録番号', ''))
    horse_name = str(row.get('馬名', ''))
    return {
        'horse_name': horse_name,
        'sex': str(row.get('性別', '')),
        'dam': str(row.get('母名', '')),
        'sire': str(row.get('父名', '')),
        'trainer': str(row.get('調教師', '')),
        'stable': '',
        'reg_no': reg_no,
        'region': str(row.get('産地', '')),
        'price': str(row.get('取引価格', '')),
        'achievement_flag': bool(row.get('称号候補', False)),
        'achievement_desc': str(row.get('称号説明', '')),
        'dam_nominated_year': dam_nominated_year,
        'netkeiba_url': f'https://db.netkeiba.com/horse/{reg_no}/' if reg_no else '',
        'netkeiba_bbs_url': f'https://db.netkeiba.com/?pid=horse_board&id={reg_no}' if reg_no else '',
        'netkeiba': {
            'comment': '',
            'trainer': str(row.get('調教師', '')),
            'siblings': '',
            'siblings_prize': 0,
        },
        'umanariku': {'rank': 0, 'score': 0, 'comment': ''},
        'pog_ou': {'rank': 0, 'comment': ''},
    }


def get_reideouro_offspring(use_cache: bool = True) -> list[dict]:
    if use_cache:
        cached = load_research_cache(CACHE_REIDEOURO)
        if cached is not None:
            return cached
    from data_loader import load_horses_with_flags
    df = load_horses_with_flags()
    # 過去指名牝馬の仔はタブ2優先なので除外
    past_mare_names = _get_nominated_mare_names()
    rei = df[(df['父名'] == 'レイデオロ') & (~df['母名'].isin(past_mare_names))].copy()
    results = [_row_to_research_item(row, dam_nominated_year=None) for _, row in rei.iterrows()]
    save_research_cache(CACHE_REIDEOURO, results)
    return results


def _get_nominated_mare_names() -> set[str]:
    if not HISTORY_PATH.exists():
        return set()
    history = json.loads(HISTORY_PATH.read_text(encoding='utf-8'))
    names: set[str] = set()
    for horses in history.values():
        for h in horses:
            if h.get('sex') == '牝':
                names.add(h['name'])
    return names


def get_past_nominated_mares(use_cache: bool = True) -> list[dict]:
    if use_cache:
        cached = load_research_cache(CACHE_PAST_MARES)
        if cached is not None:
            return cached
    if not HISTORY_PATH.exists():
        return []
    history = json.loads(HISTORY_PATH.read_text(encoding='utf-8'))
    nominated_mares: dict[str, int] = {}
    for year_str, horses in history.items():
        year = int(year_str)
        for h in horses:
            if h.get('sex') == '牝':
                name = h['name']
                if name not in nominated_mares or year < nominated_mares[name]:
                    nominated_mares[name] = year
    from data_loader import load_horses_with_flags
    df = load_horses_with_flags()
    results = []
    for mare_name, nom_year in nominated_mares.items():
        foals = df[df['母名'] == mare_name]
        for _, row in foals.iterrows():
            results.append(_row_to_research_item(row, dam_nominated_year=nom_year))
    save_research_cache(CACHE_PAST_MARES, results)
    return results


def fetch_netkeiba_profile(reg_no: str) -> dict:
    """血統登録番号から netkeiba のプロフィール情報を取得する。失敗時は空dictを返す。"""
    url = f'https://db.netkeiba.com/horse/{reg_no}/'
    try:
        r = requests.get(url, headers=_HEADERS, timeout=15)
        r.raise_for_status()
        text = r.content.decode('euc-jp', errors='replace')
        soup = BeautifulSoup(text, 'lxml')

        trainer = ''
        siblings_text = ''
        comment = ''
        is_valid = False

        prof = soup.find('table', class_='db_prof_table')
        if prof:
            prof_text = prof.get_text(' ', strip=True)
            if re.search(r'生年月日\s+\d{4}年', prof_text):
                is_valid = True
                trainer_m = re.search(r'調教師\s+(\S+(?:\s+\S+)?)\s+(?:馬主|生産者)', prof_text)
                if trainer_m:
                    trainer = trainer_m.group(1).strip()
                kin_m = re.search(r'近親馬\s+(.+?)(?:\s{2,}|$)', prof_text)
                if kin_m:
                    siblings_text = kin_m.group(1).strip()

        if not is_valid:
            return {'trainer': '', 'comment': '', 'siblings': '', 'siblings_prize': 0}

        news_box = soup.find('div', class_='db_h_news_box')
        if news_box:
            items = news_box.find_all('li')
            if items:
                comment = items[0].get_text(' ', strip=True)

        return {
            'trainer': trainer,
            'comment': comment,
            'siblings': siblings_text,
            'siblings_prize': 0,
        }
    except Exception:
        return {'trainer': '', 'comment': '', 'siblings': '', 'siblings_prize': 0}


def enrich_with_netkeiba(items: list[dict], delay: float = 0.5) -> list[dict]:
    enriched = []
    for item in items:
        reg_no = item.get('reg_no', '')
        if reg_no and reg_no != 'nan':
            profile = fetch_netkeiba_profile(reg_no)
            item = item.copy()
            item['netkeiba'] = profile
            if not item['trainer'] and profile['trainer']:
                item['trainer'] = profile['trainer']
        enriched.append(item)
        time.sleep(delay)
    return enriched
