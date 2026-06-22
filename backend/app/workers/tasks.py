from backend.app.workers.celery_app import celery_app


@celery_app.task(name="astralith.execute_operation_task")
def execute_operation_task(task_id: int) -> dict[str, int | str]:
    """Celery 异步任务入口。

    正确流程是：读取 Task -> 生成 inventory/playbook -> 调用 AnsibleService -> 写入结果。
    这里先保留最小骨架，避免 FastAPI 请求线程承担长时间远程执行。
    """
    return {"task_id": task_id, "status": "pending"}
