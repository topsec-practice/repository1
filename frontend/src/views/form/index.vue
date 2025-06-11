<template>
  <div class="app-container">
    <el-card class="box-card">
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
  </div>
</template>

<script>
import { submitStrategy } from '@/api/Strategy'// 导入API请求方法

export default {
  name: 'StrategySubmit',
  data() {
    return {
      form: {
        strategy: ''
      },
      rules: {
        strategy: [
          { required: true, message: '请输入策略内容', trigger: 'blur' },
          { max: 200, message: '策略内容不能超过200个字符', trigger: 'blur' }
        ]
      },
      submitting: false
    }
  },
  methods: {
    submitForm() {
      this.$refs.form.validate(valid => {
        if (valid) {
          this.submitting = true
          
          // 调用API提交策略
          submitStrategy(this.form.strategy)
            .then(response => {
              this.$message.success('策略提交成功！')
              this.resetForm()
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
    }
  }
}
</script>

<style scoped>
.box-card {
  max-width: 800px;
  margin: 20px auto;
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