import request from '@/utils/request'

export function getPolicyList(params) {
  return request({
    url: '/frontend/policy/list',
    method: 'get',
    params
  })
}