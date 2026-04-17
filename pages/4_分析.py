# pages/4_分析.py
import json
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="分析", layout="wide")
st.title("📊 過去20年の傾向分析")

HISTORY_PATH = Path(__file__).parent.parent / 'cache' / 'history.json'

try:
    with HISTORY_PATH.open(encoding='utf-8') as f:
        raw = json.load(f)
except FileNotFoundError:
    st.error(f"history.jsonが見つかりません: {HISTORY_PATH}\nDocumentsフォルダからcache/にコピーしてください。")
    st.stop()

# 全馬をフラットに
rows = []
for year, horses in raw.items():
    for h in horses:
        h['year'] = int(year)
        rows.append(h)

df = pd.DataFrame(rows)

# ===== 父別成功率 =====
st.subheader("父別 平均ポイント（指名3頭以上）")
sire_stats = (
    df[df['sire'] != '']
    .groupby('sire')
    .agg(指名数=('points', 'count'), 平均Pt=('points', 'mean'), 大活躍=('points', lambda x: (x >= 10000).sum()))
    .reset_index()
    .rename(columns={'sire': '父名'})
)
sire_stats = sire_stats[sire_stats['指名数'] >= 3].sort_values('平均Pt', ascending=False)
fig1 = px.bar(sire_stats.head(15), x='父名', y='平均Pt',
              color='大活躍', text='指名数',
              title='父別 平均獲得ポイントTOP15（指名3頭以上）',
              labels={'平均Pt': '平均ポイント', '大活躍': '大活躍(1万Pt+)頭数'})
st.plotly_chart(fig1, use_container_width=True)

# ===== 年別ポイント推移 =====
st.subheader("年別 指名馬の獲得ポイント分布")
year_stats = (
    df.groupby('year')
    .agg(合計Pt=('points', 'sum'), 平均Pt=('points', 'mean'), 頭数=('points', 'count'))
    .reset_index()
)
fig2 = px.bar(year_stats, x='year', y='合計Pt',
              title='年別 総獲得ポイント',
              labels={'year': '年度', '合計Pt': '総ポイント'})
st.plotly_chart(fig2, use_container_width=True)

# ===== サマリー =====
st.subheader("当たり馬の共通点")
success = df[df['points'] >= 10000]
col1, col2, col3 = st.columns(3)
with col1:
    top_sires = success['sire'].value_counts().head(5)
    st.write("**父TOP5**")
    st.dataframe(top_sires.rename('大活躍頭数'), use_container_width=True)
with col2:
    top_stable = success['stable'].value_counts().head(5)
    st.write("**厩舎TOP5**")
    st.dataframe(top_stable.rename('大活躍頭数'), use_container_width=True)
with col3:
    st.metric("大活躍馬（1万Pt+）", f"{len(success)}頭")
    st.metric("全指名馬", f"{len(df)}頭")
    st.metric("大活躍率", f"{len(success)/len(df)*100:.1f}%")
