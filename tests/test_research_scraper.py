import sys
sys.path.insert(0, r'C:\Users\aktfk\pog-tool')
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from research_scraper import (
    get_past_nominated_mares,
    get_reideouro_offspring,
    load_research_cache,
    save_research_cache,
    CACHE_REIDEOURO,
    CACHE_PAST_MARES,
)

def test_get_reideouro_offspring_returns_list():
    result = get_reideouro_offspring()
    assert isinstance(result, list)
    assert len(result) > 0

def test_reideouro_offspring_has_required_keys():
    result = get_reideouro_offspring()
    item = result[0]
    for key in ['horse_name', 'sex', 'dam', 'trainer', 'reg_no', 'achievement_flag']:
        assert key in item, f"キー '{key}' がありません"

def test_get_past_nominated_mares_offspring_returns_list():
    result = get_past_nominated_mares()
    assert isinstance(result, list)

def test_past_mares_offspring_has_required_keys():
    result = get_past_nominated_mares()
    if len(result) == 0:
        return
    item = result[0]
    for key in ['horse_name', 'sex', 'dam', 'dam_nominated_year', 'reg_no']:
        assert key in item, f"キー '{key}' がありません"

def test_save_and_load_cache(tmp_path):
    cache_file = tmp_path / 'test_cache.json'
    data = [{'horse_name': 'テスト馬', 'sex': '牡'}]
    save_research_cache(cache_file, data)
    loaded = load_research_cache(cache_file, ttl_hours=24)
    assert loaded == data

def test_load_cache_expired_returns_none(tmp_path):
    import time
    import os
    cache_file = tmp_path / 'test_cache.json'
    data = [{'horse_name': 'テスト馬'}]
    save_research_cache(cache_file, data)
    old_time = time.time() - 90000  # 25時間前
    os.utime(cache_file, (old_time, old_time))
    result = load_research_cache(cache_file, ttl_hours=24)
    assert result is None

def test_fetch_netkeiba_profile_returns_dict():
    from research_scraper import fetch_netkeiba_profile
    result = fetch_netkeiba_profile('2024100195')
    assert isinstance(result, dict)
    assert 'trainer' in result
    assert 'comment' in result
    assert 'siblings_prize' in result

def test_fetch_netkeiba_profile_unknown_horse():
    from research_scraper import fetch_netkeiba_profile
    result = fetch_netkeiba_profile('0000000000')
    assert result['comment'] == ''
    assert result['trainer'] == ''
