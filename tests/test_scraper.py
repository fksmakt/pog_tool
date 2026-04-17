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
