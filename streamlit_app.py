"""
GXQ_Create — 环境病毒宿主预测软件
Streamlit 演示界面 v0.6
"""

import importlib.util
import pathlib
import io
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from Bio import SeqIO

st.set_page_config(
    page_title="GXQ_Create — 病毒宿主预测",
    page_icon="🦠",
    layout="wide",
)

# ── 加载预测模块 ─────────────────────────────────────────
@st.cache_resource(show_spinner="正在加载模型（ESM-2 + SVM）…")
def load_predictor():
    spec = importlib.util.spec_from_file_location(
        "predict",
        pathlib.Path(__file__).parent / "scripts" / "09_predict.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.predict

predict = load_predictor()

# ── 宿主配置 ─────────────────────────────────────────────
HOST_COLOR = {
    "fungi":        "#2ecc71",
    "algae":        "#3498db",
    "protozoa":     "#f39c12",
    "bacteria":     "#e74c3c",
    "plant":        "#1abc9c",
    "invertebrate": "#9b59b6",
}
HOST_CN = {
    "fungi":        "真菌",
    "algae":        "藻类",
    "protozoa":     "原生动物",
    "bacteria":     "细菌",
    "plant":        "植物",
    "invertebrate": "无脊椎动物",
}
HOST_ICON = {
    "fungi":        "🍄",
    "algae":        "🌊",
    "protozoa":     "🔬",
    "bacteria":     "🦠",
    "plant":        "🌿",
    "invertebrate": "🦋",
}

# ── 示例序列（从训练数据实时读取完整基因组）────────────────
@st.cache_data(show_spinner=False)
def _load_example_genome() -> str:
    fasta = pathlib.Path(__file__).parent / "data" / "raw" / "real_virus.fasta"
    try:
        rec = next(SeqIO.parse(str(fasta), "fasta"))
        return str(rec.seq)
    except (FileNotFoundError, StopIteration):
        return ""

EXAMPLE_GENOME = _load_example_genome()
EXAMPLE_PROTEINS = """\
>YP_013031199.1
MASSSSSRSARTLNEQISSLPTRPILQGEVVPSQPNGLCYLNFFHPASHSLFDKTRVWEKPAEIVQHAISVGAVLVADQKFSVQLGGQYLRKLSSSGPSIEYAHVARSGSWTPAQILSAECFAETRFGGESHSTGLAPMILSLLLSFFLFIGTAVGGYLWAWQPAHYSSPPNYGPGSCYLVYFHPLVRPFAFALLGLRPRLWSVRLLALVLPTVSETNLMVQKAFTLADGTAVYHVTACTGGSWAGFGPRMSLASLDPSARLGQFSPSPEDQVIETKDAPVAKAVTGVPSLQSLGGVRQVPTSLPVPQISPGFQRRWSPSTFPASLTSENLVWEHSEDGHLAVKRVSEFVRHFPEDSAISRLPQRFAETLLVKWFARRDCNEASTVPASYRRSFDRDIVQRTVLDEFSSIGQVLDNNLTLDVLKDADSSAAYSRGLGSRNQRLVPGWEAAVMTRWLRFRDFATRSASARSYKEFVFRLASRFTLATAAQDIVNSVPDYATHVADTATDVQIIHLNADPIIPAPVAGQPPPPPVWGEAQLWDPAMIQALVDGRAQLIDAEGFTKEEIAQIIGCLAPSGAGNVPILRRSVVPDPATPDATEDVDMLPACARFTYPNGVTHIIVHHGNSAIPDQADQQWIAAHAFDFPSLAILATVMRTYATRHALEDLFKWAFEAVAYRTAFYTAADALGARHDLHSDLLISAQGASELHLPRNVTGSAYFDTFFAPVQVTGDLEMYLYATPQQLVTSATLASHCRAVALAWACKSGSLLGLSFTRAAARQNQFTRNQQDKWLRMYYGELNIFSALHANAMGFQYGFAPSALVRRTEGGLLPDWWKNYVAPTLVNHYLELWAMQSIPTFQVLPYYDATAKTSHVQWPEDTPDSTAALPSFNTERKVRLAREFSPLTGHSWLGDGGAEYNAQFYYAQGADGRFAYEGAEPKANFSSWTGTFARSFPSTPAAARGISLTNGRLGEAFSDFILPGSFISYRVASDKVINWGVNQIDDRALNNSEVRRWWLASKGAAHTSLMVNYVSPISQHYELDDFADYSVTLWEKEGRFAALSFGPLPRLLAPDTFDPVNITRDQSAFNLRFDSKPYALDQLSTSRITHNARSDVPASGPQTKYTPAEVNARVAAAISSRRNRPSGQVSYQAKNPIFADQLPHLNDYSVDVREEGLDFSRPNENSGALPAQDETSSDRLRQIQEAEARLDNAFQEYMADQQQKRAIRQARVAHVQPTFTPVPIHAPIPQRRRRLPTVTDNGPPVPVSVPVSRHKGHMTYSANRPLQQQAPPVVPNDAAAASVQQMSVNLAELQRRRASLTPTLAGPNGRRAASPRARYLSKRNEAGQPTARFGDVVHMHHIKEQDAPPTVSSPKPGEPLPDLSWAQPQPFLTNQQPPDPAQALPPQPTEEEYPRLANRARPSSAPEQVDFSQIDWDHGSGDARAQMLEEFSRKAHQHVDMTKPKN
>YP_013031200.1
MFKPIWDLMNVVADAAYKLSDSPFVLIFDVERVVAQFDLDRAPTTFSQAFLQYVFFSPVPTEAYEFIPDFPAIAAQQPAFIPTISYEGVGYLSSLMTQDPPVCHRGYYLFHNILRDDQSCATRLLRVLGLHNLEGERYYDISKVGMHRNALNKTLASIWVRGVHTSRSDLKVADADVNAVVRYLSNEVDMALRPKRDVNVCNVLIHVFSDHVAFAVRSDYLDMLRLNALAHPVHENFRSLTDCFPHTTGRAGGKVFVFPSNILSLGRPSQLQNACLNWFLSLKGKVDWQHVMPCALLLLPYIDICGPTLLHFILVNRSFLSVDTAEFAKIMKGVHASIRTTFRLPNYMRSSSTPRHAREFARTAYGLETLAGRSELLKLDINKEFAMRSVDPATRAYPSICTPLGAEFSTIRFSFSKFHQLIPKLARGMVDTLLADDIQLYTLHEFFQSRLFWGASGGAPGATVTWDGQEKLRMNKRGALLSLKETHIREILKSVVAPDSRTPVQWSVNAIKFESGKLRSILNTILEHYVIQGYLSHHIDSNATHNSWYSVGQHNPARIANTLRRICDLKRHVGFMWDYSDFNINHIFTLMAQQTLAQVDGLLARAHTSGRSAAYIEEAARDLKQAAAYVVLARFNTYLSDHETGVVARTARGLQSGERQTSRINSDSNYIDTQLVRHVSRDMFGRQLLTRITEHSGDDAFETAYSYFDGMLAAALYNLTGSAGQVHKVLMSFPQHGGGLGEYLRVSYDASNHVVNGYPVRALMGFIHGEFFSNPLPQPFERAAAFITQFAKLRRRGADLPQAFVKSVIRTNCSLTFTVGTDKRFFRPDLDIVRLPAILGGVGIEDTEKGLLAGPSPITFYHSRGATGFQLLIVANELLVKFKTALRARMNVLMLDDHIHSLALALGAYTKGIETGWWDDYYAIGKQEYERALTQLPTPGTVGSTLVLSAHPQMFEDISTAIGIVPASKTGDRLNRASHAAILRSLQHVVTLNNPSNLFSVVYDLTRDEQHPAMCTYRRASNAKFPSIPLYEMPKINARETVRSAKNPIPDFNILHKAGVTNIQPLYEEIAKSTLSGAWPKHALNESLADYGRQLAEWAHHNRFSTGVMAMPPLPDLARIRTAVKSKLMETLSIKGQSGGVVAFRENSLGFPATSTLRHSYNASTALVKPIGATISKTLTLLFDAAKGSDRLDKIINALQDRHEIAPVPALTTKLGHLRAISRALTTPRARANFADYFEGGWSLIPPVNTGWSADILTLVRDLTLNLVESADLAPITLPNLCSMDRLRAVIALHYLETVINAETVDYLQTLIPGVIIRD
"""

MAX_BATCH = 500   # 批量预测上限，防止内存溢出


# ════════════════════════════════════════════════════════
# 侧边栏
# ════════════════════════════════════════════════════════
with st.sidebar:
    st.title("🦠 GXQ_Create")
    st.caption("环境病毒宿主预测软件 v0.6")
    st.divider()
    st.markdown("**模型信息**")
    st.markdown(
        "- D1：3-mer k-mer SVM（66 维）\n"
        "- D2：ESM-2 语言模型（320 维）\n"
        "- 融合：D1×0.4 + D2×0.6\n"
        "- 5 折交叉验证准确率：**96.4%**"
    )
    st.divider()
    st.markdown("**支持宿主**")
    for host, cn in HOST_CN.items():
        st.markdown(f"{HOST_ICON[host]} **{cn}** `{host}`")
    st.divider()
    st.markdown("**开发者**")
    st.markdown("Aphria")

# ════════════════════════════════════════════════════════
# 主界面
# ════════════════════════════════════════════════════════
st.title("🦠 GXQ_Create — 环境病毒宿主预测")
st.markdown("输入病毒基因组序列，预测其最可能感染的宿主类型（6 类）。")
st.divider()

tab_single, tab_batch = st.tabs(["🔬 单条预测", "📋 批量预测"])


# ════════════════════════════════════════════════════════
# Tab 1：单条预测（原有功能）
# ════════════════════════════════════════════════════════
with tab_single:
    col_input, col_result = st.columns([1, 1], gap="large")

    # ── 输入区 ───────────────────────────────────────────
    with col_input:
        st.subheader("① 输入序列")

        input_mode = st.radio(
            "方式", ["粘贴序列", "上传 FASTA"], horizontal=True,
            label_visibility="collapsed",
        )

        genome_seq   = ""
        protein_seqs = []

        if input_mode == "粘贴序列":
            if EXAMPLE_GENOME and st.button("载入示例序列", use_container_width=True):
                st.session_state["genome_input"]  = EXAMPLE_GENOME
                st.session_state["protein_input"] = EXAMPLE_PROTEINS

            genome_seq = st.text_area(
                "基因组序列（DNA）",
                value=st.session_state.get("genome_input", ""),
                height=160,
                placeholder="粘贴病毒基因组 DNA 序列，至少 100 bp…",
                key="genome_input",
            )
            protein_raw = st.text_area(
                "蛋白质序列（可选，FASTA 格式）",
                value=st.session_state.get("protein_input", ""),
                height=80,
                placeholder="不填则自动从基因组翻译 ORF…",
                key="protein_input",
            )
            if protein_raw.strip():
                try:
                    protein_seqs = [
                        str(r.seq)
                        for r in SeqIO.parse(io.StringIO(protein_raw), "fasta")
                    ]
                except Exception:
                    st.warning("蛋白质解析失败，将自动翻译。")

        else:
            genome_file  = st.file_uploader("基因组 FASTA", type=["fasta", "fa", "fna"])
            protein_file = st.file_uploader("蛋白质 FASTA（可选）", type=["fasta", "fa", "faa"])
            if genome_file:
                try:
                    rec = next(SeqIO.parse(io.StringIO(genome_file.read().decode()), "fasta"))
                    genome_seq = str(rec.seq).upper()
                    st.success(f"已读取：{rec.id}（{len(genome_seq):,} bp）")
                except Exception as e:
                    st.error(f"解析失败：{e}")
            if protein_file:
                try:
                    protein_seqs = [
                        str(r.seq)
                        for r in SeqIO.parse(io.StringIO(protein_file.read().decode()), "fasta")
                    ]
                    st.success(f"已读取 {len(protein_seqs)} 条蛋白质序列")
                except Exception as e:
                    st.warning(f"蛋白质解析失败：{e}")

        if genome_seq:
            seq_clean = genome_seq.upper().replace(" ", "").replace("\n", "")
            gc = (seq_clean.count("G") + seq_clean.count("C")) / len(seq_clean) * 100
            c1, c2, c3 = st.columns(3)
            c1.metric("长度", f"{len(seq_clean):,} bp")
            c2.metric("GC 含量", f"{gc:.1f}%")
            c3.metric("蛋白质数", len(protein_seqs) if protein_seqs else "自动")

        st.divider()
        predict_btn = st.button(
            "🔍 开始预测", type="primary", use_container_width=True,
            disabled=len(genome_seq.strip()) < 100,
        )
        if genome_seq.strip() and len(genome_seq.strip()) < 100:
            st.caption("序列过短，至少需要 100 bp")

    # ── 结果区 ───────────────────────────────────────────
    with col_result:
        st.subheader("② 预测结果")

        if predict_btn and len(genome_seq.strip()) >= 100:
            with st.spinner("分析中…"):
                try:
                    result = predict(genome_seq.strip(), protein_seqs)
                except Exception as e:
                    st.error(f"预测出错：{e}")
                    st.stop()

            host   = result["predicted_host"]
            conf   = result["confidence"]
            probs  = result["probabilities"]
            color  = HOST_COLOR.get(host, "#888888")
            cn     = HOST_CN.get(host, host)
            icon   = HOST_ICON.get(host, "🦠")
            auto_t       = result.get("auto_translated", False)
            n_prot       = result.get("protein_count", 0)
            short_genome = result.get("short_genome", False)
            genome_len   = result.get("genome_length", 0)

            st.markdown(f"### {icon} {cn}")
            st.caption(f"host: `{host}`")

            conf_pct = int(conf * 100)
            st.progress(conf_pct, text=f"置信度 **{conf*100:.1f}%**")

            if short_genome:
                st.warning(
                    f"⚠️ 基因组较短（{genome_len:,} bp < 5,000 bp）：k-mer 统计样本不足，ORF 数量极少，"
                    "预测结果**可靠性较低**。建议提供注释蛋白质序列以提高准确率。"
                )
            if auto_t:
                st.info(f"⚡ 仅 DNA 输入：已自动翻译 {n_prot} 条 ORF 并通过 ESM-2 编码（D2）。权重调整为 D1×70% + D2×30%，无需手动提供蛋白质序列。")

            st.divider()

            # ── 环形图：6 个宿主概率，渐变配色 ──────────────
            DONUT_COLORS = {
                "fungi":        "#9333EA",
                "algae":        "#3B82F6",
                "protozoa":     "#06B6D4",
                "bacteria":     "#10B981",
                "plant":        "#22C55E",
                "invertebrate": "#6366F1",
            }

            hosts_list = list(HOST_CN.keys())
            values_pie = [probs.get(h, 0) * 100 for h in hosts_list]
            labels_pie = [f"{HOST_ICON[h]} {HOST_CN[h]}" for h in hosts_list]
            colors_pie = [DONUT_COLORS[h] for h in hosts_list]
            pull_vals  = [0.1 if h == host else 0 for h in hosts_list]

            fig = go.Figure(go.Pie(
                labels=labels_pie,
                values=values_pie,
                hole=0.60,
                pull=pull_vals,
                marker=dict(
                    colors=colors_pie,
                    line=dict(color="rgba(255,255,255,0.4)", width=2),
                ),
                textinfo="label+percent",
                textposition="outside",
                textfont=dict(size=12),
                hovertemplate="<b>%{label}</b><br>占比: %{value:.1f}%<extra></extra>",
                sort=False,
                direction="clockwise",
                rotation=60,
            ))

            fig.add_annotation(
                x=0.5, y=0.58,
                text=icon,
                showarrow=False,
                xref="paper", yref="paper",
                font=dict(size=32),
                align="center",
            )
            fig.add_annotation(
                x=0.5, y=0.44,
                text=f"<b>{cn}</b>",
                showarrow=False,
                xref="paper", yref="paper",
                font=dict(size=15, color=color),
                align="center",
            )
            fig.add_annotation(
                x=0.5, y=0.32,
                text=f"{conf*100:.1f}%",
                showarrow=False,
                xref="paper", yref="paper",
                font=dict(size=13, color="#888"),
                align="center",
            )

            fig.update_layout(
                showlegend=False,
                margin=dict(l=80, r=80, t=20, b=20),
                height=390,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True)

            c1, c2 = st.columns(2)
            c1.metric("D1 基因组 k-mer", f"{result['d1_contribution']*100:.0f}%")
            if result['auto_translated']:
                d2_label = f"{result['d2_contribution']*100:.0f}%（ORF 自动翻译）"
            else:
                d2_label = f"{result['d2_contribution']*100:.0f}%"
            c2.metric("D2 ESM-2 蛋白质", d2_label)

        else:
            st.markdown(
                """
                <div style="border:2px dashed #ddd; border-radius:10px;
                            padding:70px 20px; text-align:center; color:#bbb;">
                    <div style="font-size:44px">🧬</div>
                    <div style="margin-top:14px; font-size:15px; color:#999;">
                        在左侧输入序列后点击「开始预测」
                    </div>
                    <div style="margin-top:6px; font-size:13px;">
                        仅需 DNA 序列，蛋白质可选
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ════════════════════════════════════════════════════════
# Tab 2：批量预测
# ════════════════════════════════════════════════════════
with tab_batch:
    st.subheader("批量预测")
    st.markdown(
        f"上传包含多条病毒基因组序列的 FASTA 文件，全部使用 **仅 DNA 模式**（自动翻译 ORF）预测。"
        f"最多支持 **{MAX_BATCH} 条**序列。"
    )

    batch_file = st.file_uploader(
        "上传多序列 FASTA 文件",
        type=["fasta", "fa", "fna"],
        key="batch_fasta",
    )

    if batch_file:
        try:
            raw_text = batch_file.read().decode("utf-8", errors="replace")
            records  = list(SeqIO.parse(io.StringIO(raw_text), "fasta"))
        except Exception as e:
            st.error(f"FASTA 解析失败：{e}")
            records = []

        if records:
            n_seqs = len(records)
            if n_seqs > MAX_BATCH:
                st.warning(f"检测到 {n_seqs} 条序列，超过上限，只预测前 {MAX_BATCH} 条。")
                records = records[:MAX_BATCH]
                n_seqs  = MAX_BATCH
            else:
                st.success(f"检测到 **{n_seqs}** 条序列，点击下方按钮开始预测。")

            if st.button("🚀 开始批量预测", type="primary", use_container_width=True):
                rows     = []
                progress = st.progress(0.0, text="准备中…")
                status   = st.empty()

                for i, rec in enumerate(records):
                    status.text(f"预测中 {i+1}/{n_seqs}：{rec.id}")
                    seq = str(rec.seq).upper()
                    try:
                        r = predict(seq, [])
                        host = r["predicted_host"]
                        seq_clean = seq.replace(" ", "").replace("\n", "")
                        slen = len(seq_clean)
                        gc   = (seq_clean.count("G") + seq_clean.count("C")) / slen * 100 if slen else 0
                        rows.append({
                            "序列ID":      rec.id,
                            "长度(bp)":    slen,
                            "GC含量(%)":   round(gc, 1),
                            "预测宿主":    host,
                            "宿主(中文)":  HOST_CN.get(host, host),
                            "置信度(%)":   round(r["confidence"] * 100, 1),
                            "ORF数量":     r["protein_count"],
                            "短序列警告":  "⚠" if r["short_genome"] else "",
                        })
                    except Exception as e:
                        rows.append({
                            "序列ID":      rec.id,
                            "长度(bp)":    len(str(rec.seq)),
                            "GC含量(%)":   "",
                            "预测宿主":    "ERROR",
                            "宿主(中文)":  str(e)[:40],
                            "置信度(%)":   "",
                            "ORF数量":     "",
                            "短序列警告":  "",
                        })
                    progress.progress((i + 1) / n_seqs,
                                      text=f"进度：{i+1}/{n_seqs}")

                status.empty()
                progress.empty()
                st.success(f"✅ 预测完成，共 {len(rows)} 条")

                df = pd.DataFrame(rows)
                st.session_state["batch_df"] = df

        # ── 显示结果（预测完成后持久显示）─────────────────
        if "batch_df" in st.session_state and batch_file:
            df = st.session_state["batch_df"]

            # 结果表格（带颜色高亮宿主列）
            st.markdown("#### 预测结果")

            def highlight_host(val):
                color = HOST_COLOR.get(val, "")
                if color:
                    return f"background-color:{color}22; color:{color}; font-weight:bold"
                return ""

            styled = df.style.map(highlight_host, subset=["预测宿主"])
            st.dataframe(styled, use_container_width=True, height=400)

            # CSV 下载
            csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button(
                label="⬇️ 下载 CSV",
                data=csv_bytes,
                file_name="gxq_predictions.csv",
                mime="text/csv",
                use_container_width=True,
            )

            st.divider()

            # 宿主分布汇总图（水平条形图）
            valid_df = df[df["预测宿主"] != "ERROR"]
            if not valid_df.empty:
                st.markdown("#### 宿主分布")
                counts = (
                    valid_df["预测宿主"]
                    .value_counts()
                    .reindex(list(HOST_CN.keys()), fill_value=0)
                    .reset_index()
                )
                counts.columns = ["host", "count"]
                counts["label"] = counts["host"].map(
                    lambda h: f"{HOST_ICON.get(h,'')} {HOST_CN.get(h, h)}"
                )
                counts["color"] = counts["host"].map(HOST_COLOR)
                counts = counts[counts["count"] > 0]

                fig_bar = go.Figure(go.Bar(
                    x=counts["count"],
                    y=counts["label"],
                    orientation="h",
                    marker_color=counts["color"],
                    text=counts["count"],
                    textposition="outside",
                ))
                fig_bar.update_layout(
                    xaxis_title="序列数量",
                    yaxis=dict(autorange="reversed"),
                    margin=dict(l=10, r=40, t=10, b=40),
                    height=max(200, len(counts) * 52),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig_bar, use_container_width=True)

                # 短序列统计
                n_short = (df["短序列警告"] == "⚠").sum()
                if n_short:
                    st.caption(
                        f"⚠ {n_short} 条序列短于 5,000 bp，预测可靠性较低（结果表中标注 ⚠）。"
                    )

st.divider()
st.caption(
    "**GXQ_Create** · Multimodal eukaryotic virus-host prediction · "
    "© 2026 Yixuan Xu, Ocean University of China · "
    "License: [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) · "
    "Contact: yixuan.xu01@student.adelaide.edu.au"
)
