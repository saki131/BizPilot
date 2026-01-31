# Gemini API Keys 複数設定ガイド

## 概要
Gemini APIの利用上限を超過した場合に、自動的に別のAPIキーに切り替えて実行を続ける機能が実装されています。

## 環境変数の設定方法

### 方法1: 番号付きキー（推奨）
`.env`ファイルに以下のように設定します：

```env
GEMINI_KEY_1=your_first_api_key_here
GEMINI_KEY_2=your_second_api_key_here
GEMINI_KEY_3=your_third_api_key_here
```

必要な数だけキーを追加できます。番号は1から連続して設定してください。

### 方法2: カンマ区切り
複数のキーをカンマで区切って設定します：

```env
GEMINI_KEYS=key1,key2,key3
```

### 方法3: 単一キー（後方互換性）
従来通り単一のキーも使用できます：

```env
GEMINI_KEY=your_api_key_here
```

## 動作仕様

1. **自動切り替え**: APIリクエストがquota/rate limitエラーで失敗した場合、自動的に次のキーに切り替えます

2. **エラー検出**: 以下のようなエラーを検出します：
   - "quota exceeded"
   - "rate limit"
   - "resource exhausted"
   - "429 Too Many Requests"
   - "limit exceeded"

3. **リトライ**: デフォルトでは全てのキーを1回ずつ試行します

4. **待機時間**: キー切り替え時には1秒の待機時間を挟みます

5. **ログ出力**: 
   - キー切り替え時にログが出力されます
   - 失敗したキーの数が記録されます
   - 成功したキーが記録されます

## デバッグログの例

```
[DEBUG genai_wrapper] Loaded 3 API keys for rotation
[DEBUG] Loaded 3 Gemini API key(s)
[DEBUG] API Key 1: ...xyz12345
[DEBUG] API Key 2: ...abc67890
[DEBUG] API Key 3: ...def13579
[DEBUG genai_wrapper] Attempt 1/3 with key ...xyz12345
[WARN genai_wrapper] Quota exceeded for API key ...xyz12345, trying next key
[WARN genai_wrapper] Marked API key ...xyz12345 as failed (1/3 failed)
[DEBUG genai_wrapper] Attempt 2/3 with key ...abc67890
[DEBUG genai_wrapper] Successfully generated content with key ...abc67890
```

## 本番環境への適用

### Fly.io
```bash
flyctl secrets set GEMINI_KEY_1="your_first_key"
flyctl secrets set GEMINI_KEY_2="your_second_key"
flyctl secrets set GEMINI_KEY_3="your_third_key"
```

### Vercel
Environment Variablesセクションで以下を追加：
- `GEMINI_KEY_1`
- `GEMINI_KEY_2`
- `GEMINI_KEY_3`

## ベストプラクティス

1. **複数プロジェクト**: 異なるGoogle Cloudプロジェクトから複数のAPIキーを取得することを推奨
2. **キー数**: 最低3つのキーを設定すると安定性が向上
3. **モニタリング**: ログを定期的に確認し、失敗率の高いキーを交換
4. **セキュリティ**: APIキーは絶対にコードにハードコードせず、環境変数で管理

## トラブルシューティング

### 全てのキーが失敗する場合
- 全てのキーでquotaが超過している可能性
- 一時的に待機してから再試行
- Google Cloud Consoleでquotaを確認

### キーが読み込まれない場合
- 環境変数が正しく設定されているか確認
- サーバーを再起動
- ログで"Loaded X Gemini API key(s)"を確認
