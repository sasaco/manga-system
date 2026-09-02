# Krita テンプレート

- `instagram-portrait.ora`: 1080×1350、SNS 投稿向け
- `b5-print-600dpi.ora`: B5 仕上がり + 3mm 塗り足し、600dpi

OpenRaster (`.ora`) はレイヤー構成を受け渡すテンプレートです。採用画像を置いたら `.\manga.ps1 compose -Project NAME -Panel NNN` で正規の `projects/NAME/pages/NNN.kra` を作り、以後は `.kra` だけを原稿本体にしてください。

レイヤーは「文字・フキダシ」「仕上げ」「作画」「下描き」に分けています。非表示のガイドレイヤーには、Instagram 版では安全域、B5 版では裁ち落とし線と安全域があります。

テンプレートを再生成する場合:

```powershell
uv run python scripts/create_krita_template.py templates/krita
```
