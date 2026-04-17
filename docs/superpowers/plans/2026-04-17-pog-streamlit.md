# POG Streamlit アプリ 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ぽぐ！の指名リスト作成を効率化するStreamlitアプリを構築する。称号狙い候補の自動ハイライト、リスト作成UIとサイト自動送信まで含む。

**Architecture:** Streamlitのマルチページアプリ。`data_loader.py`がExcelとキャッシュJSONを読み込んでDataFrameを提供し、`scraper.py`がぽぐ！サイトのスクレイピングと送信を担当。UIはすべて`app.py`とpages/配下のファイルで構成する。

**Tech Stack:** Python 3.x, Streamlit, pandas, openpyxl, requests, BeautifulSoup4, plotly

---

## ファイル構成

```
C:\Users\aktfk\pog-tool\
├── app.py                      # Streamlitエントリーポイント（ページナビゲーション）
├── pages\
│   ├── 1_馬リスト.py           # 全頭リスト・フィルタ・リスト追加
│   ├── 2_称号狙い.py           # 血統つながり候補の専用ページ
│   ├── 3_マイリスト.py         # 指名リスト管理・サイト送信
│   └── 4_分析.py               # 過去20年の傾向グラフ
├── data_loader.py              # Excel読み込み・データマージ
├── scraper.py                  # ぽぐ！スクレイピング・ログイン・送信
├── requirements.txt
├── cache\
│   ├── advice_male.json        # 称号候補（牡）キャッシュ
│   ├── advice_female.json      # 称号候補（牝）キャッシュ
│   └── history.json            # 過去指名履歴（既存JSONを流用）
└── tests\
    ├── test_data_loader.py
    └── test_scraper.py
```

---

## Task 1: プロジェクトセットアップ

**Files:**
- Create: `C:\Users\aktfk\pog-tool\requirements.txt`
- Create: `C:\Users\aktfk\pog-tool\app.py`
- Create: `C:\Users\aktfk\pog-tool\cache\.gitkeep`

- [ ] **Step 1: requirements.txtを作成する**

```
streamlit>=1.32.0
pandas>=2.0.0
openpyxl>=3.1.0
requests>=2.31.0
beautifulsoup4>=4.12.0
plotly>=5.18.0
```

- [ ] **Step 2: 依存関係をインストールする**

```bash
cd C:\Users\aktfk\pog-tool
python -m pip install -r requirements.txt
```

期待出力: `Successfully installed streamlit...` など

- [ ] **Step 3: cacheディレクトリを作成する**

```bash
mkdir -p cache
```

- [ ] **Step 4: app.pyのスケルトンを作成する**

```python
import streamlit as st

st.set_page_config(
    page_title="ぷにのPOGツール",
    page_icon="🏇",
    layout="wide",
)

st.title("🏇 ぷにのPOGツール 2026-2027")
st.markdown("""
左のサイドバーからページを選んでください。

- **馬リスト**: 全頭検索・フィルタ・リスト追加
- **称号狙い**: 血統つながり候補の一覧
- **マイリスト**: 指名リスト管理・ぽぐ！送信
- **分析**: 過去20年の傾向グラフ
""")
```

- [ ] **Step 5: Streamlitを起動して表示を確認する**

```bash
cd C:\Users\aktfk\pog-tool
streamlit run app.py
```

期待: ブラウザで `http://localhost:8501` が開き、タイトルが表示される

- [ ] **Step 6: コミットする**

```bash
git init
git add .
git commit -m "feat: プロジェクト初期セットアップ"
```

---

## Task 2: data_loader.py — Excelデータ読み込み

**Files:**
- Create: `C:\Users\aktfk\pog-tool\data_loader.py`
- Create: `C:\Users\aktfk\pog-tool\tests\test_data_loader.py`

- [ ] **Step 1: テストファイルを作成する**

```python
# tests/test_data_loader.py
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
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
cd C:\Users\aktfk\pog-tool
python -m pytest tests/test_data_loader.py -v
```

期待: `ImportError: cannot import name 'load_horses'`

- [ ] **Step 3: data_loader.pyを実装する**

```python
# data_loader.py
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
```

- [ ] **Step 4: テストを実行して確認する**

```bash
python -m pytest tests/test_data_loader.py -v
```

期待: 4テストすべてPASS

- [ ] **Step 5: コミットする**

```bash
git add data_loader.py tests/test_data_loader.py
git commit -m "feat: Excelデータ読み込みモジュール"
```

---

## Task 3: scraper.py — ぽぐ！認証と称号候補取得

**Files:**
- Create: `C:\Users\aktfk\pog-tool\scraper.py`
- Create: `C:\Users\aktfk\pog-tool\tests\test_scraper.py`

- [ ] **Step 1: テストを作成する**

```python
# tests/test_scraper.py
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
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
python -m pytest tests/test_scraper.py -v
```

期待: `ImportError: cannot import name 'get_session'`

- [ ] **Step 3: scraper.pyを実装する**

```python
# scraper.py
import json
import os
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_URL = 'https://tep.sakura.ne.jp/pog'
USER_ID = '8'
PASSWORD = 'sika'
YEAR = 2026
CACHE_DIR = Path(r'C:\Users\aktfk\pog-tool\cache')
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


def _parse_advice_html(html: str) -> list[dict]:
    soup = BeautifulSoup(html, 'html.parser')
    main = soup.find('div', id='NoColumn')
    if not main:
        return []

    results = []
    current = None

    for elem in main.descendants:
        if elem.name != 'p' and not hasattr(elem, 'find'):
            continue
        # 馬名ブロック検出（No.X で始まるdl/div）
        if elem.name in ['dl', 'div']:
            text = elem.get_text(' ', strip=True)
            m = re.match(r'No\.(\d+)\s+(\S+)', text)
            if m:
                if current:
                    results.append(current)
                # 父・母を抽出
                sire_m = re.search(r'父：\s*(\S+)', text)
                dam_m = re.search(r'母：\s*(\S+)', text)
                trainer_m = re.search(r'厩舎\s*(\S+)\s*\(([^)]+)\)', text)
                current = {
                    'rank': int(m.group(1)),
                    'horse_name': m.group(2),
                    'sire': sire_m.group(1) if sire_m else '',
                    'dam': dam_m.group(1) if dam_m else '',
                    'trainer': trainer_m.group(1) if trainer_m else '',
                    'stable': trainer_m.group(2) if trainer_m else '',
                    'connections': [],
                }
            elif current:
                # つながり行（年・馬名・成績）を収集
                year_m = re.findall(r'\[(\d{4})\]([^[]+)', text)
                for yr, detail in year_m:
                    current['connections'].append(detail.strip())

    if current:
        results.append(current)
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
    r = s.get(url)
    r.raise_for_status()
    data = _parse_advice_html(r.text)
    cache_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    return data
```

- [ ] **Step 4: テストを実行して確認する**

```bash
python -m pytest tests/test_scraper.py::test_get_session_returns_session_with_cookies -v
python -m pytest tests/test_scraper.py::test_fetch_advice_male_returns_list -v
python -m pytest tests/test_scraper.py::test_fetch_advice_each_item_has_required_keys -v
```

期待: 3テストすべてPASS（fetch_adviceはネットワークアクセスあり）

- [ ] **Step 5: コミットする**

```bash
git add scraper.py tests/test_scraper.py cache/
git commit -m "feat: ぽぐ！スクレイピング・称号候補取得"
```

---

## Task 4: data_loader.py — 称号候補マージ

**Files:**
- Modify: `C:\Users\aktfk\pog-tool\data_loader.py`
- Modify: `C:\Users\aktfk\pog-tool\tests\test_data_loader.py`

- [ ] **Step 1: テストを追加する**

`tests/test_data_loader.py` の末尾に追加:

```python
from data_loader import load_horses, apply_achievement_flags

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
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
python -m pytest tests/test_data_loader.py::test_apply_achievement_flags_adds_flag_column -v
```

期待: `ImportError: cannot import name 'apply_achievement_flags'`

- [ ] **Step 3: data_loader.pyに関数を追加する**

`data_loader.py` の末尾に追加:

```python
from scraper import fetch_advice

def fetch_advice_both() -> list[dict]:
    return fetch_advice(sex=1) + fetch_advice(sex=2)


def apply_achievement_flags(df: pd.DataFrame, advice: list[dict]) -> pd.DataFrame:
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
    df = load_horses()
    advice = fetch_advice_both()
    return apply_achievement_flags(df, advice)
```

- [ ] **Step 4: テストを実行する**

```bash
python -m pytest tests/test_data_loader.py -v
```

期待: すべてPASS

- [ ] **Step 5: コミットする**

```bash
git add data_loader.py tests/test_data_loader.py
git commit -m "feat: 称号候補フラグのマージ処理"
```

---

## Task 5: Page 1 — 馬リスト画面

**Files:**
- Create: `C:\Users\aktfk\pog-tool\pages\1_馬リスト.py`

- [ ] **Step 1: pages/1_馬リスト.pyを作成する**

```python
# pages/1_馬リスト.py
import streamlit as st
import pandas as pd
from data_loader import load_horses_with_flags

st.set_page_config(page_title="馬リスト", layout="wide")
st.title("🐎 馬リスト")

# セッション状態の初期化
if 'male_list' not in st.session_state:
    st.session_state.male_list = []   # 血統登録番号のリスト
if 'female_list' not in st.session_state:
    st.session_state.female_list = []

with st.spinner("データ読み込み中..."):
    df = load_horses_with_flags()

# ===== フィルタ =====
with st.sidebar:
    st.header("🔍 フィルタ")
    sex_filter = st.radio("性別", ["全て", "牡", "牝"])
    sire_filter = st.text_input("父名（部分一致）")
    achievement_only = st.checkbox("🏆 称号候補のみ表示")
    price_filter = st.checkbox("取引価格あり（--以外）")

filtered = df.copy()
if sex_filter != "全て":
    filtered = filtered[filtered['性別'] == sex_filter]
if sire_filter:
    filtered = filtered[filtered['父名'].str.contains(sire_filter, na=False)]
if achievement_only:
    filtered = filtered[filtered['称号候補'] == True]
if price_filter:
    filtered = filtered[~filtered['取引価格'].astype(str).str.contains('--')]

st.caption(f"{len(filtered):,}頭表示中 / 全{len(df):,}頭")

# ===== テーブル表示 =====
display_cols = ['馬名', '性別', '父名', '母名', '母父名', '産地', '調教師', '取引価格', '称号候補', '称号説明', '血統登録番号']
display_cols = [c for c in display_cols if c in filtered.columns]

# 称号候補に🏆マーク
show_df = filtered[display_cols].copy()
show_df.insert(0, '称号', show_df['称号候補'].apply(lambda x: '🏆' if x else ''))

st.dataframe(
    show_df.drop(columns=['称号候補']),
    use_container_width=True,
    hide_index=True,
    column_config={
        '取引価格': st.column_config.TextColumn(width='small'),
        '称号説明': st.column_config.TextColumn(width='large'),
    }
)

# ===== リスト追加 =====
st.divider()
st.subheader("リストに追加")
col1, col2 = st.columns(2)
with col1:
    selected_no = st.text_input("血統登録番号を入力（または上のテーブルからコピー）")
with col2:
    add_sex = st.radio("追加先", ["牡リスト", "牝リスト"], horizontal=True)

if st.button("➕ リストに追加", type="primary"):
    if selected_no:
        match = df[df['血統登録番号'] == selected_no]
        if match.empty:
            st.error(f"番号 {selected_no} の馬が見つかりません")
        elif add_sex == "牡リスト":
            if selected_no not in st.session_state.male_list:
                st.session_state.male_list.append(selected_no)
                st.success(f"✅ {match.iloc[0]['馬名']} を牡リストに追加しました")
            else:
                st.warning("すでにリストに入っています")
        else:
            if selected_no not in st.session_state.female_list:
                st.session_state.female_list.append(selected_no)
                st.success(f"✅ {match.iloc[0]['馬名']} を牝リストに追加しました")
            else:
                st.warning("すでにリストに入っています")
```

- [ ] **Step 2: Streamlitで動作確認する**

```bash
streamlit run app.py
```

サイドバーから「馬リスト」を選び、以下を確認:
- テーブルが表示される
- フィルタが動く
- 称号候補に🏆が表示される
- リスト追加ボタンが動く

- [ ] **Step 3: コミットする**

```bash
git add pages/
git commit -m "feat: 馬リスト画面（フィルタ・リスト追加）"
```

---

## Task 6: Page 2 — 称号狙い専用画面

**Files:**
- Create: `C:\Users\aktfk\pog-tool\pages\2_称号狙い.py`

- [ ] **Step 1: pages/2_称号狙い.pyを作成する**

```python
# pages/2_称号狙い.py
import streamlit as st
from data_loader import load_horses_with_flags
from scraper import fetch_advice

st.set_page_config(page_title="称号狙い", layout="wide")
st.title("🏆 称号狙い候補")

st.markdown("""
過去にぷにさんが指名した馬の**父・母・兄弟姉妹**を持つ馬を一覧表示しています。
ぽぐ！サイトの `advice.php` データを元にしています。
""")

if 'male_list' not in st.session_state:
    st.session_state.male_list = []
if 'female_list' not in st.session_state:
    st.session_state.female_list = []

with st.spinner("データ読み込み中..."):
    df = load_horses_with_flags()
    advice_male = fetch_advice(sex=1)
    advice_female = fetch_advice(sex=2)

tab_m, tab_f = st.tabs(["牡馬", "牝馬"])

def show_advice(advice_list, sex_label):
    df_sub = df[df['性別'] == sex_label]
    for item in advice_list:
        horse_name = item['horse_name']
        row = df_sub[df_sub['馬名'] == horse_name]

        with st.expander(f"🏆 **{horse_name}** （{item.get('sire','')} × {item.get('dam','')}）　{item.get('trainer','')}（{item.get('stable','')}）"):
            if not row.empty:
                reg_no = row.iloc[0]['血統登録番号']
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**血統登録番号**: `{reg_no}`")
                    st.write(f"**産地**: {row.iloc[0].get('産地','')}")
                    st.write(f"**取引価格**: {row.iloc[0].get('取引価格','')}")
                with col2:
                    if st.button(f"➕ {sex_label}リストへ", key=f"add_{reg_no}"):
                        target = st.session_state.male_list if sex_label == '牡' else st.session_state.female_list
                        if reg_no not in target:
                            target.append(reg_no)
                            st.success("追加しました！")
            else:
                st.warning(f"⚠️ この馬は全頭リストに見つかりませんでした: {horse_name}")

            st.write("**血統つながり:**")
            for conn in item['connections']:
                st.write(f"  → {conn}")

with tab_m:
    st.caption(f"牡の称号候補: {len(advice_male)}頭")
    show_advice(advice_male, '牡')

with tab_f:
    st.caption(f"牝の称号候補: {len(advice_female)}頭")
    show_advice(advice_female, '牝')
```

- [ ] **Step 2: 動作確認する**

```bash
streamlit run app.py
```

「称号狙い」ページを開き、血統つながりが展開表示されることを確認する。

- [ ] **Step 3: コミットする**

```bash
git add pages/2_称号狙い.py
git commit -m "feat: 称号狙い専用ページ"
```

---

## Task 7: scraper.py — 自動送信機能

**Files:**
- Modify: `C:\Users\aktfk\pog-tool\scraper.py`
- Modify: `C:\Users\aktfk\pog-tool\tests\test_scraper.py`

- [ ] **Step 1: テストを追加する**

`tests/test_scraper.py` の末尾に追加:

```python
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
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
python -m pytest tests/test_scraper.py::test_build_draft_payload_formats_correctly -v
```

期待: `ImportError: cannot import name 'build_draft_payload'`

- [ ] **Step 3: scraper.pyに送信機能を追加する**

`scraper.py` の末尾に追加:

```python
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
    r = s.post(url, data=payload)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, 'html.parser')
    main = soup.find('div', id='NoColumn') or soup.find('body')
    text = main.get_text(' ', strip=True) if main else r.text[:200]

    if '登録' in text and ('完了' in text or '受付' in text or 'リスト順' in text):
        return {'success': True, 'message': '登録完了しました！'}
    elif 'エラー' in text or 'error' in text.lower():
        return {'success': False, 'message': f'エラー: {text[:200]}'}
    else:
        return {'success': True, 'message': f'送信完了（応答: {text[:100]}）'}
```

- [ ] **Step 4: テストを実行する**

```bash
python -m pytest tests/test_scraper.py -v
```

期待: すべてPASS

- [ ] **Step 5: コミットする**

```bash
git add scraper.py tests/test_scraper.py
git commit -m "feat: ぽぐ！自動送信機能"
```

---

## Task 8: Page 3 — マイリスト・送信画面

**Files:**
- Create: `C:\Users\aktfk\pog-tool\pages\3_マイリスト.py`

- [ ] **Step 1: pages/3_マイリスト.pyを作成する**

```python
# pages/3_マイリスト.py
import streamlit as st
from data_loader import load_horses_with_flags
from scraper import submit_draft

st.set_page_config(page_title="マイリスト", layout="wide")
st.title("📋 マイリスト")

if 'male_list' not in st.session_state:
    st.session_state.male_list = []
if 'female_list' not in st.session_state:
    st.session_state.female_list = []

with st.spinner("データ読み込み中..."):
    df = load_horses_with_flags()

id_to_info = df.set_index('血統登録番号')[['馬名', '父名', '称号候補', '称号説明']].to_dict('index')


def render_list(session_key: str, sex_label: str):
    lst = st.session_state[session_key]
    max_count = 50
    count = len(lst)
    st.caption(f"{count}/{max_count}頭 | 上位5頭が指名確定予想")

    indices_to_remove = []
    for i, reg_no in enumerate(lst):
        info = id_to_info.get(reg_no, {})
        name = info.get('馬名', reg_no)
        sire = info.get('父名', '')
        is_ach = info.get('称号候補', False)
        bg = "🏆 " if is_ach else ""
        nominated = "🟢" if i < 5 else "⚪"

        col1, col2, col3, col4 = st.columns([1, 5, 3, 1])
        with col1:
            st.write(f"{nominated} **{i+1}**")
        with col2:
            st.write(f"{bg}{name}（{sire}）")
        with col3:
            ach_text = info.get('称号説明', '')
            if ach_text:
                st.caption(ach_text[:60])
        with col4:
            if st.button("✕", key=f"rm_{session_key}_{i}"):
                indices_to_remove.append(i)

    for i in sorted(indices_to_remove, reverse=True):
        lst.pop(i)
    st.session_state[session_key] = lst


col_m, col_f = st.columns(2)

with col_m:
    st.subheader("🔵 牡馬リスト")
    render_list('male_list', '牡')

with col_f:
    st.subheader("🔴 牝馬リスト")
    render_list('female_list', '牝')

# ===== 送信セクション =====
st.divider()
st.subheader("🚀 ぽぐ！に送信")

male_count = len(st.session_state.male_list)
female_count = len(st.session_state.female_list)
st.info(f"牡: {male_count}頭 / 牝: {female_count}頭がリストに入っています")

if male_count == 0 and female_count == 0:
    st.warning("リストが空です。馬リストから追加してください。")
else:
    if st.checkbox("⚠️ 送信内容を確認しました。ぽぐ！に登録します。"):
        if st.button("✅ この内容でぽぐ！に登録する", type="primary"):
            with st.spinner("送信中...（10秒ほどかかる場合があります）"):
                result = submit_draft(
                    st.session_state.male_list,
                    st.session_state.female_list,
                )
            if result['success']:
                st.success(f"🎉 {result['message']}")
            else:
                st.error(f"❌ {result['message']}")
```

- [ ] **Step 2: 動作確認する**

```bash
streamlit run app.py
```

「マイリスト」ページを開き、以下を確認:
- 馬リストページで追加した馬が表示される
- ✕ボタンで削除できる
- 上位5頭が🟢表示される
- 送信チェックボックスが機能する

- [ ] **Step 3: コミットする**

```bash
git add pages/3_マイリスト.py
git commit -m "feat: マイリスト管理・ぽぐ！自動送信UI"
```

---

## Task 9: Page 4 — 分析画面

**Files:**
- Create: `C:\Users\aktfk\pog-tool\pages\4_分析.py`

- [ ] **Step 1: 過去指名履歴JSONをcache/にコピーする**

```bash
copy "C:\Users\aktfk\Documents\pog_full_history.json" "C:\Users\aktfk\pog-tool\cache\history.json"
```

- [ ] **Step 2: pages/4_分析.pyを作成する**

```python
# pages/4_分析.py
import json
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="分析", layout="wide")
st.title("📊 過去20年の傾向分析")

HISTORY_PATH = Path(r'C:\Users\aktfk\pog-tool\cache\history.json')

with HISTORY_PATH.open(encoding='utf-8') as f:
    raw = json.load(f)

# 全馬をフラットに
rows = []
for year, horses in raw.items():
    for h in horses:
        h['year'] = int(year)
        rows.append(h)

df = pd.DataFrame(rows)

# ===== 父別成功率 =====
st.subheader("父別 平均ポイント（指名3頭以上）")
sire_stats = (
    df[df['sire'] != '']
    .groupby('sire')
    .agg(指名数=('points', 'count'), 平均Pt=('points', 'mean'), 大活躍=('points', lambda x: (x >= 10000).sum()))
    .reset_index()
    .rename(columns={'sire': '父名'})
)
sire_stats = sire_stats[sire_stats['指名数'] >= 3].sort_values('平均Pt', ascending=False)
fig1 = px.bar(sire_stats.head(15), x='父名', y='平均Pt',
              color='大活躍', text='指名数',
              title='父別 平均獲得ポイントTOP15（指名3頭以上）',
              labels={'平均Pt': '平均ポイント', '大活躍': '大活躍(1万Pt+)頭数'})
st.plotly_chart(fig1, use_container_width=True)

# ===== 年別ポイント推移 =====
st.subheader("年別 指名馬の獲得ポイント分布")
year_stats = (
    df.groupby('year')
    .agg(合計Pt=('points', 'sum'), 平均Pt=('points', 'mean'), 頭数=('points', 'count'))
    .reset_index()
)
fig2 = px.bar(year_stats, x='year', y='合計Pt',
              title='年別 総獲得ポイント',
              labels={'year': '年度', '合計Pt': '総ポイント'})
st.plotly_chart(fig2, use_container_width=True)

# ===== サマリー =====
st.subheader("当たり馬の共通点")
success = df[df['points'] >= 10000]
col1, col2, col3 = st.columns(3)
with col1:
    top_sires = success['sire'].value_counts().head(5)
    st.write("**父TOP5**")
    st.dataframe(top_sires.rename('大活躍頭数'), use_container_width=True)
with col2:
    top_stable = success['stable'].value_counts().head(5)
    st.write("**厩舎TOP5**")
    st.dataframe(top_stable.rename('大活躍頭数'), use_container_width=True)
with col3:
    st.metric("大活躍馬（1万Pt+）", f"{len(success)}頭")
    st.metric("全指名馬", f"{len(df)}頭")
    st.metric("大活躍率", f"{len(success)/len(df)*100:.1f}%")
```

- [ ] **Step 3: 動作確認する**

```bash
streamlit run app.py
```

「分析」ページでグラフが表示されることを確認する。

- [ ] **Step 4: コミットする**

```bash
git add pages/4_分析.py cache/history.json
git commit -m "feat: 過去20年分析ページ"
```

---

## Task 10: 動作確認・送信テスト

- [ ] **Step 1: 全ページの動作を確認する**

以下をチェック:
- [ ] 馬リスト: フィルタ、称号ハイライト、リスト追加
- [ ] 称号狙い: 血統つながりの表示
- [ ] マイリスト: 追加・削除・順序確認
- [ ] 分析: グラフの表示

- [ ] **Step 2: テストを全件実行する**

```bash
python -m pytest tests/ -v
```

期待: すべてPASS

- [ ] **Step 3: 送信テスト（空リストで試す）**

マイリストページで1〜2頭だけ追加し、チェックボックスをONにして送信ボタンを押す。
ぽぐ！サイト（ `https://tep.sakura.ne.jp/pog/draftEntry.php?year=2026` ）でリストが更新されているか確認する。

- [ ] **Step 4: 最終コミット**

```bash
git add .
git commit -m "feat: POG Streamlitアプリ完成"
```

---

## セルフレビュー

- **Spec coverage**:
  - ✅ 馬リスト画面（Task 5）
  - ✅ 称号狙い専用画面（Task 6）
  - ✅ マイリスト（Task 8）
  - ✅ 分析画面（Task 9）
  - ✅ 自動送信（Task 7 + 8）
  - ✅ 認証（lovepogid/lovepogpass cookie）
  - ✅ 称号候補マージ（Task 4）
  - ✅ 送信確認ダイアログ（Task 8）

- **Placeholder scan**: なし ✅

- **Type consistency**: `load_horses_with_flags()` → DataFrame、`fetch_advice()` → list[dict]、`submit_draft()` → dict すべて一貫 ✅
