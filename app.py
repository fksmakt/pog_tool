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
