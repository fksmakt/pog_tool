# pages/5_調査.py
import streamlit as st
from style import inject_css
from research_scraper import (
    get_reideouro_offspring,
    get_past_nominated_mares,
    enrich_with_netkeiba,
    save_research_cache,
    CACHE_REIDEOURO,
    CACHE_PAST_MARES,
)
from list_store import init_lists, save_lists

st.set_page_config(page_title="調査")
inject_css()
st.title("🔍 調査")
st.markdown("レイデオロ産駒・過去指名牝馬の仔を複数サイトから調査します。")

init_lists()

with st.sidebar:
    st.header("🔍 フィルタ")
    sex_filter = st.radio("性別", ["全て", "牡", "牝"])
    achievement_only = st.checkbox("🏆 称号候補のみ")
    sort_by = st.selectbox("並び順", ["馬名順", "称号候補優先"])
    st.divider()
    st.header("🔄 データ更新")
    force_refresh = st.button("netkeibаから再取得（時間がかかります）", type="secondary")


def apply_filters(items: list[dict]) -> list[dict]:
    if sex_filter != "全て":
        items = [x for x in items if x.get('sex') == sex_filter]
    if achievement_only:
        items = [x for x in items if x.get('achievement_flag')]
    if sort_by == "称号候補優先":
        items = sorted(items, key=lambda x: (not x.get('achievement_flag'), x.get('horse_name', '')))
    else:
        items = sorted(items, key=lambda x: x.get('horse_name', ''))
    return items


def _pog_links(horse_name: str, reg_no: str = '') -> str:
    from urllib.parse import quote
    name_enc = quote(horse_name)
    links = []
    if reg_no and reg_no not in ('nan', ''):
        links.append(f"[net競馬POG](https://pog.netkeiba.com/?pid=pog_regist_list&horseid={reg_no})")
        umatoku_id = reg_no[2:] if len(reg_no) >= 3 else reg_no
        links.append(f"[うま徳POG](https://umatoku.hochi.co.jp/pog/horse/{umatoku_id})")
    links.append(f"[X(Twitter)](https://x.com/search?q={name_enc}+POG)")
    return " / ".join(links)


def render_horse_table(items: list[dict], show_dam_year: bool = False, tab_prefix: str = ""):
    if not items:
        st.info("該当する馬が見つかりません。")
        return

    for item in items:
        name = item.get('horse_name', '')
        sex = item.get('sex', '')
        dam = item.get('dam', '')
        sire = item.get('sire', '')
        trainer = item.get('trainer', '') or item.get('netkeiba', {}).get('trainer', '')
        region = item.get('region', '')
        price = item.get('price', '')
        is_ach = item.get('achievement_flag', False)
        ach_desc = item.get('achievement_desc', '')
        reg_no = item.get('reg_no', '')
        comment = item.get('netkeiba', {}).get('comment', '')
        siblings = item.get('netkeiba', {}).get('siblings', '')
        dam_year = item.get('dam_nominated_year')
        _valid_no = reg_no and reg_no not in ('nan', '')
        netkeiba_url = item.get('netkeiba_url') or (f"https://db.netkeiba.com/horse/{reg_no}/" if _valid_no else '')
        netkeiba_bbs_url = item.get('netkeiba_bbs_url') or (f"https://db.netkeiba.com/?pid=horse_board&id={reg_no}" if _valid_no else '')

        badge = "🏆 " if is_ach else ""
        label_parts = [f"{badge}{name}（{sex}）"]
        if show_dam_year and dam_year:
            label_parts.append(f"父: {sire}　母: {dam}（{dam_year}年指名）")
        else:
            label_parts.append(f"母: {dam} × {sire}")
        if comment:
            label_parts.append(f"💬 {comment[:40]}...")
        label = "　".join(label_parts)

        _valid_no2 = reg_no and reg_no not in ('nan', '')
        umatoku_url = f"https://umatoku.hochi.co.jp/pog/horse/{reg_no[2:]}" if _valid_no2 and len(reg_no) >= 3 else ''
        link_parts = []
        if netkeiba_url:
            link_parts.append(f"[🔗 net競馬]({netkeiba_url})　[💬 掲示板]({netkeiba_bbs_url})")
        if umatoku_url:
            link_parts.append(f"[🐎 うま徳POG]({umatoku_url})")
        if link_parts:
            st.markdown(f"<small>{'　'.join(link_parts)}</small>", unsafe_allow_html=True)

        with st.expander(label):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**性別:** {sex}　**産地:** {region}")
                st.write(f"**調教師:** {trainer}")
                st.write(f"**取引価格:** {price}")
            with col2:
                if is_ach:
                    st.success(f"🏆 称号候補: {ach_desc[:60]}" if ach_desc else "🏆 称号候補")
                if siblings:
                    st.write(f"**近親馬:** {siblings}")


            # 他POGサイトリンク
            st.markdown("**POG情報源:** " + _pog_links(name, reg_no))

            # 近況コメント
            st.divider()
            st.write("**📰 net競馬 近況**")
            if comment:
                st.info(comment)
            else:
                st.caption("近況情報なし（「net競馬プロフィール」から直接確認できます）")

            st.divider()
            col_m, col_f = st.columns(2)
            with col_m:
                if st.button("➕ 牡リストへ", key=f"{tab_prefix}_add_m_{reg_no}"):
                    if reg_no not in st.session_state.male_list:
                        st.session_state.male_list.append(reg_no)
                        save_lists()
                        st.success(f"{name} を牡リストに追加")
                    else:
                        st.warning("すでに牡リストにあります")
            with col_f:
                if st.button("➕ 牝リストへ", key=f"{tab_prefix}_add_f_{reg_no}"):
                    if reg_no not in st.session_state.female_list:
                        st.session_state.female_list.append(reg_no)
                        save_lists()
                        st.success(f"{name} を牝リストに追加")
                    else:
                        st.warning("すでに牝リストにあります")


tab1, tab2 = st.tabs(["🐴 レイデオロ産駒", "👑 過去指名牝馬の仔"])

def render_by_sex(items: list[dict], show_dam_year: bool, tab_prefix: str):
    males = [x for x in items if x.get('sex') == '牡']
    females = [x for x in items if x.get('sex') == '牝']
    others = [x for x in items if x.get('sex') not in ('牡', '牝')]

    st.subheader(f"🔵 牡馬 ({len(males)}頭)")
    render_horse_table(males, show_dam_year=show_dam_year, tab_prefix=f"{tab_prefix}_m")

    st.subheader(f"🔴 牝馬 ({len(females)}頭)")
    render_horse_table(females, show_dam_year=show_dam_year, tab_prefix=f"{tab_prefix}_f")

    if others:
        st.subheader(f"その他 ({len(others)}頭)")
        render_horse_table(others, show_dam_year=show_dam_year, tab_prefix=f"{tab_prefix}_o")


with tab1:
    with st.spinner("レイデオロ産駒を読み込み中..."):
        rei_items = get_reideouro_offspring(use_cache=not force_refresh)
        if force_refresh:
            rei_items = enrich_with_netkeiba(rei_items)
            save_research_cache(CACHE_REIDEOURO, rei_items)
    filtered_rei = apply_filters(rei_items)
    st.caption(f"計{len(filtered_rei)}頭（過去指名牝馬の仔はタブ2に表示）")
    render_by_sex(filtered_rei, show_dam_year=False, tab_prefix="tab1")

with tab2:
    with st.spinner("過去指名牝馬の仔を読み込み中..."):
        mare_items = get_past_nominated_mares(use_cache=not force_refresh)
        if force_refresh:
            mare_items = enrich_with_netkeiba(mare_items)
            save_research_cache(CACHE_PAST_MARES, mare_items)
    filtered_mares = apply_filters(mare_items)
    st.caption(f"計{len(filtered_mares)}頭（父レイデオロ含む）")
    render_by_sex(filtered_mares, show_dam_year=True, tab_prefix="tab2")
