# 基础镜像：轻量级 Python 3.11
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 先只复制依赖文件，利用 Docker 缓存层——
# 只要 requirements.txt 不变，这一层就不会重新安装
COPY requirements.txt .
RUN pip install --no-cache-dir \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r requirements.txt

# 预下载 ESM-2 模型，缓存进镜像层——避免首次请求时才下载导致超时
RUN python -c "\
from transformers import AutoTokenizer, AutoModel; \
AutoTokenizer.from_pretrained('facebook/esm2_t6_8M_UR50D'); \
AutoModel.from_pretrained('facebook/esm2_t6_8M_UR50D'); \
print('ESM-2 模型已缓存')"

# 再复制项目代码和模型文件
COPY app.py .
COPY scripts/ ./scripts/
COPY models/  ./models/

# 容器对外暴露 5000 端口
EXPOSE 5000

# 用 gunicorn 替代 Flask 开发服务器（生产环境更稳定）
# 4 个工作进程，超时 120 秒（预测可能稍慢）
CMD ["gunicorn", "--workers", "4", "--timeout", "120", \
     "--bind", "0.0.0.0:5000", "app:app"]
