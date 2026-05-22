FROM python:3.11-slim

# 安装 Node.js（用于编译 React 前端）
RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 安装 Python 依赖（CPU-only torch，体积小）
COPY requirements-app.txt .
RUN pip install --no-cache-dir \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r requirements-app.txt

# 预下载 ESM-2 模型，缓存进镜像
RUN python -c "\
from transformers import AutoTokenizer, AutoModel; \
AutoTokenizer.from_pretrained('facebook/esm2_t6_8M_UR50D'); \
AutoModel.from_pretrained('facebook/esm2_t6_8M_UR50D'); \
print('ESM-2 cached')"

# 编译 React 前端
COPY frontend/package*.json ./frontend/
RUN cd frontend && npm install
COPY frontend/ ./frontend/
RUN cd frontend && npm run build

# 复制 Flask 代码和模型
COPY app.py .
COPY scripts/ ./scripts/
COPY models/  ./models/

# Hugging Face Spaces 要求端口 7860
EXPOSE 7860

CMD ["gunicorn", "--workers", "2", "--timeout", "180", \
     "--bind", "0.0.0.0:7860", "app:app"]
