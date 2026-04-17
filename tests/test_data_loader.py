import sys
sys.path.insert(0, r'C:\Users\aktfk\pog-tool')
import pandas as pd
from data_loader import load_horses

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
