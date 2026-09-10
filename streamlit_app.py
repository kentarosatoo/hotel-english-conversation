import streamlit as st
import random
import pandas as pd
import requests
from supabase import create_client, Client

# --- 🌟 Supabaseの初期化 ---
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# --- CSVファイルから問題データを読み込む ---
@st.cache_data
def load_questions():
    try:
        df = pd.read_csv('questions.csv', encoding='utf-8')
        df = df.rename(columns={'日本文': 'ja', '英文': 'en'})
        return df.to_dict('records')
    except FileNotFoundError:
        st.error("⚠️ questions.csv が見つかりません。")
        return []
    except Exception as e:
         st.error(f"問題の読み込みエラー: {e}")
         return []

questions_data = load_questions()

# --- 音声APIの関数を追加---
@st.cache_data(show_spinner=False)
def get_audio(text):
    api_key = st.secrets["VOICERSS_API_KEY"]
    url = "http://api.voicerss.org/"
    params = {"key": api_key, "hl": "en-us", "src": text, "c": "MP3", "f": "44khz_16bit_stereo"}
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200 and not response.content.startswith(b"ERROR"):
            return response.content
    except:
        pass
    return None

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
    
    words = q['en'].replace('?', '').replace('.', '').replace(',', '').split()
    shuffled = random.sample(words, len(words))
    
    st.session_state.available_blocks = [{'id': i, 'word': w} for i, w in enumerate(shuffled)]
    st.session_state.selected_blocks = []
    st.session_state.answered = False
    return True

# --- 解答ボタンの処理の中に追加 ---
                    if is_correct:
                        st.success(f"正解！ 🎉\n\n正解文: **{q['en']}**")
                    else:
                        st.error(f"惜しい！ 💦\n\n正解文: **{q['en']}**\n\nあなたの解答: {user_sentence}")
                    
                    # 🌟 ここに音声再生を追加 🌟
                    with st.spinner("音声を読み込み中..."):
                        audio_bytes = get_audio(q['en'])
                        if audio_bytes:
                            st.audio(audio_bytes, format="audio/mp3")

# --- 🌟 データベース操作関数（Supabase版） ---
def save_result(ja, correct, user, is_correct):
    try:
        supabase.table("history").insert({
            "japanese": ja,
            "correct_answer": correct,
            "user_answer": user,
            "is_correct": is_correct
        }).execute()
    except Exception as e:
        st.error(f"学習履歴の保存に失敗しました: {e}")

def get_wrong_questions():
    try:
        # is_correct が False のデータだけを取得
        response = supabase.table("history").select("japanese, correct_answer").eq("is_correct", False).execute()
        df = pd.DataFrame(response.data)
        
        wrong_list = []
        if not df.empty:
            df_unique = df.drop_duplicates(subset=['correct_answer'])
            for _, row in df_unique.iterrows():
                wrong_list.append({"ja": row['japanese'], "en": row['correct_answer']})
        return wrong_list
    except Exception as e:
        st.error(f"復習問題の読み込みエラー: {e}")
        return []

# --- UI構築 ---
st.title("🏨 ホテル英会話マスター")

st.markdown("""
<style>
div[data-testid="stHorizontalBlock"] { gap: 0.2rem !important; }
[data-testid="stButton"] button { padding: 0.2rem 0.5rem !important; min-height: 2.5rem !important; margin-bottom: 0.2rem !important; }
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
    
    try:
        # Supabaseから全履歴を取得（新しい順）
        response = supabase.table("history").select("id, japanese, correct_answer, user_answer, is_correct").order("id", desc=True).execute()
        df = pd.DataFrame(response.data)
        
        if df.empty:
            st.write("まだ学習記録がありません。")
        else:
            # カラム名を日本語に変換
            df = df.rename(columns={'japanese': '日本語', 'correct_answer': '正解', 'user_answer': 'あなたの解答', 'is_correct': '判定'})
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
    except Exception as e:
        st.error(f"学習記録の読み込みエラー: {e}")
