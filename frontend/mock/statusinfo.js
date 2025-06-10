const Mock = require('mockjs')

const data = Mock.mock({
  'items|20': [{
    id: '@id',
    name: "name",
    "status|1": ["在线","离线"],
  }]
})

module.exports = [
  {
    url: '/frontend/statusinfo',
    type: 'get',
    response: config => {
      const items = data.items
      return {
        code: 20000,
        data: {
          total: items.length,
          items: items
        }
      }
    }
  }
]
