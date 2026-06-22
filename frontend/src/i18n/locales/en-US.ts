export default {
  app: {
    name: 'Astralith',
  },
  nav: {
    dashboard: 'Dashboard',
    hosts: 'Hosts',
    hostGroups: 'Host Groups',
    operationModules: 'Operation Modules',
    tasks: 'Tasks',
    scheduledJobs: 'Scheduled Jobs',
  },
  dashboard: {
    title: 'Astralith Dashboard',
    description: 'Scaffold for the lightweight automated operations dashboard.',
    hosts: 'Hosts',
    tasks: 'Tasks',
    success: 'Success',
    scheduled: 'Scheduled',
  },
  pages: {
    hosts: {
      title: 'Hosts',
      description: 'Host management scaffold: create, edit, delete hosts and test connectivity later.',
    },
    hostGroups: {
      title: 'Host Groups',
      description: 'Host group scaffold: manage groups and host membership later.',
    },
    operationModules: {
      title: 'Operation Modules',
      empty: 'No operation modules available.',
    },
    tasks: {
      title: 'Tasks',
      description: 'Task creation, status tracking, and log entry scaffold.',
    },
    scheduledJobs: {
      title: 'Scheduled Jobs',
      description: 'Scheduled inspection scaffold: enable, disable, and manually trigger jobs later.',
    },
  },
} as const
