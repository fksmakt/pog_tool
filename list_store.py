"""マイリストのファイル永続化。セッションをまたいでリストを保持する。"""
import json
from pathlib import Path

import streamlit as st

_STORE_PATH = Path(__file__).parent / 'data' / 'mylist.json'


def _load_from_file() -> dict:
    if _STORE_PATH.exists():
        try:
            return json.loads(_STORE_PATH.read_text(encoding='utf-8'))
        except Exception:
            pass
    return {'male_list': [], 'female_list': [], 'horse_marks': {}}


def _save_to_file() -> None:
    data = {
        'male_list': st.session_state.get('male_list', []),
        'female_list': st.session_state.get('female_list', []),
        'horse_marks': st.session_state.get('horse_marks', {}),
    }
    _STORE_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def init_lists() -> None:
    """セッション開始時に呼ぶ。session_stateが空ならファイルから復元する。"""
    if 'mylist_loaded' not in st.session_state:
        saved = _load_from_file()
        st.session_state.male_list = saved.get('male_list', [])
        st.session_state.female_list = saved.get('female_list', [])
        st.session_state.horse_marks = saved.get('horse_marks', {})
        st.session_state.mylist_loaded = True


def save_lists() -> None:
    """リスト変更後に呼ぶ。"""
    _save_to_file()
