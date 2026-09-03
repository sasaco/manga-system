# 第7話 新モデル／新工程 比較テスト

実施日: 2026-09-03

A〜Dの初回比較に加え、ユーザー提供の2枚の画風資料を正式基準にしたE比較と、物語の読みやすさを修正したF比較を実施した。Eは「何の話かわからない」というユーザー評価により不採用。FのSD1.5版を本番の `panels/selected/007.png`、`pages/007.kra`、`export/007.png` へ反映した。

## 比較条件

全条件で第7話の本番プロンプト、seed `2001111`、768×1024、24 steps、CFG 6.5、DPM++ 2M Karras を使用した。

| 条件 | モデル | 工程 | 構図入力 | 結果 |
|---|---|---|---|---|
| A | Stable Diffusion 1.5 base | Scribble ControlNet | `refs/007-control.png`、strength 2.0 | 現行の採用Comfy素材。構図は守るが、茶色い紙工作・3D表現になり、固定画風から外れる。 |
| B | DreamShaper 8 | Scribble ControlNet | `refs/007-control.png`、strength 2.0 | 人物と小物の立体的な描写は改善。ただし3Dイラスト化が強まり、白地・揺れ線・限定ベタ色という固定画風には不採用。 |
| C | Stable Diffusion 1.5 base | img2img、denoise 0.35 | 現行 `export/007.png` | 固定画風、構図、文字なしを維持。線と色面が少し整理されるが、入力からの改善は小さい。 |
| D | DreamShaper 8 | img2img、denoise 0.35 | 現行 `export/007.png` | 固定画風を維持した条件では最良。Cより輪郭と色面がわずかに安定するが、元絵の造形そのものはほぼ維持される。 |
| E1 | Stable Diffusion 1.5 base | 改善下絵からimg2img、denoise 0.35 | 添付資料に合わせた疎な新下絵 | 画風には近づいたが、一冊の本と二人だけでは第7話固有の意味が伝わらないため不採用。 |
| E2 | DreamShaper 8 | 改善下絵からimg2img、denoise 0.35 | E1と同じ下絵 | E1とほぼ同じ。新下絵が十分にスタイルを決めるため、この画風ではモデル差がほとんど出ない。比較用として保存。 |
| F | Stable Diffusion 1.5 base | 物語アンカーを加えた下絵からimg2img、denoise 0.35、Krita文字仕上げ | 師匠が渡す一冊、主人公横の大量ページ、正確な台詞 | 添付資料の簡潔さを保ちながら、「サンプルだけ渡され、数百ページを自力で直す」という第7話の意味が読める。本番採用。 |

4条件の配置は、比較画像の左上=A、右上=B、左下=C、右下=D。

## 定量確認

現行のKrita最終画像を768×1024へ縮小した画像に対する平均絶対画素差は、Aが98.37、Bが73.94、Cが4.68、Dが4.52だった。C/Dが固定画風と構図をほぼ維持し、A/Bが別画風へ大きく変化したことと整合する。

## 結論

新モデルだけを入れ替えると一般的な描画品質は上がるが、シリーズの固定画風から外れる。固定画風を守るには、低denoiseのimg2img工程が安全である。

E比較で、入力を添付資料に合わせて描き直す方がモデル交換より大きく効くことを確認した。一方、情報を削るだけでは物語まで消える。Fでは、計算表や黄色い糸は戻さず、師匠から渡される一冊、大量ページの束、正確な短い台詞の3点だけを復元した。今回の主要ボトルネックはモデルではなく、入力原画・情報量の選別・人物サイズだった。

プロジェクトは `manual-krita-text`。Comfy素材は文字なしのまま、FのKrita原稿では「サンプルの a を1から2に変えろ」を `文字`、吹き出しを `フキダシ` の別レイヤーへ配置した。自動生成画像へ文字は焼き込んでいない。

## 成果物

- `comparison-grid.png`: A〜Dの無文字4分割比較
- `B-dreamshaper-scribble/007B_2001111_01.png`: モデルだけ変更
- `C-base-img2img/007C_2001111_01.png`: 工程だけ変更
- `D-dreamshaper-img2img/007D_2001111_01.png`: モデルと工程を変更した採用候補
- `D-dreamshaper-img2img/page.kra`: D案のレイヤー付きKrita比較原稿
- `D-dreamshaper-img2img/finished.png`: D案のKrita書き出し
- `panel_img2img_api.json`: 比較に使用したComfy img2imgワークフロー
- `E-reference-style/reference-style-comparison.png`: 変更前、新下絵、SD1.5本番、DreamShaper比較の4分割画像
- `E-reference-style/source.png`: 添付資料に合わせて情報量と人物サイズを描き直した無文字入力
- `E-reference-style/generated-base/007_2001115_01.png`: 本番採用したSD1.5低denoise候補
- `E-reference-style/generated/007_2001114_01.png`: DreamShaper低denoise比較候補
- `E-reference-style/balloon-guide.png`: Krita手作業用の無文字吹き出しガイド
- `F-story-readable/007-story-readable.png`: 物語の読みやすさを修正した最終比較画像
- `F-story-readable/generated/007_2001116_01.png`: 本番採用した文字なしComfy素材
- `F-story-readable/page.kra`: `AI素材`、`線画`、`トーン・色`、`文字`、`フキダシ` を分離したKrita原稿
- `F-story-readable/finished.png`: F案のKrita書き出し

DreamShaper 8は共有Comfyチェックポイントへ追加したが、`config/manga.json` の本番既定モデルは変更していない。DreamShaper版を本番採用すると既定モデル照合に失敗するため、シリーズ全話を移行しない限り比較用途に留める。
