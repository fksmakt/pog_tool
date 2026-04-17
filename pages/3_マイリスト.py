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
