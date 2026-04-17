# pages/1_馬リスト.py
import streamlit as st
import pandas as pd
from data_loader import load_horses_with_flags

st.set_page_config(page_title="馬リスト")
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
if '称号候補' in show_df.columns:
    show_df.insert(0, '称号', show_df['称号候補'].apply(lambda x: '🏆' if x else ''))
    show_df = show_df.drop(columns=['称号候補'])

st.dataframe(
    show_df,
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
selected_no = st.text_input("血統登録番号を入力（上のテーブルからコピー）")
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
