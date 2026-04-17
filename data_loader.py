# POG馬データローダー。
# Documents/POG_LIST (2).xlsx を読み込んでDataFrameを返す。
# load_horses() はプロセス内でキャッシュされる。呼び出し側はDataFrameをin-placeで変更しないこと。
import pandas as pd
from functools import lru_cache

from scraper import fetch_advice

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
    try:
        df = pd.read_excel(EXCEL_PATH, engine='openpyxl')
    except Exception as e:
        raise RuntimeError(
            f"Excelファイルの読み込みに失敗しました: {EXCEL_PATH}\n原因: {e}"
        ) from e
    cols = [c for c in COLUMN_MAP.keys() if c in df.columns]
    df = df[cols].rename(columns=COLUMN_MAP)
    df['血統登録番号'] = df['血統登録番号'].astype(str).str.strip()
    # 称号候補/称号説明はTask4のapply_achievement_flagsで上書きされる初期値
    df['称号候補'] = False
    df['称号説明'] = ''
    return df.copy()


def fetch_advice_both() -> list[dict]:
    return fetch_advice(sex=1) + fetch_advice(sex=2)


def apply_achievement_flags(df: pd.DataFrame, advice: list[dict]) -> pd.DataFrame:
    df = df.copy()
    advice_names = {item['horse_name']: item for item in advice}
    for idx, row in df.iterrows():
        horse_name = str(row.get('馬名', ''))
        if horse_name in advice_names:
            item = advice_names[horse_name]
            df.at[idx, '称号候補'] = True
            conn_str = ' / '.join(item['connections'][:3]) if item['connections'] else ''
            df.at[idx, '称号説明'] = conn_str
    return df


@lru_cache(maxsize=1)
def load_horses_with_flags() -> pd.DataFrame:
    df = load_horses().copy()  # load_horsesのキャッシュを汚染しないようにコピー
    advice = fetch_advice_both()
    return apply_achievement_flags(df, advice)
