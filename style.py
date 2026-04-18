import streamlit as st


def inject_css() -> None:
    st.markdown("""
<style>
/* メインコンテンツの余白を縮小 */
.main .block-container {
    padding-top: 1.5rem;
    padding-left: 1.5rem;
    padding-right: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1100px;
}
/* サイドバーの幅を少し縮小 */
section[data-testid="stSidebar"] {
    width: 230px !important;
}
section[data-testid="stSidebar"] > div:first-child {
    width: 230px;
}
/* サイドバー展開時のメインシフト量を合わせる */
.main {
    margin-left: 230px;
}
</style>
""", unsafe_allow_html=True)
