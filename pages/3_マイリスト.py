# pages/3_マイリスト.py
import streamlit as st
from data_loader import load_horses_with_flags
from scraper import submit_draft
from list_store import init_lists, save_lists

st.set_page_config(page_title="マイリスト")
st.title("📋 マイリスト")

init_lists()

with st.spinner("データ読み込み中..."):
    df = load_horses_with_flags()

id_to_info = df.set_index('血統登録番号')[['馬名', '父名', '称号候補', '称号説明']].to_dict('index')


def render_list(session_key: str):
    lst = st.session_state[session_key]
    max_count = 50
    st.caption(f"{len(lst)}/{max_count}頭 | 上位5頭が指名確定予想")

    indices_to_remove = []
    move_up = None
    move_down = None

    for i, reg_no in enumerate(lst):
        info = id_to_info.get(reg_no, {})
        name = info.get('馬名', reg_no)
        sire = info.get('父名', '')
        is_ach = info.get('称号候補', False)
        badge = "🏆 " if is_ach else ""
        nominated = "🟢" if i < 5 else "⚪"
        ach_text = info.get('称号説明', '')

        col_rank, col_name, col_up, col_down, col_rm = st.columns([1, 7, 1, 1, 1])
        with col_rank:
            st.write(f"{nominated} **{i+1}**")
        with col_name:
            st.write(f"{badge}{name}（{sire}）")
            if ach_text:
                st.caption(ach_text[:60])
        with col_up:
            if i > 0 and st.button("↑", key=f"up_{session_key}_{i}"):
                move_up = i
        with col_down:
            if i < len(lst) - 1 and st.button("↓", key=f"dn_{session_key}_{i}"):
                move_down = i
        with col_rm:
            if st.button("✕", key=f"rm_{session_key}_{i}"):
                indices_to_remove.append(i)

    changed = False
    if move_up is not None:
        lst[move_up - 1], lst[move_up] = lst[move_up], lst[move_up - 1]
        changed = True
    if move_down is not None:
        lst[move_down], lst[move_down + 1] = lst[move_down + 1], lst[move_down]
        changed = True
    if indices_to_remove:
        for i in sorted(indices_to_remove, reverse=True):
            lst.pop(i)
        changed = True
    st.session_state[session_key] = lst
    if changed:
        save_lists()


def render_bulk_input(session_key: str, label: str):
    current = '\n'.join(st.session_state[session_key])
    new_text = st.text_area(
        f"{label} — 血統登録番号を1行1頭で貼り付け（1〜50位順）",
        value=current,
        height=200,
        key=f"bulk_{session_key}",
        placeholder="2024100001\n2024100002\n...",
    )
    if st.button(f"✅ {label}を更新", key=f"bulk_apply_{session_key}"):
        lines = [l.strip() for l in new_text.splitlines() if l.strip()]
        valid = [l for l in lines if df['血統登録番号'].eq(l).any()]
        invalid = [l for l in lines if l not in valid]
        st.session_state[session_key] = valid[:50]
        save_lists()
        if invalid:
            st.warning(f"⚠️ 見つからない番号をスキップしました: {', '.join(invalid[:5])}")
        st.success(f"{len(valid[:50])}頭を{label}に設定しました")
        st.rerun()

    if st.session_state[session_key]:
        st.caption("📋 現在のリスト（コピー用）")
        st.code('\n'.join(st.session_state[session_key]), language=None)


# ===== 牡馬リスト =====
st.subheader("🔵 牡馬リスト")
tab_m_list, tab_m_edit = st.tabs(["並び替え", "一括貼り付け"])
with tab_m_list:
    render_list('male_list')
with tab_m_edit:
    render_bulk_input('male_list', '牡リスト')

st.divider()

# ===== 牝馬リスト =====
st.subheader("🔴 牝馬リスト")
tab_f_list, tab_f_edit = st.tabs(["並び替え", "一括貼り付け"])
with tab_f_list:
    render_list('female_list')
with tab_f_edit:
    render_bulk_input('female_list', '牝リスト')

# ===== 送信セクション =====
st.divider()
st.subheader("🚀 ぽぐ！に送信")

male_count = len(st.session_state.male_list)
female_count = len(st.session_state.female_list)
st.info(f"牡: {male_count}頭 / 牝: {female_count}頭がリストに入っています")
if male_count > 50:
    st.warning(f"⚠️ 牡リストが{male_count}頭あります。送信時は上位50頭のみ登録されます。")
if female_count > 50:
    st.warning(f"⚠️ 牝リストが{female_count}頭あります。送信時は上位50頭のみ登録されます。")

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
