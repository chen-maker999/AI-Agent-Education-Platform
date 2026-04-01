<template>
  <div class="ac-page">
    <div class="ac-window">
      <header class="ac-head">
        <div class="ac-head__left">
          <div class="ac-dots" aria-hidden="true">
            <span class="ac-dot ac-dot--r"></span>
            <span class="ac-dot ac-dot--y"></span>
            <span class="ac-dot ac-dot--g"></span>
          </div>
          <div class="ac-head__titles">
            <h1 class="ac-head__title">Agent 配置中心</h1>
            <p class="ac-head__hint">{{ modeHint }}</p>
          </div>
        </div>
        <div class="mode-pill" role="group" aria-label="配置模式">
          <div class="mode-pill__thumb" :class="{ 'is-right': configMode === 'full' }" aria-hidden="true" />
          <button
            type="button"
            class="mode-pill__seg"
            :class="{ active: configMode === 'simple' }"
            @click="configMode = 'simple'"
          >
            <svg
              v-if="configMode === 'simple'"
              class="mode-pill__icon"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.75"
              stroke-linejoin="round"
              aria-hidden="true"
            >
              <path d="M12 2 2 7l10 5 10-5L12 2zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
            <span v-else class="mode-pill__label">简易</span>
          </button>
          <button
            type="button"
            class="mode-pill__seg"
            :class="{ active: configMode === 'full' }"
            @click="configMode = 'full'"
          >
            <span
              v-if="configMode === 'simple'"
              class="mode-pill__label mode-pill__label--full"
            >完整</span>
            <svg
              v-else
              class="mode-pill__icon"
              viewBox="0 0 24 24"
              fill="none"
              aria-hidden="true"
            >
              <rect x="5" y="7" width="14" height="10" rx="1.5" stroke="currentColor" stroke-width="2" />
              <circle cx="10" cy="12" r="1.35" fill="currentColor" />
              <circle cx="14" cy="12" r="1.35" fill="currentColor" />
            </svg>
          </button>
        </div>
      </header>

      <div class="ac-split">
        <aside class="ac-rail" aria-label="章节导航">
          <div class="ac-rail__title">章节</div>
          <nav class="ac-rail__nav">
            <button
              v-for="item in navItems"
              :key="item.id"
              type="button"
              class="ac-rail__link"
              :class="{ active: activeSection === item.id }"
              @click="goSection(item.id)"
            >
              <span class="ac-rail__idx">{{ item.idx }}</span>
              <span class="ac-rail__text">{{ item.label }}</span>
            </button>
          </nav>
        </aside>
        <main ref="mainScrollEl" class="ac-main">
          <div class="config-scroll">

      <!-- ═══ 简易模式 ═══ -->
      <div v-if="configMode === 'simple'" class="config-panel">
        <div id="ac-s-role" class="panel-section">
          <h3 class="panel-title">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="12" cy="8" r="4"/>
              <path d="M4 20c0-4 4-6 8-6s8 2 8 6"/>
            </svg>
            Agent 角色
          </h3>
          <div class="config-item">
            <label>身份设定</label>
            <div class="role-grid">
            <div
              v-for="role in simpleRoles"
              :key="role.value"
              class="role-card"
              :class="{ active: config.simple.role === role.value }"
              @click="config.simple.role = role.value"
            >
              <div class="role-icon-wrap">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path v-if="role.value === 'tutor'" d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2zM22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
                  <path v-else-if="role.value === 'helper'" d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 0 1-3.46 0"/>
                  <path v-else-if="role.value === 'critic'" d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7zM12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6z"/>
                  <path v-else d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zM12 8v4M12 16h.01"/>
                </svg>
              </div>
              <span class="role-label">{{ role.label }}</span>
              <span class="role-desc">{{ role.desc }}</span>
            </div>
            </div>
          </div>
          <div class="config-item">
            <label>性格倾向</label>
            <div class="slider-row">
              <span class="slider-label">严谨</span>
              <input type="range" min="0" max="100" v-model="config.simple.personality">
              <span class="slider-label">活泼</span>
            </div>
          </div>
        </div>

        <div id="ac-s-style" class="panel-section">
          <h3 class="panel-title">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
            </svg>
            响应风格
          </h3>
          <div class="config-item">
            <label>详细程度</label>
            <div class="button-group">
              <button :class="{ active: config.simple.verbosity === 'brief' }" @click="config.simple.verbosity = 'brief'">简洁</button>
              <button :class="{ active: config.simple.verbosity === 'normal' }" @click="config.simple.verbosity = 'normal'">适中</button>
              <button :class="{ active: config.simple.verbosity === 'detailed' }" @click="config.simple.verbosity = 'detailed'">详细</button>
            </div>
          </div>
          <div class="config-item">
            <label>创造力</label>
            <div class="slider-row">
              <span class="slider-label">精确</span>
              <input type="range" min="0" max="100" v-model="config.simple.temperature">
              <span class="slider-label">创造</span>
            </div>
            <span class="hint">数值越高回答越有创意，越低越确定</span>
          </div>
        </div>

        <div id="ac-s-safety" class="panel-section">
          <h3 class="panel-title">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
            安全等级
          </h3>
          <div class="config-item">
            <label>内容过滤</label>
            <div class="safety-options">
              <label class="safety-option" :class="{ active: config.simple.safetyLevel === 'strict' }">
                <input type="radio" v-model="config.simple.safetyLevel" value="strict">
                <div class="safety-icon-wrap">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <rect x="3" y="11" width="18" height="11" rx="2"/>
                    <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                  </svg>
                </div>
                <span>严格</span>
              </label>
              <label class="safety-option" :class="{ active: config.simple.safetyLevel === 'balanced' }">
                <input type="radio" v-model="config.simple.safetyLevel" value="balanced">
                <div class="safety-icon-wrap">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M12 3v18M3 12h18M5.6 5.6l12.8 12.8M5.6 18.4L18.4 5.6"/>
                  </svg>
                </div>
                <span>平衡</span>
              </label>
              <label class="safety-option" :class="{ active: config.simple.safetyLevel === 'open' }">
                <input type="radio" v-model="config.simple.safetyLevel" value="open">
                <div class="safety-icon-wrap">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <rect x="3" y="11" width="18" height="11" rx="2"/>
                    <path d="M7 11V7a5 5 0 0 1 9.9-1"/>
                  </svg>
                </div>
                <span>开放</span>
              </label>
            </div>
          </div>
        </div>

        <div class="action-bar">
          <button class="btn btn--secondary" @click="resetSimple">恢复默认</button>
          <button class="btn btn--primary" @click="saveSimple">保存配置</button>
        </div>
      </div>

      <!-- ═══ 完整模式 ═══ -->
      <div v-else class="config-panel">

        <!-- 基础配置 -->
        <div id="ac-f-base" class="panel-section">
          <h3 class="panel-title">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 16v-4M12 8h.01"/>
            </svg>
            基础设置
          </h3>
          <div class="config-item full">
            <label>系统提示词</label>
            <textarea
              v-model="config.full.systemPrompt"
              placeholder="定义 Agent 的角色、行为规范和特殊能力..."
              rows="5"
            ></textarea>
            <div class="char-count">{{ config.full.systemPrompt.length }} / 4000</div>
          </div>
          <div class="config-row">
            <div class="config-item">
              <MacSelect v-model="config.full.role" label="Agent 角色" :options="fullRoleOptions" />
            </div>
            <div class="config-item">
              <MacSelect v-model="config.full.personality" label="性格倾向" :options="fullPersonalityOptions" />
            </div>
          </div>
        </div>

        <!-- 模型配置 -->
        <div id="ac-f-model" class="panel-section">
          <h3 class="panel-title">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <rect x="2" y="3" width="20" height="14" rx="2"/>
              <path d="M8 21h8M12 17v4"/>
            </svg>
            模型参数
          </h3>
          <div class="config-item">
            <MacSelect v-model="config.full.model" label="模型选择" :options="modelOptions" />
          </div>
          <div class="model-params">
            <div class="param-item">
              <label class="param-label">
                <span>Temperature</span>
                <span class="param-hint">
                  ?
                  <span class="param-hint-tooltip">
                    <span class="param-hint-tooltip-content">控制输出的随机性。较高的值使输出更随机，较低的值使输出更确定</span>
                  </span>
                </span>
              </label>
              <div class="slider-row">
                <input type="range" min="0" max="100" v-model="config.full.temperature">
                <span class="value">{{ config.full.temperature / 100 }}</span>
              </div>
            </div>
            <div class="param-item">
              <label class="param-label">
                <span>Top P</span>
                <span class="param-hint">
                  ?
                  <span class="param-hint-tooltip">
                    <span class="param-hint-tooltip-content">核采样参数。控制模型从概率最高的词中采样的比例，较低的值只考虑高概率词</span>
                  </span>
                </span>
              </label>
              <div class="slider-row">
                <input type="range" min="0" max="100" v-model="config.full.topP">
                <span class="value">{{ config.full.topP / 100 }}</span>
              </div>
            </div>
            <div class="param-item">
              <label class="param-label">
                <span>Max Tokens</span>
                <span class="param-hint">
                  ?
                  <span class="param-hint-tooltip">
                    <span class="param-hint-tooltip-content">生成内容的最大 token 数量上限</span>
                  </span>
                </span>
              </label>
              <div class="input-with-unit param-input">
                <input type="number" v-model="config.full.maxTokens" min="1" max="32000">
                <span>tokens</span>
              </div>
            </div>
            <div class="param-item">
              <label class="param-label">
                <span>Frequency Penalty</span>
                <span class="param-hint">
                  ?
                  <span class="param-hint-tooltip">
                    <span class="param-hint-tooltip-content">减少重复 token 的使用。正值会惩罚已出现过的词，使其不太可能再次出现</span>
                  </span>
                </span>
              </label>
              <div class="slider-row">
                <input type="range" min="-200" max="200" v-model="config.full.frequencyPenalty">
                <span class="value">{{ config.full.frequencyPenalty / 100 }}</span>
              </div>
            </div>
            <div class="param-item">
              <label class="param-label">
                <span>Presence Penalty</span>
                <span class="param-hint">
                  ?
                  <span class="param-hint-tooltip">
                    <span class="param-hint-tooltip-content">鼓励模型讨论新话题。正值会增加生成新 token 的可能性</span>
                  </span>
                </span>
              </label>
              <div class="slider-row">
                <input type="range" min="-200" max="200" v-model="config.full.presencePenalty">
                <span class="value">{{ config.full.presencePenalty / 100 }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- RAG 配置 -->
        <div id="ac-f-rag" class="panel-section">
          <h3 class="panel-title">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
            </svg>
            RAG 检索增强
          </h3>
          <div class="config-item">
            <label class="toggle-label">
              启用知识库检索
              <label class="toggle">
                <input type="checkbox" v-model="config.full.enableRag">
                <span class="toggle__slider"></span>
              </label>
            </label>
            <span class="hint">开启后 Agent 将从知识库中检索相关信息</span>
          </div>
          <div v-if="config.full.enableRag" class="rag-options">
            <div class="config-row">
              <div class="config-item">
                <MacSelect v-model="config.full.ragMode" label="检索模式" :options="ragModeOptions" />
              </div>
              <div class="config-item">
                <label>返回数量</label>
                <div class="input-with-unit">
                  <input type="number" v-model="config.full.topK" min="1" max="20">
                  <span>条</span>
                </div>
              </div>
            </div>
            <div class="config-item">
              <label>相似度阈值</label>
              <div class="slider-row">
                <input type="range" min="0" max="100" v-model="config.full.similarityThreshold">
                <span class="value">{{ config.full.similarityThreshold }}%</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 工具权限 -->
        <div id="ac-f-tools" class="panel-section">
          <h3 class="panel-title">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
            </svg>
            工具权限
          </h3>
          <div class="tools-list">
            <div
              v-for="tool in tools"
              :key="tool.id"
              class="tool-row"
              :class="{ active: config.full.tools.includes(tool.id) }"
            >
              <div class="tool-info">
                <div class="tool-icon-wrap">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path v-if="tool.id === 'knowledge_search'" d="M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16zM21 21l-4.35-4.35"/>
                    <path v-else-if="tool.id === 'web_search'" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                    <path v-else-if="tool.id === 'download_to_knowledge'" d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/>
                    <path v-else-if="tool.id === 'reading'" d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6"/>
                    <path v-else-if="tool.id === 'editing'" d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zM2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
                    <path v-else d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                  </svg>
                </div>
                <div class="tool-text">
                  <span class="tool-name">{{ tool.name }}</span>
                  <span class="tool-desc">{{ tool.desc }}</span>
                </div>
              </div>
              <label class="toggle">
                <input type="checkbox" :value="tool.id" v-model="config.full.tools">
                <span class="toggle__slider"></span>
              </label>
            </div>
          </div>
        </div>

        <!-- 安全设置 -->
        <div id="ac-f-security" class="panel-section">
          <h3 class="panel-title">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
            安全与边界
          </h3>
          <div class="config-item">
            <label>内容过滤强度</label>
            <div class="safety-slider">
              <span>宽松</span>
              <input type="range" min="0" max="100" v-model="config.full.safetyLevel">
              <span>严格</span>
            </div>
          </div>
          <div class="config-item">
            <label>允许访问的域名</label>
            <textarea
              v-model="config.full.allowedDomains"
              placeholder="每行一个域名，例如: example.com"
              rows="3"
            ></textarea>
          </div>
          <div class="config-item">
            <label class="toggle-label">
              允许生成代码并执行
              <label class="toggle">
                <input type="checkbox" v-model="config.full.allowCodeExecution">
                <span class="toggle__slider"></span>
              </label>
            </label>
          </div>
          <div class="config-item">
            <label class="toggle-label">
              允许访问外部链接
              <label class="toggle">
                <input type="checkbox" v-model="config.full.allowExternalLinks">
                <span class="toggle__slider"></span>
              </label>
            </label>
          </div>
        </div>

        <!-- 快捷操作 -->
        <div id="ac-f-presets" class="panel-section">
          <h3 class="panel-title">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
            </svg>
            预设配置
          </h3>
          <div class="presets-grid">
            <div
              v-for="preset in presets"
              :key="preset.id"
              class="preset-card"
              :class="{ active: activePreset === preset.id }"
              @click="applyPreset(preset)"
            >
              <div class="preset-icon-wrap">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <circle v-if="preset.id === 'default'" cx="12" cy="12" r="3"/>
                  <path v-if="preset.id === 'default'" d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
                  <path v-else-if="preset.id === 'academic'" d="M22 10v6M2 10l10-5 10 5-10 5zM6 12v5c3 3 9 3 12 0v-5"/>
                  <path v-else-if="preset.id === 'creative'" d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                  <path v-else d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10zM8 14s1.5 2 4 2 4-2 4-2M9 9h.01M15 9h.01"/>
                </svg>
              </div>
              <span class="preset-name">{{ preset.name }}</span>
              <span class="preset-desc">{{ preset.desc }}</span>
            </div>
          </div>
        </div>

        <div class="action-bar">
          <button class="btn btn--secondary" @click="resetFull">恢复默认</button>
          <button class="btn btn--primary" @click="saveFull">保存配置</button>
        </div>
      </div>
          </div>
        </main>
      </div>
    </div>

    <!-- 通知提示 -->
    <transition name="toast">
      <div v-if="showToast" class="toast" :class="toastType">
        {{ toastMessage }}
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import MacSelect from '@/components/ui/MacSelect.vue'

const fullRoleOptions = [
  { value: 'tutor', label: '课程导师' },
  { value: 'helper', label: '学习助手' },
  { value: 'critic', label: '批评者' },
  { value: 'explainer', label: '解释者' },
  { value: 'custom', label: '自定义' }
]

const fullPersonalityOptions = [
  { value: 'formal', label: '严谨正式' },
  { value: 'balanced', label: '平衡适中' },
  { value: 'casual', label: '轻松活泼' }
]

const modelOptions = [
  { value: 'kimi-k2.5', label: 'kimi-k2.5', desc: 'Kimi 迄今最智能的模型，在 Agent、代码、视觉理解及一系列通用智能任务上取得开源 SoTA 表现。同时 Kimi K2.5 也是 Kimi 迄今最全能的模型，原生的多模态架构设计，同时支持视觉与文本输入、思考与非思考模式、对话与 Agent 任务。上下文 256k' },
  { value: 'kimi-k2-0905-preview', label: 'kimi-k2-0905-preview', desc: '上下文长度 256k，在 0711 版本基础上增强了 Agentic Coding 能力、前端代码美观度和实用性、以及上下文理解能力' },
  { value: 'kimi-k2-0711-preview', label: 'kimi-k2-0711-preview', desc: '上下文长度 128k，MoE 架构基础模型，总参数 1T，激活参数 32B。具备超强代码和 Agent 能力' },
  { value: 'kimi-k2-turbo-preview', label: 'kimi-k2-turbo-preview', desc: 'K2 的高速版本，对标最新版本(0905)。输出速度提升至每秒 60-100 tokens，上下文长度 256k' },
  { value: 'kimi-k2-thinking', label: 'kimi-k2-thinking', desc: 'K2 长思考模型，支持 256k 上下文，支持多步工具调用与思考，擅长解决更复杂的问题' },
  { value: 'kimi-k2-thinking-turbo', label: 'kimi-k2-thinking-turbo', desc: 'K2 长思考模型的高速版本，支持 256k 上下文，擅长深度推理，输出速度提升至每秒 60-100 tokens' },
  { value: 'moonshot-v1-8k', label: 'moonshot-v1-8k', desc: '适用于生成短文本，上下文长度 8k' },
  { value: 'moonshot-v1-32k', label: 'moonshot-v1-32k', desc: '适用于生成长文本，上下文长度 32k' },
  { value: 'moonshot-v1-128k', label: 'moonshot-v1-128k', desc: '适用于生成超长文本，上下文长度 128k' },
  { value: 'moonshot-v1-8k-vision-preview', label: 'moonshot-v1-8k-vision-preview', desc: 'Vision 视觉模型，理解图片内容并输出文本，上下文长度 8k' },
  { value: 'moonshot-v1-32k-vision-preview', label: 'moonshot-v1-32k-vision-preview', desc: 'Vision 视觉模型，理解图片内容并输出文本，上下文长度 32k' },
  { value: 'moonshot-v1-128k-vision-preview', label: 'moonshot-v1-128k-vision-preview', desc: 'Vision 视觉模型，理解图片内容并输出文本，上下文长度 128k' }
]


const ragModeOptions = [
  { value: 'semantic', label: '语义相似度' },
  { value: 'keyword', label: '关键词匹配' },
  { value: 'hybrid', label: '混合模式' }
]

// 模式
const configMode = ref('simple')
const mainScrollEl = ref(null)
const activeSection = ref('ac-s-role')

const modeHint = computed(() =>
  configMode.value === 'simple'
    ? '快速配置，适合大多数场景'
    : '完整配置，支持高级自定义'
)

const navItems = computed(() => {
  if (configMode.value === 'simple') {
    return [
      { id: 'ac-s-role', idx: '01', label: 'Agent 角色' },
      { id: 'ac-s-style', idx: '02', label: '响应风格' },
      { id: 'ac-s-safety', idx: '03', label: '安全等级' }
    ]
  }
  return [
    { id: 'ac-f-base', idx: '01', label: '基础设置' },
    { id: 'ac-f-model', idx: '02', label: '模型参数' },
    { id: 'ac-f-rag', idx: '03', label: 'RAG 检索' },
    { id: 'ac-f-tools', idx: '04', label: '工具权限' },
    { id: 'ac-f-security', idx: '05', label: '安全边界' },
    { id: 'ac-f-presets', idx: '06', label: '预设配置' }
  ]
})

function goSection(id) {
  activeSection.value = id
  const root = mainScrollEl.value
  const el = root?.querySelector(`#${id}`) ?? (typeof document !== 'undefined' ? document.getElementById(id) : null)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

watch(configMode, (m) => {
  activeSection.value = m === 'simple' ? 'ac-s-role' : 'ac-f-base'
  nextTick(() => goSection(activeSection.value))
})

// 简易模式角色
const simpleRoles = [
  { value: 'tutor', label: '课程导师', desc: '专注知识讲解与答疑' },
  { value: 'helper', label: '学习助手', desc: '提供即时帮助与提示' },
  { value: 'critic', label: '批评者', desc: '指出错误并引导反思' },
  { value: 'explainer', label: '解释者', desc: '深入浅出剖析概念' }
]

// 完整模式工具（与后端 registry.py 中的 TOOL_DEFINITIONS 对应）
// 注意：reading 和 editing 工具只允许访问用户在对话中上传的文件，不允许访问工作区或项目文件
const tools = [
  { id: 'knowledge_search', name: '知识库检索', desc: '搜索知识库中的相关资料，当询问需要查找资料、解释概念时使用' },
  { id: 'web_search', name: '联网搜索', desc: '搜索和用户任务相关的网页内容，获取最新信息' },
  { id: 'download_to_knowledge', name: '下载资料', desc: '从网上下载PDF、网页并保存到知识库' },
  { id: 'reading', name: '读取上传文件', desc: '读取用户在对话中上传的文件内容' },
  { id: 'editing', name: '编辑上传文件', desc: '修改用户在对话中上传的文件内容' },
  { id: 'terminal', name: '终端命令', desc: '执行终端命令，如运行代码、安装依赖等' },
  { id: 'preview', name: '结果预览', desc: '生成HTML、图表等可视化结果的预览' }
]

// 预设配置
const presets = [
  { id: 'default', name: '默认配置', desc: '开箱即用的标准配置' },
  { id: 'academic', name: '学术模式', desc: '严谨学术风格回答' },
  { id: 'creative', name: '创意模式', desc: '开放创意的发散思维' },
  { id: 'beginner', name: '入门模式', desc: '适合初学者的简单解释' }
]
const activePreset = ref('default')

// 配置数据
const config = ref({
  simple: {
    role: 'tutor',
    personality: 50,
    verbosity: 'normal',
    temperature: 30,
    safetyLevel: 'balanced'
  },
  full: {
    systemPrompt: '你是一个教育 AI 助手，专注于帮助学生理解和掌握知识。你应该友好、耐心地回答问题，并根据学生的水平调整解释的深度。',
    role: 'tutor',
    personality: 'balanced',
    model: 'kimi-k2.5',
    enableRag: true,
    ragMode: 'hybrid',
    topK: 5,
    similarityThreshold: 70,
    tools: ['search', 'calculator'],
    safetyLevel: 50,
    allowedDomains: '',
    allowCodeExecution: false,
    allowExternalLinks: true,
    temperature: 70,
    topP: 95,
    maxTokens: 4096,
    frequencyPenalty: 0,
    presencePenalty: 0
  }
})

// 应用预设
function applyPreset(preset) {
  activePreset.value = preset.id
  if (preset.id === 'default') {
    config.value.full.temperature = 30
    config.value.full.systemPrompt = '你是一个教育 AI 助手，专注于帮助学生理解和掌握知识。'
    config.value.full.verbosity = 'normal'
  } else if (preset.id === 'academic') {
    config.value.full.temperature = 20
    config.value.full.systemPrompt = '你是一个严谨的学术导师，强调逻辑严密、引用权威来源、提供深度分析。'
    config.value.full.verbosity = 'detailed'
  } else if (preset.id === 'creative') {
    config.value.full.temperature = 80
    config.value.full.systemPrompt = '你是一个富有创意和想象力的学习伙伴，鼓励发散思维，提供多样化的解决方案。'
    config.value.full.verbosity = 'normal'
  } else if (preset.id === 'beginner') {
    config.value.full.temperature = 25
    config.value.full.systemPrompt = '你是一个耐心的启蒙老师，用简单生动的语言解释复杂概念，多用比喻和实例。'
    config.value.full.verbosity = 'detailed'
  }
  showToastMessage('已应用预设配置', 'success')
}

// 重置和保存
function resetSimple() {
  config.value.simple = {
    role: 'tutor',
    personality: 50,
    verbosity: 'normal',
    temperature: 30,
    safetyLevel: 'balanced'
  }
  // 同时同步到完整配置
  config.value.full = mapSimpleToFull(config.value.simple)
  showToastMessage('已恢复默认配置', 'info')
}

// 角色系统提示词映射
const roleSystemPrompts = {
  tutor: '你是一个教育 AI 助手，专注于帮助学生理解和掌握知识。你应该友好、耐心地回答问题，并根据学生的水平调整解释的深度。',
  helper: '你是一个乐于助人的学习伙伴，随时准备为用户提供即时帮助和提示。当你看到用户遇到困难时，可以适当给予引导性提示，而不是直接给出完整答案，鼓励用户自己思考和探索。',
  critic: '你是一个严谨的批评者，你的职责是指出用户的错误并引导深度反思。请用建设性的方式提出质疑，鼓励用户重新审视自己的理解和答案。',
  explainer: '你是一个擅长深入浅出解释概念的教育者。无论多么复杂的概念，你都能用简单生动的语言、恰当的比喻和实际例子来阐述。'
}

// 性格倾向影响系数（0-100 严谨到活泼）
function getPersonalityModifier(personality) {
  // 严谨（0）→ 正式的语气，更精确的回答
  // 活泼（100）→ 轻松的语气，更创造性的回答
  return personality / 100
}

// 详细程度影响最大 token
const verbosityTokens = {
  brief: 1024,
  normal: 4096,
  detailed: 8192
}

// 安全等级映射
const safetyLevelMapping = {
  strict: 80,
  balanced: 50,
  open: 20
}

// 将简单模式配置映射到完整模式
function mapSimpleToFull(simpleConfig) {
  const personalityMod = getPersonalityModifier(simpleConfig.personality)

  // 根据性格倾向调整 temperature（基础值 + 偏移）
  // 严谨（0）→ temperature 偏低（精确）
  // 活泼（100）→ temperature 偏高（创造）
  const baseTemp = 30
  const tempRange = 50 // 30-80
  const mappedTemperature = Math.round(baseTemp + personalityMod * tempRange)

  // 详细程度影响其他参数
  const mappedMaxTokens = verbosityTokens[simpleConfig.verbosity] || 4096

  return {
    systemPrompt: roleSystemPrompts[simpleConfig.role] || roleSystemPrompts.tutor,
    role: simpleConfig.role,
    personality: personalityMod < 0.4 ? 'formal' : personalityMod > 0.6 ? 'casual' : 'balanced',
    model: 'kimi-k2.5',
    enableRag: true,
    ragMode: 'hybrid',
    topK: simpleConfig.verbosity === 'detailed' ? 8 : simpleConfig.verbosity === 'brief' ? 3 : 5,
    similarityThreshold: 70,
    tools: ['knowledge_search', 'web_search'],
    safetyLevel: safetyLevelMapping[simpleConfig.safetyLevel] || 50,
    allowedDomains: '',
    allowCodeExecution: false,
    allowExternalLinks: true,
    temperature: mappedTemperature,
    topP: 95,
    maxTokens: mappedMaxTokens,
    frequencyPenalty: 0,
    presencePenalty: 0
  }
}

function saveSimple() {
  localStorage.setItem('agent-config-simple', JSON.stringify(config.value.simple))
  // 同时映射到完整模式配置并保存
  config.value.full = mapSimpleToFull(config.value.simple)
  localStorage.setItem('agent-config-full', JSON.stringify(config.value.full))
  showToastMessage('简易配置已保存，已同步到完整参数', 'success')
}

function resetFull() {
  config.value.full = {
    systemPrompt: '你是一个教育 AI 助手，专注于帮助学生理解和掌握知识。你应该友好、耐心地回答问题，并根据学生的水平调整解释的深度。',
    role: 'tutor',
    personality: 'balanced',
    model: 'kimi-k2.5',
    enableRag: true,
    ragMode: 'hybrid',
    topK: 5,
    similarityThreshold: 70,
    tools: ['search', 'calculator'],
    safetyLevel: 50,
    allowedDomains: '',
    allowCodeExecution: false,
    allowExternalLinks: true,
    temperature: 70,
    topP: 95,
    maxTokens: 4096,
    frequencyPenalty: 0,
    presencePenalty: 0
  }
  activePreset.value = 'default'
  showToastMessage('已恢复默认配置', 'info')
}

function saveFull() {
  localStorage.setItem('agent-config-full', JSON.stringify(config.value.full))
  showToastMessage('完整配置已保存', 'success')
}

// Toast 提示
const showToast = ref(false)
const toastMessage = ref('')
const toastType = ref('success')

function showToastMessage(message, type = 'success') {
  toastMessage.value = message
  toastType.value = type
  showToast.value = true
  setTimeout(() => {
    showToast.value = false
  }, 3000)
}

// 加载保存的配置
function loadConfig() {
  const savedSimple = localStorage.getItem('agent-config-simple')
  const savedFull = localStorage.getItem('agent-config-full')
  if (savedSimple) {
    config.value.simple = JSON.parse(savedSimple)
    // 如果没有完整配置或简单配置更新过，则同步
    if (!savedFull) {
      config.value.full = mapSimpleToFull(config.value.simple)
    }
  }
  if (savedFull) {
    config.value.full = JSON.parse(savedFull)
  }
}

loadConfig()
</script>

<style scoped>
/* 页面壳：与知识图谱「窗口卡」区分 — 浅紫灰衬底 + 单卡片主区 */
.ac-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  background: linear-gradient(165deg, #eef0f8 0%, #e8eaf2 45%, #f2f0f7 100%);
  overflow: hidden;
}

.ac-window {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  margin: 12px 16px 16px;
  background: #fafafc;
  border-radius: 14px;
  border: 1px solid rgba(76, 81, 191, 0.12);
  box-shadow:
    0 18px 48px rgba(45, 42, 80, 0.08),
    0 0 0 1px rgba(255, 255, 255, 0.6) inset;
  overflow: hidden;
}

/* 顶栏：标题 + 深色胶囊模式切换（同一块区域内） */
.ac-head {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 18px 14px;
  background: linear-gradient(180deg, #ffffff 0%, #f6f6fa 100%);
  border-bottom: 1px solid rgba(76, 81, 191, 0.1);
}

.ac-head__left {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.ac-dots {
  display: flex;
  gap: 7px;
  flex-shrink: 0;
}

.ac-dot {
  width: 11px;
  height: 11px;
  border-radius: 50%;
}

.ac-dot--r { background: #ff5f57; }
.ac-dot--y { background: #febc2e; }
.ac-dot--g { background: #28c840; }

.ac-head__titles {
  min-width: 0;
}

.ac-head__title {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: #1d1d1f;
}

.ac-head__hint {
  margin: 4px 0 0;
  font-size: 12px;
  color: #63637b;
  line-height: 1.35;
}

/* 分段胶囊：灰色轨道 + 滑块 + 完整模式渐变文字 */
.mode-pill {
  position: relative;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px;
  width: min(220px, 42vw);
  flex-shrink: 0;
  padding: 4px;
  background: #d1d1d6;
  border-radius: 11px;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.15);
}

.mode-pill__thumb {
  position: absolute;
  top: 4px;
  left: 4px;
  width: calc(50% - 6px);
  height: calc(100% - 8px);
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.22);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  pointer-events: none;
  z-index: 0;
}

.mode-pill__thumb.is-right {
  transform: translateX(calc(100% + 4px));
}

.mode-pill__seg {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 34px;
  padding: 0 8px;
  border: none;
  border-radius: 8px;
  background: transparent;
  cursor: pointer;
  font-family: inherit;
  transition: color 0.2s;
}

.mode-pill__icon {
  width: 18px;
  height: 18px;
  color: #0a0a0b;
}

.mode-pill__label {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: rgba(100, 100, 108, 0.8);
}

.mode-pill__label--full {
  background: linear-gradient(90deg, #007aff 0%, #ff6a00 55%, #ff3822 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
  font-size: 12px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: transparent;
}

/* 左右分栏：左侧编号导航（非图谱那种三栏 Finder） */
.ac-split {
  flex: 1;
  display: flex;
  min-height: 0;
  background: #f3f3f7;
}

.ac-rail {
  width: 232px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  padding: 16px 0 16px 14px;
  background: #f0f0f2;
  border-right: 1px dashed rgba(76, 81, 191, 0.2);
  box-shadow: 4px 0 24px rgba(45, 42, 80, 0.04);
}

.ac-rail__title {
  padding: 0 12px 10px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #7c7c90;
}

.ac-rail__nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow-y: auto;
}

.ac-rail__link {
  display: flex;
  align-items: baseline;
  gap: 10px;
  padding: 10px 12px;
  margin-right: 8px;
  border: none;
  border-radius: 10px;
  background: transparent;
  text-align: left;
  cursor: pointer;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  transition: background 0.15s, color 0.15s;
  color: #4b4b57;
}

.ac-rail__link:hover {
  background: rgba(99, 102, 241, 0.08);
  color: #1d1d1f;
}

.ac-rail__link.active {
  background: rgba(99, 102, 241, 0.16);
  color: #3730a3;
  box-shadow: inset 3px 0 0 #6366f1;
}

.ac-rail__idx {
  font-size: 11px;
  font-weight: 600;
  opacity: 0.55;
  min-width: 1.5em;
}

.ac-rail__link.active .ac-rail__idx {
  opacity: 1;
  color: #6366f1;
}

.ac-rail__text {
  font-size: 12px;
  font-weight: 500;
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Segoe UI', sans-serif;
}

.ac-main {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  overflow-x: hidden;
}

.config-scroll {
  padding: 20px 28px 28px;
}

.config-panel {
  max-width: 820px;
}

.panel-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #1d1d1f;
  margin: 0 0 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(0,0,0,0.06);
}

.panel-title svg {
  color: #007aff;
}

.config-item {
  margin-bottom: 16px;
}

.config-item:last-child {
  margin-bottom: 0;
}

.config-item label {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: #6e6e73;
  margin-bottom: 8px;
}

.config-item input[type="text"],
.config-item input[type="number"],
.config-item textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid rgba(0,0,0,0.1);
  border-radius: 8px;
  font-size: 13px;
  font-family: inherit;
  color: #1d1d1f;
  background: #f5f5f7;
  transition: border-color 0.2s, background-color 0.2s, box-shadow 0.2s;
}

.config-item input[type="text"]:hover,
.config-item input[type="number"]:hover,
.config-item textarea:hover {
  background-color: #ebebed;
}

.config-item input:focus,
.config-item textarea:focus {
  outline: none;
  border-color: #007aff;
  background-color: white;
  box-shadow: 0 0 0 3px rgba(0,122,255,0.15);
}

.config-item textarea {
  resize: vertical;
  min-height: 100px;
}

.config-item.full {
  grid-column: 1 / -1;
}

.config-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.char-count {
  font-size: 11px;
  color: #86868b;
  text-align: right;
  margin-top: 4px;
}

/* 角色卡片 */
.role-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.role-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 12px;
  background: #f5f5f7;
  border: 2px solid transparent;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.role-card:hover {
  background: #ebebed;
}

.role-card.active {
  background: rgba(0,122,255,0.08);
  border-color: #007aff;
}

.role-icon {
  font-size: 24px;
  margin-bottom: 8px;
  color: #86868b;
}

.role-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  margin-bottom: 8px;
  color: #86868b;
  transition: color 0.2s;
}

.role-card.active .role-icon-wrap {
  color: #007aff;
}

.role-label {
  font-size: 13px;
  font-weight: 600;
  color: #1d1d1f;
}

.role-desc {
  font-size: 11px;
  color: #86868b;
  text-align: center;
  margin-top: 4px;
}

/* 滑块 */
.slider-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.slider-row input[type="range"] {
  flex: 1;
  height: 4px;
  -webkit-appearance: none;
  background: #d2d2d7;
  border-radius: 2px;
  outline: none;
}

.slider-row input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 18px;
  height: 18px;
  background: white;
  border-radius: 50%;
  box-shadow: 0 1px 4px rgba(0,0,0,0.2);
  cursor: pointer;
  border: 2px solid #007aff;
}

.slider-label {
  font-size: 12px;
  color: #86868b;
  min-width: 32px;
}

.value {
  font-size: 12px;
  color: #007aff;
  font-weight: 500;
  min-width: 40px;
  text-align: right;
}

.model-desc {
  margin-top: 12px;
  padding: 12px 14px;
  background: linear-gradient(135deg, #f8f9ff 0%, #f0f4ff 100%);
  border-radius: 8px;
  font-size: 12px;
  color: #4a4a5a;
  line-height: 1.6;
  border-left: 3px solid #007aff;
}

.model-params {
  margin-top: 16px;
  padding: 16px;
  background: linear-gradient(135deg, #f8f9ff 0%, #f5f7fc 100%);
  border-radius: 12px;
  border: 1px solid rgba(99, 102, 241, 0.1);
}

.param-item {
  margin-bottom: 16px;
  padding: 12px 14px;
  background: white;
  border-radius: 10px;
  border: 1px solid rgba(0, 0, 0, 0.05);
  transition: all 0.2s;
}

.param-item:hover {
  border-color: rgba(0, 122, 255, 0.2);
  box-shadow: 0 2px 8px rgba(0, 122, 255, 0.08);
}

.param-item:last-child {
  margin-bottom: 0;
}

.param-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #1d1d1f;
  margin-bottom: 10px;
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

.param-hint {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 19px;
  height: 19px;
  border-radius: 50%;
  background: #d2d2d7;
  color: #63647b;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.param-hint:hover {
  background: #b8b8bf;
  color: #4a4a57;
}

/* 自定义 Tooltip 样式 */
.param-hint-tooltip {
  position: absolute;
  left: 50%;
  bottom: calc(100% + 10px);
  transform: translateX(-50%);
  padding: 10px 14px;
  background: white;
  color: #1d1d1f;
  font-size: 12px;
  font-weight: 400;
  line-height: 1.6;
  border-radius: 10px;
  white-space: normal;
  width: 240px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  opacity: 0;
  visibility: hidden;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  pointer-events: none;
}

.param-hint-tooltip::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 6px solid transparent;
  border-top-color: white;
}

.param-hint:hover .param-hint-tooltip {
  opacity: 1;
  visibility: visible;
  transform: translateX(-50%) translateY(-4px);
}

.param-hint-tooltip-content {
  letter-spacing: 0;
  text-transform: none;
}

/* 参数输入框 */
.param-input input {
  width: 100px;
  padding: 8px 12px;
  border: 1px solid #d2d2d7;
  border-radius: 8px;
  font-size: 13px;
  font-family: inherit;
  color: #1d1d1f;
  background: #f5f5f7;
  transition: all 0.2s;
}

.param-input input:hover {
  border-color: #b8b8bf;
  background-color: #ebebed;
}

.param-input input:focus {
  outline: none;
  border-color: #007aff;
  background-color: white;
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.15);
}

.hint {
  display: block;
  font-size: 11px;
  color: #86868b;
  margin-top: 6px;
}

/* 按钮组 */
.button-group {
  display: flex;
  gap: 8px;
}

.button-group button {
  flex: 1;
  padding: 10px 16px;
  border: 1px solid rgba(0,0,0,0.1);
  border-radius: 8px;
  background: #f5f5f7;
  font-size: 13px;
  color: #1d1d1f;
  cursor: pointer;
  transition: all 0.2s;
}

.button-group button:hover {
  background: #ebebed;
}

.button-group button.active {
  background: #007aff;
  border-color: #007aff;
  color: white;
}

/* 安全选项 */
.safety-options {
  display: flex;
  gap: 12px;
}

.safety-option {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 14px;
  background: #f5f5f7;
  border: 2px solid transparent;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.safety-option input {
  display: none;
}

.safety-option:hover {
  background: #ebebed;
}

.safety-option.active {
  background: rgba(0,122,255,0.08);
  border-color: #007aff;
}

.safety-icon {
  font-size: 20px;
}

.safety-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  margin-bottom: 6px;
  color: #86868b;
  transition: color 0.2s;
}

.safety-option.active .safety-icon-wrap {
  color: #007aff;
}

.safety-option span:last-child {
  font-size: 12px;
  font-weight: 500;
}

/* Toggle 开关 */
.toggle-label {
  display: flex !important;
  justify-content: space-between;
  align-items: center;
}

.toggle {
  position: relative;
  width: 44px;
  height: 24px;
}

.toggle input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle__slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: #d2d2d7;
  border-radius: 12px;
  transition: 0.3s;
}

.toggle__slider::before {
  position: absolute;
  content: "";
  height: 20px;
  width: 20px;
  left: 2px;
  bottom: 2px;
  background: white;
  border-radius: 50%;
  transition: 0.3s;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}

.toggle input:checked + .toggle__slider {
  background: #34c759;
}

.toggle input:checked + .toggle__slider::before {
  transform: translateX(20px);
}

/* 输入 + 单位 */
.input-with-unit {
  display: flex;
  align-items: center;
  gap: 8px;
}

.input-with-unit input {
  flex: 1;
}

.input-with-unit span {
  font-size: 12px;
  color: #86868b;
}

/* RAG 选项 */
.rag-options {
  margin-top: 16px;
  padding: 16px;
  background: #f9f9fb;
  border-radius: 8px;
}

/* 工具网格 */
/* 工具列表 */
.tools-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tools-grid {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tool-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #f5f5f7;
  border-radius: 8px;
  transition: all 0.2s;
}

.tool-row:hover {
  background: #ebebed;
}

.tool-row.active {
  background: rgba(0,122,255,0.06);
}

.tool-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.tool-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.tool-row .tool-name {
  font-size: 13px;
  font-weight: 500;
  color: #1d1d1f;
}

.tool-row .tool-desc {
  font-size: 11px;
  color: #86868b;
}

.tool-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 14px 10px;
  background: #f5f5f7;
  border: 2px solid transparent;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.tool-item input {
  display: none;
}

.tool-item:hover {
  background: #ebebed;
}

.tool-item.active {
  background: rgba(0,122,255,0.08);
  border-color: #007aff;
}

.tool-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  color: #86868b;
  transition: color 0.2s;
}

.tool-row .tool-icon-wrap {
  margin-bottom: 0;
}

.tool-item .tool-icon-wrap {
  margin-bottom: 6px;
}

.tool-item.active .tool-icon-wrap {
  color: #007aff;
}

.tool-name {
  font-size: 12px;
  font-weight: 600;
  color: #1d1d1f;
}

.tool-desc {
  font-size: 10px;
  color: #86868b;
  margin-top: 2px;
}

/* 安全滑块 */
.safety-slider {
  display: flex;
  align-items: center;
  gap: 12px;
}

.safety-slider input {
  flex: 1;
}

.safety-slider span {
  font-size: 12px;
  color: #86868b;
  min-width: 40px;
}

/* 预设配置 */
.presets-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.preset-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 12px;
  background: #f5f5f7;
  border: 2px solid transparent;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.preset-card:hover {
  background: #ebebed;
}

.preset-card.active {
  background: rgba(0,122,255,0.08);
  border-color: #007aff;
}

.preset-icon {
  font-size: 24px;
  margin-bottom: 8px;
}

.preset-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  margin-bottom: 8px;
  color: #86868b;
  transition: color 0.2s;
}

.preset-card.active .preset-icon-wrap {
  color: #007aff;
}

.preset-name {
  font-size: 13px;
  font-weight: 600;
  color: #1d1d1f;
}

.preset-desc {
  font-size: 10px;
  color: #86868b;
  text-align: center;
  margin-top: 4px;
}

/* 操作栏 */
.action-bar {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid rgba(0,0,0,0.06);
}

.btn {
  padding: 10px 24px;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn--secondary {
  background: #f5f5f7;
  color: #1d1d1f;
}

.btn--secondary:hover {
  background: #e5e5ea;
}

.btn--primary {
  background: #007aff;
  color: white;
}

.btn--primary:hover {
  background: #0070e0;
}

/* Toast 提示 */
.toast {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 24px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 500;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  z-index: 1000;
  background: white;
  color: #1d1d1f;
  border: 1px solid rgba(0,0,0,0.08);
}

.toast.success {
  border-color: rgba(52, 199, 89, 0.3);
}

.toast.info {
  border-color: rgba(88, 86, 214, 0.3);
}

.toast.error {
  border-color: rgba(255, 59, 48, 0.3);
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
}

/* 响应式 */
@media (max-width: 768px) {
  .ac-window {
    margin: 8px;
    border-radius: 12px;
  }

  .ac-head {
    flex-wrap: wrap;
    padding-bottom: 12px;
  }

  .mode-pill {
    width: 100%;
    max-width: 280px;
  }

  .ac-split {
    flex-direction: column;
  }

  .ac-rail {
    width: 100%;
    flex-direction: row;
    align-items: center;
    padding: 10px 12px;
    border-right: none;
    border-bottom: 1px dashed rgba(76, 81, 191, 0.2);
    overflow-x: auto;
    box-shadow: none;
  }

  .ac-rail__title {
    display: none;
  }

  .ac-rail__nav {
    flex-direction: row;
    flex-wrap: nowrap;
    gap: 6px;
  }

  .ac-rail__link {
    margin-right: 0;
    white-space: nowrap;
    flex-shrink: 0;
    box-shadow: none;
  }

  .ac-rail__link.active {
    box-shadow: none;
    border-bottom: 2px solid #6366f1;
  }

  .config-scroll {
    padding: 16px;
  }

  .role-grid,
  .presets-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .tools-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .config-row {
    grid-template-columns: 1fr;
  }

  .safety-options {
    flex-direction: column;
  }
}
</style>
