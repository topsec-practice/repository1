<template>
  <div class="app-container">
    <el-table
      v-loading="listLoading"
      :data="list"
      element-loading-text="加载中..."
      border
      fit
      highlight-current-row
      :row-class-name="tableRowClassName"
    >
      <el-table-column align="center" label="序号" width="95">
        <template slot-scope="scope">
          {{ scope.$index + 1 }}
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
  filters: {
    statusFilter(status) {
      const statusMap = {
        published: 'success',
        draft: 'gray',
        deleted: 'danger'
      }
      return statusMap[status]
    }
  },
  data() {
    return {
      list: null,
      listLoading: true
    }
  },
  created() {
    this.fetchData()
  },
  methods: {
    fetchData() {
      this.listLoading = true
      getList().then(response => {
        this.list = response.data.items
        this.listLoading = false
      })
    },
    // 行样式分类方法
    tableRowClassName({ rowIndex }) {
      return rowIndex % 2 === 0 ? '偶数行' : '奇数行'
    }
  }
}
</script>

<style scoped>
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