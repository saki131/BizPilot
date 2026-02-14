# Vercel ステージング環境設定ガイド

## 環境変数の設定

### 1. Vercel Dashboardにアクセス
https://vercel.com/dashboard

### 2. プロジェクトを選択
BizPilot プロジェクトを選択

### 3. 環境変数の設定
**Settings** → **Environment Variables** へ移動

### 4. ステージング環境用の環境変数を追加

#### バックエンドAPIエンドポイント
- **Key**: `NEXT_PUBLIC_API_URL`
- **Value**: `https://bizpilot-backend-staging.fly.dev`
- **Environment**: `Preview` のみ選択
- **Git Branch**: `backlog/master` を指定

「Save」をクリック

### 5. ブランチベースのデプロイ設定確認

**Settings** → **Git** → **Production Branch** で以下を確認：
- **Production Branch**: `master`
- **Preview Deployments**: すべてのブランチで有効

### 6. デプロイの確認

#### ステージング環境（backlog/masterブランチ）
```bash
git checkout backlog/master
git push origin backlog/master
```

デプロイ後、Vercel Dashboardで以下を確認：
- **URL**: `bizpilot-git-backlog-master-<your-username>.vercel.app`
- **Branch**: backlog/master
- **Environment**: Preview

#### 本番環境（masterブランチ）
```bash
git checkout master
git merge backlog/master
git push origin master
```

デプロイ後、Vercel Dashboardで以下を確認：
- **URL**: `bizpilot.vercel.app` (カスタムドメイン設定済みの場合)
- **Branch**: master
- **Environment**: Production

## 環境ごとのAPI URL

| 環境 | ブランチ | Vercel URL | API URL |
|------|---------|-----------|---------|
| Local | - | localhost:3000 | http://localhost:8000 |
| Staging | backlog/master | bizpilot-git-backlog-master-*.vercel.app | https://bizpilot-backend-staging.fly.dev |
| Production | master | bizpilot.vercel.app | https://bizpilot-backend.fly.dev |

## トラブルシューティング

### 環境変数が反映されない場合
1. Vercel Dashboard → Deployments → 対象のデプロイ → **Redeploy**
2. "Use existing Build Cache" のチェックを外す
3. "Redeploy" をクリック

### APIエンドポイントの確認
ブラウザのコンソールで以下を実行：
```javascript
console.log(process.env.NEXT_PUBLIC_API_URL)
```

ステージング環境では `https://bizpilot-backend-staging.fly.dev` が表示されるはずです。
