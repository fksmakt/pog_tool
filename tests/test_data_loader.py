import sys
sys.path.insert(0, r'C:\Users\aktfk\pog-tool')
import pandas as pd
from data_loader import load_horses, apply_achievement_flags, fetch_advice_both
from scraper import fetch_advice

def test_load_horses_returns_dataframe():
    df = load_horses()
    assert isinstance(df, pd.DataFrame)

def test_load_horses_has_required_columns():
    df = load_horses()
    required = ['血統登録番号', '馬名', '性別', '父名', '母名', '母父名', '産地', '取引価格']
    for col in required:
        assert col in df.columns, f"列 '{col}' が見つかりません"

def test_load_horses_sex_values():
    df = load_horses()
    assert set(df['性別'].dropna().unique()).issubset({'牡', '牝'})

def test_load_horses_count():
    df = load_horses()
    assert len(df) > 7000, f"馬の数が少なすぎます: {len(df)}"


def test_apply_achievement_flags_adds_flag_column():
    df = load_horses()
    advice = [
        {
            'rank': 1, 'horse_name': 'テスト馬', 'sire': 'エピファネイア',
            'dam': 'チェッキーノ', 'connections': ['テスト接続'],
            'trainer': '福永祐一', 'stable': '栗東',
        }
    ]
    result = apply_achievement_flags(df.copy(), advice)
    assert '称号候補' in result.columns
    assert '称号説明' in result.columns


def test_apply_achievement_flags_marks_matching_horse():
    df = load_horses()
    # advice内の馬名と一致する馬を確認
    advice = fetch_advice_both()
    result = apply_achievement_flags(df.copy(), advice)
    flagged = result[result['称号候補'] == True]
    assert len(flagged) > 0, "称号候補が1頭も見つかりません"
