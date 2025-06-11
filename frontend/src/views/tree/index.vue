<template>
  <div class="dashboard-container">
    <!-- 顶部搜索框 -->
    <div class="search-bar">
      <el-input
        v-model="filterText"
        placeholder="搜索规则ID、策略ID、文件ID或用户ID"
        clearable
        style="width: 300px"
        @input="handleSearch"
      >
        <template #append>
          <el-button icon="el-icon-search" />
        </template>
      </el-input>
    </div>

    <el-table
      v-loading="listLoading"
      :data="filteredMatches"
      element-loading-text="加载中..."
      border
      fit
      highlight-current-row
    >
      <el-table-column label="策略ID" prop="policy_id" width="180" align="center">
        <template #default="{row}">
          <el-tag>{{ row.policy_id }}</el-tag>
        </template>
      </el-table-column>

      <el-table-column label="规则ID" prop="rule_id" width="180" align="center" />

      <el-table-column label="文件ID" prop="file_id" width="180" align="center" />

      <el-table-column label="用户ID" prop="user_id" width="180" align="center" />
    </el-table>

    <el-pagination
      background
      layout="prev, pager, next"
      :total="filteredTotal"
      :page-size="pageSize"
      @current-change="handlePageChange"
      style="margin-top: 20px;"
    />
  </div>
</template>

<script>
import { getMatchesList } from '@/api/matches'

export default {
  name: 'MatchesList',
  data() {
    return {
      filterText: '',
      listLoading: false,
      matchesList: [], // 从数据库获取的原始数据
      filteredList: [], // 过滤后的完整列表
      filteredMatches: [], // 当前页显示的数据
      pageSize: 10
    }
  },
  computed: {
    filteredTotal() {
      return this.filteredList.length
    }
  },
  created() {
    this.fetchData()
  },
  methods: {
    fetchData() {
      this.listLoading = true
      getMatchesList().then(response => {
        this.matchesList = response.data.items
        this.filteredList = this.matchesList
        this.handlePageChange(1)
        this.listLoading = false
      }).catch(() => {
        this.listLoading = false
      })
    },
    handleSearch() {
      if (!this.filterText) {
        this.filteredList = this.matchesList
      } else {
        const searchText = this.filterText.toLowerCase()
        this.filteredList = this.matchesList.filter(item => {
          return (
            (item.policy_id && item.policy_id.toLowerCase().includes(searchText)) ||
            (item.rule_id && item.rule_id.toLowerCase().includes(searchText)) ||
            (item.file_id && item.file_id.toLowerCase().includes(searchText)) ||
            (item.user_id && item.user_id.toLowerCase().includes(searchText))
          )
        })
      }
      this.handlePageChange(1) // 搜索后重置到第一页
    },
    handlePageChange(page) {
      const start = (page - 1) * this.pageSize
      const end = start + this.pageSize
      this.filteredMatches = this.filteredList.slice(start, end)
    }
  }
}
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
}

.search-bar {
  margin-bottom: 20px;
}
</style>