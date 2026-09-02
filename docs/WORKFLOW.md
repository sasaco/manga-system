# Krita + Comfy Desktop 制作手順

## 役割分担

Comfy は「素材案を複数出す場所」、Krita は「正解を決めて完成原稿にする場所」です。台詞や擬音を生成画像へ焼き込むと修正しにくいため、画像生成時は文字なしにし、Krita の最上段レイヤーで組みます。

## 初回だけ行うこと

1. ComfyUI が表示された状態で `.\manga.ps1 doctor` を実行する
2. `Comfy API: OK` を確認する
3. Comfy Desktop の Model Library またはテンプレートからチェックポイントを1つ導入する
4. 再度 `doctor` を実行し、チェックポイント数が 1 以上になったことを確認する

この PC は RTX 3050 Laptop 6GB です。初期値は 768×1024、batch 1、24 steps に抑えています。最初からページ全体を高解像度生成せず、1コマずつ生成して Krita でページに組む方が安定します。

## 新しい作品

```powershell
.\manga.ps1 new -Project coffee-debug -Title "コーヒーとデバッグ"
```

生成される構成:

```text
projects/coffee-debug/
├── project.json       作品設定
├── script.yaml        ページ・コマ・台詞
├── prompts/           Comfy 用の1コマ単位プロンプト
├── refs/              キャラクター表・背景資料
├── panels/
│   ├── ai/            Comfy の生成結果（Git対象外）
│   └── selected/      採用・加筆用素材
├── pages/             Krita 原稿
└── export/            投稿・入稿データ（Git対象外）
```

## コマ生成

`prompts/001.txt` を編集してから実行します。

```powershell
.\manga.ps1 generate -Project coffee-debug -Panel 001
```

モデルを明示する場合:

```powershell
.\manga.ps1 generate -Project coffee-debug -Panel 001 -Model "model-name.safetensors" -Seed 1234
```

既定では Comfy に見つかった最初のチェックポイントを使います。固定したい場合は `config/manga.json` の `checkpoint` に Comfy 上の正確な名前を設定します。

## Krita 仕上げ

`.\manga.ps1 open -Project coffee-debug` で `pages/001.ora` と Comfy Desktop を開きます。

1. `.ora` をすぐ `.kra` として保存する
2. `AI素材` に採用コマを配置する
3. `ラフ` で構図を直す
4. `線画` で顔・手・服・背景の破綻を修正する
5. `トーン・色` と `効果` を調整する
6. `フキダシ`、最後に `文字` を入れる
7. `export/` に PNG/JPEG を書き出す

印刷原稿を始める場合は、`project.json` の `page_template` を `b5-print-600dpi.ora` に変更してから新しいページを作るか、同テンプレートを Krita で直接開いてください。

## 必須の制作ゲート

このrepoの制作契約は **Comfyで画像生成し、Kritaで文字入れと仕上げを行う** ことです。Codex内蔵画像生成や外部生成画像を `panels/selected/` に直接置くことは禁止します。Comfyが利用できない場合は別方式へ自動フォールバックせず、制作を止めて不足しているAPI・モデル・起動状態を報告します。

`prompts/NNN.txt` は画像素材専用です。必ず `no text` または `文字なし` を明記し、ナレーション・台詞・タイトルはKritaの `文字` レイヤーで追加します。

完成前に次を実行します。

```powershell
.\manga.ps1 validate -Project PROJECT_NAME
```

検査内容:

1. `project.json` が `generator: comfy` / `finisher: krita` を宣言している
2. Comfy用プロンプトが文字生成を要求していない
3. `panels/selected/NNN.png` に正しいComfy `prompt` メタデータが残り、対応する `prompts/NNN.txt` と一致する
4. 編集可能な `pages/NNN.kra` または `pages/NNN.ora` に `AI素材`・`文字` レイヤーがある
5. Kritaからの最終PNG/JPEGが `export/` にある

1件でも失敗した場合は完成・投稿可能と判断しません。検査の回避、緩和、メタデータの偽造は禁止です。

## 既知の状態

2026-09-02 時点で NVIDIA ドライバは 616.56、Comfy の Python は PyTorch 2.12.1+cu130 で、CUDA と RTX 3050 を正常認識し、Comfy API も `http://127.0.0.1:8188` で応答しています。CUDA Toolkit の別途インストールは不要です。現在の未完了項目はチェックポイントの導入だけです。
