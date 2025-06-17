<template>
  <div class="app-container">
    <!-- 策略提交模块 -->
    <el-card class="box-card" style="margin-bottom: 20px;">
      <div slot="header" class="clearfix">
        <span>策略提交</span>
      </div>
      
      <el-form ref="form" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="策略内容" prop="strategy">
          <el-input
            v-model="form.strategy"
            type="textarea"
            :rows="3"
            placeholder="请输入您的策略"
            clearable
          ></el-input>
        </el-form-item>
        
        <el-form-item>
          <el-button 
            type="primary" 
            :loading="submitting"
            @click="submitForm"
          >
            提交策略
          </el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 策略列表模块 -->
    <el-card class="box-card">
      <div slot="header" class="clearfix">
        <span>策略列表</span>
        <el-input
          v-model="searchQuery"
          placeholder="搜索策略"
          style="width: 200px; float: right;"
          @keyup.enter.native="fetchPolicies"
        >
          <el-button slot="append" icon="el-icon-search" @click="fetchPolicies"></el-button>
        </el-input>
      </div>
      
      <el-table
        :data="sortedPolicyList"
        style="width: 100%"
        v-loading="loading"
      >
        <el-table-column
          prop="policy_id"
          label="策略ID"
          width="180"
        ></el-table-column>
        
        <el-table-column
          prop="description"
          label="策略描述"
        ></el-table-column>
        
        <el-table-column
          label="操作"
          width="180"
        >
          <template slot-scope="scope">
            <el-button
              size="mini"
              @click="handleViewRules(scope.row)"
            >查看规则</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <el-pagination
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        :current-page="currentPage"
        :page-sizes="[10, 20, 30, 50]"
        :page-size="pageSize"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
      ></el-pagination>
    </el-card>
  </div>
</template>

<script>
import { submitStrategy } from '@/api/Strategy'
import { getPolicyList } from '@/api/policy'

export default {
  name: 'StrategyPage',
  data() {
    return {
      // 策略提交模块数据
      form: {
        strategy: ''
      },
      rules: {
        strategy: [
          { required: true, message: '请输入策略内容', trigger: 'blur' },
          { max: 200, message: '策略内容不能超过200个字符', trigger: 'blur' }
        ]
      },
      submitting: false,
      
      // 策略列表模块数据
      policyList: [],
      searchQuery: '',
      loading: false,
      currentPage: 1,
      pageSize: 10,
      total: 0
    }
  },

  computed: {
    // 新增计算属性，用于反向排序策略列表
    sortedPolicyList() {
      return [...this.policyList].sort((a, b) => {
        // 将policy_id转为数字比较
        const idA = parseInt(a.policy_id)
        const idB = parseInt(b.policy_id)
        return idB - idA  // 降序排列
      })
    }
  },

  created() {
    this.fetchPolicies()
  },
  methods: {
    // 策略提交模块方法
    submitForm() {
  this.$refs.form.validate(valid => {
    if (valid) {
      this.submitting = true
      
      submitStrategy(this.form.strategy)
        .then(response => {
          this.$message.success('策略提交成功！策略ID: ' + response.data.policy_id)
          this.resetForm()
          this.fetchPolicies() // 刷新策略列表
        })
        .catch(error => {
          console.error('提交失败:', error)
          this.$message.error('策略提交失败，请重试')
        })
        .finally(() => {
          this.submitting = false
        })
    } else {
      return false
    }
  })
},
    resetForm() {
      this.$refs.form.resetFields()
    },
    
    // 策略列表模块方法
    fetchPolicies() {
      this.loading = true
      const params = {
        page: this.currentPage,
        limit: this.pageSize
      }
      
      if (this.searchQuery) {
        params.search = this.searchQuery
      }
      
      getPolicyList(params).then(response => {
        this.policyList = response.data.items
        this.total = response.data.total
        this.loading = false
      }).catch(() => {
        this.loading = false
      })
    },
    handleViewRules(row) {
      this.$router.push({
        path: '/rules',
        query: { policy_id: row.policy_id }
      })
    },
    handleSizeChange(val) {
      this.pageSize = val
      this.fetchPolicies()
    },
    handleCurrentChange(val) {
      this.currentPage = val
      this.fetchPolicies()
    }
  }
}
</script>

<style scoped>
.box-card {
  max-width: 800px;
  margin: 0 auto;
}
.clearfix:before,
.clearfix:after {
  display: table;
  content: "";
}
.clearfix:after {
  clear: both;
}
</style>