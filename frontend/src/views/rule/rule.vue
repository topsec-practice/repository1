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
        @selection-change="handleSelectionChange"
        :default-sort="{prop: 'rule_id', order: 'ascending'}"
      >
        <el-table-column
          type="selection"
          width="55"
        ></el-table-column>
        
        <el-table-column
          prop="rule_id"
          label="规则ID"
          width="180"
          sortable
        ></el-table-column>
        
        <el-table-column
          prop="rule_description"
          label="规则类型"
        >
          <template slot-scope="scope">
            {{ getRuleName(scope.row.rule_description) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script>
import { getRulesByPolicyId,} from '@/api/rules'

export default {
  name: 'RulesPage',
  data() {
    return {
      policyId: '',
      ruleList: [],
      loading: false,
      selectedRules: [], // 表格中选中的规则
      
      // 规则映射
      ruleNameMap: {
        1: {key: 'phone', name: '手机号码'},
        2: {key: 'ip', name: 'IPv4地址'},
        3: {key: 'mac', name: 'MAC地址'},
        4: {key: 'ipv6', name: 'IPv6地址'},
        5: {key: 'bank_card', name: '银行卡号'},
        6: {key: 'email', name: '电子邮件地址'},
        7: {key: 'passport', name: '护照号码'},
        8: {key: 'id_number', name: '身份证号码'},
        9: {key: 'gender', name: '性别信息'},
        10: {key: 'national', name: '民族信息'},
        11: {key: 'carnum', name: '车牌号码'},
        12: {key: 'telephone', name: '固定电话号码'},
        13: {key: 'officer', name: '军官证号码'},
        14: {key: 'HM_pass', name: '港澳通行证号码'},
        15: {key: 'jdbc', name: 'JDBC连接字符串'},
        16: {key: 'organization', name: '组织机构代码'},
        17: {key: 'business', name: '工商注册号'},
        18: {key: 'credit', name: '统一社会信用代码'},
        19: {key: 'address_name', name: '中文地址和姓名'}
      }
    }
  },
  created() {
    this.policyId = this.$route.query.policy_id
    this.fetchRules()
  },
  methods: {
    getRuleName(ruleKey) {
      const rule = Object.values(this.ruleNameMap).find(item => item.key === ruleKey)
      if (rule) {
        return `${rule.key} - ${rule.name}`
      }
      return `${ruleKey} - 未知规则`
    },
    
    fetchRules() {
      this.loading = true
      getRulesByPolicyId(this.policyId)
        .then(response => {
          this.ruleList = response.data.items || []
        })
        .finally(() => {
          this.loading = false
        })
    },
    
    goBack() {
      this.$router.push('/form/index')
    },
    
    handleSelectionChange(val) {
      this.selectedRules = val.map(item => item.rule_id)
    },
  }
}
</script>


<style scoped>
.box-card {
  max-width: 1200px;
  margin: 0 auto;
}

.el-table {
  margin-top: 20px;
}
</style>