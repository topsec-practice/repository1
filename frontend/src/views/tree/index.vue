<template>
  <div class="dashboard-container">
    <!-- 顶部搜索框和用户ID输入 -->
    <div class="search-bar">
      <el-input
        v-model="userId"
        placeholder="请输入用户ID"
        clearable
        style="width: 200px; margin-right: 10px;"
      />
      <el-button type="primary" @click="fetchData">查询</el-button>
      <el-input
        v-model="filterText"
        placeholder="搜索规则ID、文件ID或用户ID"
        clearable
        style="width: 300px; margin-left: 20px;"
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
      userId: '', // 新增
      filterText: '',
      listLoading: false,
      matchesList: [],
      filteredList: [],
      filteredMatches: [],
      pageSize: 10
    }
  },
  computed: {
    filteredTotal() {
      return this.filteredList.length
    }
  },
  methods: {
    fetchData() {
      if (!this.userId) {
        this.$message.warning('请先输入用户ID')
        return
      }
      this.listLoading = true
      getMatchesList({ user_id: this.userId }).then(response => {
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
            (item.rule_id && String(item.rule_id).toLowerCase().includes(searchText)) ||
            (item.file_id && String(item.file_id).toLowerCase().includes(searchText)) ||
            (item.user_id && String(item.user_id).toLowerCase().includes(searchText))
          )
        })
      }
      this.handlePageChange(1)
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