<template>
  <div class="portrait-page">
    <div class="portrait-layout">
      <!-- 左侧主栏 -->
      <div class="portrait-main">
        <!-- 个人资料卡片 -->
        <div class="profile-card">
          <div class="profile-header">
            <div class="avatar-wrap">
              <div class="avatar">
                <img v-if="avatarUrl" :src="avatarUrl" alt="头像">
                <span v-else class="avatar-placeholder">👤</span>
              </div>
            </div>
            <div class="profile-meta">
              <div class="profile-name-row">
                <h2 class="profile-name">{{ studentInfo.name }}</h2>
                <span class="crown-icon" title="认证">👑</span>
              </div>
              <p class="join-date">{{ studentInfo.joinDate }} 加入</p>
              <button type="button" class="link-btn" @click="addTitle">+ 添加头衔</button>
              <div class="profile-stats-row">
                <span>被关注 {{ studentInfo.followers }}</span>
                <span>总浏览量 {{ studentInfo.views }}</span>
              </div>
            </div>
            <div class="profile-actions">
              <button type="button" class="btn-outline" @click="onEditProfile">
                <span class="btn-icon">✏️</span>
                编辑
              </button>
              <button type="button" class="btn-outline" @click="onShare">
                <span class="btn-icon">↗</span>
                分享
              </button>
            </div>
          </div>
        </div>

        <!-- 主导航 -->
        <div class="nav-section">
          <h3 class="nav-title active">主页</h3>
          <router-link to="/settings" class="settings-link" title="设置">⚙️</router-link>
        </div>

        <!-- 简介卡片 -->
        <div class="intro-card">
          <div class="intro-card-header">
            <div class="intro-tabs">
              <button
                type="button"
                class="tab"
                :class="{ active: introTab === 'zh' }"
                @click="introTab = 'zh'"
              >
                中文简介
              </button>
              <button
                type="button"
                class="tab"
                :class="{ active: introTab === 'en' }"
                @click="introTab = 'en'"
              >
                英文简介
              </button>
            </div>
            <button type="button" class="btn-outline btn-edit" @click="onEditIntro">
              <span class="btn-icon">✏️</span>
              编辑
            </button>
          </div>
          <div class="intro-body">
            <template v-if="introContent[introTab]">
              <p class="intro-text">{{ introContent[introTab] }}</p>
            </template>
            <div v-else class="empty-state">
              <div class="empty-icon">📦</div>
              <p class="empty-text">
                展现您的科研风采，完善您的个人介绍<br>
                是您在科学逐梦之路上闪耀的第一步。立即行动吧！
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧栏 -->
      <div class="portrait-side">
        <!-- 研究方向 -->
        <div class="side-card">
          <h4 class="side-card-title">研究方向</h4>
          <div v-if="researchDirections.length" class="side-card-list">
            <div v-for="(item, i) in researchDirections" :key="i" class="side-card-item">
              {{ item }}
              <button class="remove-btn" @click="removeResearchDirection(i)">&times;</button>
            </div>
          </div>
          <div v-else class="empty-state small">
            <div class="empty-icon">📦</div>
            <p class="empty-text">还没有研究方向，快去添加吧~</p>
            <button type="button" class="btn-primary" @click="showAddResearch = true">
              <span>+</span> 添加研究方向
            </button>
          </div>
          <button v-if="researchDirections.length > 0" class="btn-add-more" @click="showAddResearch = true">+ 添加更多</button>
        </div>

        <!-- 教育背景 -->
        <div class="side-card">
          <h4 class="side-card-title">教育背景</h4>
          <div v-if="educationList.length" class="side-card-list">
            <div v-for="(item, i) in educationList" :key="i" class="side-card-item">
              <strong>{{ item.school }}</strong> · {{ item.degree }} · {{ item.period }}
              <button class="remove-btn" @click="removeEducation(i)">&times;</button>
            </div>
          </div>
          <div v-else class="empty-state small">
            <div class="empty-icon">📦</div>
            <p class="empty-text">还没有教育背景，快去添加吧~</p>
            <button type="button" class="btn-primary" @click="showAddEducation = true">
              <span>+</span> 添加教育背景
            </button>
          </div>
          <button v-if="educationList.length > 0" class="btn-add-more" @click="showAddEducation = true">+ 添加更多</button>
        </div>

        <!-- 工作经历 -->
        <div class="side-card">
          <h4 class="side-card-title">工作经历</h4>
          <div v-if="workExperiences.length" class="side-card-list">
            <div v-for="(item, i) in workExperiences" :key="i" class="side-card-item">
              <strong>{{ item.company }}</strong> · {{ item.role }} · {{ item.period }}
              <button class="remove-btn" @click="removeWorkExperience(i)">&times;</button>
            </div>
          </div>
          <div v-else class="empty-state small">
            <div class="empty-icon">📦</div>
            <p class="empty-text">还没有工作经历，快去添加吧~</p>
            <button type="button" class="btn-primary" @click="showAddWork = true">
              <span>+</span> 添加工作经历
            </button>
          </div>
          <button v-if="workExperiences.length > 0" class="btn-add-more" @click="showAddWork = true">+ 添加更多</button>
        </div>
      </div>
    </div>

    <!-- 编辑个人信息弹窗 -->
    <el-dialog v-model="isEditingProfile" title="编辑个人信息" width="450px">
      <el-form :model="editProfileForm" label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="editProfileForm.name" placeholder="输入用户名" />
        </el-form-item>
        <el-form-item label="头像URL">
          <el-input v-model="editProfileForm.avatarUrl" placeholder="输入头像图片URL" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="isEditingProfile = false">取消</el-button>
        <el-button type="primary" @click="saveProfile">保存</el-button>
      </template>
    </el-dialog>

    <!-- 编辑简介弹窗 -->
    <el-dialog v-model="isEditingIntro" title="编辑简介" width="500px">
      <el-form :model="editIntroForm" label-width="80px">
        <el-form-item label="中文简介">
          <el-input v-model="editIntroForm.zh" type="textarea" :rows="4" placeholder="输入中文简介" />
        </el-form-item>
        <el-form-item label="英文简介">
          <el-input v-model="editIntroForm.en" type="textarea" :rows="4" placeholder="输入英文简介" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="isEditingIntro = false">取消</el-button>
        <el-button type="primary" @click="saveIntro">保存</el-button>
      </template>
    </el-dialog>

    <!-- 添加研究方向弹窗 -->
    <el-dialog v-model="showAddResearch" title="添加研究方向" width="400px">
      <el-form>
        <el-form-item label="研究方向">
          <el-input v-model="newResearch" placeholder="输入研究方向，如：机器学习" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddResearch = false">取消</el-button>
        <el-button type="primary" @click="addResearchDirection">添加</el-button>
      </template>
    </el-dialog>

    <!-- 添加教育背景弹窗 -->
    <el-dialog v-model="showAddEducation" title="添加教育背景" width="450px">
      <el-form :model="newEducation" label-width="80px">
        <el-form-item label="学校">
          <el-input v-model="newEducation.school" placeholder="学校名称" />
        </el-form-item>
        <el-form-item label="学位">
          <el-input v-model="newEducation.degree" placeholder="如：本科、硕士" />
        </el-form-item>
        <el-form-item label="时间">
          <el-input v-model="newEducation.period" placeholder="如：2020-2024" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddEducation = false">取消</el-button>
        <el-button type="primary" @click="addEducation">添加</el-button>
      </template>
    </el-dialog>

    <!-- 添加工作经历弹窗 -->
    <el-dialog v-model="showAddWork" title="添加工作经历" width="450px">
      <el-form :model="newWork" label-width="80px">
        <el-form-item label="公司">
          <el-input v-model="newWork.company" placeholder="公司名称" />
        </el-form-item>
        <el-form-item label="职位">
          <el-input v-model="newWork.role" placeholder="如：软件工程师" />
        </el-form-item>
        <el-form-item label="时间">
          <el-input v-model="newWork.period" placeholder="如：2024-至今" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddWork = false">取消</el-button>
        <el-button type="primary" @click="addWorkExperience">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { portraitApi } from '@/api'
import { ElMessage } from 'element-plus'

const authStore = useAuthStore()

const studentInfo = ref({
  name: authStore.user?.username || '学习者',
  joinDate: '2026-03-05',
  followers: 0,
  views: 0,
  avatarUrl: null
})

const avatarUrl = computed(() => studentInfo.value.avatarUrl || null)

const introTab = ref('zh') // 'zh' | 'en'
const introContent = ref({
  zh: '',
  en: ''
})

const researchDirections = ref([])
const educationList = ref([])
const workExperiences = ref([])

// 编辑状态
const isEditingProfile = ref(false)
const isEditingIntro = ref(false)
const showAddResearch = ref(false)
const showAddEducation = ref(false)
const showAddWork = ref(false)

// 编辑表单
const editProfileForm = ref({
  name: '',
  avatarUrl: ''
})

const editIntroForm = ref({
  zh: '',
  en: ''
})

const newResearch = ref('')
const newEducation = ref({
  school: '',
  degree: '',
  period: ''
})

const newWork = ref({
  company: '',
  role: '',
  period: ''
})

// 加载学生画像数据
const loadPortrait = async () => {
  try {
    const studentId = authStore.user?.id || 'current_user'
    const res = await portraitApi.get(studentId)
    if (res.code === 200 && res.data) {
      const data = res.data
      if (data.name) studentInfo.value.name = data.name
      if (data.join_date) studentInfo.value.joinDate = data.join_date
      if (data.followers) studentInfo.value.followers = data.followers
      if (data.views) studentInfo.value.views = data.views
      if (data.avatar_url) studentInfo.value.avatarUrl = data.avatar_url
      if (data.intro) {
        introContent.value.zh = data.intro.zh || ''
        introContent.value.en = data.intro.en || ''
      }
      if (data.research_directions) {
        researchDirections.value = data.research_directions
      }
      if (data.education) {
        educationList.value = data.education
      }
      if (data.work_experience) {
        workExperiences.value = data.work_experience
      }
    }
  } catch (error) {
    console.error('加载画像失败:', error)
  }
}

// 保存个人信息编辑
const saveProfile = async () => {
  try {
    const studentId = authStore.user?.id || 'current_user'
    await portraitApi.update(studentId, {
      name: editProfileForm.value.name,
      avatar_url: editProfileForm.value.avatarUrl
    })
    studentInfo.value.name = editProfileForm.value.name
    studentInfo.value.avatarUrl = editProfileForm.value.avatarUrl
    isEditingProfile.value = false
    ElMessage.success('保存成功')
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
  }
}

// 保存简介编辑
const saveIntro = async () => {
  try {
    const studentId = authStore.user?.id || 'current_user'
    await portraitApi.update(studentId, {
      intro: editIntroForm.value
    })
    introContent.value = { ...editIntroForm.value }
    isEditingIntro.value = false
    ElMessage.success('保存成功')
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
  }
}

// 添加研究方向
const addResearchDirection = async () => {
  if (!newResearch.value.trim()) return
  researchDirections.value.push(newResearch.value)
  newResearch.value = ''
  showAddResearch.value = false

  try {
    const studentId = authStore.user?.id || 'current_user'
    await portraitApi.update(studentId, {
      research_directions: researchDirections.value
    })
    ElMessage.success('添加成功')
  } catch (error) {
    console.error('保存失败:', error)
  }
}

// 删除研究方向
const removeResearchDirection = async (index) => {
  researchDirections.value.splice(index, 1)
  try {
    const studentId = authStore.user?.id || 'current_user'
    await portraitApi.update(studentId, {
      research_directions: researchDirections.value
    })
    ElMessage.success('删除成功')
  } catch (error) {
    console.error('保存失败:', error)
  }
}

// 添加教育背景
const addEducation = async () => {
  if (!newEducation.value.school.trim()) return
  educationList.value.push({ ...newEducation.value })
  newEducation.value = { school: '', degree: '', period: '' }
  showAddEducation.value = false

  try {
    const studentId = authStore.user?.id || 'current_user'
    await portraitApi.update(studentId, {
      education: educationList.value
    })
    ElMessage.success('添加成功')
  } catch (error) {
    console.error('保存失败:', error)
  }
}

// 删除教育背景
const removeEducation = async (index) => {
  educationList.value.splice(index, 1)
  try {
    const studentId = authStore.user?.id || 'current_user'
    await portraitApi.update(studentId, {
      education: educationList.value
    })
    ElMessage.success('删除成功')
  } catch (error) {
    console.error('保存失败:', error)
  }
}

// 添加工作经历
const addWorkExperience = async () => {
  if (!newWork.value.company.trim()) return
  workExperiences.value.push({ ...newWork.value })
  newWork.value = { company: '', role: '', period: '' }
  showAddWork.value = false

  try {
    const studentId = authStore.user?.id || 'current_user'
    await portraitApi.update(studentId, {
      work_experience: workExperiences.value
    })
    ElMessage.success('添加成功')
  } catch (error) {
    console.error('保存失败:', error)
  }
}

// 删除工作经历
const removeWorkExperience = async (index) => {
  workExperiences.value.splice(index, 1)
  try {
    const studentId = authStore.user?.id || 'current_user'
    await portraitApi.update(studentId, {
      work_experience: workExperiences.value
    })
    ElMessage.success('删除成功')
  } catch (error) {
    console.error('保存失败:', error)
  }
}

// 加载优势分析
const loadStrengths = async () => {
  try {
    const studentId = authStore.user?.id || 'current_user'
    const res = await portraitApi.strengths(studentId)
    if (res.code === 200) {
      // 处理优势数据
    }
  } catch (error) {
    console.error('加载优势分析失败:', error)
  }
}

// 加载薄弱点分析
const loadWeaknesses = async () => {
  try {
    const studentId = authStore.user?.id || 'current_user'
    const res = await portraitApi.weaknesses(studentId)
    if (res.code === 200) {
      // 处理薄弱点数据
    }
  } catch (error) {
    console.error('加载薄弱点失败:', error)
  }
}

// 加载进步追踪
const loadProgress = async () => {
  try {
    const studentId = authStore.user?.id || 'current_user'
    const res = await portraitApi.progress(studentId)
    if (res.code === 200) {
      // 处理进步数据
    }
  } catch (error) {
    console.error('加载进步数据失败:', error)
  }
}

onMounted(() => {
  loadPortrait()
  loadStrengths()
  loadWeaknesses()
  loadProgress()
})

// 编辑按钮处理函数
const onEditProfile = () => {
  editProfileForm.value = {
    name: studentInfo.value.name,
    avatarUrl: studentInfo.value.avatarUrl || ''
  }
  isEditingProfile.value = true
}

const onEditIntro = () => {
  editIntroForm.value = {
    zh: introContent.value.zh,
    en: introContent.value.en
  }
  isEditingIntro.value = true
}

const onShare = () => {
  ElMessage.info('分享功能开发中')
}

const addTitle = () => {
  ElMessage.info('头衔功能开发中')
}
</script>

<style scoped>
.portrait-page {
  padding: 24px;
  min-height: calc(100vh - 64px);
  background: var(--bg-secondary);
}

.portrait-layout {
  max-width: 1100px;
  margin: 0 auto;
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.portrait-main {
  flex: 1;
  min-width: 0;
}

.portrait-side {
  width: 320px;
  flex-shrink: 0;
}

/* 个人资料卡片 */
.profile-card {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  padding: 24px;
  margin-bottom: 20px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border);
}

.profile-header {
  display: flex;
  align-items: flex-start;
  gap: 20px;
}

.avatar-wrap {
  flex-shrink: 0;
}

.avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: var(--bg-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  font-size: 36px;
}

.profile-meta {
  flex: 1;
  min-width: 0;
}

.profile-name-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.profile-name {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.crown-icon {
  font-size: 16px;
}

.join-date {
  font-size: 13px;
  color: var(--text-muted);
  margin: 0 0 8px 0;
}

.link-btn {
  background: none;
  border: none;
  color: var(--primary);
  font-size: 14px;
  cursor: pointer;
  padding: 0;
  margin-bottom: 12px;
}

.link-btn:hover {
  text-decoration: underline;
}

.profile-stats-row {
  font-size: 13px;
  color: var(--text-muted);
}

.profile-stats-row span + span {
  margin-left: 16px;
}

.profile-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.btn-outline {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  font-size: 14px;
  color: var(--text-secondary);
  cursor: pointer;
}

.btn-outline:hover {
  background: var(--bg-tertiary);
}

.btn-icon {
  font-size: 14px;
}

/* 主导航 */
.nav-section {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.nav-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  padding-bottom: 6px;
  border-bottom: 3px solid var(--primary);
}

.nav-title.active {
  color: var(--primary);
}

.settings-link {
  font-size: 18px;
  text-decoration: none;
  color: var(--text-muted);
}

.settings-link:hover {
  color: var(--primary);
}

/* 简介卡片 */
.intro-card {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border);
}

.intro-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.intro-tabs {
  display: flex;
  gap: 0;
}

.intro-tabs .tab {
  padding: 8px 20px;
  border: none;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  font-size: 14px;
  cursor: pointer;
  border-radius: var(--radius-sm);
  margin-right: 4px;
}

.intro-tabs .tab.active {
  background: var(--primary-dark);
  color: white;
}

.btn-edit {
  padding: 6px 12px;
}

.intro-body {
  min-height: 200px;
}

.intro-text {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.7;
  margin: 0;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
}

.empty-state.small {
  padding: 24px 16px;
  min-height: 140px;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.6;
}

.empty-state.small .empty-icon {
  font-size: 36px;
  margin-bottom: 12px;
}

.empty-text {
  font-size: 14px;
  color: var(--text-muted);
  line-height: 1.6;
  margin: 0 0 20px 0;
}

.empty-state.small .empty-text {
  margin-bottom: 16px;
}

/* 右侧卡片 */
.side-card {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border);
}

.side-card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 16px 0;
}

.side-card-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.side-card-item {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 20px;
  background: var(--primary);
  color: white;
  border: none;
  border-radius: var(--radius);
  font-size: 14px;
  cursor: pointer;
}

.btn-primary:hover {
  background: var(--primary-dark);
}

.remove-btn {
  background: none;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  font-size: 16px;
  margin-left: 8px;
  padding: 2px 6px;
  border-radius: 4px;
  transition: all 0.2s;
}

.remove-btn:hover {
  background: #fee2e2;
  color: #ef4444;
}

.btn-add-more {
  width: 100%;
  padding: 8px;
  margin-top: 12px;
  background: none;
  border: 1px dashed #d1d5db;
  border-radius: 8px;
  color: #6b7280;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-add-more:hover {
  border-color: #3b82f6;
  color: #3b82f6;
  background: #f0f7ff;
}

@media (max-width: 900px) {
  .portrait-layout {
    flex-direction: column;
  }

  .portrait-side {
    width: 100%;
  }
}
</style>
