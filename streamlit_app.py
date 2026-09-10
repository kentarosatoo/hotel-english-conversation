import streamlit as st
import sqlite3
import random
import pandas as pd

# --- データベースの初期化 ---
def init_db():
    conn = sqlite3.connect('hotel_english.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  japanese TEXT, 
                  correct_answer TEXT, 
                  user_answer TEXT, 
                  is_correct BOOLEAN)''')
    conn.commit()
    return conn

conn = init_db()

# --- 🌟 CSVファイルから問題データを読み込む ---
@st.cache_data
def load_questions():
    try:
        # CSVファイルを読み込み
        df = pd.read_csv('questions.csv', encoding='utf-8')
        
        # 列名が「日本文」「英文」の場合、プログラム用に「ja」「en」に変更
        df = df.rename(columns={'日本文': 'ja', '英文': 'en'})
        
        # 辞書のリスト形式に変換して返す
        return df.to_dict('records')
        
    except FileNotFoundError:
        st.error("⚠️ questions.csv が見つかりません。GitHubの同じフォルダにアップロードされているか確認してください。")
        return []
    except Exception as e:
         st.error(f"問題の読み込みエラー: {e}")
         return []

# 関数を実行して100問のデータを取得
questions_data = load_questions()

# --- セッションステートの管理 ---
if 'current_q' not in st.session_state:
    st.session_state.current_q = None
if 'available_blocks' not in st.session_state:
    st.session_state.available_blocks = []
if 'selected_blocks' not in st.session_state:
    st.session_state.selected_blocks = []
if 'answered' not in st.session_state:
    st.session_state.answered = False

def set_new_question(q_list):
    if not q_list:
        return False
    q = random.choice(q_list)
    st.session_state.current_q = q
    
    # 記号を除去して分割し、シャッフル
    words = q['en'].replace('?', '').replace('.', '').replace(',', '').split()
    shuffled = random.sample(words, len(words))
    
    # 各単語に一意のIDを付与
    st.session_state.available_blocks = [{'id': i, 'word': w} for i, w in enumerate(shuffled)]
    st.session_state.selected_blocks = []
    st.session_state.answered = False
    return True

# --- データベース操作関数 ---
def save_result(ja, correct, user, is_correct):
    c = conn.cursor()
    c.execute("INSERT INTO history (japanese, correct_answer, user_answer, is_correct) VALUES (?, ?, ?, ?)",
              (ja, correct, user, is_correct))
    conn.commit()

def get_wrong_questions():
    df = pd.read_sql_query("SELECT japanese, correct_answer FROM history WHERE is_correct = 0", conn)
    wrong_list = []
    if not df.empty:
        df_unique = df.drop_duplicates(subset=['correct_answer'])
        for _, row in df_unique.iterrows():
            wrong_list.append({"ja": row['japanese'], "en": row['correct_answer']})
    return wrong_list

# --- UI構築 ---
st.title("🏨 ホテル英会話マスター")

# --- UIデザインの微調整 ---
st.markdown("""
<style>
div[data-testid="stHorizontalBlock"] {
    gap: 0.2rem !important;
}
[data-testid="stButton"] button {
    padding: 0.2rem 0.5rem !important;
    min-height: 2.5rem !important;
    margin-bottom: 0.2rem !important;
}
</style>
""", unsafe_allow_html=True)

mode = st.sidebar.radio("モードを選択してください", ["学習モード", "復習モード（間違えた問題）", "学習記録・弱点一覧"])

# ---------------------------------
# 1. 学習モード & 2. 復習モード
# ---------------------------------
if mode in ["学習モード", "復習モード（間違えた問題）"]:
    st.subheader(mode)
    
    target_questions = questions_data if mode == "学習モード" else get_wrong_questions()
    
    if not target_questions:
        st.success("素晴らしい！現在間違えた問題はありません。")
    else:
        if st.session_state.current_q is None:
            set_new_question(target_questions)

        q = st.session_state.current_q
        st.write("### お客様への声かけ:")
        st.write(f"**{q['ja']}**")
        
        st.write("▼ あなたの解答")
        selected_text = " ".join([b['word'] for b in st.session_state.selected_blocks])
        if selected_text:
            st.info(f"**{selected_text}**")
        else:
            st.info("（下の単語をタップして文章を作成してください）")
            
        st.write("---")

        if not st.session_state.answered:
            cols = st.columns(4, gap="small")
            for i, block in enumerate(st.session_state.available_blocks):
                if cols[i % 4].button(block['word'], key=f"btn_{block['id']}", use_container_width=True):
                    st.session_state.selected_blocks.append(block)
                    st.session_state.available_blocks.remove(block)
                    st.rerun()

            st.write("")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔄 選択をやり直す", use_container_width=True):
                    st.session_state.available_blocks.extend(st.session_state.selected_blocks)
                    st.session_state.available_blocks.sort(key=lambda x: x['id'])
                    st.session_state.selected_blocks = []
                    st.rerun()
                    
            with col2:
                if st.button("✅ 解答する", type="primary", use_container_width=True):
                    user_sentence = " ".join([b['word'] for b in st.session_state.selected_blocks])
                    # カンマなどの記号を除去して判定を柔軟にする
                    correct_clean = q['en'].replace('?', '').replace('.', '').replace(',', '').lower()
                    user_clean = user_sentence.lower()
                    
                    is_correct = (correct_clean == user_clean)
                    
                    if is_correct:
                        st.success(f"正解！ 🎉\n\n正解文: **{q['en']}**")
                    else:
                        st.error(f"惜しい！ 💦\n\n正解文: **{q['en']}**\n\nあなたの解答: {user_sentence}")
                    
                    save_result(q['ja'], q['en'], user_sentence, is_correct)
                    st.session_state.answered = True
                    st.rerun()
        
        else:
            if st.button("次の問題へ", type="primary"):
                set_new_question(target_questions)
                st.rerun()

# ---------------------------------
# 3. 学習記録・弱点一覧モード
# ---------------------------------
elif mode == "学習記録・弱点一覧":
    st.subheader("これまでの学習記録")
    
    df = pd.read_sql_query("SELECT id, japanese as '日本語', correct_answer as '正解', user_answer as 'あなたの解答', is_correct as '判定' FROM history ORDER BY id DESC", conn)
    
    if df.empty:
        st.write("まだ学習記録がありません。")
    else:
        df['判定'] = df['判定'].apply(lambda x: "⭕️" if x else "❌")
        st.dataframe(df, use_container_width=True)
        
        st.subheader("⚠️ よく間違える単語・フレーズ")
        wrong_df = df[df['判定'] == "❌"]
        if not wrong_df.empty:
            wrong_counts = wrong_df['正解'].value_counts().reset_index()
            wrong_counts.columns = ['間違えたフレーズ', '回数']
            st.table(wrong_counts)
        else:
            st.write("パーフェクト！間違えたフレーズはありません。")
