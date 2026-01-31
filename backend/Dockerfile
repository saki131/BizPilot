FROM python:3.11-slim

# 作業ディレクトリ
WORKDIR /app

# 必要なパッケージをインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    fonts-ipafont-gothic \
    fonts-ipafont-mincho \
    && rm -rf /var/lib/apt/lists/*

# Python の依存を追加
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# アプリをコピー
COPY . /app

# 環境変数 PORT は Fly.io が提供
ENV PYTHONUNBUFFERED=1

# デフォルトのポート
EXPOSE 8000

# 起動コマンド
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
