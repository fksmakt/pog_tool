# pages/3_マイリスト.py
import streamlit as st
from data_loader import load_horses_with_flags
from scraper import submit_draft
from list_store import init_lists, save_lists
from style import inject_css
from research_scraper import fetch_horse_card_info, load_cached_card_info

st.set_page_config(page_title="マイリスト")
inject_css()
st.title("📋 マイリスト")

init_lists()

with st.spinner("データ読み込み中..."):
    df = load_horses_with_flags()

_EXTRA_COLS = ['馬名', '父名', '母名', '母父名', '生産者', '調教師',
               '称号候補', '称号説明', '兄弟賞金合計', '兄弟賞金平均']
_available = [c for c in _EXTRA_COLS if c in df.columns]
id_to_info = df.set_index('血統登録番号')[_available].to_dict('index')


def _format_prize(amount) -> str:
    try:
        v = float(amount)
    except (TypeError, ValueError):
        return ''
    if not (v > 0):  # NaN・0・負をまとめて除外
        return ''
    if v >= 1e8:
        return f'{v / 1e8:.1f}億円'
    return f'{int(v / 1e4):,}万円'


def _render_card(info: dict, card: dict | None):
    sire = info.get('父名', '') or ''
    dam = info.get('母名', '') or ''
    damsire = info.get('母父名', '') or ''
    breeder = info.get('生産者', '') or ''
    trainer = info.get('調教師', '') or ''
    siblings_total = info.get('兄弟賞金合計', 0)

    # 血統行
    pedigree = f"父 **{sire}**" if sire else ''
    if dam:
        pedigree += f"　母 {dam}"
        if damsire:
            pedigree += f"（母父 {damsire}）"
    if pedigree:
        st.caption(pedigree)

    # 生産牧場・厩舎（最重要）
    farm_line = ''
    if breeder:
        farm_line += f"🌾 {breeder}"
    if trainer and str(trainer) not in ('nan', ''):
        farm_line += f"　🏛 {trainer}"
    if farm_line:
        st.caption(farm_line)

    # 兄弟賞金＋BBS
    detail_parts = []
    prize_str = _format_prize(siblings_total)
    if prize_str:
        detail_parts.append(f"兄弟賞金合計: {prize_str}")
    if card is not None:
        bbs = card.get('bbs_count', 0)
        detail_parts.append(f"💬 掲示板: {bbs}件")
    else:
        detail_parts.append("💬 掲示板: 未取得")
    st.caption("　".join(detail_parts))

    # 活躍近親
    if card is not None:
        rels = card.get('relatives', [])
        if rels:
            st.caption("活躍近親: " + " / ".join(rels[:3]))


def render_list(session_key: str):
    lst = st.session_state[session_key]
    max_count = 50
    st.caption(f"{len(lst)}/{max_count}頭 | 上位5頭が指名確定予想")

    # キャッシュ済みのカード情報をまとめてロード
    card_cache = load_cached_card_info(lst)

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

        netkeiba_url = f"https://db.netkeiba.com/horse/{reg_no}/"
        col_rank, col_name, col_up, col_down, col_rm = st.columns([1, 7, 1, 1, 1])
        with col_rank:
            st.write(f"{nominated} **{i+1}**")
        with col_name:
            st.markdown(f"{badge}**{name}**（{sire}）　[🔗]({netkeiba_url})")
            if ach_text:
                st.caption(ach_text[:60])
            _render_card(info, card_cache.get(reg_no))
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

    # 未取得馬の一括取得ボタン
    uncached = [r for r in lst if card_cache.get(r) is None]
    if uncached:
        if st.button(f"🔄 情報を一括取得（残り{len(uncached)}頭）", key=f"fetch_{session_key}"):
            bar = st.progress(0)
            for idx, reg_no in enumerate(uncached):
                fetch_horse_card_info(reg_no, use_cache=False)
                bar.progress((idx + 1) / len(uncached))
            st.rerun()


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
