<template>
  <div class="dashboard-page">
    <div class="dash-top">
      <div class="dash-title">
        <h1>欢迎回来，{{ authStore.user?.username || '用户' }}</h1>
        <p>想学习什么？从搜索开始</p>
      </div>
      <div class="dash-search">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8" />
          <path d="m21 21-4.35-4.35" />
        </svg>
        <input v-model="searchQuery" type="text" placeholder="搜索课程、知识点、作业..." />
      </div>
    </div>

    <section class="hero-section">
      <div class="hero-cards">
        <div class="hero-card hero-left">
          <div class="hero-content">
            <div class="hero-badge">AI 学习助手</div>
            <h2>开启你的新学习旅程</h2>
            <p>上传资料到知识库，用智能问答快速理解与复习。</p>
            <div class="hero-actions">
              <router-link to="/knowledge" class="btn-solid">构建知识库</router-link>
              <router-link to="/chat" class="btn-ghost">立即提问</router-link>
            </div>
          </div>
          <div class="hero-art" aria-hidden="true">
            <div class="art-pill">RAG</div>
            <div class="art-pill">Graph</div>
            <div class="art-pill">Eval</div>
          </div>
        </div>

        <div class="hero-card hero-right">
          <div class="hero-content">
            <div class="hero-badge badge-dark">学习画像</div>
            <h2>看见进步，找到薄弱点</h2>
            <p>用学习画像与评估结果，持续优化你的学习策略。</p>
            <div class="hero-actions">
              <router-link to="/portrait" class="btn-solid btn-solid-dark">查看画像</router-link>
              <router-link to="/evaluation" class="btn-ghost">开始评估</router-link>
            </div>
          </div>
          <div class="hero-icons" aria-hidden="true">
            <span>📚</span><span>🧠</span><span>✨</span>
          </div>
        </div>
      </div>
      <div class="hero-dots" aria-hidden="true">
        <span class="dot active"></span>
        <span class="dot"></span>
        <span class="dot"></span>
      </div>
    </section>

    <section class="entry-section">
      <div class="entry-grid">
        <div class="entry-card" @click="$router.push('/chat')">
          <div class="entry-icon">💬</div>
          <div class="entry-text">
            <h3>智能问答</h3>
            <p>快速获得可解释的答案</p>
          </div>
        </div>
        <div class="entry-card" @click="$router.push('/knowledge')">
          <div class="entry-icon">📦</div>
          <div class="entry-text">
            <h3>知识库管理</h3>
            <p>上传、整理与检索资料</p>
          </div>
        </div>
        <div class="entry-card" @click="$router.push('/graph')">
          <div class="entry-icon">🕸️</div>
          <div class="entry-text">
            <h3>知识图谱</h3>
            <p>重点展示知识关系网络</p>
          </div>
        </div>
      </div>
    </section>

    <section class="trust-section">
      <h3>学习来自优质资源与智能技术</h3>
      <div class="trust-row">
        <span class="trust-badge">RAG 检索增强</span>
        <span class="trust-badge">向量 + 关键词</span>
        <span class="trust-badge">知识图谱</span>
        <span class="trust-badge">个性化推荐</span>
        <span class="trust-badge">学习画像</span>
        <span class="trust-badge">智能评估</span>
      </div>
    </section>

    <section class="trending-section">
      <div class="trending-head">
        <h3>热门学习</h3>
        <div class="trending-tabs">
          <a href="#" class="tab" @click.prevent>最受欢迎 →</a>
          <a href="#" class="tab" @click.prevent>本周聚焦 →</a>
          <a href="#" class="tab" @click.prevent>AI 与编程 →</a>
        </div>
      </div>
      <div class="trending-empty">
        <p>当前账号暂无推荐内容。完成一次提问或上传资料后会生成个性化推荐。</p>
        <div class="trending-actions">
          <router-link to="/chat" class="btn-solid">去提问</router-link>
          <router-link to="/knowledge" class="btn-ghost">去上传资料</router-link>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const searchQuery = ref('')
</script>

<style scoped>
.dashboard-page {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.dash-top {
  display: grid;
  grid-template-columns: 1fr 520px;
  gap: 24px;
  align-items: end;
  margin-bottom: 18px;
}

.dash-title h1 {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 6px 0;
}

.dash-title p {
  margin: 0;
  color: var(--text-muted);
  font-size: 14px;
}

.dash-search {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 44px;
  padding: 0 14px;
  border: 1px solid var(--border);
  border-radius: 22px;
  background: var(--bg-primary);
  box-shadow: var(--shadow-sm);
}

.dash-search svg {
  color: var(--text-muted);
}

.dash-search input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 14px;
  color: var(--text-primary);
}

.hero-section {
  margin-bottom: 26px;
}

.hero-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.hero-card {
  border-radius: 16px;
  padding: 28px 30px;
  min-height: 260px;
  position: relative;
  overflow: hidden;
}

.hero-left {
  background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
  color: #fff;
}

.hero-right {
  background: #0b1b4a;
  color: #fff;
}

.hero-content {
  position: relative;
  z-index: 1;
  max-width: 420px;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  height: 26px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.2);
  margin-bottom: 14px;
}

.badge-dark {
  background: rgba(255, 255, 255, 0.18);
}

.hero-card h2 {
  margin: 0 0 10px 0;
  font-size: 22px;
  font-weight: 800;
  letter-spacing: 0.2px;
}

.hero-card p {
  margin: 0 0 20px 0;
  font-size: 14px;
  line-height: 1.6;
  opacity: 0.92;
}

.hero-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.btn-solid {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 40px;
  padding: 0 16px;
  border-radius: 999px;
  background: #fff;
  color: #1d4ed8;
  font-weight: 700;
  text-decoration: none;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-solid:hover {
  filter: brightness(1.02);
  transform: translateY(-1px);
}

.btn-ghost {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 40px;
  padding: 0 16px;
  border-radius: 999px;
  background: transparent;
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.35);
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-ghost:hover {
  background: rgba(255, 255, 255, 0.08);
}

.btn-solid-dark {
  background: #fff;
  color: #0b1b4a;
}

.hero-art {
  position: absolute;
  right: 18px;
  bottom: 18px;
  display: flex;
  gap: 10px;
  opacity: 0.35;
}

.art-pill {
  padding: 8px 12px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.35);
  font-weight: 800;
  letter-spacing: 0.6px;
}

.hero-icons {
  position: absolute;
  right: 18px;
  bottom: 18px;
  display: flex;
  gap: 10px;
  font-size: 30px;
  opacity: 0.55;
}

.hero-dots {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 16px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: var(--border);
}

.dot.active {
  width: 26px;
  border-radius: 6px;
  background: var(--primary);
}

.entry-section {
  margin-bottom: 28px;
}

.entry-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
}

.entry-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px;
  border-radius: 12px;
  background: var(--bg-primary);
  border: 1px solid var(--border);
  cursor: pointer;
  transition: var(--transition);
}

.entry-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow);
  border-color: rgba(59, 130, 246, 0.35);
}

.entry-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: rgba(59, 130, 246, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
}

.entry-text h3 {
  margin: 0 0 4px 0;
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
}

.entry-text p {
  margin: 0;
  font-size: 13px;
  color: var(--text-muted);
}

.trust-section {
  margin: 10px 0 28px;
}

.trust-section h3 {
  margin: 0 0 14px 0;
  text-align: center;
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
}

.trust-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}

.trust-badge {
  padding: 10px 16px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: #fff;
  font-size: 13px;
  color: var(--text-secondary);
}

.trending-section {
  border-top: 1px solid var(--border-light);
  padding-top: 20px;
}

.trending-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}

.trending-head h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}

.trending-tabs {
  display: flex;
  gap: 18px;
  flex-wrap: wrap;
}

.trending-tabs .tab {
  color: var(--primary);
  text-decoration: none;
  font-weight: 600;
  font-size: 14px;
}

.trending-tabs .tab:hover {
  text-decoration: underline;
}

.trending-empty {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 28px;
}

.trending-empty p {
  margin: 0 0 16px 0;
  color: var(--text-muted);
  font-size: 14px;
}

.trending-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

@media (max-width: 980px) {
  .dash-top {
    grid-template-columns: 1fr;
  }

  .hero-cards {
    grid-template-columns: 1fr;
  }

  .entry-grid {
    grid-template-columns: 1fr;
  }
}
</style>
