# macOS 风格知识库页面设计规范

## 1. Concept & Vision

仿 macOS Finder/Safari 的设计风格，打造一个现代、优雅的知识库管理界面。整体感觉应该是**轻盈、通透、精致**，如同 macOS 原生应用一般自然流畅。采用毛玻璃效果、柔和阴影和精心设计的微交互，让用户感受到 Apple 生态的设计美学。

## 2. Design Language

### 2.1 Aesthetic Direction
- **参考**：macOS Sonoma/Ventura 系统界面
- **特点**：毛玻璃背景、圆角设计、柔和阴影、精致的图标

### 2.2 Color Palette
```
Primary Background:    #1E1E1E (深色模式主背景)
Secondary Background:  rgba(255,255,255,0.05) (卡片背景)
Tertiary Background:   rgba(255,255,255,0.08) (悬浮态)
Accent Color:         #007AFF (macOS Blue)
Accent Secondary:      #5E5CE6 (macOS Purple)
Success:              #34C759 (macOS Green)
Warning:              #FF9500 (macOS Orange)
Danger:               #FF3B30 (macOS Red)
Text Primary:         #FFFFFF
Text Secondary:       rgba(255,255,255,0.6)
Text Tertiary:        rgba(255,255,255,0.3)
Border:               rgba(255,255,255,0.1)
```

### 2.3 Typography
- **字体族**：SF Pro Display, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif
- **标题**：18-24px, font-weight: 600
- **正文**：13-14px, font-weight: 400
- **辅助文字**：11-12px, font-weight: 400

### 2.4 Spatial System
- **窗口圆角**：12px
- **卡片圆角**：10px
- **按钮圆角**：8px
- **间距基准**：8px (4, 8, 12, 16, 24, 32)

### 2.5 Motion Philosophy
- **时长**：150-300ms
- **缓动**：cubic-bezier(0.4, 0, 0.2, 1)
- **弹性**：cubic-bezier(0.34, 1.56, 0.64, 1)
- **特点**：
  - 悬浮效果：scale(1.02) + shadow 增强
  - 点击效果：scale(0.98) 压缩反馈
  - 展开/收起：高度 + opacity 平滑过渡
  - 加载动画：脉冲呼吸效果

### 2.6 Visual Assets
- **图标库**：Lucide Icons (线性风格)
- **装饰效果**：
  - 毛玻璃：backdrop-filter: blur(20px) saturate(180%)
  - 渐变边框：1px 渐变边框
  - 微光效果：subtle inner glow

## 3. Layout & Structure

### 3.1 Window Chrome
```
┌─────────────────────────────────────────────────────────────┐
│ ● ● ●              知识库                    ─ [] ✕         │ ← 交通灯按钮 + 标题栏
├─────────┬───────────────────────────────────────────────────┤
│         │  ┌─────────────────────────────────────────────┐   │
│ 📚 知识库 │  │ 🔍 搜索文档...                    ⌘K      │   │ ← 搜索栏
│ 📄 文档  │  └─────────────────────────────────────────────┘   │
│ 🏷️ 标签  │  ┌───────────┬───────────────────────────────┐   │
│ ⚙️ 设置  │  │ 过滤器    │  文档列表 & 内容区              │   │
│         │  │           │                                │   │
│ ─────── │  │ 全部文档   │  ┌────────────────────────┐   │   │
│ 📊 统计  │  │ PDF       │  │ 文档卡片               │   │   │
│         │  │ Word      │  │ 标题 | 状态 | 知识点数 │   │   │
│         │  │ 索引完成   │  └────────────────────────┘   │   │
│         │  │ 索引中     │                                │   │
│         │  │ 待索引     │  ┌────────────────────────┐   │   │
│         │  │           │  │ 文档卡片               │   │   │
│         │  └───────────┴───────────────────────────────┘   │
├─────────┴───────────────────────────────────────────────────┤
│ 已选择 3 个文档  |  索引进度: 78%  |  ▶ 开始索引  ⏸ 暂停   │ ← 状态栏
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Responsive Strategy
- **桌面优先**：最小宽度 1024px
- **侧边栏**：固定 200px，可折叠至 60px
- **内容区**：自适应填充

## 4. Features & Interactions

### 4.1 导入文档
- **拖放区域**：虚线边框 + 图标，hover 时高亮
- **点击上传**：点击打开文件选择器
- **支持格式**：PDF, Word (.docx), Text (.txt), Markdown (.md)
- **导入动画**：进度条 + 文件图标飞入效果

### 4.2 过滤与搜索
- **搜索栏**：圆角输入框，带搜索图标
- **快捷键**：⌘K 聚焦搜索
- **过滤器**：
  - 文件类型（多选）
  - 索引状态
  - 时间范围
- **实时筛选**：输入时 300ms 防抖

### 4.3 文档列表
- **卡片展示**：
  - 文档图标（根据类型变化）
  - 文档名称（最多2行，超出省略）
  - 索引状态标签
  - 知识点数量
  - 更新时间
- **悬浮效果**：背景变亮 + 轻微上浮
- **选中效果**：左侧蓝色边框
- **右键菜单**：预览、编辑、删除、导出

### 4.4 知识点关联
- **知识点标签**：彩色圆角标签
- **悬浮预览**：显示知识点摘要
- **点击跳转**：平滑滚动到相关内容

### 4.5 索引状态与动作
- **状态指示器**：
  - 已完成：绿色勾选
  - 索引中：蓝色旋转图标 + 进度
  - 待处理：灰色时钟
  - 失败：红色感叹号
- **动作按钮**：
  - 开始索引（主按钮）
  - 暂停/继续
  - 重新索引
  - 批量操作

## 5. Component Inventory

### 5.1 Window Frame
- **交通灯按钮**：12px 圆形，红(#FF5F57)、黄(#FEBC2E)、绿(#28C840)
- **标题栏**：高度 40px，居中标题
- **窗口阴影**：0 25px 50px rgba(0,0,0,0.5)
- **状态**：default, maximized, minimized

### 5.2 Sidebar
- **宽度**：200px
- **项目高度**：28px
- **图标大小**：16px
- **悬浮态**：背景 rgba(255,255,255,0.1)
- **选中态**：背景 rgba(0,122,255,0.3) + 左侧 3px 蓝色边框

### 5.3 Search Bar
- **高度**：28px
- **圆角**：8px
- **背景**：rgba(255,255,255,0.1)
- **聚焦态**：边框高亮 + 轻微发光

### 5.4 Document Card
- **最小高度**：80px
- **圆角**：10px
- **背景**：rgba(255,255,255,0.05)
- **边框**：1px solid rgba(255,255,255,0.1)
- **悬浮态**：
  - 背景 rgba(255,255,255,0.08)
  - transform: translateY(-2px)
  - box-shadow 增强

### 5.5 Status Badge
- **圆角**：12px
- **内边距**：4px 10px
- **状态颜色**：成功(#34C759)、进行中(#007AFF)、待处理(#8E8E93)、错误(#FF3B30)

### 5.6 Action Button
- **Primary**：背景 #007AFF，hover 亮度+10%
- **Secondary**：背景 rgba(255,255,255,0.1)，hover 背景+10%
- **Danger**：背景 #FF3B30
- **高度**：32px
- **圆角**：8px
- **点击态**：scale(0.98)

### 5.7 Progress Bar
- **高度**：4px
- **圆角**：2px
- **背景**：rgba(255,255,255,0.1)
- **填充**：渐变 #007AFF → #5E5CE6
- **动画**：进度条脉冲光效

## 6. Technical Approach

### 6.1 Framework
- **单文件 HTML**：便于演示和部署
- **纯 CSS**：使用 CSS Variables 管理主题
- **Vanilla JavaScript**：无外部依赖

### 6.2 CSS Architecture
```
CSS Variables (设计令牌)
├── colors
├── typography
├── spacing
├── animations
└── shadows
Base Styles
├── reset
├── typography
└── utilities
Components
├── window-frame
├── sidebar
├── search-bar
├── document-card
├── status-badge
├── action-button
└── progress-bar
Animations
├── transitions
├── keyframes
└── micro-interactions
```

### 6.3 JavaScript Structure
```
State Management
├── documents[]
├── filters{}
├── searchQuery
└── selectedIds[]

Event Handlers
├── Search (debounced)
├── Filter Toggle
├── Document Selection
├── Import Handler
└── Index Control

Render Functions
├── renderSidebar()
├── renderDocuments()
├── renderStatusBar()
└── updateProgress()
```

### 6.4 Animation Implementation
- **CSS Transitions**：所有 hover/active 状态
- **CSS @keyframes**：加载、旋转、脉冲动画
- **JavaScript**：复杂序列动画控制
