class ScheduleService:
    def trigger_scheduled_job(self, scheduled_job_id: int) -> None:
        # TODO: 创建任务记录，并投递 Celery 异步执行。
        _ = scheduled_job_id
