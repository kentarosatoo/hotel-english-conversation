# 🏨 ホテル英会話マスター (Hotel English Conversation Master)

Streamlitを利用した、ホテルの専門学校生向けの英会話学習Webアプリケーションです。
フロントやレストランで頻出する接客フレーズを「単語の並び替え（整序問題）」形式で直感的に学び、外部APIによるネイティブ音声で発音も同時に確認することができます。

## URL

このURLで試すことができます（スリープ状態のときは青色の起動ボタンを押してください）：
https://(あなたのアプリのURL).streamlit.app/

## 🌟 主な機能

並び替え学習モード: スマートフォンからの操作を想定し、タップのみで単語ブロックを組み立てる直感的なUIを採用しています（選択したブロックは位置が固定され、視線移動の負担を減らしています）。

ネイティブ音声再生機能 (Web API連携): 解答直後に VoiceRSS API を呼び出し、正解の英語音声を再生します。テキストの構造理解と聴覚からのインプットを連携させ、より実践的な学習を促します。

復習モード: 過去に間違えたフレーズだけを抽出して集中的に学習し、効率的に弱点を克服できます。

学習記録のクラウド保存と可視化: Supabase（PostgreSQL）と連携し、学習履歴をクラウド上に永続化。よく間違える「苦手なフレーズ」をランキング形式で表示します。

CSVによる問題管理: プログラムを直接編集せずとも、questions.csv を更新するだけで教務担当者が簡単に問題を追加・修正できる運用しやすい設計です。

## 🛠 セットアップ方法
1. 依存ライブラリのインストール
Python環境がインストールされていることを確認し、必要なライブラリをインストールしてください。

Bash
pip install streamlit pandas supabase requests
2. 単語データの準備
プロジェクトのルートディレクトリに questions.csv という名前でCSVファイルを配置してください。アプリ起動時に自動的に読み込まれます。

questions.csv のフォーマット例:

コード スニペット
ja,en
お荷物をお持ちしましょうか？,Shall I carry your baggage?
こちらがルームキーになります。,Here is your room key.
何泊ご滞在ですか？,How many nights will you be staying?

3. 環境変数（シークレット）の設定
データベースとAPIを使用するため、Streamlit Community Cloudの Secrets（ローカル環境の場合は .streamlit/secrets.toml）に以下の情報を設定してください。

Ini, TOML
SUPABASE_URL = "あなたのSupabaseプロジェクトURL"
SUPABASE_KEY = "あなたのSupabase anon publicキー"
VOICERSS_API_KEY = "取得したVoiceRSSのAPIキー"
4. アプリの起動
以下のコマンドでアプリを起動します。

Bash
streamlit run app.py
(※ファイル名が streamlit_app.py の場合は適宜読み替えてください)

データの仕組み
このアプリは Supabase (クラウドデータベース) を使用して学習履歴を管理し、アプリが再起動してもデータが保持される仕組みになっています。

history テーブル: ユーザーの解答結果（日本語文、正解文、ユーザーの解答文、正誤判定、解答日時）を保存します。

## 使用技術
Frontend/UI: Streamlit

Data Handling: Pandas

Database: Supabase (PostgreSQL)

External API: VoiceRSS Text-to-Speech API (音声合成API)

## 今後のロードマップ（カスタマイズ例）
教員向けダッシュボードの実装: Supabaseのデータを集計し、クラス全体で正答率の低いフレーズを可視化して授業改善（形成的評価）に繋げる機能。

学生アカウント（ログイン）機能の追加: 学生ごとの学習進捗管理とゲーミフィケーション（バッジ付与など）の導入。

シチュエーション画像の動的表示: 画像検索APIと連携し、問題文に合わせて「フロント」「レストラン」などの背景画像を表示する機能。
