import request from '@/utils/request'

// 策略提交API
export function submitStrategy(strategy) {
  return request({
    url: '/frontend/strategy/submit', // 替换为实际API地址
    method: 'post',
    data: {
      strategy: strategy
    }
  })
}

// 如果需要获取策略状态
export function getStrategyStatus() {
  return request({
    url: '/frontend/strategy/status', // 替换为实际API地址
    method: 'get'
  })
}