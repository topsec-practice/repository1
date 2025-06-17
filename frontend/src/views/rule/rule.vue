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
        <div style="float: right;">
          <el-button 
            type="primary" 
            icon="el-icon-plus"
            @click="showCreateDialog"
          >
            添加规则
          </el-button>
          <el-button 
            type="danger" 
            icon="el-icon-delete"
            :disabled="selectedRules.length === 0"
            @click="batchDelete"
          >
            批量删除
          </el-button>
        </div>
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
        
        <el-table-column
          label="操作"
          width="180"
        >
          <template slot-scope="scope">
            <el-button
              size="mini"
              type="danger"
              @click="handleDelete(scope.$index, scope.row)"
            >删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 添加规则对话框 -->
    <el-dialog :title="dialogTitle" :visible.sync="dialogVisible" width="50%">
      <el-form :model="ruleForm" :rules="rules" ref="ruleForm" label-width="100px">
        <el-form-item label="规则类型" prop="selectedRules">
          <el-checkbox-group v-model="ruleForm.selectedRules">
            <el-checkbox 
              v-for="item in ruleOptions" 
              :key="item.value" 
              :label="item.value"
              :disabled="existingRules.includes(item.value)"
            >
              {{ item.label }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button @click="dialogVisible = false">取 消</el-button>
        <el-button type="primary" @click="submitForm">确 定</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import { getRulesByPolicyId, createRule, deleteRule, batchDeleteRules } from '@/api/rules'

export default {
  name: 'RulesPage',
  data() {
    return {
      policyId: '',
      ruleList: [],
      loading: false,
      dialogVisible: false,
      dialogTitle: '添加规则',
      selectedRules: [], // 表格中选中的规则
      
      // 规则选项
      ruleOptions: [
        { value: 1, label: 'phone - 手机号码' },
        { value: 2, label: 'ip - IPv4地址' },
        { value: 3, label: 'mac - MAC地址' },
        { value: 4, label: 'ipv6 - IPv6地址' },
        { value: 5, label: 'bank_card - 银行卡号' },
        { value: 6, label: 'email - 电子邮件地址' },
        { value: 7, label: 'passport - 护照号码' },
        { value: 8, label: 'id_number - 身份证号码' },
        { value: 9, label: 'gender - 性别信息' },
        { value: 10, label: 'national - 民族信息' },
        { value: 11, label: 'carnum - 车牌号码' },
        { value: 12, label: 'telephone - 固定电话号码' },
        { value: 13, label: 'officer - 军官证号码' },
        { value: 14, label: 'HM_pass - 港澳通行证号码' },
        { value: 15, label: 'jdbc - JDBC连接字符串' },
        { value: 16, label: 'organization - 组织机构代码' },
        { value: 17, label: 'business - 工商注册号' },
        { value: 18, label: 'credit - 统一社会信用代码' },
        { value: 19, label: 'address_name - 中文地址和姓名' }
      ],
      
      // 规则映射
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
},
      
      // 表单数据
      ruleForm: {
        selectedRules: [] // 对话框中选中的规则
      },
      
      // 表单验证规则
      rules: {
        selectedRules: [
          { type: 'array', required: true, message: '请至少选择一个规则', trigger: 'change' }
        ]
      }
    }
  },
  computed: {
    // 已存在的规则类型
    existingRules() {
      return this.ruleList.map(rule => {
        const ruleKey = Object.keys(this.ruleNameMap).find(
          key => key === rule.rule_description
        )
        return this.ruleOptions.find(item => item.label.startsWith(ruleKey))?.value
      }).filter(Boolean)
    }
  },
  created() {
    this.policyId = this.$route.query.policy_id
    this.fetchRules()
  },
  methods: {
    // 获取规则名称
    getRuleName(ruleKey) {
  const rule = Object.values(this.ruleNameMap).find(item => item.key === ruleKey);
  if (rule) {
    return `${rule.key} - ${rule.name}`;
  }
  return `${ruleKey} - 未知规则`;
},
    
    // 获取规则列表
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
    
    // 返回策略列表
    goBack() {
      this.$router.push('/form/index')
    },
    
    // 显示创建对话框
    showCreateDialog() {
      this.dialogTitle = '添加规则'
      this.ruleForm.selectedRules = []
      this.dialogVisible = true
      this.$nextTick(() => {
        this.$refs.ruleForm.clearValidate()
      })
    },
    
    // 表格选择变化
    handleSelectionChange(val) {
      this.selectedRules = val.map(item => item.rule_id)
    },
    
    // 批量删除
    batchDelete() {
      this.$confirm(`确认删除选中的 ${this.selectedRules.length} 条规则吗?`, '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        batchDeleteRules({ rule_ids: this.selectedRules })
          .then(response => {
            this.$message.success(`成功删除 ${response.data.deleted_count} 条规则`)
            this.fetchRules()
            this.selectedRules = []
          })
      }).catch(() => {
        this.$message.info('已取消删除')
      })
    },

    // 单个删除
    handleDelete(index, row) {
      this.$confirm('确认删除该规则吗?', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        deleteRule(row.rule_id)
          .then(() => {
            this.$message.success('删除成功')
            this.fetchRules()
          })
      })
    },
    
    // 提交表单（批量添加）
  submitForm() {
  this.$refs.ruleForm.validate(valid => {
    if (valid) {
      if (this.dialogTitle === '添加规则') {
        // 添加规则逻辑（原有代码）
        const requests = this.ruleForm.selectedRules.map(ruleType => 
          createRule({
            policy_id: this.policyId,
            rule_type: ruleType
          })
        )
        Promise.all(requests)
          .then(() => {
            this.$message.success('添加成功')
            this.dialogVisible = false
            this.fetchRules()
          })
      } 
    }
  })
}
  }
}
</script>

<style scoped>
.box-card {
  max-width: 1200px;
  margin: 0 auto;
}

.el-checkbox-group {
  display: flex;
  flex-wrap: wrap;
}

.el-checkbox {
  margin-right: 15px;
  margin-bottom: 10px;
  width: 200px;
}

.el-table {
  margin-top: 20px;
}
</style>