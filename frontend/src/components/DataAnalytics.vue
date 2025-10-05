<template>
  <div class="analytics-container">
    <div class="analytics-header">
      <h2>跌倒检测数据分析</h2>
      <div class="date-filter">
        <label for="date-range">时间范围:</label>
        <select id="date-range" v-model="dateRange">
          <option value="30day">近30天</option>
          <option value="7days">近7天</option>
          <option value="90day">近90天</option>
          <option value="all">全部数据</option>
        </select>
      </div>
    </div>
    
    <!-- 核心指标卡片 -->
    <div class="metrics-grid">
      <div class="metric-card">
        <div class="metric-title">总检测次数</div>
        <div class="metric-value">7,490</div>
        <div class="metric-change positive">
          <i class="fas fa-arrow-up"></i> 2.3% 较上期
        </div>
      </div>
      
      <div class="metric-card">
        <div class="metric-title">跌倒事件数</div>
        <div class="metric-value">183</div>
        <div class="metric-change positive">
          <i class="fas fa-arrow-up"></i> 2.3% 较上期
        </div>
      </div>
      
      <div class="metric-card">
        <div class="metric-title">平均检测准确率</div>
        <div class="metric-value">93.09%</div>
        <div class="metric-change positive">
          <i class="fas fa-arrow-up"></i> 1.3% 较上期
        </div>
      </div>
      
      <div class="metric-card">
        <div class="metric-title">平均响应时间</div>
        <div class="metric-value">264.85ms</div>
        <div class="metric-change negative">
          <i class="fas fa-arrow-down"></i> 3.6% 较上期
        </div>
      </div>
    </div>
    
    <!-- 固定图表区域 -->
    <div class="charts-container">
      <div class="charts-grid">
        <!-- 1. 检测趋势分析（完全写死折线图） -->
        <div class="chart-card">
          <h3>检测趋势分析</h3>
          <div class="chart-legend">
            <div class="legend-item">
              <span class="legend-color" style="background-color: #667eea;"></span>
              <span class="legend-text">总检测次数</span>
            </div>
            <div class="legend-item">
              <span class="legend-color" style="background-color: #e74c3c;"></span>
              <span class="legend-text">跌倒事件数</span>
            </div>
          </div>
          <canvas ref="detectionTrendChart"></canvas>
        </div>
        
        <!-- 2. 跌倒事件分布（完全写死饼图） -->
        <div class="chart-card">
          <h3>跌倒事件分布</h3>
          <canvas ref="fallDistributionChart"></canvas>
          <!-- 固定弹窗数据 -->
          <div v-if="showPieDetail" class="pie-detail-popup">
            <div class="popup-header">
              <h4>{{ pieDetail.scene }}</h4>
              <button class="close-popup" @click="showPieDetail = false">×</button>
            </div>
            <div class="popup-content">
              <p><strong>跌倒事件数：</strong>{{ pieDetail.count }}</p>
              <p><strong>占比：</strong>{{ pieDetail.percentage }}%</p>
              <p><strong>平均处理时间：</strong>{{ pieDetail.avgHandleTime }}分钟</p>
              <p><strong>高发时段：</strong>{{ pieDetail.highRiskTime }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { 
  Chart, CategoryScale, LinearScale, PointElement, LineElement, 
  LineController, ArcElement, PieController, Tooltip, Legend, Filler
} from 'chart.js'

// 注册Chart.js必要组件
Chart.register(
  CategoryScale, LinearScale, PointElement, LineElement, LineController,
  ArcElement, PieController, Tooltip, Legend, Filler
)

// 图表DOM引用
const detectionTrendChart = ref(null)
const fallDistributionChart = ref(null)

// 饼图弹窗状态（固定数据）
const showPieDetail = ref(false)
const pieDetail = ref({
  scene: '',
  count: 0,
  percentage: 0,
  avgHandleTime: '',
  highRiskTime: ''
})

// 时间范围（仅展示，不影响图表）
const dateRange = ref('30day')

// ---------------------------
// 完全固定的折线图数据（写死）
// ---------------------------
const fixedTrendData = {
  labels: ['9-26', '9-27', '9-28', '9-29', '9-30', '10-1', '10-2', '10-3', '10-4', '10-5'],
  detectionData: [220, 235, 242, 250, 265, 278, 282, 290, 285, 295], // 总检测次数
  fallData: [5, 6, 4, 7, 8, 9, 7, 10, 8, 9] // 跌倒事件数
}

// ---------------------------
// 完全固定的饼图数据（写死）
// ---------------------------
const fixedPieData = {
  labels: ['居家环境', '医院病房', '养老院', '公共场所'],
  values: [65, 42, 50, 26], // 各场景跌倒数
  colors: ['#667eea', '#764ba2', '#3498db', '#e67e22'], // 固定颜色
  details: {
    '居家环境': { avg: '8.2', time: '18:00-22:00' },
    '医院病房': { avg: '4.5', time: '22:00-06:00' },
    '养老院': { avg: '6.3', time: '08:00-10:00, 15:00-17:00' },
    '公共场所': { avg: '10.7', time: '10:00-12:00, 16:00-18:00' }
  }
}
// 固定占比计算
const totalFalls = fixedPieData.values.reduce((a, b) => a + b, 0)
const piePercentages = fixedPieData.values.map(v => ((v / totalFalls) * 100).toFixed(1))

// 初始化折线图（完全写死，无动态逻辑）
const initDetectionTrend = () => {
  // 销毁旧实例（如果存在）
  if (window.detectionChart) window.detectionChart.destroy()
  
  // 创建新图表（使用固定数据）
  window.detectionChart = new Chart(detectionTrendChart.value, {
    type: 'line',
    data: {
      labels: '检测趋势',
      labels: fixedTrendData.labels,
      datasets: [
        {
          label: '总检测次数',
          data: fixedTrendData.detectionData,
          borderColor: '#667eea',
          backgroundColor: 'rgba(102, 126, 234, 0.1)',
          borderWidth: 2,
          tension: 0.4,
          fill: true,
          pointBackgroundColor: '#667eea',
          pointRadius: 4,
          yAxisID: 'y'
        },
        {
          label: '跌倒事件数',
          data: fixedTrendData.fallData,
          borderColor: '#e74c3c',
          backgroundColor: 'rgba(231, 76, 60, 0.1)',
          borderWidth: 2,
          tension: 0.4,
          fill: true,
          pointBackgroundColor: '#e74c3c',
          pointRadius: 4,
          yAxisID: 'y1'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false },           ticks: { maxRotation: 0 } },
        y: { beginAtZero: true, title: { display: true, text: '检测次数' } },
        y1: { 
          beginAtZero: true, 
          position: 'right', 
          title: { display: true, text: '跌倒事件' },
          grid: { display: false } 
        }
      },
      // 禁止图表修改
      animation: false,
      responsive: true
    }
  })
}

// 初始化饼图（完全写死，无动态逻辑）
const initFallDistribution = () => {
  // 销毁旧实例（如果存在）
  if (window.pieChart) window.pieChart.destroy()
  
  // 创建新图表（使用固定数据）
  window.pieChart = new Chart(fallDistributionChart.value, {
    type: 'pie',
    data: {
      labels: fixedPieData.labels,
      datasets: [{
        data: fixedPieData.values,
        backgroundColor: fixedPieData.colors,
        borderColor: '#fff',
        borderWidth: 2,
        hoverOffset: 10
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: {
            padding: 15,
            font: { size: 12 },
            generateLabels: () => {
              return fixedPieData.labels.map((label, i) => ({
                text: `${label} (${piePercentages[i]}%)`,
                fillStyle: fixedPieData.colors[i],
                strokeStyle: '#fff',
                lineWidth: 2,
                hidden: false,
                index: i
              }))
            }
          }
        },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.label}: ${fixedPieData.values[ctx.dataIndex]} 次 (${piePercentages[ctx.dataIndex]}%)`
          }
        }
      },
      onClick: (e, elements) => {
        if (elements.length) {
          const i = elements[0].index
          pieDetail.value = {
            scene: fixedPieData.labels[i],
            count: fixedPieData.values[i],
            percentage: piePercentages[i],
            avgHandleTime: fixedPieData.details[fixedPieData.labels[i]].avg,
            highRiskTime: fixedPieData.details[fixedPieData.labels[i]].time
          }
          showPieDetail.value = true
        }
      },
      // 禁止图表修改
      animation: false
    }
  })
}

// 页面加载时初始化图表（仅一次，不随任何操作重复执行）
onMounted(() => {
  nextTick(() => {
    initDetectionTrend()
    initFallDistribution()
  })
})
</script>

<style scoped>
.analytics-container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto; /* 整体居中 */
  padding: 20px;
  box-sizing: border-box;
}

.analytics-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 30px;
}

.metric-card {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.metric-title {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
  margin-bottom: 5px;
}

.metric-change {
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 5px;
}

.positive { color: #2ecc71; }
.negative { color: #e74c3c; }

/* 图表区域（固定居中） */
.charts-container {
  display: flex;
  justify-content: center;
  width: 100%;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 30px;
  width: 100%;
}

.chart-card {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  min-height: 400px; /* 固定高度确保图表完整显示 */
  position: relative;
}

.chart-card canvas {
  width: 100% !important;
  height: 320px !important; /* 固定图表高度 */
}

.chart-legend {
  margin-bottom: 15px;
  display: flex;
  gap: 15px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 3px;
}

/* 饼图弹窗样式 */
.pie-detail-popup {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: white;
  border-radius: 6px;
  box-shadow: 0 3px 15px rgba(0,0,0,0.1);
  width: 80%;
  max-width: 280px;
  padding: 15px;
  z-index: 10;
}

.popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.close-popup {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  color: #999;
}
</style>