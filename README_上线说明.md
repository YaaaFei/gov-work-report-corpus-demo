# 2024–2026 政府工作报告小型语料库上线演示

这是一个基于 Streamlit 的教学版语料库检索页面。

## 文件结构

```text
gov_report_corpus_streamlit/
├─ app.py
├─ requirements.txt
├─ data/
│  ├─ 04_2024_auto_usable_parallel.csv
│  ├─ 04_2025_auto_usable_parallel.csv
│  └─ 04_2026_auto_usable_parallel.csv
└─ README_上线说明.md
```

## 本地运行

在 VS Code 终端中进入这个文件夹，然后运行：

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

运行后，浏览器会自动打开一个本地网页。

## 教学定位

- 如何把清洗后的 CSV 语料做成网页；
- 如何按年份筛选语料；
- 如何输入关键词检索；
- 如何显示简易 KWIC 上下文；
- 如何下载检索结果。

## 数据说明

本页面为课程教学演示项目，语料来源于公开发布的 2024–2026 年政府工作报告文本；本页面不是官方发布平台。
