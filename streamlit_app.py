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

# --- 問題データ ---
questions_data = [
    {"ja": "お荷物をお持ちしましょうか？", "en": "Shall I carry your baggage?"},
    {"ja": "こちらがルームキーになります。", "en": "Here is your room key."},
    {"ja": "こちらの用紙にご記入いただけますか？", "en": "Could you fill out this form?"},
    {"ja": "ご滞在はお楽しみいただけましたか？", "en": "Did you enjoy your stay?"},
    {"ja": "朝食は6時半から9時半までご用意しております。", "en": "Breakfast is served from 6:30 to 9:30."}
]

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
    words = q['en'].replace('?', '').replace('.', '').split()
    shuffled = random.sample(words, len(words))
    
    # Streamlitのボタンキー重複エラーを防ぐため、各単語に一意のIDを付与
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
        
        # 組み立て中の解答を表示
        st.write("▼ あなたの解答")
        selected_text = " ".join([b['word'] for b in st.session_state.selected_blocks])
        if selected_text:
            st.info(f"**{selected_text}**")
        else:
            st.info("（下の単語をタップして文章を作成してください）")
            
        st.write("---")

        if not st.session_state.answered:
            # 単語ブロックの表示（4列で折り返し表示）
            cols = st.columns(4)
            for i, block in enumerate(st.session_state.available_blocks):
                # クリックされたら利用可能リストから削除し、選択済みリストへ追加
                if cols[i % 4].button(block['word'], key=f"btn_{block['id']}"):
                    st.session_state.selected_blocks.append(block)
                    st.session_state.available_blocks.remove(block)
                    st.rerun()

            st.write("")
            col1, col2 = st.columns(2)
            
            with col1:
                # 選択をリセットするボタン
                if st.button("🔄 選択をやり直す", use_container_width=True):
                    # 選択済みブロックを利用可能ブロックに戻してID順（元のシャッフル順）に並び替え
                    st.session_state.available_blocks.extend(st.session_state.selected_blocks)
                    st.session_state.available_blocks.sort(key=lambda x: x['id'])
                    st.session_state.selected_blocks = []
                    st.rerun()
                    
            with col2:
                # 解答ボタン
                if st.button("✅ 解答する", type="primary", use_container_width=True):
                    user_sentence = " ".join([b['word'] for b in st.session_state.selected_blocks])
                    correct_clean = q['en'].replace('?', '').replace('.', '').lower()
                    user_clean = user_sentence.lower()
                    
                    is_correct = (correct_clean == user_clean)
                    
                    if is_correct:
                        st.success(f"正解！ 🎉\n\n正解文: **{q['en']}**")
                    else:
                        st.error(f"惜しい！ 💦\n\n正解文: **{q['en']}**\n\nあなたの解答: {user_sentence}")
                    
                    save_result(q['ja'], q['en'], user_sentence, is_correct)
                    st.session_state.answered = True
                    st.rerun()
        
        # 解答後の画面
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
            st.write("パーフェクト！間違えたフレーズはありません。")import streamlit as st
import sqlite3
import random
import pandas as pd

# --- データベースの初期化 ---
def init_db():
    conn = sqlite3.connect('hotel_english.db')
    c = conn.cursor()
    # 学習履歴テーブルの作成
    c.execute('''CREATE TABLE IF NOT EXISTS history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  japanese TEXT, 
                  correct_answer TEXT, 
                  user_answer TEXT, 
                  is_correct BOOLEAN)''')
    conn.commit()
    return conn

conn = init_db()

# --- 問題データ ---
# 実際の授業に合わせて追加・変更してください
questions_data = [
    {"ja": "お荷物をお持ちしましょうか？", "en": "Shall I carry your baggage?"},
    {"ja": "こちらがルームキーになります。", "en": "Here is your room key."},
    {"ja": "こちらの用紙にご記入いただけますか？", "en": "Could you fill out this form?"},
    {"ja": "ご滞在はお楽しみいただけましたか？", "en": "Did you enjoy your stay?"},
    {"ja": "朝食は6時半から9時半までご用意しております。", "en": "Breakfast is served from 6:30 to 9:30."}
]

# --- セッションステートの管理 ---
if 'current_q' not in st.session_state:
    st.session_state.current_q = None
if 'shuffled_words' not in st.session_state:
    st.session_state.shuffled_words = []
if 'answered' not in st.session_state:
    st.session_state.answered = False

def set_new_question(q_list):
    if not q_list:
        return False
    q = random.choice(q_list)
    st.session_state.current_q = q
    # 単語を分割してシャッフル（記号などは実際のアプリではよしなに処理します）
    words = q['en'].replace('?', '').replace('.', '').split()
    st.session_state.shuffled_words = random.sample(words, len(words))
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
    # 重複を排除して問題データの形式に変換
    wrong_list = []
    if not df.empty:
        df_unique = df.drop_duplicates(subset=['correct_answer'])
        for _, row in df_unique.iterrows():
            wrong_list.append({"ja": row['japanese'], "en": row['correct_answer']})
    return wrong_list

# --- UI構築 ---
st.title("🏨 ホテル英会話マスター")

# サイドバーでモード切替
mode = st.sidebar.radio("モードを選択してください", ["学習モード", "復習モード（間違えた問題）", "学習記録・弱点一覧"])

# ---------------------------------
# 1. 学習モード & 2. 復習モード
# ---------------------------------
if mode in ["学習モード", "復習モード（間違えた問題）"]:
    st.subheader(mode)
    
    # 出題リストの決定
    target_questions = questions_data if mode == "学習モード" else get_wrong_questions()
    
    if not target_questions:
        st.success("素晴らしい！現在間違えた問題はありません。")
    else:
        # 初回または「次の問題」ボタンが押された時の処理
        if st.session_state.current_q is None:
            set_new_question(target_questions)

        # 現在の問題を表示
        q = st.session_state.current_q
        st.write("### お客様への声かけ:")
        st.info(f"**{q['ja']}**")
        
        st.write("正しい順番で単語を選択してください：")
        # st.multiselectを利用して順番に選ばせる（選んだ順にリスト化されます）
        user_selection = st.multiselect("単語候補", st.session_state.shuffled_words, key=f"ms_{q['en']}")
        
        if not st.session_state.answered:
            if st.button("解答する"):
                user_sentence = " ".join(user_selection)
                # 大文字小文字や記号の揺れを簡易的に吸収して判定
                correct_clean = q['en'].replace('?', '').replace('.', '').lower()
                user_clean = user_sentence.lower()
                
                is_correct = (correct_clean == user_clean)
                
                if is_correct:
                    st.success(f"正解！ 🎉\n\n正解文: **{q['en']}**")
                else:
                    st.error(f"惜しい！ 💦\n\n正解文: **{q['en']}**\n\nあなたの解答: {user_sentence}")
                
                # DBに保存
                save_result(q['ja'], q['en'], user_sentence, is_correct)
                st.session_state.answered = True
        
        if st.session_state.answered:
            if st.button("次の問題へ"):
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
        # 判定カラムをわかりやすく変換
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
