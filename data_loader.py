import pandas as pd
from functools import lru_cache

EXCEL_PATH = r'C:\Users\aktfk\Documents\POG_LIST (2).xlsx'

COLUMN_MAP = {
    'No.': 'No',
    '状態': '状態',
    '馬名': '馬名',
    '性別': '性別',
    '年齢': '年齢',
    '毛色': '毛色',
    '父名': '父名',
    '母名': '母名',
    '母父名': '母父名',
    '生産者': '生産者',
    '産地': '産地',
    '生年月日': '生年月日',
    '調教師': '調教師',
    '取引価格': '取引価格',
    '血統登録番号': '血統登録番号',
    '兄弟5頭本賞合計': '兄弟賞金合計',
    '兄弟5頭本賞平均': '兄弟賞金平均',
    '父チェックType': '父血統系統',
    '母父チェックType': '母父血統系統',
}

@lru_cache(maxsize=1)
def load_horses() -> pd.DataFrame:
    df = pd.read_excel(EXCEL_PATH, engine='openpyxl')
    # 必要な列だけ残す
    cols = [c for c in COLUMN_MAP.keys() if c in df.columns]
    df = df[cols].rename(columns=COLUMN_MAP)
    # 血統登録番号を文字列に統一
    df['血統登録番号'] = df['血統登録番号'].astype(str).str.strip()
    # 称号候補フラグの初期値
    df['称号候補'] = False
    df['称号説明'] = ''
    return df.copy()
