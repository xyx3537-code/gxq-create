"""
GXQ_Create Flask API

端点：
  POST /predict/sequence   — 接收原始序列文本，返回宿主预测结果
  POST /predict/fasta      — 接收 FASTA 格式文件上传，返回宿主预测结果
  GET  /example            — 返回演示用示例序列（NC_116874.1，9651 bp 真菌病毒）
  GET  /health             — 健康检查
  GET  /classes            — 返回支持的宿主类别列表
"""

import io
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import importlib.util, pathlib
from Bio import SeqIO

# 09_predict.py 以数字开头，不能直接 import，用 importlib 加载
_spec = importlib.util.spec_from_file_location(
    "predict", pathlib.Path(__file__).parent / "scripts/09_predict.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
predict = _mod.predict

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 最大上传 50 MB
CORS(app)  # 允许 React 开发服务器跨域调用

# 启动时预加载示例序列（NC_116874.1_fungi，9651 bp Mycoflexivirus OXF-1）
_EXAMPLE_ID  = ""
_EXAMPLE_SEQ = ""
_EXAMPLE_PROT = "MASSSSSRSARTLNEQISSLPTRPILQGEVVPSQPNGLCYLNFFHPASHSLFDKTRVWEKPAEIVQHAISVGAVLVADQKFSVQLGGQYLRKLSSSGPSIEYAHVARSGSWTPAQILSAECFAETRFGGESHSTGLAPMILSLLLSFFLFIGTAVGGYLWAWQPAHYSSPPNYGPGSCYLVYFHPLVRPFAFALLGLRPRLWSVRL"

try:
    _fasta_path = pathlib.Path(__file__).parent / "data/raw/real_virus.fasta"
    for _rec in SeqIO.parse(str(_fasta_path), "fasta"):
        if "NC_116874" in _rec.id:
            _EXAMPLE_ID  = _rec.id
            _EXAMPLE_SEQ = str(_rec.seq).upper()
            break
    if not _EXAMPLE_SEQ:
        _rec = next(SeqIO.parse(str(_fasta_path), "fasta"))
        _EXAMPLE_ID  = _rec.id
        _EXAMPLE_SEQ = str(_rec.seq).upper()
    print(f"[GXQ_Create] 示例序列已加载：{_EXAMPLE_ID} ({len(_EXAMPLE_SEQ)} bp)")
except Exception as _e:
    print(f"[GXQ_Create] 示例序列加载失败：{_e}")


# ── 示例序列 ─────────────────────────────────────────────
@app.get("/example")
def example():
    if not _EXAMPLE_SEQ:
        return jsonify({"error": "示例序列未加载"}), 500
    return jsonify({
        "genome_id":      _EXAMPLE_ID,
        "genome_fasta":   f">{_EXAMPLE_ID}\n{_EXAMPLE_SEQ}",
        "genome_length":  len(_EXAMPLE_SEQ),
        "protein_fasta":  f">YP_013031199.1 hypothetical protein\n{_EXAMPLE_PROT}",
    })


# ── 健康检查 ─────────────────────────────────────────────
@app.get("/health")
def health():
    return jsonify({"status": "ok", "model": "GXQ_Create v0.2 (ESM-2)"})


# ── 支持的宿主类别 ────────────────────────────────────────
@app.get("/classes")
def classes():
    import joblib
    le = joblib.load("models/label_encoder.joblib")
    return jsonify({"host_types": list(le.classes_)})


# ── 工具：从请求 JSON 中解析序列 ─────────────────────────
def _parse_json_input(data: dict):
    """
    期望 JSON 格式：
    {
      "genome": "ATCG...",          # 必填：基因组序列
      "proteins": ["MAST...", ...]  # 可选：蛋白质序列列表
    }
    """
    genome = data.get("genome", "").strip().upper()
    if not genome:
        return None, None, "缺少 genome 字段"
    proteins = data.get("proteins", [])
    if not isinstance(proteins, list):
        return None, None, "proteins 字段须为数组"
    return genome, proteins, None


# ── POST /predict/sequence ───────────────────────────────
@app.post("/predict/sequence")
def predict_sequence():
    """
    请求示例：
      curl -X POST http://localhost:5000/predict/sequence \
           -H "Content-Type: application/json" \
           -d '{"genome":"ATCGATCG...","proteins":["MAST..."]}'
    """
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "请求体须为 JSON 格式"}), 400

    genome, proteins, err = _parse_json_input(data)
    if err:
        return jsonify({"error": err}), 400

    if len(genome) < 100:
        return jsonify({"error": "基因组序列过短（< 100 bp）"}), 400

    result = predict(genome, proteins)
    return jsonify(result)


# ── POST /predict/fasta ──────────────────────────────────
@app.post("/predict/fasta")
def predict_fasta():
    """
    请求示例（multipart 上传）：
      curl -X POST http://localhost:5000/predict/fasta \
           -F "genome=@virus.fasta" \
           -F "proteins=@proteins.fasta"   # 可选

    genome.fasta 中只取第一条序列；proteins.fasta 中取所有序列。
    """
    if "genome" not in request.files:
        return jsonify({"error": "请上传 genome FASTA 文件（字段名：genome）"}), 400

    genome_file = request.files["genome"]
    try:
        genome_text = genome_file.read().decode("utf-8")
        rec = next(SeqIO.parse(io.StringIO(genome_text), "fasta"))
        genome_seq = str(rec.seq).upper()
    except Exception as e:
        return jsonify({"error": f"FASTA 解析失败：{e}"}), 400

    proteins = []
    if "proteins" in request.files:
        prot_file = request.files["proteins"]
        try:
            prot_text = prot_file.read().decode("utf-8")
            proteins = [str(r.seq) for r in SeqIO.parse(io.StringIO(prot_text), "fasta")]
        except Exception as e:
            return jsonify({"error": f"蛋白质 FASTA 解析失败：{e}"}), 400

    if len(genome_seq) < 100:
        return jsonify({"error": "基因组序列过短（< 100 bp）"}), 400

    result = predict(genome_seq, proteins)
    result["genome_id"]    = rec.id
    result["protein_count_input"] = len(proteins)
    return jsonify(result)


REACT_BUILD = pathlib.Path(__file__).parent / "frontend" / "dist"

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react(path):
    if REACT_BUILD.exists():
        target = REACT_BUILD / path
        if path and target.exists():
            return send_from_directory(REACT_BUILD, path)
        return send_from_directory(REACT_BUILD, "index.html")
    return jsonify({"status": "GXQ_Create API running"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860, debug=False)
