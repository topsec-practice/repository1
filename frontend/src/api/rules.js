import request from '@/utils/request'

export function getRulesByPolicyId(policyId) {
  return request({
    url: '/frontend/rules/list',
    method: 'get',
    params: { policy_id: policyId }
  })
}