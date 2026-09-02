# manga-system

Krita を仕上げ、Comfy Desktop / ComfyUI をローカル画像生成に使う、Windows 向けのマンガ制作リポジトリです。既存の Gemini 生成スクリプトも `scripts/` に残しています。

## 最初に実行

PowerShell でこのフォルダを開きます。

```powershell
.\manga.ps1 doctor
```

現在の PC では Krita 5.3.3 と Comfy Desktop 1.0.46、CUDA 対応 GPU、Comfy API を自動検出します。

次に、作品フォルダを作ります。

```powershell
.\manga.ps1 new -Project first-manga -Title "最初のマンガ"
.\manga.ps1 open -Project first-manga
```

作成先は `projects/first-manga/` です。Krita 用ページ、脚本、プロンプト、参照画像、AI コマ、完成原稿が一作品の中にまとまります。

## 1コマをローカル生成

Comfy Desktop でチェックポイントを1つ導入し、ComfyUI が起動している状態で実行します。

```powershell
.\manga.ps1 generate -Project first-manga -Panel 001
```

`projects/first-manga/prompts/001.txt` を読み、6GB VRAM 向けの 768×1024 / 24 steps で生成します。結果は `projects/first-manga/panels/ai/` に保存され、Comfy のワークフロー情報も元画像に残ります。

## 制作フロー

1. `script.yaml` でネームと台詞を決める
2. `prompts/NNN.txt` を書き、Comfy で人物・背景・構図の素材を生成する
3. Krita の `pages/001.ora` に AI 素材を置き、線画・修正・トーン・吹き出しを分離して仕上げる
4. 完成物を `export/` に書き出す

詳細は [docs/WORKFLOW.md](docs/WORKFLOW.md) を参照してください。

## 主なコマンド

```powershell
.\manga.ps1 doctor                         # アプリ、GPU、API、モデルを診断
.\manga.ps1 new -Project NAME -Title TITLE # 新規作品を作成
.\manga.ps1 open -Project NAME             # Krita と Comfy Desktop を開く
.\manga.ps1 generate -Project NAME -Panel 001
.\manga.ps1 help
```

## 既存のクラウド生成

従来の YAML → Gemini 画像生成は引き続き利用できます。API キーを `.env` に設定し、`setup.ps1` / `generate.ps1` を使用してください。新規制作では、文字を AI 画像に直接描かせず、Krita で台詞を組むローカルファーストの流れを推奨します。
