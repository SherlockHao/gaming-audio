def test_ping_task_registered():
    """Verify the ping task is registered in Celery."""
    from app.worker.celery_app import celery_app, ping_task
    assert "ping" in celery_app.tasks or ping_task.name == "ping"

def test_ping_task_runs_eagerly():
    """Verify the ping task can execute (eager mode, no broker needed)."""
    from app.worker.celery_app import celery_app, ping_task
    celery_app.conf.task_always_eager = True
    result = ping_task.delay()
    assert result.get() == "pong"
    celery_app.conf.task_always_eager = False
