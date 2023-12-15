import streamlit as st
import pandas as pd
import random
import subprocess
import os

# セッション状態の初期化
def initialize_session_state():
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
    if 'user_answers' not in st.session_state:
        st.session_state['user_answers'] = {}
    if 'test_results' not in st.session_state:
        st.session_state['test_results'] = []
    if 'test_type' not in st.session_state:
        st.session_state['test_type'] = 'English to Japanese'
    if 'test_format' not in st.session_state:
        st.session_state['test_format'] = 'Multiple Choice'
    if 'chapter_data' not in st.session_state:
        st.session_state['chapter_data'] = None
    if 'last_chapter' not in st.session_state:
        st.session_state['last_chapter'] = None
    if 'last_test_type' not in st.session_state:
        st.session_state['last_test_type'] = None
    if 'last_test_format' not in st.session_state:
        st.session_state['last_test_format'] = None
    if 'last_num_words' not in st.session_state:
        st.session_state['last_num_words'] = 5

initialize_session_state()

# GitリポジトリからCSVファイルのリストを取得する関数
def get_csv_files_from_repo(repo_url, repo_dir):
    if not os.path.exists(repo_dir):
        subprocess.run(['git', 'clone', repo_url, repo_dir])
    return [f[:-4] for f in os.listdir(repo_dir) if f.endswith('.csv')] # '.csv'を取り除いてファイル名を返す

# ファイル選択セッション
def file_selection_session():
    repo_url = 'https://github.com/taikihoriesub/vocabulary'
    repo_dir = 'vocabulary'

    if not st.session_state['data_loaded']:
        file_names = get_csv_files_from_repo(repo_url, repo_dir)
        selected_file_name = st.radio("Select a file", file_names)

        if st.button('Load File'):
            selected_file = selected_file_name + '.csv' # ファイル名に'.csv'を追加
            st.session_state['chapter_data'] = pd.read_csv(os.path.join(repo_dir, selected_file))
            st.session_state['data_loaded'] = True
            st.session_state['test_state'] = 'setup'

# テスト設定セッション
def setup_session():
    if st.session_state['data_loaded']:
        # Default values for the test settings
        default_chapter = st.session_state.get('last_chapter', st.session_state['chapter_data']['Chapter'].unique()[0])
        default_test_type = st.session_state.get('last_test_type', 'English to Japanese')
        default_test_format = st.session_state.get('last_test_format', 'Multiple Choice')
        default_num_words = st.session_state.get('last_num_words', 5)

        chapter = st.selectbox('Choose a Chapter', st.session_state['chapter_data']['Chapter'].unique(), index=st.session_state['chapter_data']['Chapter'].unique().tolist().index(default_chapter))
        test_types = ['English to Japanese', 'Japanese to English']
        st.session_state['test_type'] = st.radio("Select test type", test_types, index=test_types.index(default_test_type))
        test_formats = ['Multiple Choice', 'Descriptive']
        st.session_state['test_format'] = st.radio("Select test format", test_formats, index=test_formats.index(default_test_format))
        num_words = st.number_input('Number of words to test', min_value=5, max_value=len(st.session_state['chapter_data']), value=default_num_words)

        if st.button('Start Test'):
            if num_words < 5:
                st.error('Please select at least 5 words.')
            else:
                # Save the current test settings for the next session
                st.session_state['last_chapter'] = chapter
                st.session_state['last_test_type'] = st.session_state['test_type']
                st.session_state['last_test_format'] = st.session_state['test_format']
                st.session_state['last_num_words'] = num_words

                filtered_data = st.session_state['chapter_data'][st.session_state['chapter_data']['Chapter'] == chapter]
                st.session_state['test_questions'] = filtered_data.sample(n=num_words).to_dict('records')
                st.session_state['test_index'] = 0
                st.session_state['user_choices'] = {}
                st.session_state['user_answers'] = {}
                st.session_state['test_results'] = []
                st.session_state['test_state'] = 'question'
  
# 質問セッション
def question_session():
    if st.session_state['test_index'] < len(st.session_state['test_questions']):
        question_data = st.session_state['test_questions'][st.session_state['test_index']]
        question = question_data['English'] if st.session_state['test_type'] == 'English to Japanese' else question_data['Japanese']
        correct_answer = question_data['Japanese'] if st.session_state['test_type'] == 'English to Japanese' else question_data['English']

        if st.session_state['test_format'] == 'Multiple Choice':
            if st.session_state['test_index'] not in st.session_state['user_choices']:
                chapter_data = st.session_state['chapter_data'][st.session_state['chapter_data']['Chapter'] == question_data['Chapter']]
                other_choices = [row['Japanese' if st.session_state['test_type'] == 'English to Japanese' else 'English']
                                 for index, row in chapter_data.iterrows() if row['English'] != question_data['English'] and row['Japanese'] != question_data['Japanese']]
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

        elif st.session_state['test_format'] == 'Descriptive':
            with st.form(key=f'question_form_{st.session_state["test_index"]}'):
                user_answer = st.text_input(f"Translate this word: {question}", key=f"text_{st.session_state['test_index']}")
                submit_button = st.form_submit_button(label='Submit Answer')

            if submit_button:
                is_correct = user_answer.strip().lower() == correct_answer.lower()
                st.session_state['test_results'].append((question, user_answer, correct_answer, is_correct))
                if st.session_state['test_index'] < len(st.session_state['test_questions']) - 1:
                    st.session_state['test_index'] += 1
                else:
                    st.session_state['test_state'] = 'feedback'

# フィードバックセッション
def feedback_session():
    correct_count = sum(result[3] for result in st.session_state['test_results'])
    st.write(f"Total Correct Answers: {correct_count}/{len(st.session_state['test_questions'])}")
    for question, user_response, correct_answer, is_correct in st.session_state['test_results']:
        status = "✅ Correct" if is_correct else "❌ Incorrect"
        st.write(f"{status} - Question: {question} - Your Response: {user_response} - Correct Answer: {correct_answer}")

    if st.button('Start New Test'):
        st.session_state['test_state'] = 'setup'
        st.session_state['data_loaded'] = True

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
