from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler(timezone="UTC")


def start_scheduler() -> None:
    """启动 APScheduler；远程执行仍由 Celery 和 Ansible Runner 完成。"""

    if not scheduler.running:
        scheduler.start()


def stop_scheduler() -> None:
    """关闭 APScheduler，应用退出时不等待后台调度线程继续运行。"""

    if scheduler.running:
        scheduler.shutdown(wait=False)
