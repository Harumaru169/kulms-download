kulms-download is a CLI tool for downloading site resources from KULMS (Kyoto University Learning Management System). It uses asynchronous processing to quickly handle network and file I/O tasks.
This project is under active development and is not yet stable.

kulms-downloadはKULMS(京大学習管理システム)のサイトリソースをダウンロードするためのCLIツールです。非同期処理によってネットワークやファイルのIOタスクを高速に処理します。
これは現在開発中のプロジェクトであり、安定版ではありません。

# Usage (使い方)

```sh
>>> kulms-download
>>> ? === KULMS Download === サイトリソースのダウンロード
>>> ? 資料をダウンロードしたいサイトをすべて選択: [[2026前期月２]工業数学Ａ３]
>>> ? ダウンロード先のディレクトリパスを入力: /Users/user_name/Downloads
>>> ? ダウンロードを開始しますか？ Yes
ダウンロードが完了しました
```

# Features (機能)

- **高速ダウンロード** : 複数のファイルを非同期処理によって高速に取得します。
- **高速にパスワードを入力** : 前もってECS-IDとパスワードを入力しておけば、ログイン画面で自動入力します。パスワードはOS標準の方法で暗号化されて保存されるので安全です。
- **パスワード管理アプリを一緒に起動** : 設定することで、パスワード.appや1Password.appなどをログイン画面で自動起動します。ワンタイムパスワードを入力する手間を極限まで小さくします。

# Getting Started (導入方法)

## 1. 簡単インストール

Pythonとか知らないけどとりあえず最短経路でkulms-downloadを使いたい、という方は......

### Step.1 `uv`のインストール

**Mac** : ターミナル.appで以下を入力してEnter

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows** : PowerShellで以下を入力してEnter

```sh
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Step.2 実行

`uv`がインストールされたら、以下のコマンドだけで常に最新版の`kulms-download`が起動します。

```sh
uvx kulms-download
```

## 2. 開発者向け

すでにPython 3.12以上の環境が整っている場合は、venvなどの仮想環境で`pip`を用いてインストールできます。

```sh
pip install kulms-download
```

また、ツールとして独立した環境で管理したい場合は、`pipx`を推奨します。

```sh
pipx install kulms-download
```
