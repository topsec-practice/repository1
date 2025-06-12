<template>
  <div class="app-container">
    <el-card class="box-card">
      <div slot="header" class="clearfix">
        <el-button 
          type="primary" 
          icon="el-icon-arrow-left"
          @click="goBack"
          style="float: left;"
        >
          返回策略列表
        </el-button>
        <span style="margin-left: 20px;">策略ID: {{ policyId }} 的规则列表</span>
      </div>
      
      <el-table
        :data="ruleList"
        style="width: 100%"
        v-loading="loading"
        border
      >
        <el-table-column
          prop="rule_id"
          label="规则ID"
          width="180"
        ></el-table-column>
        
        <el-table-column
          prop="rule_description"
          label="规则描述"
        ></el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script>
import { getRulesByPolicyId } from '@/api/rules'

export default {
  name: 'RulesPage',
  data() {
    return {
      policyId: '',
      ruleList: [],
      loading: false
    }
  },
  created() {
    this.policyId = this.$route.query.policy_id
    this.fetchRules()
  },
  methods: {
    fetchRules() {
      this.loading = true
      getRulesByPolicyId(this.policyId)
        .then(response => {
          this.ruleList = response.data.items
        })
        .catch(error => {
          console.error('获取规则失败:', error)
          this.$message.error('获取规则失败')
        })
        .finally(() => {
          this.loading = false
        })
    },
    goBack() {
      this.$router.push('/')
    }
  }
}
</script>

<style scoped>
.box-card {
  max-width: 1000px;
  margin: 0 auto;
}
</style>