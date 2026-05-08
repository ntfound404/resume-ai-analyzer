# Frontend — AI 智能简历分析系统

基于 **Vue 3 + Vite + Element Plus** 的单页应用：PDF 与可选 JD 上传、分析结果与岗位匹配可视化。

---

## 前端功能说明

- **上传区**：拖拽或选择 PDF（`el-upload`），限制数量与类型
- **岗位 JD**：多行文本框（可选），随表单一并提交
- **结果展示**：基本信息、技能、教育、工作、项目、AI 总结与综合分
- **岗位匹配**（仅当填写 JD 且后端返回 `match_analysis`）：匹配分、已匹配/缺失技能、关键词、总结、优势/差距/建议
- **状态提示**：简历解析为离线演示或大模型失败时，顶部标签与 JD 区标签区分场景

---

## 安装依赖

```bash
cd frontend
npm install
```

---

## 启动命令

```bash
npm run dev
```

默认通过 `vite.config.js` 将 **`/api` 代理到 `http://127.0.0.1:8000`**，请先启动后端。

---

## 打包命令

```bash
npm run build
```

产物在 `dist/`。预览本地构建：

```bash
npm run preview
```

---

## VITE_API_BASE 说明

- **开发**：一般**不需要**设置，走 Vite 代理即可。
- **生产 / 直连后端**：构建前设置环境变量，例如 `.env.production`：

```env
VITE_API_BASE=http://127.0.0.1:8000
```

`src/api/resume.js` 中 `axios` 的 `baseURL` 为 `import.meta.env.VITE_API_BASE ?? ""`。  
若前端与 API 同域且由 Nginx 转发 `/api`，也可置空并由网关转发。

---

## 页面模块说明

| 模块 | 文件/位置 | 说明 |
|------|-----------|------|
| 入口 | `src/main.js` | 挂载 Vue、Element Plus 中文语言包 |
| 布局 | `src/App.vue` | 引入分析页 |
| 分析页 | `src/views/ResumeAnalyzer.vue` | 上传、JD、结果与匹配 UI |
| API | `src/api/resume.js` | `fetchHealth`、`analyzeResumePdf(file, jdText)` |

---

## 相关文档

- [根目录 README（总览）](../README.md)
- [API 说明](../docs/API.md)
