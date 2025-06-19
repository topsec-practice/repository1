import request from '@/utils/request'

export function getMatchesList(params) {
  return request({
    url: '/frontend/matches/list',
    method: 'get',
    params: params  // 这里必须加上
  })
}