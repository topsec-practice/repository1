import request from '@/utils/request'

//获得策略
export function getRulesByPolicyId(policyId) {
  return request({
    url: '/frontend/rules/list',
    method: 'get',
    params: { policy_id: policyId }
  })
}

//新建
// export function createRule(data) {
//   return request({
//     url: '/frontend/rules/create',
//     method: 'post',
//     data: {
//       policy_id: data.policy_id,
//       rule_type: data.rule_type  // 修改为发送rule_type
//     }
//   })
// }


// //单个删除
// export function deleteRule(ruleId) {
//   return request({
//     url: '/frontend/rules/delete',
//     method: 'delete',
//     params: { rule_id: ruleId }
//   })
// }

// // 批量删除规则
// export function batchDeleteRules(data) {
//   return request({
//     url: '/frontend/rules/batch-delete',
//     method: 'post',
//     data: {
//       rule_ids: data.rule_ids
//     }
//   })
// }