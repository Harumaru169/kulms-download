kulms-download is a CLI tool for downloading site resources from KULMS (Kyoto University Learning Management System). It uses asynchronous processing to quickly handle network and file I/O tasks.

kulms-downloadはKULMS(京大学習管理システム)のサイトリソースをダウンロードするためのCLIツールです。非同期処理によってネットワークやファイルのIOタスクを高速に処理します。

---

# Install

kulms-download can be installed using pip

```shell
$ pip install kulms-download
```

# Usage

```pycon
>>> kulms-download
>>> ? === KULMS Download === サイトリソースのダウンロード
>>> ? 資料をダウンロードしたいサイトをすべて選択: [[2026前期月２]工業数学Ａ３]
>>> ? ダウンロード先のディレクトリパスを入力: /Users/user_name/Downloads
>>> ? ダウンロードを開始しますか？ Yes
ダウンロードが完了しました
```

# Features

- Download multiple site resources simultaneously
- Retain cookie data
- Open password management app with a login window
