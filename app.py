import streamlit as st

st.set_page_config(
    page_title="ぷにのPOGツール",
    page_icon="🏇",
)

st.title("🏇 ぷにのPOGツール 2026-2027")
st.markdown("""
左のサイドバー（☰）からページを選んでください。

- **馬リスト**: 全頭検索・フィルタ・リスト追加
- **称号狙い**: 血統つながり候補の一覧
- **マイリスト**: 指名リスト管理・ぽぐ！送信
- **分析**: 過去20年の傾向グラフ
""")

st.info("📱 スマホ・iPad からアクセスする場合は、PCと同じWi-Fiに接続して `http://<PCのIPアドレス>:8501` を開いてください。")
