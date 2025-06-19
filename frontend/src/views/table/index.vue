<template>
  <div class="app-container">
    <el-card>
      <div slot="header" class="clearfix">
        <span>上传日志</span>
      </div>
      <el-table
        v-loading="loading"
        :data="logList"
        border
        style="width: 100%"
      >
        <el-table-column prop="time" label="上报时间" width="180" />
        <el-table-column prop="user_id" label="用户ID" width="100" />
        <el-table-column prop="file_name" label="文件名" width="180" />
        <el-table-column prop="md5" label="MD5" width="160" />
        <el-table-column prop="count" label="敏感信息个数" width="120" />
        <el-table-column prop="rule_id" label="规则ID" width="120">
          <template slot-scope="scope">
            <span v-if="Array.isArray(scope.row.rule_id)">
              {{ scope.row.rule_id.join(', ') }}
            </span>
            <span v-else>{{ scope.row.rule_id }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="policy_id" label="策略ID" width="100" />
        <el-table-column prop="discovery_time" label="发现时间" width="180" />
        <el-table-column label="操作" width="120">
          <template slot-scope="scope">
            {{ flagText(scope.row.flag) }}
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        style="margin-top: 20px; text-align: right;"
        background
        layout="total, prev, pager, next, jumper"
        :total="total"
        :page-size="pageSize"
        :current-page="currentPage"
        @current-change="handlePageChange"
      />
    </el-card>
  </div>
</template>

<script>
import request from '@/utils/request'

export default {
  name: 'UploadLog',
  data() {
    return {
      logList: [],
      loading: false,
      total: 0,
      pageSize: 20,
      currentPage: 1
    }
  },
  created() {
    this.fetchData()
  },
  methods: {
    fetchData(page = 1) {
      this.loading = true
      request({
        url: '/frontend/uploadlog/list',
        method: 'get',
        params: {
          page,
          limit: this.pageSize
        }
      }).then(res => {
        this.logList = res.data.items
        this.total = res.data.total
        this.currentPage = page
        this.loading = false
      }).catch(() => {
        this.loading = false
      })
    },
    handlePageChange(page) {
      this.fetchData(page)
    },
    flagText(flag) {
      switch (flag) {
        case 0: return '删除'
        case 1: return '更新'
        case 2: return '增添'
        case 3: return '删除件'
        default: return '未知'
      }
    }
  }
}
</script>

<style scoped>
.app-container {
  padding: 20px;
}
</style>