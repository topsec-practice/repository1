import request from '@/utils/request'

// 策略提交API
export function submitStrategy(data) {
  return request({
    url: '/frontend/strategy/submit',
    method: 'post',
    data: {
      strategy: data.strategy,
      rule_types: data.selectedRules,
      path: data.path,
    }
  });
};

// 如果需要获取策略状态
// export function getStrategyStatus() {
//   return request({
//     url: '/frontend/strategy/status', // 替换为实际API地址
//     method: 'get'
//   })
// }