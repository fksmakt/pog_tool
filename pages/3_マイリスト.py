# pages/3_マイリスト.py
import streamlit as st
from streamlit_sortables import sort_items
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

MARK_CYCLE = ['', 'red', 'blue', 'green']
MARK_EMOJI = {'': '', 'red': '🔴', 'blue': '🔵', 'green': '🟢'}


def _format_prize(amount) -> str:
    try:
        v = float(amount)
    except (TypeError, ValueError):
        return ''
    if not (v > 0):
        return ''
    if v >= 1e8:
        return f'{v / 1e8:.1f}億円'
    return f'{int(v / 1e4):,}万円'


def _make_display(reg_no: str) -> str:
    """ドラッグリスト用の表示文字列（マーク絵文字は含めない）。"""
    info = id_to_info.get(reg_no, {})
    name = info.get('馬名', reg_no)
    sire = info.get('父名', '') or ''
    return f"{name}（{sire}）"


def render_list(session_key: str):
    lst = list(st.session_state[session_key])
    max_count = 50
    st.caption(f"{len(lst)}/{max_count}頭 | 上位5頭が指名確定予想")

    marks = st.session_state.setdefault('horse_marks', {})
    card_cache = load_cached_card_info(lst)

    # ── ドラッグ&ドロップ並び替え ──
    # マーク絵文字は含めない（絵文字変更時に逆引きがずれるのを防ぐ）
    seen: set[str] = set()
    unique_items = []
    for reg_no in lst:
        item = _make_display(reg_no)
        # 同名馬がいる場合のみ reg_no 末尾6桁を付加して一意化
        if item in seen:
            item = f"{item} [{reg_no[-6:]}]"
        seen.add(item)
        unique_items.append(item)

    display_to_reg = dict(zip(unique_items, lst))

    sorted_display = sort_items(unique_items, direction="vertical", key=f"sort_{session_key}")

    # 逆引きできない項目（コンポーネントの状態ずれ）はスキップして安全にフォールバック
    new_lst = [display_to_reg[d] for d in sorted_display if d in display_to_reg]
    if len(new_lst) != len(lst):
        new_lst = lst  # 件数不一致は無視して現状維持

    if new_lst != lst:
        st.session_state[session_key] = new_lst
        save_lists()
        lst = new_lst

    st.divider()

    # ── 詳細カード（✕・カラーマーク・情報） ──
    indices_to_remove = []

    for i, reg_no in enumerate(lst):
        info = id_to_info.get(reg_no, {})
        name = info.get('馬名', reg_no)
        sire = info.get('父名', '') or ''
        is_ach = info.get('称号候補', False)
        badge = "🏆 " if is_ach else ""
        nominated = "🟢" if i < 5 else "⚪"
        ach_text = info.get('称号説明', '')
        current_mark = marks.get(reg_no, '')
        mark_emoji = MARK_EMOJI.get(current_mark, '')

        netkeiba_url = f"https://db.netkeiba.com/horse/{reg_no}/"
        col_rank, col_name, col_rm = st.columns([1, 8, 1])

        with col_rank:
            st.write(f"{nominated} **{i+1}**")

        with col_name:
            header = f"{mark_emoji + ' ' if mark_emoji else ''}{badge}**{name}**（{sire}）　[🔗]({netkeiba_url})"
            st.markdown(header)
            if ach_text:
                st.caption(ach_text[:60])

            # カラーマークボタン
            mc1, mc2, mc3, mc4 = st.columns([1, 1, 1, 5])
            with mc1:
                if st.button('🔴', key=f'red_{session_key}_{i}',
                             type='primary' if current_mark == 'red' else 'secondary'):
                    marks[reg_no] = '' if current_mark == 'red' else 'red'
                    save_lists()
                    st.rerun()
            with mc2:
                if st.button('🔵', key=f'blue_{session_key}_{i}',
                             type='primary' if current_mark == 'blue' else 'secondary'):
                    marks[reg_no] = '' if current_mark == 'blue' else 'blue'
                    save_lists()
                    st.rerun()
            with mc3:
                if st.button('🟢', key=f'green_{session_key}_{i}',
                             type='primary' if current_mark == 'green' else 'secondary'):
                    marks[reg_no] = '' if current_mark == 'green' else 'green'
                    save_lists()
                    st.rerun()

            # 情報カード
            card = card_cache.get(reg_no)
            sire_v = info.get('父名', '') or ''
            dam = info.get('母名', '') or ''
            damsire = info.get('母父名', '') or ''
            breeder = info.get('生産者', '') or ''
            trainer = info.get('調教師', '') or ''
            siblings_total = info.get('兄弟賞金合計', 0)

            pedigree = f"父 **{sire_v}**" if sire_v else ''
            if dam:
                pedigree += f"　母 {dam}"
                if damsire:
                    pedigree += f"（母父 {damsire}）"
            if pedigree:
                st.caption(pedigree)

            farm_line = ''
            if breeder:
                farm_line += f"🌾 {breeder}"
            if trainer and str(trainer) not in ('nan', ''):
                farm_line += f"　🏛 {trainer}"
            if farm_line:
                st.caption(farm_line)

            detail_parts = []
            prize_str = _format_prize(siblings_total)
            if prize_str:
                detail_parts.append(f"兄弟賞金合計: {prize_str}")
            if card is not None:
                detail_parts.append(f"💬 掲示板: {card.get('bbs_count', 0)}件")
            else:
                detail_parts.append("💬 掲示板: 未取得")
            st.caption("　".join(detail_parts))

            if card is not None:
                rels = card.get('relatives', [])
                if rels:
                    st.caption("活躍近親: " + " / ".join(rels[:3]))

        with col_rm:
            if st.button("✕", key=f"rm_{session_key}_{i}"):
                indices_to_remove.append(i)

    if indices_to_remove:
        for i in sorted(indices_to_remove, reverse=True):
            lst.pop(i)
        st.session_state[session_key] = lst
        save_lists()
        st.rerun()

    # BBS情報取得ボタン
    uncached = [r for r in lst if card_cache.get(r) is None]
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if uncached and st.button(f"🔄 情報を取得（{len(uncached)}頭未取得）", key=f"fetch_{session_key}"):
            bar = st.progress(0)
            for idx, reg_no in enumerate(uncached):
                fetch_horse_card_info(reg_no, use_cache=False)
                bar.progress((idx + 1) / len(uncached))
            st.rerun()
    with col_btn2:
        if lst and st.button("🔃 全馬を再取得（BBS更新）", key=f"refetch_{session_key}"):
            bar = st.progress(0)
            for idx, reg_no in enumerate(lst):
                fetch_horse_card_info(reg_no, use_cache=False)
                bar.progress((idx + 1) / len(lst))
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
