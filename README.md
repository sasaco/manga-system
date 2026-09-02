# manga-system

Krita を仕上げ、Comfy Desktop / ComfyUI をローカル画像生成に使う、Windows 向けのマンガ制作リポジトリです。

## 最初に実行

PowerShell でこのフォルダを開きます。

```powershell
.\manga.ps1 doctor
```

現在の PC では Krita 5.3.3 と Comfy Desktop 1.0.46、CUDA 対応 GPU、Comfy API を自動検出します。

次に、作品フォルダを作ります。

```powershell
.\manga.ps1 new -Project first-manga -Title "最初のマンガ"
```

作成先は `projects/first-manga/` です。脚本、プロンプト、参照画像、AI コマ、Krita原稿、完成原稿が一作品の中にまとまります。

## 1コマをローカル生成

Comfy Desktop でチェックポイントを1つ導入し、ComfyUI が起動している状態で実行します。

```powershell
.\manga.ps1 generate -Project first-manga -Panel 001
```

`projects/first-manga/prompts/001.txt` を読み、6GB VRAM 向けの 768×1024 / 24 steps で生成します。結果は `projects/first-manga/panels/ai/` に保存され、Comfy のワークフロー情報も元画像に残ります。

## 制作フロー

1. `script.yaml` でネームと台詞を決める
2. `prompts/NNN.txt` を書き、Comfy で人物・背景・構図の素材を生成する
3. 採用画像を `panels/selected/NNN.png` に置き、`.\manga.ps1 compose -Project first-manga -Panel NNN` で `pages/NNN.kra` を作る
4. Kritaで `.kra` の線画・修正・トーン・吹き出しを分離して仕上げる
5. 完成物を `export/` に書き出す

詳細は [docs/WORKFLOW.md](docs/WORKFLOW.md) を参照してください。

## 完成前の必須ゲート

完成・投稿可能と判断する前に、必ず制作ハーネスを実行します。

```powershell
.\manga.ps1 validate -Project first-manga
```

このゲートは、`panels/selected/` のPNGが対応するプロンプトを使ったComfy生成物であること、Kritaの編集可能な `.kra` 原稿があること、Kritaからの最終書き出しが `export/` にあることを検査します。`.ora` はテンプレート交換用で、原稿としては受理しません。Comfy用プロンプトへ文字を焼き込む指定も拒否します。1件でも違反があれば、その作品を完成扱いにしてはいけません。

## 主なコマンド

```powershell
.\manga.ps1 doctor                         # アプリ、GPU、API、モデルを診断
.\manga.ps1 new -Project NAME -Title TITLE # 新規作品を作成
.\manga.ps1 open -Project NAME             # Krita と Comfy Desktop を開く
.\manga.ps1 generate -Project NAME -Panel 001
.\manga.ps1 compose -Project NAME -Panel 001 # 採用画像入りのKRA原稿を作る
.\manga.ps1 validate -Project NAME         # Comfy → Krita 制作契約を検証
.\manga.ps1 help
```
