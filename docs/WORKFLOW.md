# Krita + Comfy Desktop 制作手順

## 役割分担

Comfy は「素材案を複数出す場所」、Krita は「正解を決めて完成原稿にする場所」です。生成画像は常に文字なしにします。`project.json` の `image_text_policy` が `manual-krita-text` の作品だけ、台詞や擬音をKritaで追加できます。`textless` の作品は完成画像にも文字を置きません。

## 初回だけ行うこと

1. ComfyUI が表示された状態で `.\manga.ps1 doctor` を実行する
2. `Comfy API: OK` を確認する
3. Comfy Desktop の Model Library またはテンプレートからチェックポイントを1つ導入する
4. 再度 `doctor` を実行し、チェックポイント数が 1 以上になったことを確認する

画像サイズ、steps、使用モデルなどの実行値は `config/manga.json` を正本とします。環境の現在値は `doctor` で確認してください。1回の生成・採用画像・KRA・最終出力は同じ `NNN` で対応させます。

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
├── reviews/           textless作品のハッシュ付き目視確認記録
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

既定モデルは `config/manga.json` の `checkpoint` で固定します。モデルを変更したら、Comfy 上の正確な名前を設定し、`doctor` と生成を再確認してください。

## Krita 仕上げ

採用画像を `panels/selected/001.png` に置いたあと、次を実行します。

```powershell
.\manga.ps1 compose -Project coffee-debug -Panel 001
.\manga.ps1 open -Project coffee-debug -Panel 001
```

`compose` は `.ora` テンプレートへ採用画像を配置し、Krita自身で正規の `pages/001.kra` に変換します。`.ora` は交換用テンプレートであり、編集原稿には使いません。

1. `AI素材` に採用コマが表示されていることを確認する
2. `ラフ` で構図を直す
3. `線画` で顔・手・服・背景の破綻を修正する
4. `トーン・色` と `効果` を調整する
5. `manual-krita-text` の場合だけ、`フキダシ`、最後に `文字` を入れる。`textless` では両レイヤーを空のままにする
6. `export/` に PNG/JPEG を書き出す

印刷原稿を始める場合は、`project.json` の `page_template` を `b5-print-600dpi.ora` に変更してから新しいページを作るか、同テンプレートを Krita で直接開いてください。

## 必須の制作ゲート

このrepoの制作契約は **Comfyで画像生成し、Kritaでレイヤー仕上げを行う** ことです。Codex内蔵画像生成や外部生成画像を `panels/selected/` に直接置くことは禁止します。Comfyが利用できない場合は別方式へ自動フォールバックせず、制作を止めて不足しているAPI・モデル・起動状態を報告します。

`prompts/NNN.txt` は画像素材専用です。必ず `no text` または `文字なし` を明記します。`manual-krita-text` ではナレーション・台詞・タイトルをKritaで追加し、`textless` では投稿文など画像外に置きます。

`textless` の場合、採用PNG、KRA内の `mergedimage.png`、最終書き出しを読み取れる倍率で目視確認します。文字・数字・ロゴ・署名・透かしが1つでも見えたら修正またはComfy再生成し、確認が終わった後だけ記録します。

```powershell
.\manga.ps1 review -Project PROJECT_NAME -Panel 001 -Reviewer "your-name" -ConfirmNoVisibleText
```

完成前に次を実行します。

```powershell
.\manga.ps1 validate -Project PROJECT_NAME
```

検査内容:

1. `project.json` がスキーマに適合し、`generator: comfy` / `finisher: krita` を宣言している
2. Comfy用プロンプトが文字生成を要求していない
3. `panels/selected/NNN.png` に必要なComfyノード・モデル・seed・正しいプロンプトのメタデータがある
4. 正規の `pages/NNN.kra` に一意な必須レイヤー、非空の `AI素材`、有効な統合プレビューがある（`.ora` は不可）
5. 各採用画像と完成状態のエピソードに対応する最終PNG/JPEGがあり、KRAと画像サイズが一致し、KRAより古くない
6. `textless` では空の `文字`・`フキダシ` レイヤーと、現在の3成果物に一致する目視確認記録がある

1件でも失敗した場合は完成・投稿可能と判断しません。検査の回避、緩和、メタデータの偽造は禁止です。

## リポジトリ自体の検査

規則、設定、テンプレート、skill、Pythonテストの整合を外部アプリなしで確認します。

```powershell
.\manga.ps1 check
```

`doctor` はPC環境の診断、`check` はrepoインフラ、`validate` は特定作品の完成条件を担当します。
