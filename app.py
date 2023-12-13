import streamlit as st
import pandas as pd
import random
import subprocess
import os

# セッション状態の初期化
if 'data_loaded' not in st.session_state:
    st.session_state['data_loaded'] = False
if 'test_state' not in st.session_state:
    st.session_state['test_state'] = 'setup'
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

# 設定セッション
def setup_session():
    repo_url = 'https://github.com/taikihoriesub/vocabulary.git'  # GitリポジトリのURL
    repo_dir = 'vocabulary'  # ローカルにクローンするディレクトリ名

    # GitリポジトリからCSVファイルを取得
    if not st.session_state['data_loaded']:
        csv_files = get_csv_files_from_repo(repo_url, repo_dir)
        selected_file = st.radio("Select a CSV file", csv_files)

        if selected_file:
            st.session_state['chapter_data'] = pd.read_csv(os.path.join(repo_dir, selected_file))
            st.session_state['data_loaded'] = True

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

# 問題セッション
def question_session():
    if st.session_state['test_index'] < len(st.session_state['test_questions']):
        question_data = st.session_state['test_questions'][st.session_state['test_index']]
        question = question_data['English'] if st.session_state['test_type'] == 'English to Japanese' else question_data['Japanese']
        correct_answer = question_data['Japanese'] if st.session_state['test_type'] == 'English to Japanese' else question_data['English']

        if st.session_state['test_index'] not in st.session_state['user_choices']:
            other_choices = [row[st.session_state['test_type'].split(' to ')[1]] for row in st.session_state['test_questions'] if row != question_data]
            choices = [correct_answer] + random.sample(other_choices, min(3, len(other_choices)))
            random.shuffle(choices)
            st.session_state['user_choices'][st.session_state['test_index']] = choices

        with st.form(key=f'question_form_{st.session_state["test_index"]}'):
            user_choice = st.radio(
                f"Translate this word: {question}",
                st.session_state['user_choices'][st.session_state['test_index']],
                key=f"radio_{st.session_state['test_index']}"
            )
            submit_button = st.form_submit_button(label='Submit Answer')

        if submit_button:
            is_correct = user_choice == correct_answer
            st.session_state['test_results'].append((question, user_choice, correct_answer, is_correct))
            if st.session_state['test_index'] < len(st.session_state['test_questions']) - 1:
                st.session_state['test_index'] += 1
            else:
                st.session_state['test_state'] = 'feedback'

# フィードバックセッション
def feedback_session():
    correct_count = sum(result[3] for result in st.session_state['test_results'])
    st.write(f"Total Correct Answers: {correct_count}/{len(st.session_state['test_questions'])}")
    for question, user_choice, correct_answer, is_correct in st.session_state['test_results']:
        status = "✅ Correct" if is_correct else "❌ Incorrect"
        st.write(f"{status} - Question: {question} - Your Choice: {user_choice} - Correct Answer: {correct_answer}")

    if st.button('Start New Test'):
        st.session_state['test_state'] = 'setup'

# アプリのメイン関数
def main():
    st.title('Medical English Vocabulary Test')

    if st.session_state['test_state'] == 'setup':
        setup_session()

    elif st.session_state['test_state'] == 'question':
        question_session()

    elif st.session_state['test_state'] == 'feedback':
        feedback_session()

if __name__ == "__main__":
    main()
