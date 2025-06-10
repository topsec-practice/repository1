import request from '@/utils/request'

export function StatusInfo(token) {
  return request({
    url: '/frontend/statusinfo',
    method: 'get',
    // params: { token }
  })
}