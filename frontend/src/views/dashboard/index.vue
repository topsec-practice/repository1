<template>
  <div class="dashboard-container">
    <!-- 顶部搜索框 -->
    <div class="search-bar">
      <el-input
        v-model="searchQuery"
        placeholder="输入用户名或ID搜索"
        clearable
        style="width: 300px"
        @keyup.enter="handleSearch"
      >
        <template #append>
          <el-button icon="el-icon-search" @click="handleSearch" />
        </template>
      </el-input>
    </div>

    <!-- 用户状态表格 -->
    <el-table 
      :data="filteredUserList" 
      style="width: 100%" 
      border
      highlight-current-row
      @row-click="handleRowClick"
    >
      <el-table-column prop="id" label="用户ID" align="center" />
      <el-table-column prop="name" label="用户名" align="center" />
      <el-table-column prop="key" label="用户密码" align="center" />
      <el-table-column prop="LastEchoTime" label="最后登录时间" align="center" />
      <el-table-column prop="LastScanTime" label="最后扫描时间" align="center" />
      <el-table-column prop="IP" label="ip" align="center" />
      <el-table-column prop="status" label="状态" align="center">
        <template #default="{ row }">
          <el-tag 
            :type="row.status === 'online' ? 'success' : 'info'"
            effect="dark"
          >
            {{ row.status === 'online' ? '在线' : '离线' }}
          </el-tag>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script>
import { StatusInfo } from '@/api/statusinfo';

export default {
  name: 'UserStatus',
  data() {
    return {
      searchQuery: '',
      userList: null
    }
  },
  computed: {
    filteredUserList() {
      if (!this.searchQuery) return this.userList
      const query = this.searchQuery.toLowerCase()
      return this.userList.filter(
        user => 
          user.name.toLowerCase().includes(query) || 
          user.id.toString().includes(query)
      )
    }
  },
  created() {
    this.fetchData()
  },
  methods: {
    handleSearch() {
      console.log('当前搜索词:', this.searchQuery)
    },
    fetchData() {
      this.listLoading = true
      StatusInfo().then(response => {
        this.userList = response.data.items
      })
    },
    // handleRowClick(row) {
    //   // 跳转到敏感信息页面并传递用户ID
    //   this.$router.push({
    //     path: '/example/tree',
    //     query: { userId: row.id }
    //   })
    // }
    handleRowClick(row) {
      // 使用命名路由跳转
      this.$router.push({
        name: 'Tree',  // 使用路由名称而不是路径
        query: { userId: row.id }
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.dashboard-container {
  margin: 30px;
  
  .search-bar {
    margin-bottom: 20px;
    display: flex;
    justify-content: flex-end;
  }

  .el-table {
    margin-top: 10px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
    
    ::v-deep .el-table__cell {
      padding: 12px 0;
    }
    
    // 添加行点击效果
    ::v-deep .el-table__row {
      cursor: pointer;
      &:hover {
        background-color: #f5f7fa;
      }
    }
  }

  .el-tag {
    font-weight: bold;
    min-width: 60px;
    text-align: center;
  }
}
</style>