import request from '@/utils/request'

export function getMatchesList(params) {
  return request({
    url: '/frontend/matches/list',
    method: 'get',
    //params: params  // 添加搜索参数支持
  })
}

// 移除deleteMatch函数，因为您要求去掉删除功能