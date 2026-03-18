<template>
  <div class="home-page">
    <!-- 登录弹窗 -->
    <Teleport to="body">
      <div v-if="showLoginModal" class="login-modal-overlay" @click.self="closeLoginModal">
        <LoginCard @close="closeLoginModal" />
      </div>
    </Teleport>

    <!-- Hero：左右两块大卡片 -->
    <section class="hero-section">
      <div class="hero-cards">
        <div class="hero-card hero-card-left" style="background-image: url('../../icons/icon_u7adlm4fwln/first page/1.jpg');">
          <div class="hero-card-overlay"></div>
          <div class="hero-card-content">
            <h2 class="hero-card-title">AI 智能学习平台</h2>
            <p class="hero-card-desc">基于 RAG 的智能教育助手，为你提供精准答疑与个性化学习路径。</p>
            <router-link v-if="authStore.isAuthenticated" to="/dashboard" class="btn-hero">进入学习 →</router-link>
            <a v-else href="#" class="btn-hero" @click.prevent="showLoginModal = true">立即体验 →</a>
          </div>
        </div>
        <div class="hero-card hero-card-right" style="background-image: url('../../icons/icon_u7adlm4fwln/first page/2.jpg');">
          <div class="hero-card-overlay"></div>
          <div class="hero-card-content">
            <h2 class="hero-card-title">知识库 + 智能问答</h2>
            <p class="hero-card-desc">上传教材与笔记，随时向 AI 提问，巩固知识点、备考更高效。</p>
            <router-link to="/chat" class="btn-hero btn-hero-outline">进入智能问答 →</router-link>
          </div>
          <div class="hero-card-decoration">
            <span class="deco-icon">📚</span>
            <span class="deco-icon">💬</span>
            <span class="deco-icon">✨</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 三张功能卡片 -->
    <section class="feature-cards-section">
      <div class="feature-cards">
        <div class="feature-card-item" @click="$router.push('/knowledge')">
          <img src="../../icons/icon_u7adlm4fwln/shujia.png" alt="构建个人知识库" class="feature-card-icon" />
          <p class="feature-card-text">构建个人知识库</p>
        </div>
        <div class="feature-card-item" @click="$router.push('/chat')">
          <img src="../../icons/icon_u7adlm4fwln/duihua.png" alt="智能问答与检索" class="feature-card-icon" />
          <p class="feature-card-text">智能问答与检索</p>
        </div>
        <div class="feature-card-item" @click="$router.push('/evaluation')">
          <img src="../../icons/icon_u7adlm4fwln/tongji.png" alt="学习评估与画像" class="feature-card-icon" />
          <p class="feature-card-text">学习评估与画像</p>
        </div>
      </div>
    </section>

    <!-- 合作/信任区 -->
    <section class="partners-section">
      <h3 class="partners-title">学习来自优质资源与智能技术</h3>
      <div class="partners-scroll">
        <div class="partners-track">
          <span class="partner-badge">RAG 检索增强</span>
          <span class="partner-badge">向量 + 关键词</span>
          <span class="partner-badge">知识图谱</span>
          <span class="partner-badge">个性化推荐</span>
          <span class="partner-badge">智能评估</span>
          <span class="partner-badge">多端同步</span>
        </div>
      </div>
      <button type="button" class="partners-arrow" aria-label="查看更多">→</button>
    </section>

    <!-- 热门学习 / 趋势课程 -->
    <section class="trending-section">
      <h3 class="trending-title">热门学习</h3>
      <div class="trending-tabs">
        <a href="#" class="trending-tab">最受欢迎 →</a>
        <a href="#" class="trending-tab">本周聚焦 →</a>
        <a href="#" class="trending-tab">AI 与编程 →</a>
      </div>
      <div class="trending-placeholder">
        <p>登录后即可查看推荐课程与学习计划</p>
        <router-link to="/login" class="btn-primary">登录 / 注册</router-link>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import LoginCard from './LoginCard.vue'

const authStore = useAuthStore()
const showLoginModal = ref(false)

onMounted(() => {
  // 未登录时自动弹出登录框
  if (!authStore.isAuthenticated) {
    showLoginModal.value = true
  }
})

const closeLoginModal = () => {
  showLoginModal.value = false
}
</script>

<style scoped>
.home-page {
  padding: 0 24px 60px;
  max-width: 1200px;
  margin: 0 auto;
  background: #fff;
}

/* Hero：左右两块大卡片 */
.hero-section {
  margin-bottom: 32px;
}

.hero-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.hero-card {
  min-height: 280px;
  border-radius: 16px;
  padding: 32px 36px;
  position: relative;
  overflow: hidden;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
}

.hero-card-left {
  color: white;
  transform: translateY(15px);
}

.hero-card-right {
  color: white;
  transform: translateY(15px);
}

.hero-card-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.7));
  backdrop-filter: blur(5px);
  z-index: 0;
}

.hero-card-content {
  position: relative;
  z-index: 1;
}

.hero-card-title {
  font-size: 22px;
  font-weight: 700;
  margin: 0 0 12px 0;
}

.hero-card-desc {
  font-size: 15px;
  line-height: 1.6;
  margin: 0 0 24px 0;
  opacity: 0.95;
}

.hero-card-right .hero-card-desc {
  color: white;
  opacity: 0.95;
}

.btn-hero {
  display: inline-block;
  padding: 12px 24px;
  background: rgba(255, 255, 255, 0.95);
  color: #2563eb;
  font-weight: 600;
  font-size: 14px;
  border-radius: 8px;
  text-decoration: none;
  transition: all 0.2s;
}

.btn-hero:hover {
  background: white;
  transform: translateY(-1px);
}

.btn-hero-outline {
  background: transparent;
  color: white;
  border: 2px solid white;
}

.btn-hero-outline:hover {
  background: rgba(255, 255, 255, 0.1);
}

.hero-card-decoration {
  position: absolute;
  right: 24px;
  bottom: 24px;
  display: flex;
  gap: 12px;
  font-size: 32px;
  opacity: 0.5;
}

/* 三张功能卡片 */
.feature-cards-section {
  margin-bottom: 48px;
}

.feature-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.feature-card-item {
  background: #f1f5f9;
  border-radius: 12px;
  padding: 28px 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.feature-card-item:hover {
  background: #e2e8f0;
  border-color: var(--primary);
  transform: translateY(-2px);
}

.feature-card-icon {
  width: 48px;
  height: 48px;
  object-fit: contain;
  display: block;
  margin: 0 auto 12px;
  opacity: 0.9;
}

.feature-card-text {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

/* 合作/信任区 */
.partners-section {
  margin-bottom: 48px;
  position: relative;
  padding: 40px 24px;
  border-radius: 16px;
  overflow: hidden;
  background-color: #87CEFA; /* 天蓝色背景 */
}

.partners-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: url('../../icons/icon_u7adlm4fwln/element.png');
  background-size: contain;
  background-position: center;
  background-repeat: no-repeat;
  opacity: 0.5; /* 增加不透明度，让图标更明显 */
  z-index: 0;
  transform: scale(1.05); /* 放大1.05倍，更合适的大小 */
  filter: brightness(0) invert(1); /* 将图标变为纯白 */
}

.partners-section > * {
  position: relative;
  z-index: 1;
}

.partners-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 20px 0;
  text-align: center;
}

.partners-scroll {
  overflow-x: auto;
  padding: 8px 0;
  scrollbar-width: none;
}

.partners-scroll::-webkit-scrollbar {
  display: none;
}

.partners-track {
  display: flex;
  gap: 16px;
  padding: 12px 0;
  justify-content: center;
  flex-wrap: wrap;
}

.partner-badge {
  flex-shrink: 0;
  padding: 10px 20px;
  background: white;
  border: 1px solid var(--border);
  border-radius: 24px;
  font-size: 14px;
  color: var(--text-secondary);
}

.partners-arrow {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 40px;
  height: 40px;
  border: 1px solid var(--border);
  border-radius: 50%;
  background: white;
  font-size: 18px;
  cursor: pointer;
  color: var(--text-muted);
}

.partners-arrow:hover {
  background: var(--bg-tertiary);
  color: var(--primary);
}

/* 热门学习 */
.trending-section {
  padding-top: 24px;
  border-top: 1px solid var(--border-light);
}

.trending-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 16px 0;
}

.trending-tabs {
  display: flex;
  gap: 24px;
  margin-bottom: 24px;
}

.trending-tab {
  font-size: 15px;
  font-weight: 500;
  color: var(--primary);
  text-decoration: none;
}

.trending-tab:hover {
  text-decoration: underline;
}

.trending-placeholder {
  background: #f8fafc;
  border-radius: 12px;
  padding: 48px;
  text-align: center;
}

.trending-placeholder p {
  font-size: 15px;
  color: var(--text-muted);
  margin: 0 0 20px 0;
}

.btn-primary {
  display: inline-block;
  padding: 12px 24px;
  background: var(--primary);
  color: white;
  font-weight: 500;
  font-size: 14px;
  border-radius: 8px;
  text-decoration: none;
  border: none;
  cursor: pointer;
}

.btn-primary:hover {
  background: var(--primary-dark);
}

@media (max-width: 768px) {
  .hero-cards {
    grid-template-columns: 1fr;
  }

  .hero-card {
    min-height: 220px;
  }

  .feature-cards {
    grid-template-columns: 1fr;
  }

  .partners-arrow {
    display: none;
  }

  .trending-tabs {
    flex-wrap: wrap;
  }
}

/* 登录弹窗样式 */
.login-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}
</style>
