import axios from "axios";

/**
 * 后端基址：开发环境默认走 Vite 代理（见 vite.config.js），
 * 生产或直连时可设置 VITE_API_BASE，例如 http://127.0.0.1:8000
 */
const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE ?? "",
  timeout: 120000,
});

/**
 * 健康检查
 * @returns {Promise<import('axios').AxiosResponse<{ code: number; message: string; data: unknown }>>}
 */
export function fetchHealth() {
  return client.get("/api/health");
}

/**
 * 上传 PDF 分析简历（multipart：file 必填，jd_text 选填）
 * @param {File} file
 * @param {string} [jdText] 岗位 JD，非空时后端返回 match_analysis
 */
export function analyzeResumePdf(file, jdText = "") {
  const form = new FormData();
  form.append("file", file);
  const jd = (jdText || "").trim();
  if (jd) {
    form.append("jd_text", jd);
  }
  return client.post("/api/resume/analyze", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
}
