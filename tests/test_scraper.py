import sys
sys.path.insert(0, r'C:\Users\aktfk\pog-tool')
from scraper import get_session, fetch_advice

def test_get_session_returns_session_with_cookies():
    s = get_session()
    assert s.cookies.get('lovepogid') == '8'
    assert s.cookies.get('lovepogpass') == 'sika'

def test_fetch_advice_male_returns_list():
    result = fetch_advice(sex=1)
    assert isinstance(result, list)
    assert len(result) > 0

def test_fetch_advice_each_item_has_required_keys():
    result = fetch_advice(sex=1)
    item = result[0]
    assert 'horse_name' in item
    assert 'sire' in item
    assert 'dam' in item
    assert 'connections' in item
    assert isinstance(item['connections'], list)

from scraper import build_draft_payload

def test_build_draft_payload_formats_correctly():
    male_ids = ['2024100001', '2024100002', '2024100003']
    female_ids = ['2024200001', '2024200002']
    payload = build_draft_payload(male_ids, female_ids)
    assert payload['draftEntry1'] == '2024100001\n2024100002\n2024100003'
    assert payload['draftEntry2'] == '2024200001\n2024200002'
    assert payload['draftEntry'] == 'この内容で登録する'

def test_build_draft_payload_max_50():
    male_ids = [str(i) for i in range(60)]   # 60頭（上限超え）
    female_ids = ['2024200001']
    payload = build_draft_payload(male_ids, female_ids)
    lines = payload['draftEntry1'].split('\n')
    assert len(lines) == 50
