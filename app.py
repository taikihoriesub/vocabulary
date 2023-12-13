import streamlit as st
import pandas as pd
import random
import subprocess
import os

# セッション状態の初期化
if 'data_loaded' not in st.session_state:
    st.session_state['data_loaded'] = False
if 'test_state' not in st.session_state:
    st.session_state['test_state'] = 'file_selection'
if 'test_questions' not in st.session_state:
    st.session_state['test_questions'] = []
if 'test_index' not in st.session_state:
    st.session_state['test_index'] = 0
if 'user_choices' not in st.session_state:
    st.session_state['user_choices'] = {}
if 'test_results' not in st.session_state:
    st.session_state['test_results'] = []
if 'test_type' not in st.session_state:
    st.session_state['test_type'] = None
if 'chapter_data' not in st.session_state:
    st.session_state['chapter_data'] = None

# GitリポジトリからCSVファイルのリストを取得する関数
def get_csv_files_from_repo(repo_url, repo_dir):
    if not os.path.exists(repo_dir):
        subprocess.run(['git', 'clone', repo_url, repo_dir])
    return [f for f in os.listdir(repo_dir) if f.endswith('.csv')]

# ファイル選択セッション
def file_selection_session():
    repo_url = 'https://github.com/taikihoriesub/vocabulary.git'  # GitリポジトリのURL
    repo_dir = 'vocabulary'  # ローカルにクローンするディレクトリ名

    if not st.session_state['data_loaded']:
        csv_files = get_csv_files_from_repo(repo_url, repo_dir)
        selected_file = st.radio("Select a CSV file", csv_files)

        if selected_file:
            st.session_state['chapter_data'] = pd.read_csv(os.path.join(repo_dir, selected_file))
            st.session_state['data_loaded'] = True
            st.session_state['test_state'] = 'setup'

# テスト設定セッション
def setup_session():
    if st.session_state['data_loaded']:
        chapter = st.selectbox('Choose a Chapter', st.session_state['chapter_data']['Chapter'].unique())
        st.session_state['test_type'] = st.radio("Select test type", ('English to Japanese', 'Japanese to English'))
        num_words = st.number_input('Number of words to test', min_value=1, max_value=len(st.session_state['chapter_data']), value=5)

        if st.button('Start Test'):
            filtered_data = st.session_state['chapter_data'][st.session_state['chapter_data']['Chapter'] == chapter]
            st.session_state['test_questions'] = filtered_data.sample(n=num_words).to_dict('records')
            st.session_state['test_index'] = 0
            st.session_state['user_choices'] = {}
            st.session_state['test_results'] = []
            st.session_state['test_state'] = 'question'

# 以下の問題セッションとフィードバックセッションのコードは変更なし

# アプリのメイン関数
def main():
    st.title('Medical English Vocabulary Test')

    if st.session_state['test_state'] == 'file_selection':
        file_selection_session()

    elif st.session_state['test_state'] == 'setup':
        setup_session()

    elif st.session_state['test_state'] == 'question':
        question_session()

    elif st.session_state['test_state'] == 'feedback':
        feedback_session()

if __name__ == "__main__":
    main()
