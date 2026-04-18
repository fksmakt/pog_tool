# pages/2_称号狙い.py
import streamlit as st
from data_loader import load_horses_with_flags
from scraper import fetch_advice
from list_store import init_lists, save_lists
from style import inject_css

st.set_page_config(page_title="称号狙い")
inject_css()
st.title("🏆 称号狙い候補")

st.markdown("""
過去にぷにさんが指名した馬の**父・母・兄弟姉妹**を持つ馬を一覧表示しています。
ぽぐ！サイトの `advice.php` データを元にしています。
""")

init_lists()

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
                st.write(f"**血統登録番号**: `{reg_no}`")
                st.write(f"**産地**: {row.iloc[0].get('産地','')}　**取引価格**: {row.iloc[0].get('取引価格','')}")
                if st.button(f"➕ {sex_label}リストへ追加", key=f"add_{sex_label}_{reg_no}", type="primary"):
                    target = st.session_state.male_list if sex_label == '牡' else st.session_state.female_list
                    if reg_no not in target:
                        target.append(reg_no)
                        save_lists()
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
