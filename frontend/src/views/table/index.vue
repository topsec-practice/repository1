<template>
  <div class="app-container">
    <div class="sort-controls">
      <el-button-group>
        <el-button 
          type="primary" 
          :icon="sortOrder === 'descending' ? 'el-icon-sort-down' : 'el-icon-sort-up'"
          @click="toggleSortOrder"
        >
          {{ sortOrder === 'descending' ? '降序 ▼' : '升序 ▲' }}
        </el-button>
        <el-tooltip content="恢复默认排序" placement="top">
          <el-button 
            icon="el-icon-refresh" 
            @click="resetSort"
          />
        </el-tooltip>
      </el-button-group>
    </div>

    <el-table
      v-loading="listLoading"
      :data="sortedList" 
      element-loading-text="加载中..."
      border
      fit
      highlight-current-row
      :row-class-name="tableRowClassName"
      @sort-change="handleSortChange"
    >
      <!-- 序号列：直接显示 sortIndex -->
      <el-table-column 
        align="center" 
        label="序号" 
        width="95"
        prop="sortIndex"
        sortable
        :sort-orders="['descending', 'ascending']"
      >
        <template slot-scope="scope">
          {{ scope.row.sortIndex }} <!-- 直接显示 sortIndex -->
        </template>
      </el-table-column>

      <el-table-column label="文件名和简介">
        <template slot-scope="scope">
          {{ scope.row.title }}
        </template>
      </el-table-column>

      <el-table-column label="用户ID" width="110" align="center">
        <template slot-scope="scope">
          <span>{{ scope.row.author }}</span>
        </template>
      </el-table-column>

      <el-table-column label="ID" width="110" align="center">
        <template slot-scope="scope">
          {{ scope.row.id }}
        </template>
      </el-table-column>

      <el-table-column class-name="status-col" label="MD5" width="110" align="center">
        <template slot-scope="scope">
          {{ scope.row.md5 }}
        </template>
      </el-table-column>

      <el-table-column class-name="status-col" label="敏感信息个数" width="110" align="center">
        <template slot-scope="scope">
          {{ scope.row.pageviews }}
        </template>
      </el-table-column>

      <el-table-column align="center" prop="created_at" label="发现时间" width="200">
        <template slot-scope="scope">
          <i class="el-icon-time" />
          <span>{{ scope.row.display_time }}</span>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script>
import { getList } from '@/api/table'

export default {
  data() {
    return {
      list: null,
      listLoading: true,
      sortProp: 'sortIndex',   // 固定按 sortIndex 排序
      sortOrder: 'descending'  // 默认降序
    }
  },
  computed: {
    sortedList() {
      if (!this.list) return []
      
      // 为数据分配 sortIndex（假设数据本身已有 sortIndex 字段）
      // 如果数据没有 sortIndex，可以用 id 或其他唯一值替代
      const listWithIndex = this.list.map(item => ({
        ...item,
        sortIndex: item.sortIndex || item.id // 优先用 sortIndex，没有则用 id
      }))
      
      // 按 sortIndex 排序
      return listWithIndex.sort((a, b) => {
        return this.sortOrder === 'descending' 
          ? b.sortIndex - a.sortIndex // 降序：9,8,7...
          : a.sortIndex - b.sortIndex // 升序：1,2,3...
      })
    }
  },
  methods: {
    // 切换排序方向
    toggleSortOrder() {
      this.sortOrder = this.sortOrder === 'descending' ? 'ascending' : 'descending'
    },
    // 重置排序
    resetSort() {
      this.sortOrder = 'descending'
    },
    // 处理排序事件（Element UI 触发）
    handleSortChange({ prop, order }) {
      this.sortProp = prop
      this.sortOrder = order
    },
    // 行样式方法
    tableRowClassName({ rowIndex }) {
      return rowIndex % 2 === 0 ? '偶数行' : '奇数行'
    },
    // 获取数据
    fetchData() {
      this.listLoading = true
      getList().then(response => {
        this.list = response.data.items
        this.listLoading = false
      })
    }
  },
  created() {
    this.fetchData()
  }
}
</script>

<style scoped>
/* 排序控制按钮样式 */
.sort-controls {
  margin-bottom: 15px;
  display: flex;
  justify-content: flex-end;
}

.app-container {
  padding: 20px;
}

/* 偶数行样式 */
.el-table >>> .偶数行 {
  background-color: #ffffff;
}

/* 奇数行样式 */
.el-table >>> .奇数行 {
  background-color: #f5f7fa; /* 青灰色 */
}

/* 表头样式 */
.el-table >>> th {
  background-color: #f5f7fa !important;
  color: #333;
  font-weight: bold;
}

/* 单元格样式 */
.el-table >>> td, .el-table >>> th {
  padding: 12px 0;
  border-color: #ebeef5;
}

/* 鼠标悬停效果 */
.el-table >>> .el-table__body tr:hover > td {
  background-color: #e6f7ff !important;
}
</style>