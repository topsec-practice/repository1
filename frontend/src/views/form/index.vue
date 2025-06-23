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
            placeholder="添加对策略的描述"
            clearable
          ></el-input>
        </el-form-item>
        
        <el-form-item label="选择规则" prop="selectedRules">
          <el-checkbox-group v-model="form.selectedRules">
            <el-checkbox 
              v-for="item in ruleOptions" 
              :key="item.value" 
              :label="item.value"
            >
              {{ item.label }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <el-form-item label="策略路径" prop="path">
          <el-input
            v-model="form.path"
            type="textarea"
            :rows="1"
            placeholder="策略路径"
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
          prop="path"
          label="策略路径"
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
// import { createRule } from '@/api/rules'

export default {
  name: 'StrategyPage',
  data() {
    return {
      // 策略提交模块数据
      form: {
        strategy: '',
        path: '',
        selectedRules: []
      },
      rules: {
        strategy: [
          { required: true, message: '请输入策略内容', trigger: 'blur' },
          { max: 200, message: '策略内容不能超过200个字符', trigger: 'blur' }
        ],
        selectedRules: [
          { type: 'array', required: true, message: '请至少选择一个规则', trigger: 'change' }
        ],
        strategy: [
          { required: true, message: '请输入策略内容', trigger: 'blur' },
          { max: 200, message: '策略内容不能超过200个字符', trigger: 'blur' }
        ],
        path: [
          { required: true, trigger: 'blur'},
        ]
      },
      submitting: false,
      
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
          this.submitting = true;
          // alert(this.form.path);
          // 先提交策略
          submitStrategy({
                          strategy: this.form.strategy,
                          path: this.form.path,
                          selectedRules: this.form.selectedRules
                        })
            .then(response => {
              const policyId = response.data.policy_id
              this.$message.success('策略提交成功123！策略ID: ' + policyId)
              
              this.resetForm()
              this.fetchPolicies() // 刷新策略列表
              
              return Promise.all(rulePromises)
            })
            .finally(() => {
              this.submitting = false
            })
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