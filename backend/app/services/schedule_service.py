class ScheduleService:
    """定时任务业务服务，负责把 APScheduler 触发转换为平台任务。"""

    def trigger_scheduled_job(self, scheduled_job_id: int) -> None:
        """触发单个定时任务的临时骨架。"""

        # TODO: 创建任务记录，并投递 Celery 异步执行。
        _ = scheduled_job_id
