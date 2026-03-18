<template>
  <div class="graph-page">
    <!-- 顶部标题栏 -->
    <div class="page-header">
      <div class="header-left">
        <h1>知识图谱</h1>
        <p>可视化知识点之间的关联关系</p>
      </div>
      <div class="header-actions">
        <button class="btn btn-secondary" @click="refreshGraph">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
          </svg>
          刷新
        </button>
        <button class="btn btn-primary" @click="showAddModal = true">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          添加节点
        </button>
      </div>
    </div>

    <div class="graph-layout">
      <!-- 左侧边栏 - 精简版 -->
      <aside class="graph-sidebar">
        <!-- 知识领域 -->
        <div class="sidebar-section">
          <h3>知识领域</h3>
          <div class="domain-list">
            <div 
              v-for="domain in domains" 
              :key="domain.name"
              class="domain-item"
              :class="{ active: selectedDomain === domain.name }"
              @click="selectedDomain = domain.name"
            >
              <span class="domain-color" :style="{ background: domain.color }"></span>
              <span class="domain-name">{{ domain.name }}</span>
              <span class="domain-count">{{ domain.count }}</span>
            </div>
          </div>
        </div>

        <!-- 搜索框 -->
        <div class="sidebar-section">
          <h3>搜索知识点</h3>
          <div class="search-box">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
            </svg>
            <input type="text" v-model="searchQuery" placeholder="搜索知识点...">
          </div>
        </div>

        <!-- 图谱统计 -->
        <div class="sidebar-section">
          <h3>图谱统计</h3>
          <div class="graph-stats">
            <div class="graph-stat">
              <span class="stat-value">{{ graphStats.nodes }}</span>
              <span class="stat-label">节点数</span>
            </div>
            <div class="graph-stat">
              <span class="stat-value">{{ graphStats.edges }}</span>
              <span class="stat-label">关系数</span>
            </div>
          </div>
        </div>
      </aside>

      <!-- 右侧主图谱区域 -->
      <main class="graph-main">
        <div class="graph-container" ref="graphContainer">
          <!-- 图谱可视化 -->
          <div class="graph-placeholder">
            <div class="network-visual">
              <div v-for="(node, i) in visualNodes" :key="i" class="visual-node" :style="node.style">
                {{ node.label }}
              </div>
              <svg class="edges-svg">
                <line v-for="(edge, i) in visualEdges" :key="i" :x1="edge.x1" :y1="edge.y1" :x2="edge.x2" :y2="edge.y2" stroke="#cbd5e1" stroke-width="2"/>
              </svg>
            </div>
          </div>

          <!-- 节点详情浮层 -->
          <div class="node-detail" v-if="selectedNode">
            <div class="detail-header">
              <h3>{{ selectedNode.name }}</h3>
              <button class="close-btn" @click="selectedNode = null">&times;</button>
            </div>
            <div class="detail-content">
              <div class="detail-item">
                <span class="label">类型</span>
                <span class="value">{{ selectedNode.type }}</span>
              </div>
              <div class="detail-item">
                <span class="label">难度</span>
                <span class="value difficulty" :class="selectedNode.difficulty">{{ selectedNode.difficultyText }}</span>
              </div>
              <div class="detail-item">
                <span class="label">相关度</span>
                <span class="value">{{ selectedNode.relevance }}%</span>
              </div>
              <div class="detail-item">
                <span class="label">描述</span>
                <p class="description">{{ selectedNode.description }}</p>
              </div>
              <div class="related-nodes">
                <span class="label">相关知识点</span>
                <div class="tags">
                  <span v-for="tag in selectedNode.related" :key="tag" class="tag">{{ tag }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>

    <!-- 添加节点弹窗 -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>添加知识点</h3>
          <button class="close-btn" @click="showAddModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>知识点名称</label>
            <input type="text" v-model="newNode.name" class="input" placeholder="输入知识点名称">
          </div>
          <div class="form-group">
            <label>所属领域</label>
            <select v-model="newNode.domain" class="input">
              <option value="python">Python</option>
              <option value="java">Java</option>
              <option value="algorithm">算法</option>
              <option value="web">Web开发</option>
            </select>
          </div>
          <div class="form-group">
            <label>难度级别</label>
            <select v-model="newNode.difficulty" class="input">
              <option value="easy">简单</option>
              <option value="medium">中等</option>
              <option value="hard">困难</option>
            </select>
          </div>
          <div class="form-group">
            <label>描述</label>
            <textarea v-model="newNode.description" class="input" rows="3" placeholder="输入知识点描述"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showAddModal = false">取消</button>
          <button class="btn btn-primary" @click="addNode">确认添加</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { knowledgeApi } from '@/api'
import { ElMessage } from 'element-plus'

const selectedDomain = ref('all')
const searchQuery = ref('')
const showAddModal = ref(false)
const selectedNode = ref(null)
const graphContainer = ref(null)

const newNode = ref({ name: '', domain: 'python', difficulty: 'medium', description: '' })

const domains = ref([
  { name: 'Python', count: 0, color: '#3b82f6' },
  { name: 'Java', count: 0, color: '#f093fb' },
  { name: '算法', count: 0, color: '#4facfe' },
  { name: '数据结构', count: 0, color: '#43e97b' },
  { name: 'Web开发', count: 0, color: '#f59e0b' }
])

const graphStats = ref({ nodes: 0, edges: 0 })

const visualNodes = ref([])

const visualEdges = ref([])

const nodeDetails = ref({})

const loadGraphs = async () => {
  try {
    const res = await knowledgeApi.graph.list()
    if (res.code === 200 && res.data) {
      const graphs = res.data.items || res.data || []
      if (graphs.length > 0) {
        const graphId = graphs[0].id || graphs[0].graph_id
        // 加载节点
        const nodesRes = await knowledgeApi.graph.nodes(graphId)
        if (nodesRes.code === 200) {
          visualNodes.value = (nodesRes.data.items || nodesRes.data || []).map((n, i) => ({
            label: n.name || n.label,
            style: { top: `${20 + (i * 10)}%`, left: `${30 + (i % 3) * 20}%`, background: domains.value[i % domains.value.length].color }
          }))
          graphStats.value.nodes = visualNodes.value.length
        }
        // 加载边
        const edgesRes = await knowledgeApi.graph.edges(graphId)
        if (edgesRes.code === 200) {
          const edges = edgesRes.data.items || edgesRes.data || []
          visualEdges.value = edges.slice(0, 10).map(e => ({
            x1: `${30 + Math.random() * 20}%`,
            y1: `${30 + Math.random() * 20}%`,
            x2: `${30 + Math.random() * 20}%`,
            y2: `${50 + Math.random() * 20}%`
          }))
          graphStats.value.edges = edges.length
        }
      }
    }
  } catch (error) {
    console.error('加载知识图谱失败:', error)
    // 使用默认数据
    visualNodes.value = [
      { label: 'Python', style: { top: '20%', left: '50%', background: '#3b82f6' } },
      { label: '变量', style: { top: '35%', left: '30%', background: '#60a5fa' } },
      { label: '函数', style: { top: '35%', left: '70%', background: '#60a5fa' } }
    ]
  }
}

const queryGraph = async () => {
  try {
    const res = await knowledgeApi.graph.query({ query: searchQuery.value })
    if (res.code === 200 && res.data) {
      ElMessage.success('图谱查询完成')
    }
  } catch (error) {
    console.error('图谱查询失败:', error)
  }
}

const refreshGraph = () => {
  loadGraphs()
}

const addNode = async () => {
  try {
    await knowledgeApi.graph.create(newNode.value)
    ElMessage.success('节点添加成功')
    showAddModal.value = false
    loadGraphs()
  } catch (error) {
    ElMessage.error('添加失败')
  }
}

onMounted(() => {
  loadGraphs()
})
</script>

<style scoped>
.graph-page {
  padding: 20px 24px;
  min-height: calc(100vh - 64px);
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left h1 { font-size: 24px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px; }
.header-left p { font-size: 14px; color: var(--text-muted); margin: 0; }

.header-actions { display: flex; gap: 12px; }

.btn { display: flex; align-items: center; gap: 8px; padding: 10px 18px; border-radius: var(--radius-sm); font-size: 14px; font-weight: 500; cursor: pointer; border: none; transition: var(--transition); }
.btn-primary { background: var(--primary); color: white; }
.btn-primary:hover { background: var(--primary-dark); }
.btn-secondary { background: var(--bg-primary); color: var(--text-secondary); border: 1px solid var(--border); }
.btn-secondary:hover { background: var(--bg-tertiary); }

/* 左右布局容器 */
.graph-layout {
  flex: 1;
  display: flex;
  gap: 20px;
  min-height: 0;
}

/* 左侧边栏 */
.graph-sidebar {
  width: 260px;
  flex-shrink: 0;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  overflow-y: auto;
}

.sidebar-section h3 {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 14px;
}

.domain-list { display: flex; flex-direction: column; gap: 6px; }

.domain-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: var(--transition);
}

.domain-item:hover { background: var(--bg-tertiary); }
.domain-item.active { background: rgba(59, 130, 246, 0.1); }

.domain-color { width: 10px; height: 10px; border-radius: 3px; flex-shrink: 0; }
.domain-name { flex: 1; font-size: 14px; color: var(--text-primary); }
.domain-count { font-size: 12px; color: var(--text-muted); }

.search-box {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg-tertiary);
}

.search-box svg { color: var(--text-muted); flex-shrink: 0; }
.search-box input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 14px;
  color: var(--text-primary);
  outline: none;
}

.graph-stats { display: flex; gap: 20px; }
.graph-stat { text-align: center; flex: 1; padding: 12px; background: var(--bg-tertiary); border-radius: var(--radius-sm); }
.stat-value { display: block; font-size: 22px; font-weight: 700; color: var(--primary); }
.stat-label { font-size: 12px; color: var(--text-muted); }

/* 右侧主图谱 */
.graph-main {
  flex: 1;
  min-width: 0;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
  overflow: hidden;
  position: relative;
}

.graph-container {
  width: 100%;
  height: 100%;
  position: relative;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
}

.graph-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.network-visual {
  position: relative;
  width: 100%;
  height: 100%;
  max-width: 800px;
  max-height: 600px;
}

.visual-node {
  position: absolute;
  padding: 10px 20px;
  border-radius: 20px;
  color: white;
  font-size: 13px;
  font-weight: 500;
  transform: translate(-50%, -50%);
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.visual-node:hover {
  transform: translate(-50%, -50%) scale(1.1);
  box-shadow: 0 6px 20px rgba(0,0,0,0.2);
}

.edges-svg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

/* 节点详情浮层 */
.node-detail {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 280px;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
  z-index: 10;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-light);
}

.detail-header h3 { font-size: 16px; font-weight: 600; color: var(--text-primary); margin: 0; }
.close-btn {
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  font-size: 18px;
  cursor: pointer;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
}

.detail-content { padding: 16px 20px; }

.detail-item { margin-bottom: 14px; }
.detail-item .label { display: block; font-size: 12px; color: var(--text-muted); margin-bottom: 4px; }
.detail-item .value { font-size: 14px; font-weight: 500; color: var(--text-primary); }
.difficulty.easy { color: var(--success); }
.difficulty.medium { color: var(--warning); }
.difficulty.hard { color: var(--error); }
.description { font-size: 13px; color: var(--text-secondary); line-height: 1.6; margin: 4px 0 0 0; }

.related-nodes .label { display: block; font-size: 12px; color: var(--text-muted); margin-bottom: 8px; }
.tags { display: flex; flex-wrap: wrap; gap: 6px; }
.tag { padding: 4px 10px; background: var(--bg-tertiary); border-radius: 12px; font-size: 12px; color: var(--text-secondary); }

/* 弹窗 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  width: 90%;
  max-width: 440px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 20px;
  border-bottom: 1px solid var(--border-light);
}

.modal-header h3 { font-size: 16px; font-weight: 600; margin: 0; }
.modal-body { padding: 20px; }
.modal-footer { display: flex; justify-content: flex-end; gap: 10px; padding: 14px 20px; border-top: 1px solid var(--border-light); }

.form-group { margin-bottom: 14px; }
.form-group label { display: block; font-size: 14px; font-weight: 500; margin-bottom: 6px; color: var(--text-primary); }
.input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 14px;
  color: var(--text-primary);
  background: var(--bg-primary);
}

.input:focus { outline: none; border-color: var(--primary); }

@media (max-width: 900px) {
  .graph-layout { flex-direction: column; }
  .graph-sidebar { width: 100%; flex-direction: row; flex-wrap: wrap; }
  .sidebar-section { flex: 1; min-width: 200px; }
}
</style>
