export default {
  app: {
    name: 'Astralith',
  },
  nav: {
    dashboard: '仪表盘',
    hosts: '主机管理',
    hostGroups: '主机组',
    operationModules: '运维模块',
    tasks: '执行任务',
    scheduledJobs: '定时任务',
  },
  dashboard: {
    title: 'Astralith 仪表盘',
    description: '轻量级自动化运维平台仪表盘骨架。',
    hosts: '主机',
    tasks: '任务',
    success: '成功',
    scheduled: '定时',
  },
  pages: {
    hosts: {
      title: '主机管理',
      description: '主机管理页面骨架：后续提供新增主机、编辑主机、删除主机和连接测试。',
    },
    hostGroups: {
      title: '主机组',
      description: '主机组管理页面骨架：后续管理分组与主机成员关系。',
    },
    operationModules: {
      title: '运维模块',
      empty: '暂无可用运维模块。',
    },
    tasks: {
      title: '执行任务',
      description: '任务创建、状态查看与日志入口页面骨架。',
    },
    scheduledJobs: {
      title: '定时任务',
      description: '定时巡检任务页面骨架：后续支持启用、禁用和手动触发。',
    },
  },
} as const
