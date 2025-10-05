<template>
  <div class="knowledge-graph-container">
    <!-- 顶部控制栏 -->
    <div class="graph-controls">
      <h2>跌倒检测知识图谱</h2>
      <div class="control-buttons">
        <button @click="zoomIn" class="control-btn" title="放大"><i class="fas fa-search-plus"></i></button>
        <button @click="zoomOut" class="control-btn" title="缩小"><i class="fas fa-search-minus"></i></button>
        <button @click="resetView" class="control-btn" title="重置视图"><i class="fas fa-compress-arrows-alt"></i></button>
        <button @click="togglePhysics" class="control-btn" title="切换布局状态"><i class="fas fa-magic"></i> {{ physicsEnabled ? '冻结' : '动态' }}</button>
        <button @click="toggleSubnodes" class="control-btn" title="显示/隐藏子节点"><i class="fas fa-sitemap"></i> {{ showSubnodes ? '隐藏子节点' : '显示子节点' }}</button>
        <button @click="toggleLabels" class="control-btn" title="强制显示标签"><i class="fas fa-tags"></i> {{ forceLabels ? '自动标签' : '强制显示' }}</button>
        <button @click="refreshData" class="control-btn" title="刷新数据"><i class="fas fa-sync-alt"></i></button>
      </div>
    </div>

    <!-- 主图谱区域 -->
    <div ref="networkContainer" class="network-container"></div>

    <!-- 右侧面板 -->
    <div class="data-panel">
      <!-- 节点详情（选中节点时显示） -->
      <div v-if="selectedNode" class="node-details">
        <div class="node-header">
          <h3>{{ selectedNode.label }}</h3>
          <span class="node-type">{{ getNodeTypeLabel(selectedNode.group) }}</span>
          <span v-if="selectedNode.isSubnode" class="subnode-tag">子节点</span>
          <button @click="closeDetails" class="close-btn"><i class="fas fa-times"></i></button>
        </div>
        
        <div class="node-description">
          <p>{{ selectedNode.desc || '无详细描述信息' }}</p>
        </div>
        
        <div class="node-stats">
          <div class="stat-item">
            <span class="stat-label">关联度</span>
            <span class="stat-value">{{ (selectedNode.score * 100).toFixed(1) }}%</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">置信度</span>
            <span class="stat-value">{{ (selectedNode.confidence * 100).toFixed(1) }}%</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">数据量</span>
            <span class="stat-value">{{ selectedNode.dataVolume }}条</span>
          </div>
        </div>

        <!-- 层级关系 -->
        <div v-if="selectedNode.parentId || hasSubnodes(selectedNode.id)" class="hierarchy-info">
          <h4>层级关系</h4>
          <div class="hierarchy-links">
            <div v-if="selectedNode.parentId" class="hierarchy-item">
              <span class="relation-label">父节点:</span>
              <span class="related-node" @click="focusNode(selectedNode.parentId)">{{ getNodeById(selectedNode.parentId).label }}</span>
            </div>
            <div v-if="hasSubnodes(selectedNode.id)" class="hierarchy-item">
              <span class="relation-label">子节点({{ getSubnodes(selectedNode.id).length }}):</span>
              <div class="subnodes-list">
                <span v-for="subnode in getSubnodes(selectedNode.id)" :key="subnode.id" class="subnode-item" @click="focusNode(subnode.id)">{{ subnode.label }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 数据分析图表 -->
        <div class="chart-container">
          <h4>检测性能趋势</h4>
          <canvas ref="performanceChart"></canvas>
        </div>

        <div class="relations-list">
          <h4>关联实体 ({{ relatedEdges.length }})</h4>
          <ul>
            <li v-for="edge in relatedEdges" :key="edge.id">
              <span class="relation-type">{{ edge.label }}</span>
              <span class="related-node" @click="focusNode(edge.to)">{{ getNodeById(edge.to).label }}</span>
            </li>
          </ul>
        </div>
      </div>
      
      <!-- 默认面板组件（未选中节点时显示） -->
      <div v-else class="default-panel">
        <div class="panel-header">
          <h3>跌倒检测知识图谱</h3>
          <div class="panel-subtitle">多层级知识体系与关系网络</div>
        </div>
        
        <div class="graph-intro">
          <p>本知识图谱展示了跌倒检测领域的多级知识体系，包含6大核心类别、28个主节点和42个子节点。支持缩放查看细节，缩小视图时标签会智能适配显示。</p>
          
          <div class="entity-types">
            <h4>核心实体类型</h4>
            <div v-for="(type, key) in NODE_TYPES" :key="key" class="entity-type-item">
              <div class="type-color" :style="{ backgroundColor: type.color }"></div>
              <div class="type-info">
                <strong>{{ type.label }}</strong>
                <p>{{ type.description }}（含{{ type.subcount }}个子类型）</p>
              </div>
            </div>
          </div>
          
          <div class="graph-stats">
            <h4>图谱统计</h4>
            <div class="stats-grid">
              <div class="stat-box">
                <div class="stat-number">{{ totalNodes }}</div>
                <div class="stat-name">总实体数</div>
              </div>
              <div class="stat-box">
                <div class="stat-number">{{ edges.length }}</div>
                <div class="stat-name">关联关系数</div>
              </div>
              <div class="stat-box">
                <div class="stat-number">{{ maxDepth }}</div>
                <div class="stat-name">最大层级深度</div>
              </div>
            </div>
          </div>
          
          <div class="operation-guide">
            <h4>操作指南</h4>
            <ul>
              <li><i class="fas fa-mouse-pointer"></i> 点击节点查看详细信息</li>
              <li><i class="fas fa-sitemap"></i> 切换显示/隐藏子节点控制复杂度</li>
              <li><i class="fas fa-tags"></i> 强制显示所有标签（适合缩小视图）</li>
              <li><i class="fas fa-hand-paper"></i> 拖拽节点可调整位置</li>
              <li><i class="fas fa-search-plus"></i> 鼠标滚轮控制缩放</li>
              <li><i class="fas fa-arrows-alt"></i> 拖拽空白区域平移视图</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick, computed } from 'vue'
import { Network } from 'vis-network'
import { Chart, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler } from 'chart.js'

// 注册Chart.js组件
Chart.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

// 图谱容器和网络实例
const networkContainer = ref(null)
const network = ref(null)
const physicsEnabled = ref(true)
const selectedNode = ref(null)
const nodes = ref([])
const edges = ref([])
const allNodes = ref([]) // 存储所有节点（包括子节点）
const allEdges = ref([]) // 存储所有边（包括子节点关系）
const performanceChart = ref(null)
const chartInstance = ref(null)
const showSubnodes = ref(true) // 控制子节点显示状态
const forceLabels = ref(false) // 强制显示所有标签（缩小视图时用）

// 节点类型定义
const NODE_TYPES = {
  1: { 
    label: '检测模型', 
    color: '#3b82f6', 
    glow: 'rgba(59, 130, 246, 0.5)',
    description: '用于识别和检测跌倒行为的算法模型',
    subcount: 8
  },
  2: { 
    label: '特征参数', 
    color: '#ec4899', 
    glow: 'rgba(236, 72, 153, 0.5)',
    description: '用于判断跌倒行为的关键特征参数',
    subcount: 7
  },
  3: { 
    label: '场景类型', 
    color: '#10b981', 
    glow: 'rgba(16, 185, 129, 0.5)',
    description: '可能发生跌倒事件的环境场景',
    subcount: 6
  },
  4: { 
    label: '风险因素', 
    color: '#f59e0b', 
    glow: 'rgba(245, 158, 11, 0.5)',
    description: '增加跌倒可能性的各类因素',
    subcount: 9
  },
  5: { 
    label: '检测结果', 
    color: '#ef4444', 
    glow: 'rgba(239, 68, 68, 0.5)',
    description: '系统对监测到的行为做出的判断结果',
    subcount: 5
  },
  6: { 
    label: '算法模块', 
    color: '#8b5cf6', 
    glow: 'rgba(139, 92, 246, 0.5)',
    description: '构成跌倒检测系统的核心算法组件',
    subcount: 7
  }
}

// 初始化图谱数据（包含多级嵌套子节点）
const initGraphData = () => {
  // 1. 检测模型（主节点+子节点）
  const detectionModels = [
    { id: 1, label: 'YOLO系列', typeLabel: '检测模型', group: 1, score: 0.92, confidence: 0.96, dataVolume: 12500, desc: '实时目标检测模型家族，适用于跌倒动作捕捉' },
    { id: 101, label: 'YOLOv5', typeLabel: 'YOLO变体', group: 1, isSubnode: true, parentId: 1, score: 0.89, confidence: 0.93, dataVolume: 8700, desc: 'YOLO系列第五代模型，平衡速度与精度' },
    { id: 102, label: 'YOLOv8', typeLabel: 'YOLO变体', group: 1, isSubnode: true, parentId: 1, score: 0.94, confidence: 0.97, dataVolume: 9300, desc: 'YOLO系列第八代模型，增强了姿态估计能力' },
    { id: 103, label: 'YOLO-NAS', typeLabel: 'YOLO变体', group: 1, isSubnode: true, parentId: 1, score: 0.91, confidence: 0.95, dataVolume: 7600, desc: '神经架构搜索优化的YOLO模型' },
    
    { id: 2, label: 'ResNet系列', typeLabel: '检测模型', group: 1, score: 0.88, confidence: 0.91, dataVolume: 9800, desc: '深度残差网络家族，用于特征提取和姿态识别' },
    { id: 104, label: 'ResNet18', typeLabel: 'ResNet变体', group: 1, isSubnode: true, parentId: 2, score: 0.82, confidence: 0.88, dataVolume: 6500, desc: '18层残差网络，轻量级模型' },
    { id: 105, label: 'ResNet50', typeLabel: 'ResNet变体', group: 1, isSubnode: true, parentId: 2, score: 0.87, confidence: 0.92, dataVolume: 8200, desc: '50层残差网络，平衡深度与计算量' },
    
    { id: 3, label: 'EfficientNet', typeLabel: '检测模型', group: 1, score: 0.86, confidence: 0.90, dataVolume: 8500, desc: '高效卷积神经网络，平衡精度与计算成本' }
  ]

  // 2. 特征参数（主节点+子节点）
  const featureParams = [
    { id: 10, label: '姿态特征', typeLabel: '特征参数', group: 2, score: 0.94, confidence: 0.97, dataVolume: 25000, desc: '描述人体姿态的关键特征集合' },
    { id: 201, label: '关节角度', typeLabel: '姿态子特征', group: 2, isSubnode: true, parentId: 10, score: 0.93, confidence: 0.96, dataVolume: 12000, desc: '人体主要关节的角度变化参数' },
    { id: 202, label: '骨骼向量', typeLabel: '姿态子特征', group: 2, isSubnode: true, parentId: 10, score: 0.91, confidence: 0.95, dataVolume: 10500, desc: '骨骼关键点之间的向量关系' },
    
    { id: 11, label: '运动特征', typeLabel: '特征参数', group: 2, score: 0.89, confidence: 0.93, dataVolume: 21000, desc: '描述人体运动状态的特征集合' },
    { id: 203, label: '运动轨迹', typeLabel: '运动子特征', group: 2, isSubnode: true, parentId: 11, score: 0.88, confidence: 0.92, dataVolume: 9800, desc: '人体重心移动的路径特征' },
    { id: 204, label: '速度变化', typeLabel: '运动子特征', group: 2, isSubnode: true, parentId: 11, score: 0.86, confidence: 0.90, dataVolume: 8200, desc: '运动速度的瞬时变化率' },
    
    { id: 12, label: '骨骼关键点', typeLabel: '特征参数', group: 2, score: 0.93, confidence: 0.95, dataVolume: 23000, desc: '人体骨骼节点坐标，用于构建姿态模型' }
  ]

  // 3. 场景类型（主节点+子节点）
  const sceneTypes = [
    { id: 20, label: '居家环境', typeLabel: '场景类型', group: 3, score: 0.91, confidence: 0.94, dataVolume: 15000, desc: '家庭场景的集合，包含多个子场景' },
    { id: 301, label: '卫生间', typeLabel: '居家子场景', group: 3, isSubnode: true, parentId: 20, score: 0.93, confidence: 0.96, dataVolume: 5200, desc: '家庭中跌倒高发的湿滑环境' },
    { id: 302, label: '卧室', typeLabel: '居家子场景', group: 3, isSubnode: true, parentId: 20, score: 0.88, confidence: 0.92, dataVolume: 4100, desc: '夜间跌倒高发场景' },
    
    { id: 21, label: '医院场景', typeLabel: '场景类型', group: 3, score: 0.88, confidence: 0.92, dataVolume: 13000, desc: '医疗机构相关场景' },
    { id: 303, label: '病房', typeLabel: '医院子场景', group: 3, isSubnode: true, parentId: 21, score: 0.89, confidence: 0.93, dataVolume: 7800, desc: '患者住院期间的主要活动场景' },
    { id: 304, label: '走廊', typeLabel: '医院子场景', group: 3, isSubnode: true, parentId: 21, score: 0.85, confidence: 0.89, dataVolume: 3200, desc: '患者移动时的过渡场景' },
    
    { id: 22, label: '养老院', typeLabel: '场景类型', group: 3, score: 0.93, confidence: 0.96, dataVolume: 16000, desc: '老年照护机构，集体居住与活动场景' }
  ]

  // 4. 风险因素（主节点+子节点）
  const riskFactors = [
    { id: 30, label: '人体因素', typeLabel: '风险因素', group: 4, score: 0.95, confidence: 0.98, dataVolume: 19000, desc: '与人体自身相关的跌倒风险因素' },
    { id: 401, label: '年龄因素', typeLabel: '人体子因素', group: 4, isSubnode: true, parentId: 30, score: 0.96, confidence: 0.99, dataVolume: 8700, desc: '65岁以上人群跌倒风险显著增加' },
    { id: 402, label: '身体机能', typeLabel: '人体子因素', group: 4, isSubnode: true, parentId: 30, score: 0.92, confidence: 0.96, dataVolume: 7300, desc: '平衡能力、肌肉强度等身体机能指标' },
    { id: 403, label: '疾病影响', typeLabel: '人体子因素', group: 4, isSubnode: true, parentId: 30, score: 0.93, confidence: 0.97, dataVolume: 6500, desc: '影响运动和平衡的疾病因素' },
    
    { id: 31, label: '环境因素', typeLabel: '风险因素', group: 4, score: 0.87, confidence: 0.90, dataVolume: 14000, desc: '与环境相关的跌倒风险因素' },
    { id: 404, label: '地面状况', typeLabel: '环境子因素', group: 4, isSubnode: true, parentId: 31, score: 0.89, confidence: 0.92, dataVolume: 5200, desc: '地面平整度、湿滑度等特征' },
    { id: 405, label: '光照条件', typeLabel: '环境子因素', group: 4, isSubnode: true, parentId: 31, score: 0.83, confidence: 0.85, dataVolume: 4100, desc: '光线强度、均匀度等照明特征' },
    { id: 406, label: '障碍物', typeLabel: '环境子因素', group: 4, isSubnode: true, parentId: 31, score: 0.88, confidence: 0.91, dataVolume: 3700, desc: '地面障碍物的数量和分布' },
    
    { id: 32, label: '行为因素', typeLabel: '风险因素', group: 4, score: 0.85, confidence: 0.88, dataVolume: 12000, desc: '与个人行为相关的跌倒风险因素' },
    { id: 407, label: '独自活动', typeLabel: '行为子因素', group: 4, isSubnode: true, parentId: 32, score: 0.86, confidence: 0.89, dataVolume: 5800, desc: '无人陪同情况下的活动' },
    { id: 408, label: '夜间活动', typeLabel: '行为子因素', group: 4, isSubnode: true, parentId: 32, score: 0.84, confidence: 0.87, dataVolume: 4200, desc: '夜间起床等低光照活动' }
  ]

  // 5. 检测结果（主节点+子节点）
  const detectionResults = [
    { id: 40, label: '跌倒事件', typeLabel: '检测结果', group: 5, score: 0.96, confidence: 0.99, dataVolume: 8500, desc: '判定为跌倒的紧急事件' },
    { id: 501, label: '轻度跌倒', typeLabel: '跌倒子类型', group: 5, isSubnode: true, parentId: 40, score: 0.94, confidence: 0.97, dataVolume: 3200, desc: '无明显伤害的轻微跌倒' },
    { id: 502, label: '重度跌倒', typeLabel: '跌倒子类型', group: 5, isSubnode: true, parentId: 40, score: 0.97, confidence: 0.99, dataVolume: 1800, desc: '可能造成伤害的严重跌倒' },
    
    { id: 41, label: '正常状态', typeLabel: '检测结果', group: 5, score: 0.93, confidence: 0.97, dataVolume: 42000, desc: '无跌倒风险的正常活动状态' },
    { id: 42, label: '危险姿态', typeLabel: '检测结果', group: 5, score: 0.90, confidence: 0.94, dataVolume: 12000, desc: '可能导致跌倒的前驱姿态' }
  ]

  // 6. 算法模块（主节点+子节点）
  const algorithmModules = [
    { id: 50, label: '目标检测', typeLabel: '算法模块', group: 6, score: 0.94, confidence: 0.97, dataVolume: 35000, desc: '识别图像中人体目标的模块' },
    { id: 601, label: '目标定位', typeLabel: '检测子模块', group: 6, isSubnode: true, parentId: 50, score: 0.93, confidence: 0.96, dataVolume: 15000, desc: '确定人体在图像中位置的子模块' },
    { id: 602, label: '目标跟踪', typeLabel: '检测子模块', group: 6, isSubnode: true, parentId: 50, score: 0.92, confidence: 0.95, dataVolume: 13000, desc: '追踪人体移动轨迹的子模块' },
    
    { id: 51, label: '姿态估计', typeLabel: '算法模块', group: 6, score: 0.92, confidence: 0.95, dataVolume: 32000, desc: '计算人体姿态参数的核心模块' },
    { id: 52, label: '行为分析', typeLabel: '算法模块', group: 6, score: 0.88, confidence: 0.91, dataVolume: 28000, desc: '判断行为是否属于跌倒的决策模块' },
    { id: 603, label: '特征提取', typeLabel: '分析子模块', group: 6, isSubnode: true, parentId: 52, score: 0.89, confidence: 0.92, dataVolume: 12000, desc: '提取行为特征的子模块' },
    { id: 604, label: '分类决策', typeLabel: '分析子模块', group: 6, isSubnode: true, parentId: 52, score: 0.87, confidence: 0.90, dataVolume: 10500, desc: '对行为类型进行分类的子模块' }
  ]

  // 合并所有节点
  allNodes.value = [
    ...detectionModels,
    ...featureParams,
    ...sceneTypes,
    ...riskFactors,
    ...detectionResults,
    ...algorithmModules
  ]

  // 生成边数据（包含层级关系和关联关系）
  allEdges.value = [
    // 层级关系边（父节点->子节点）
    { from: 1, to: 101, label: '包含', width: 1, dashes: true, color: '#3b82f6' },
    { from: 1, to: 102, label: '包含', width: 1, dashes: true, color: '#3b82f6' },
    { from: 1, to: 103, label: '包含', width: 1, dashes: true, color: '#3b82f6' },
    { from: 2, to: 104, label: '包含', width: 1, dashes: true, color: '#3b82f6' },
    { from: 2, to: 105, label: '包含', width: 1, dashes: true, color: '#3b82f6' },
    
    { from: 10, to: 201, label: '包含', width: 1, dashes: true, color: '#ec4899' },
    { from: 10, to: 202, label: '包含', width: 1, dashes: true, color: '#ec4899' },
    { from: 11, to: 203, label: '包含', width: 1, dashes: true, color: '#ec4899' },
    { from: 11, to: 204, label: '包含', width: 1, dashes: true, color: '#ec4899' },
    
    { from: 20, to: 301, label: '包含', width: 1, dashes: true, color: '#10b981' },
    { from: 20, to: 302, label: '包含', width: 1, dashes: true, color: '#10b981' },
    { from: 21, to: 303, label: '包含', width: 1, dashes: true, color: '#10b981' },
    { from: 21, to: 304, label: '包含', width: 1, dashes: true, color: '#10b981' },
    
    { from: 30, to: 401, label: '包含', width: 1, dashes: true, color: '#f59e0b' },
    { from: 30, to: 402, label: '包含', width: 1, dashes: true, color: '#f59e0b' },
    { from: 30, to: 403, label: '包含', width: 1, dashes: true, color: '#f59e0b' },
    { from: 31, to: 404, label: '包含', width: 1, dashes: true, color: '#f59e0b' },
    { from: 31, to: 405, label: '包含', width: 1, dashes: true, color: '#f59e0b' },
    { from: 31, to: 406, label: '包含', width: 1, dashes: true, color: '#f59e0b' },
    { from: 32, to: 407, label: '包含', width: 1, dashes: true, color: '#f59e0b' },
    { from: 32, to: 408, label: '包含', width: 1, dashes: true, color: '#f59e0b' },
    
    { from: 40, to: 501, label: '包含', width: 1, dashes: true, color: '#ef4444' },
    { from: 40, to: 502, label: '包含', width: 1, dashes: true, color: '#ef4444' },
    
    { from: 50, to: 601, label: '包含', width: 1, dashes: true, color: '#8b5cf6' },
    { from: 50, to: 602, label: '包含', width: 1, dashes: true, color: '#8b5cf6' },
    { from: 52, to: 603, label: '包含', width: 1, dashes: true, color: '#8b5cf6' },
    { from: 52, to: 604, label: '包含', width: 1, dashes: true, color: '#8b5cf6' },

    // 跨类别关联关系（主节点）
    { from: 1, to: 50, label: '集成', width: 3, color: NODE_TYPES[1].color },
    { from: 1, to: 51, label: '集成', width: 3, color: NODE_TYPES[1].color },
    { from: 2, to: 51, label: '支持', width: 2, color: NODE_TYPES[1].color },
    
    { from: 50, to: 12, label: '提取', width: 2, color: NODE_TYPES[6].color },
    { from: 51, to: 10, label: '计算', width: 2, color: NODE_TYPES[6].color },
    { from: 51, to: 11, label: '追踪', width: 2, color: NODE_TYPES[6].color },
    { from: 52, to: 10, label: '分析', width: 2, color: NODE_TYPES[6].color },
    
    { from: 20, to: 31, label: '常见', width: 2, color: NODE_TYPES[3].color },
    { from: 21, to: 30, label: '高风险', width: 2, color: NODE_TYPES[3].color },
    { from: 22, to: 30, label: '高风险', width: 2, color: NODE_TYPES[3].color },
    
    { from: 1, to: 40, label: '核心检测', width: 3, color: NODE_TYPES[1].color },
    { from: 1, to: 42, label: '预警', width: 3, color: NODE_TYPES[1].color },
    { from: 2, to: 40, label: '辅助验证', width: 2, color: NODE_TYPES[1].color },
    
    { from: 40, to: 30, label: '关联', width: 2, color: NODE_TYPES[5].color },
    { from: 40, to: 31, label: '关联', width: 2, color: NODE_TYPES[5].color },
    { from: 42, to: 32, label: '关联', width: 2, color: NODE_TYPES[5].color },
    
    { from: 52, to: 40, label: '判定', width: 3, color: NODE_TYPES[6].color },
    { from: 52, to: 41, label: '判定', width: 2, color: NODE_TYPES[6].color },
    { from: 52, to: 42, label: '判定', width: 3, color: NODE_TYPES[6].color },
    
    // 跨类别关联关系（包含子节点）
    { from: 102, to: 601, label: '优化', width: 2, color: NODE_TYPES[1].color },
    { from: 102, to: 602, label: '优化', width: 2, color: NODE_TYPES[1].color },
    { from: 105, to: 603, label: '增强', width: 2, color: NODE_TYPES[1].color },
    
    { from: 201, to: 51, label: '输入', width: 2, color: NODE_TYPES[2].color },
    { from: 203, to: 52, label: '输入', width: 2, color: NODE_TYPES[2].color },
    
    { from: 301, to: 404, label: '高风险', width: 2, color: NODE_TYPES[3].color },
    { from: 302, to: 408, label: '高风险', width: 2, color: NODE_TYPES[3].color },
    
    { from: 401, to: 42, label: '增加', width: 2, color: NODE_TYPES[4].color },
    { from: 404, to: 502, label: '增加', width: 2, color: NODE_TYPES[4].color },
    
    { from: 501, to: 303, label: '常见', width: 2, color: NODE_TYPES[5].color },
    { from: 502, to: 301, label: '常见', width: 2, color: NODE_TYPES[5].color },
    
    { from: 604, to: 40, label: '输出', width: 2, color: NODE_TYPES[6].color },
    { from: 604, to: 41, label: '输出', width: 2, color: NODE_TYPES[6].color }
  ]

  // 初始化显示数据（根据子节点显示状态）
  updateDisplayData()
}

// 根据子节点显示状态更新显示数据
const updateDisplayData = () => {
  if (showSubnodes.value) {
    nodes.value = [...allNodes.value]
    edges.value = [...allEdges.value]
  } else {
    // 只显示主节点（非子节点）
    const mainNodes = allNodes.value.filter(node => !node.isSubnode)
    const mainNodeIds = mainNodes.map(node => node.id)
    
    // 只显示主节点之间的边
    const mainEdges = allEdges.value.filter(edge => 
      mainNodeIds.includes(edge.from) && mainNodeIds.includes(edge.to)
    )
    
    nodes.value = mainNodes
    edges.value = mainEdges
  }
}

// 初始化网络
const initNetwork = () => {
  if (!networkContainer.value) return

  // 节点基础样式（含自适应标签优化）
  const nodeStyles = {
    shape: 'circle',
    size: 30, // 主节点基础大小
    borderWidth: 2,
    borderWidthSelected: 4,
    color: {
      border: '#fff',
      background: '#3b82f6',
      highlight: { 
        background: '#3b82f6', 
        border: '#fff' 
      },
      hover: { 
        background: '#3b82f6', 
        border: '#fff' 
      }
    },
    font: {
      color: '#fff',
      size: 12, // 基础字体大小
      strokeWidth: 1,
      strokeColor: '#000', // 文字描边，增强缩小可读性
      multi: true,
      align: 'center',
      // 字体随节点缩放（核心优化1：缩小视图时字体自适应）
      scaling: {
        min: 6,   // 最小字体（缩小到极致时仍可见）
        max: 14,  // 最大字体
        label: true
      }
    },
    shadow: {
      enabled: true,
      color: 'rgba(59, 130, 246, 0.5)',
      size: 10,
      x: 0,
      y: 0
    },
    // 悬停增强（核心优化2：缩小视图时hover显示清晰标签）
    hover: {
      size: 8,       // 节点悬停放大
      strokeWidth: 3,
      font: { 
        size: 16,    // 字体临时放大
        strokeWidth: 2 // 增强描边
      }
    },
    // 选中状态增强
    selected: {
      size: 35,
      font: { size: 14 }
    }
  }

  // 边样式
  const edgeStyles = {
    color: {
      color: '#848484',
      highlight: '#3b82f6',
      hover: '#3b82f6',
      inherit: false
    },
    width: 1,
    dashes: false,
    font: {
      color: '#ccc',
      size: 10,
      strokeWidth: 0,
      // 边标签自适应缩放
      scaling: {
        min: 8,
        max: 12,
        label: true
      }
    },
    shadow: {
      enabled: true,
      color: 'rgba(59, 130, 246, 0.2)',
      size: 5
    },
    smooth: {
      enabled: true,
      type: 'dynamic'
    }
  }

  // 物理引擎配置（适应复杂网络）
  const physicsOptions = {
    enabled: physicsEnabled.value,
    solver: 'forceAtlas2Based',
    forceAtlas2Based: {
      gravitationalConstant: -350,
      centralGravity: 0.03,
      springLength: 200,
      springConstant: 0.12,
      avoidOverlap: 0.5
    },
    maxVelocity: 150,
    minVelocity: 0.75,
    friction: 0.5,
    stabilization: {
      enabled: true,
      iterations: 500,
      updateInterval: 25
    }
  }

  // 网络全局配置（含标签智能显示）
  const options = {
    nodes: {
      ...nodeStyles,
      labelHighlightBold: true,
      margin: 10,
      // 核心优化3：标签最小可见尺寸（根据forceLabels动态调整）
      label: {
        minVisibleSize: forceLabels.value ? 5 : 15, // 强制显示时降低阈值
        visible: forceLabels.value // 强制显示所有标签
      }
    },
    edges: edgeStyles,
    physics: physicsOptions,
    interaction: {
      dragNodes: true,
      dragView: true,
      zoomView: true,
      tooltipDelay: 100, // 快速显示tooltip辅助识别
      hideEdgesOnDrag: false,
      selectConnectedEdges: true,
      tooltip: {
        enabled: true,
        // 自定义tooltip显示完整标签（核心优化4：缩小视图辅助识别）
        formatter: (node) => {
          const nodeData = getNodeById(node)
          return `<div style="padding:5px;background:#1e293b;border:1px solid #3b82f6;border-radius:4px;">
                  <strong style="color:#3b82f6;">${nodeData.label}</strong>
                  <div style="color:#e2e8f0;font-size:12px;">${nodeData.typeLabel}</div>
                </div>`
        }
      }
    },
    layout: {
      randomSeed: 42
    },
    manipulation: {
      enabled: false
    }
  }

  // 格式化节点（区分主/子节点）
  const formattedNodes = nodes.value.map(node => {
    const size = node.isSubnode ? 22 : 30;
    const fontSize = node.isSubnode ? 10 : 12;
    
    return {
      ...node,
      // 节点标签显示为两行：名称 + 类型（缩小视图也能快速识别）
      label: `${node.label}\n[${node.typeLabel}]`,
      size,
      font: {
        ...nodeStyles.font,
        size: fontSize
      },
      color: {
        ...nodeStyles.color,
        background: NODE_TYPES[node.group].color,
        highlight: {
          ...nodeStyles.color.highlight,
          background: NODE_TYPES[node.group].color
        }
      },
      shadow: {
        ...nodeStyles.shadow,
        color: NODE_TYPES[node.group].glow,
        size: node.isSubnode ? 6 : 10
      },
      // 存储子节点标识，用于CSS样式控制
      data: {
        isSubnode: node.isSubnode
      }
    }
  })

  // 销毁旧实例 + 创建新网络
  if (network.value) {
    network.value.destroy()
  }
  network.value = new Network(networkContainer.value, { 
    nodes: formattedNodes, 
    edges: edges.value 
  }, options)

  // 节点点击事件
  network.value.on('click', (params) => {
    if (params.nodes.length > 0) {
      const nodeId = parseInt(params.nodes[0])
      selectedNode.value = allNodes.value.find(n => n.id === nodeId)
      initPerformanceChart()
    } else {
      selectedNode.value = null
    }
  })

  // 缩放事件监听（辅助优化：缩放时动态调整标签策略）
  network.value.on('zoom', (params) => {
    const scale = params.scale;
    // 缩放比例过小（<0.5）时自动启用强制标签模式
    if (scale < 0.5 && !forceLabels.value) {
      forceLabels.value = true;
      updateLabelVisibility();
    }
  })
}

// 更新标签可见性
const updateLabelVisibility = () => {
  if (network.value) {
    network.value.setOptions({
      nodes: {
        label: {
          minVisibleSize: forceLabels.value ? 5 : 15,
          visible: forceLabels.value
        }
      }
    })
  }
}

// 切换标签显示模式
const toggleLabels = () => {
  forceLabels.value = !forceLabels.value;
  updateLabelVisibility();
}

// 初始化性能趋势图表
const initPerformanceChart = () => {
  if (!selectedNode.value || !performanceChart.value) return

  // 销毁现有图表
  if (chartInstance.value) {
    chartInstance.value.destroy()
  }

  // 生成模拟数据
  const months = ['1月', '2月', '3月', '4月', '5月', '6月']
  const baseValue = selectedNode.value.confidence * 80 + 10
  const volatility = selectedNode.value.isSubnode ? 4 : 2
  
  const accuracyData = months.map((_, i) => 
    Math.max(70, Math.min(99, baseValue + (i * 0.6) + (Math.random() * volatility - volatility/2)))
  )
  const recallData = months.map((_, i) => 
    Math.max(65, Math.min(95, (baseValue - 5) + (i * 0.4) + (Math.random() * volatility - volatility/2)))
  )

  // 创建图表
  chartInstance.value = new Chart(performanceChart.value, {
    type: 'line',
    data: {
      labels: months,
      datasets: [
        {
          label: '准确率 (%)',
          data: accuracyData,
          borderColor: NODE_TYPES[selectedNode.value.group].color,
          backgroundColor: `${NODE_TYPES[selectedNode.value.group].glow}`,
          tension: 0.4,
          fill: true,
          pointRadius: 4,
          pointHoverRadius: 6
        },
        {
          label: '召回率 (%)',
          data: recallData,
          borderColor: '#ffffff',
          backgroundColor: 'rgba(255, 255, 255, 0.1)',
          tension: 0.4,
          fill: true,
          pointRadius: 4,
          pointHoverRadius: 6
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: '#fff' }
        },
        tooltip: {
          mode: 'index',
          intersect: false
        }
      },
      scales: {
        y: {
          beginAtZero: false,
          min: 60,
          max: 100,
          grid: { color: 'rgba(255, 255, 255, 0.1)' },
          ticks: { color: '#ccc' }
        },
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.1)' },
          ticks: { color: '#ccc' }
        }
      }
    }
  })
}

// 辅助方法
const getNodeTypeLabel = (group) => {
  return NODE_TYPES[group]?.label || '未知类型'
}

const getNodeById = (id) => {
  return allNodes.value.find(n => n.id === id) || {}
}

const focusNode = (nodeId) => {
  network.value.focus(nodeId, { scale: 1.5, animation: true, duration: 800 })
  selectedNode.value = getNodeById(nodeId)
  initPerformanceChart()
}

const hasSubnodes = (nodeId) => {
  return allNodes.value.some(node => node.parentId === nodeId)
}

const getSubnodes = (nodeId) => {
  return allNodes.value.filter(node => node.parentId === nodeId)
}

// 控制方法
const zoomIn = () => {
  network.value.zoom(0.2)
}

const zoomOut = () => {
  network.value.zoom(-0.2)
}

const resetView = () => {
  network.value.fit({ animation: true, duration: 800 })
}

const togglePhysics = () => {
  physicsEnabled.value = !physicsEnabled.value
  network.value.setOptions({
    physics: {
      enabled: physicsEnabled.value
    }
  })
}

const toggleSubnodes = () => {
  showSubnodes.value = !showSubnodes.value
  updateDisplayData()
  initNetwork()
  if (selectedNode.value && selectedNode.value.isSubnode && !showSubnodes.value) {
    selectedNode.value = null
  }
}

const refreshData = () => {
  initGraphData()
  initNetwork()
  selectedNode.value = null
}

const closeDetails = () => {
  selectedNode.value = null
}

// 计算相关边
const relatedEdges = ref([])
watch(selectedNode, (node) => {
  if (node) {
    relatedEdges.value = allEdges.value
      .filter(edge => edge.from === node.id || edge.to === node.id)
      .filter(edge => {
        if (!showSubnodes.value) {
          const fromNode = getNodeById(edge.from)
          const toNode = getNodeById(edge.to)
          return !fromNode.isSubnode && !toNode.isSubnode
        }
        return true
      })
      .map(edge => ({
        ...edge,
        isIncoming: edge.to === node.id
      }))
  } else {
    relatedEdges.value = []
  }
})

// 图谱统计数据
const totalNodes = computed(() => allNodes.value.length)
const maxDepth = computed(() => {
  let maxDepth = 1
  const getDepth = (nodeId, currentDepth = 1) => {
    const children = allNodes.value.filter(n => n.parentId === nodeId)
    if (children.length > 0) {
      const childDepth = currentDepth + 1
      if (childDepth > maxDepth) maxDepth = childDepth
      children.forEach(child => getDepth(child.id, childDepth))
    }
  }
  
  allNodes.value
    .filter(node => !node.parentId)
    .forEach(node => getDepth(node.id))
  
  return maxDepth
})

// 生命周期
onMounted(() => {
  initGraphData()
  nextTick(() => {
    initNetwork()
  })
})
</script>

<style scoped>
.knowledge-graph-container {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: radial-gradient(circle at center, #121a2e 0%, #0f172a 100%);
}

.graph-controls {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(15, 23, 42, 0.8);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(59, 130, 246, 0.3);
  z-index: 100;
}

.graph-controls h2 {
  color: #3b82f6;
  margin: 0;
  text-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
}

.control-buttons {
  display: flex;
  gap: 0.5rem;
}

.control-btn {
  background: rgba(30, 41, 59, 0.8);
  border: 1px solid rgba(59, 130, 246, 0.3);
  color: #3b82f6;
  width: 36px;
  height: 36px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.control-btn:hover {
  background: rgba(59, 130, 246, 0.2);
  box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
}

.network-container {
  position: absolute;
  top: 0;
  left: 0;
  right: 350px;
  bottom: 0;
  margin-top: 60px;
}

.data-panel {
  position: absolute;
  top: 0;
  right: 0;
  width: 350px;
  height: 100%;
  background: rgba(15, 23, 42, 0.95);
  backdrop-filter: blur(10px);
  border-left: 1px solid rgba(59, 130, 246, 0.3);
  padding: 60px 1rem 1rem;
  overflow-y: auto;
  z-index: 90;
}

/* 节点详情样式 */
.node-details {
  color: #e2e8f0;
}

.node-header {
  position: relative;
  padding-bottom: 1rem;
  border-bottom: 1px solid rgba(59, 130, 246, 0.3);
  margin-bottom: 1rem;
}

.node-header h3 {
  color: #3b82f6;
  margin: 0 0 0.5rem;
  text-shadow: 0 0 5px rgba(59, 130, 246, 0.5);
}

.node-type {
  display: inline-block;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.3);
  color: #3b82f6;
  margin-right: 0.5rem;
}

.subnode-tag {
  display: inline-block;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.7rem;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #ccc;
}

.close-btn {
  position: absolute;
  top: 0;
  right: 0;
  background: none;
  border: none;
  color: #ccc;
  cursor: pointer;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.node-description {
  background: rgba(30, 41, 59, 0.3);
  padding: 1rem;
  border-radius: 6px;
  margin-bottom: 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.node-description p {
  margin: 0;
  line-height: 1.6;
  color: #e2e8f0;
  font-size: 0.95rem;
}

.node-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.stat-item {
  background: rgba(30, 41, 59, 0.5);
  padding: 0.8rem 0.5rem;
  border-radius: 6px;
  text-align: center;
  border: 1px solid rgba(255, 255, 255, 0.05);
  transition: transform 0.2s;
}

.stat-item:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}

.stat-label {
  display: block;
  font-size: 0.8rem;
  color: #94a3b8;
  margin-bottom: 0.3rem;
}

.stat-value {
  font-size: 1.1rem;
  font-weight: bold;
  color: #fff;
}

.hierarchy-info {
  margin-bottom: 1.5rem;
  background: rgba(30, 41, 59, 0.3);
  padding: 1rem;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.hierarchy-info h4 {
  color: #3b82f6;
  margin: 0 0 1rem;
  font-size: 1.05rem;
}

.hierarchy-links {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.hierarchy-item {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
}

.relation-label {
  color: #94a3b8;
  font-size: 0.9rem;
  min-width: 70px;
}

.subnodes-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.subnode-item {
  background: rgba(59, 130, 246, 0.1);
  padding: 0.2rem 0.6rem;
  border-radius: 4px;
  font-size: 0.85rem;
  color: #e2e8f0;
  cursor: pointer;
  transition: all 0.2s;
}

.subnode-item:hover {
  background: rgba(59, 130, 246, 0.2);
  color: #fff;
}

.chart-container {
  height: 220px;
  margin-bottom: 1.5rem;
  background: rgba(30, 41, 59, 0.5);
  padding: 1rem;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.chart-container h4 {
  margin: 0 0 1rem;
  color: #e2e8f0;
  font-size: 0.95rem;
}

.relations-list h4 {
  margin: 0 0 1rem;
  color: #e2e8f0;
  font-size: 0.95rem;
}

.relations-list ul {
  list-style: none;
  padding: 0;
  margin: 0;
  max-height: 250px;
  overflow-y: auto;
}

.relations-list li {
  padding: 0.8rem;
  margin-bottom: 0.5rem;
  background: rgba(30, 41, 59, 0.3);
  border-radius: 4px;
  border-left: 3px solid #3b82f6;
  cursor: pointer;
  transition: all 0.2s;
}

.relations-list li:hover {
  background: rgba(30, 41, 59, 0.7);
  transform: translateX(5px);
}

.relation-type {
  display: inline-block;
  font-size: 0.8rem;
  color: #3b82f6;
  margin-right: 0.5rem;
  background: rgba(59, 130, 246, 0.1);
  padding: 0.1rem 0.3rem;
  border-radius: 3px;
}

.related-node {
  color: #e2e8f0;
}

/* 默认面板组件样式 */
.default-panel {
  color: #e2e8f0;
  height: 100%;
  box-sizing: border-box;
}

.panel-header {
  text-align: center;
  padding: 1.5rem 0;
  border-bottom: 1px solid rgba(59, 130, 246, 0.3);
  margin-bottom: 1.5rem;
}

.panel-header h3 {
  color: #3b82f6;
  margin: 0 0 0.5rem;
  text-shadow: 0 0 5px rgba(59, 130, 246, 0.5);
  font-size: 1.3rem;
}

.panel-subtitle {
  color: #94a3b8;
  font-size: 0.9rem;
  opacity: 0.9;
}

.graph-intro {
  padding: 0 0.5rem;
}

.graph-intro p {
  color: #e2e8f0;
  line-height: 1.6;
  margin-bottom: 1.5rem;
  font-size: 0.95rem;
}

.entity-types {
  margin-bottom: 2rem;
  background: rgba(30, 41, 59, 0.3);
  padding: 1rem;
  border-radius: 6px;
}

.entity-types h4 {
  color: #3b82f6;
  margin: 0 0 1rem;
  font-size: 1.1rem;
}

.entity-type-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: 1rem;
  padding: 0.5rem 0;
  border-bottom: 1px dashed rgba(255, 255, 255, 0.05);
}

.entity-type-item:last-child {
  margin-bottom: 0;
  border-bottom: none;
}

.type-color {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  margin-right: 0.8rem;
  margin-top: 0.3rem;
  box-shadow: 0 0 8px currentColor;
}

.type-info {
  flex: 1;
}

.type-info strong {
  color: #e2e8f0;
  display: block;
  margin-bottom: 0.3rem;
}

.type-info p {
  margin: 0;
  font-size: 0.85rem;
  color: #94a3b8;
  line-height: 1.5;
}

.graph-stats {
  margin-bottom: 2rem;
  background: rgba(30, 41, 59, 0.3);
  padding: 1rem;
  border-radius: 6px;
}

.graph-stats h4 {
  color: #3b82f6;
  margin: 0 0 1rem;
  font-size: 1.1rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.8rem;
}

.stat-box {
  background: rgba(15, 23, 42, 0.5);
  padding: 1rem 0.5rem;
  border-radius: 6px;
  text-align: center;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.stat-number {
  font-size: 1.5rem;
  font-weight: bold;
  color: #3b82f6;
  margin-bottom: 0.3rem;
}

.stat-name {
  font-size: 0.8rem;
  color: #94a3b8;
}

.operation-guide {
  background: rgba(30, 41, 59, 0.3);
  padding: 1rem;
  border-radius: 6px;
}

.operation-guide h4 {
  color: #3b82f6;
  margin: 0 0 1rem;
  font-size: 1.1rem;
}

.operation-guide ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.operation-guide li {
  margin-bottom: 0.8rem;
  display: flex;
  align-items: center;
  color: #e2e8f0;
  font-size: 0.9rem;
}

.operation-guide li:last-child {
  margin-bottom: 0;
}

.operation-guide i {
  color: #3b82f6;
  margin-right: 0.8rem;
  width: 20px;
  text-align: center;
}

/* 网格背景效果 */
.network-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-size: 50px 50px;
  background-image: 
    linear-gradient(to right, rgba(59, 130, 246, 0.05) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(59, 130, 246, 0.05) 1px, transparent 1px);
  pointer-events: none;
  z-index: -1;
  animation: gridPulse 10s infinite alternate;
}

@keyframes gridPulse {
  from { opacity: 0.5; }
  to { opacity: 1; }
}

/* 节点样式优化 */
:deep(.vis-network .vis-node .vis-label) {
  white-space: pre-line !important;
  line-height: 1.4 !important;
  font-weight: 500 !important;
  transition: font-size 0.3s ease !important;
}

/* 节点类型标签样式 */
:deep(.vis-network .vis-node .vis-label span:nth-child(2)) {
  font-size: 10px !important;
  color: rgba(255, 255, 255, 0.9) !important;
  font-style: italic !important;
  font-weight: normal !important;
}

/* 子节点样式调整 */
:deep(.vis-network .vis-node[data-is-subnode="true"]) {
  opacity: 0.9 !important;
}

/* 层级关系边样式（虚线） */
:deep(.vis-network .vis-edge.vis-dashed) {
  opacity: 0.7 !important;
}

/* 节点选中高亮效果 */
:deep(.vis-network .vis-node.vis-selected) {
  box-shadow: 0 0 15px 2px white !important;
  transform: scale(1.1) !important;
  transition: transform 0.3s ease !important;
}

/* 自定义Tooltip样式 */
:deep(.vis-network-tooltip) {
  border-radius: 6px !important;
  border: none !important;
  box-shadow: 0 5px 15px rgba(0,0,0,0.3) !important;
  padding: 0 !important;
  overflow: hidden !important;
}
</style>