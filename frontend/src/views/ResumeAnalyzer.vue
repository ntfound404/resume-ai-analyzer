<template>
  <div class="page">
    <header class="hero">
      <h1>AI 智能简历分析系统</h1>
      <p class="sub">上传 PDF 简历，一键生成结构化解析与职业洞察</p>
    </header>

    <el-card class="upload-card" shadow="hover">
      <template #header>
        <span class="card-title">简历上传</span>
      </template>
      <el-upload
        ref="uploadRef"
        drag
        :auto-upload="false"
        :limit="1"
        accept=".pdf,application/pdf"
        :on-exceed="onExceed"
        :on-change="onFileChange"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">将 PDF 拖到此处，或 <em>点击选择</em></div>
        <template #tip>
          <div class="el-upload__tip">仅支持文本型 PDF，单文件，最大建议 10MB 以内</div>
        </template>
      </el-upload>
      <div class="jd-field">
        <label class="jd-label">岗位 JD（可选）</label>
        <el-input
          v-model="jdText"
          type="textarea"
          :rows="5"
          placeholder="请输入岗位 JD，可选。填写后将进行岗位匹配分析"
          :disabled="loading"
          maxlength="8000"
          show-word-limit
        />
      </div>
      <div class="actions">
        <el-button type="primary" :loading="loading" :disabled="!currentFile" @click="submit">
          开始分析
        </el-button>
        <el-button @click="clearFile" :disabled="loading">清空</el-button>
      </div>
    </el-card>

    <el-alert
      v-if="errorMsg"
      class="mt"
      type="error"
      :closable="true"
      @close="errorMsg = ''"
      :title="errorMsg"
      show-icon
    />

    <template v-if="result">
      <el-card class="mt result-card" shadow="hover">
        <template #header>
          <div class="result-header">
            <span class="card-title">分析结果</span>
            <el-tooltip v-if="resumeStatusTag" :content="resumeStatusTag.hint" placement="bottom">
              <el-tag :type="resumeStatusTag.type" effect="plain">{{ resumeStatusTag.label }}</el-tag>
            </el-tooltip>
          </div>
        </template>

        <section class="block">
          <h3>基本信息</h3>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="姓名">{{ basic.name || "—" }}</el-descriptions-item>
            <el-descriptions-item label="手机">{{ basic.phone || "—" }}</el-descriptions-item>
            <el-descriptions-item label="邮箱">{{ basic.email || "—" }}</el-descriptions-item>
            <el-descriptions-item label="地点">{{ basic.location || "—" }}</el-descriptions-item>
            <el-descriptions-item label="学历" :span="2">
              {{ basic.education_level || "—" }}
            </el-descriptions-item>
          </el-descriptions>
        </section>

        <section class="block">
          <h3>技能标签</h3>
          <div v-if="skills.length" class="tags">
            <el-tag v-for="(s, i) in skills" :key="i" class="tag" type="info" effect="light">
              {{ s }}
            </el-tag>
          </div>
          <el-empty v-else description="暂无技能" :image-size="64" />
        </section>

        <section class="block">
          <h3>教育经历</h3>
          <el-timeline v-if="education.length">
            <el-timeline-item
              v-for="(edu, i) in education"
              :key="i"
              :timestamp="formatRange(edu.start_date, edu.end_date)"
              placement="top"
            >
              <el-card shadow="never" class="inner-card">
                <div class="strong">{{ edu.school || "学校未填" }}</div>
                <div class="muted">{{ edu.major }} · {{ edu.degree }}</div>
              </el-card>
            </el-timeline-item>
          </el-timeline>
          <el-empty v-else description="暂无教育经历" :image-size="64" />
        </section>

        <section class="block">
          <h3>工作经历</h3>
          <el-timeline v-if="work.length">
            <el-timeline-item
              v-for="(w, i) in work"
              :key="i"
              :timestamp="formatRange(w.start_date, w.end_date)"
              placement="top"
            >
              <el-card shadow="never" class="inner-card">
                <div class="strong">{{ w.company }} — {{ w.position }}</div>
                <p class="desc">{{ w.description }}</p>
              </el-card>
            </el-timeline-item>
          </el-timeline>
          <el-empty v-else description="暂无工作经历" :image-size="64" />
        </section>

        <section class="block">
          <h3>项目经历</h3>
          <div v-if="projects.length" class="project-list">
            <el-card v-for="(p, i) in projects" :key="i" class="project-card" shadow="never">
              <div class="strong">{{ p.name }}</div>
              <div class="muted">角色：{{ p.role || "—" }}</div>
              <p class="desc">{{ p.description }}</p>
              <div v-if="p.technologies?.length" class="tags">
                <el-tag
                  v-for="(t, j) in p.technologies"
                  :key="j"
                  size="small"
                  type="success"
                  effect="plain"
                >
                  {{ t }}
                </el-tag>
              </div>
              <ul v-if="p.highlights?.length" class="highlights">
                <li v-for="(h, k) in p.highlights" :key="k">{{ h }}</li>
              </ul>
            </el-card>
          </div>
          <el-empty v-else description="暂无项目" :image-size="64" />
        </section>

        <section v-if="matchAnalysis" class="block match-block">
          <div class="match-section-head">
            <h3>岗位匹配分析</h3>
            <el-tag v-if="jdMatchStatusTag" :type="jdMatchStatusTag.type" size="small" effect="plain">
              {{ jdMatchStatusTag.label }}
            </el-tag>
          </div>
          <div class="match-score-row">
            <span>匹配分数</span>
            <el-progress
              :percentage="matchScore"
              :stroke-width="18"
              :color="matchScoreColor"
              style="flex: 1; max-width: 420px"
            />
            <span class="score-num">{{ matchScore }}</span>
          </div>
          <div class="sub-block">
            <div class="sub-title">已匹配技能</div>
            <div v-if="matchAnalysis.matched_skills?.length" class="tags">
              <el-tag
                v-for="(s, i) in matchAnalysis.matched_skills"
                :key="'m-' + i"
                class="tag"
                type="success"
                effect="light"
              >
                {{ s }}
              </el-tag>
            </div>
            <el-empty v-else description="暂无" :image-size="56" />
          </div>
          <div class="sub-block">
            <div class="sub-title">缺失技能</div>
            <div v-if="matchAnalysis.missing_skills?.length" class="tags">
              <el-tag
                v-for="(s, i) in matchAnalysis.missing_skills"
                :key="'x-' + i"
                class="tag"
                type="danger"
                effect="light"
              >
                {{ s }}
              </el-tag>
            </div>
            <el-empty v-else description="暂无" :image-size="56" />
          </div>
          <div class="sub-block">
            <div class="sub-title">岗位关键词</div>
            <div v-if="matchAnalysis.job_keywords?.length" class="tags">
              <el-tag
                v-for="(k, i) in matchAnalysis.job_keywords"
                :key="'j-' + i"
                size="small"
                effect="plain"
              >
                {{ k }}
              </el-tag>
            </div>
            <el-empty v-else description="暂无" :image-size="56" />
          </div>
          <div class="sub-block">
            <div class="sub-title">候选人关键词</div>
            <div v-if="matchAnalysis.candidate_keywords?.length" class="tags">
              <el-tag
                v-for="(k, i) in matchAnalysis.candidate_keywords"
                :key="'c-' + i"
                size="small"
                type="info"
                effect="plain"
              >
                {{ k }}
              </el-tag>
            </div>
            <el-empty v-else description="暂无" :image-size="56" />
          </div>
          <el-alert
            :title="matchAnalysis.summary || '暂无匹配总结'"
            type="info"
            class="mt-inner"
            show-icon
            :closable="false"
          />
          <div class="grid-3 mt-inner">
            <el-card header="候选人优势" shadow="never">
              <ul class="list">
                <li v-for="(s, i) in matchAnalysis.advantages" :key="'a-' + i">{{ s }}</li>
                <li v-if="!matchAnalysis.advantages?.length" class="muted">暂无</li>
              </ul>
            </el-card>
            <el-card header="差距分析" shadow="never">
              <ul class="list">
                <li v-for="(s, i) in matchAnalysis.gaps" :key="'g-' + i">{{ s }}</li>
                <li v-if="!matchAnalysis.gaps?.length" class="muted">暂无</li>
              </ul>
            </el-card>
            <el-card header="提升建议" shadow="never">
              <ul class="list">
                <li v-for="(s, i) in matchAnalysis.improvement_suggestions" :key="'i-' + i">
                  {{ s }}
                </li>
                <li v-if="!matchAnalysis.improvement_suggestions?.length" class="muted">暂无</li>
              </ul>
            </el-card>
          </div>
        </section>

        <section class="block analysis">
          <h3>AI 总结与建议</h3>
          <el-alert :title="analysis.summary || '暂无总结'" type="info" show-icon :closable="false" />
          <div class="grid-3 mt-inner">
            <el-card header="优势" shadow="never">
              <ul class="list">
                <li v-for="(s, i) in analysis.strengths" :key="i">{{ s }}</li>
                <li v-if="!analysis.strengths?.length" class="muted">暂无</li>
              </ul>
            </el-card>
            <el-card header="风险" shadow="never">
              <ul class="list">
                <li v-for="(r, i) in analysis.risks" :key="i">{{ r }}</li>
                <li v-if="!analysis.risks?.length" class="muted">暂无</li>
              </ul>
            </el-card>
            <el-card header="建议" shadow="never">
              <ul class="list">
                <li v-for="(s, i) in analysis.suggestions" :key="i">{{ s }}</li>
                <li v-if="!analysis.suggestions?.length" class="muted">暂无</li>
              </ul>
            </el-card>
          </div>
          <div class="score-row">
            <span>综合评分</span>
            <el-progress
              :percentage="normalizedScore"
              :stroke-width="18"
              :color="scoreColor"
              style="flex: 1; max-width: 420px"
            />
            <span class="score-num">{{ normalizedScore }}</span>
          </div>
        </section>
      </el-card>
    </template>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";
import { ElMessage } from "element-plus";
import { UploadFilled } from "@element-plus/icons-vue";
import { analyzeResumePdf } from "../api/resume.js";

const uploadRef = ref();
const currentFile = ref(null);
const jdText = ref("");
const loading = ref(false);
const errorMsg = ref("");
const result = ref(null);

const basic = computed(() => result.value?.basic_info ?? {});
const skills = computed(() => result.value?.skills ?? []);
const education = computed(() => result.value?.education ?? []);
const work = computed(() => result.value?.work_experience ?? []);
const projects = computed(() => result.value?.projects ?? []);
const analysis = computed(() => result.value?.analysis ?? {});
/** 仅当请求时携带 JD 时后端返回 */
const matchAnalysis = computed(() => result.value?.match_analysis ?? null);

const matchScore = computed(() => {
  const s = Number(matchAnalysis.value?.match_score);
  if (Number.isFinite(s)) return Math.min(100, Math.max(0, Math.round(s)));
  return 0;
});

const matchScoreColor = computed(() => {
  const p = matchScore.value;
  if (p >= 80) return "#67c23a";
  if (p >= 60) return "#409eff";
  if (p >= 40) return "#e6a23c";
  return "#f56c6c";
});

const normalizedScore = computed(() => {
  const s = Number(analysis.value?.score);
  if (Number.isFinite(s)) return Math.min(100, Math.max(0, Math.round(s)));
  return 0;
});

const scoreColor = computed(() => {
  const p = normalizedScore.value;
  if (p >= 80) return "#67c23a";
  if (p >= 60) return "#409eff";
  if (p >= 40) return "#e6a23c";
  return "#f56c6c";
});

/**
 * 简历解析状态：优先展示「大模型调用失败」，避免与「未配置密钥的离线演示」混淆。
 */
const resumeStatusTag = computed(() => {
  const summary = analysis.value?.summary || "";
  const risks = (analysis.value?.risks || []).join("");
  if (
    summary.includes("大模型调用失败") ||
    risks.includes("大模型调用失败") ||
    risks.includes("已回退为演示数据")
  ) {
    return {
      type: "danger",
      label: "大模型调用失败",
      hint: "简历解析已降级为离线演示数据，请检查 AI_API_KEY、网络与 AI_BASE_URL。",
    };
  }
  if (
    summary.includes("离线演示") ||
    risks.includes("未配置 AI_API_KEY") ||
    risks.includes("未调用大模型")
  ) {
    return {
      type: "warning",
      label: "离线演示",
      hint: "未配置密钥，简历结构化为本地模板，未调用大模型。",
    };
  }
  return null;
});

/** 岗位匹配是否走降级 / 未调模型（大模型成功时不显示标签） */
const jdMatchStatusTag = computed(() => {
  if (!matchAnalysis.value) return null;
  const gaps = (matchAnalysis.value.gaps || []).join("");
  if (gaps.includes("大模型调用失败")) {
    return { type: "danger", label: "大模型调用失败（已降级）" };
  }
  if (gaps.includes("大模型返回无效")) {
    return { type: "warning", label: "模型输出无效（已降级）" };
  }
  if (gaps.includes("未配置 AI_API_KEY")) {
    return { type: "info", label: "本地规则（未调大模型）" };
  }
  return null;
});

function onExceed() {
  ElMessage.warning("仅可上传 1 个 PDF，请先清空再选择");
}

function onFileChange(uploadFile) {
  currentFile.value = uploadFile?.raw ?? null;
  errorMsg.value = "";
}

function clearFile() {
  currentFile.value = null;
  jdText.value = "";
  result.value = null;
  errorMsg.value = "";
  uploadRef.value?.clearFiles();
}

function formatRange(start, end) {
  const a = start || "?";
  const b = end || "?";
  return `${a} ~ ${b}`;
}

async function submit() {
  if (!currentFile.value) {
    ElMessage.warning("请先选择 PDF 文件");
    return;
  }
  loading.value = true;
  errorMsg.value = "";
  result.value = null;
  try {
    const { data: body } = await analyzeResumePdf(currentFile.value, jdText.value);
    if (body.code !== 0) {
      errorMsg.value = body.message || "分析失败";
      return;
    }
    result.value = body.data;
    ElMessage.success("分析完成");
  } catch (e) {
    errorMsg.value = e?.response?.data?.message || e.message || "网络错误";
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.page {
  max-width: 960px;
  margin: 0 auto;
  padding: 32px 20px 64px;
}
.hero {
  text-align: center;
  margin-bottom: 28px;
}
.hero h1 {
  margin: 0 0 8px;
  font-size: 1.85rem;
  color: #1e293b;
  letter-spacing: 0.02em;
}
.sub {
  margin: 0;
  color: #64748b;
  font-size: 0.95rem;
}
.upload-card {
  border-radius: 12px;
}
.card-title {
  font-weight: 600;
  color: #334155;
}
.jd-field {
  margin-top: 20px;
}
.jd-label {
  display: block;
  margin-bottom: 8px;
  font-size: 0.9rem;
  font-weight: 600;
  color: #475569;
}
.actions {
  margin-top: 16px;
  display: flex;
  gap: 12px;
}
.match-section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
.match-section-head h3 {
  margin: 0;
  padding-left: 10px;
  font-size: 1.05rem;
  color: #0f172a;
}
/* 覆盖 .block h3 的紫色竖条，保持岗位匹配区块为青色 */
.match-block .match-section-head h3 {
  border-left: 4px solid #0ea5e9;
}
.match-block > .match-section-head + * {
  margin-top: 0;
}
.match-score-row {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}
.sub-block {
  margin-bottom: 14px;
}
.sub-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: #64748b;
  margin-bottom: 8px;
}
.mt {
  margin-top: 20px;
}
.mt-inner {
  margin-top: 16px;
}
.result-card {
  border-radius: 12px;
}
.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.block {
  margin-bottom: 28px;
}
.block h3 {
  margin: 0 0 12px;
  font-size: 1.05rem;
  color: #0f172a;
  border-left: 4px solid #6366f1;
  padding-left: 10px;
}
.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.tag {
  border-radius: 999px;
}
.inner-card {
  border-radius: 8px;
  background: #fafafa;
}
.strong {
  font-weight: 600;
  color: #1e293b;
}
.muted {
  color: #64748b;
  font-size: 0.9rem;
  margin-top: 4px;
}
.desc {
  margin: 8px 0 0;
  color: #475569;
  line-height: 1.55;
  white-space: pre-wrap;
}
.project-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.project-card {
  border-radius: 8px;
  background: #fafafa;
}
.highlights {
  margin: 8px 0 0;
  padding-left: 18px;
  color: #475569;
}
.grid-3 {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}
.list {
  margin: 0;
  padding-left: 18px;
  color: #475569;
  line-height: 1.5;
}
.score-row {
  margin-top: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}
.score-num {
  font-weight: 700;
  font-size: 1.25rem;
  color: #4f46e5;
  min-width: 36px;
}
</style>
