import os
import json
import logging
from datetime import datetime
from typing import Any, Dict

import requests

logger = logging.getLogger(__name__)

SLACK_WEBHOOK_ENV = "SLACK_WEBHOOK_URL"


def _post_slack(webhook: str, message: str) -> None:
    try:
        resp = requests.post(webhook, json={"text": message}, timeout=5)
        if resp.status_code >= 300:
            logger.error("Slack webhook failed %s %s", resp.status_code, resp.text[:200])
    except Exception as e:
        logger.error("Slack webhook exception: %s", e)


def task_failure_callback(context: Dict[str, Any]) -> None:
    ti = context.get("ti")
    dag_id = context.get("dag_id")
    task_id = context.get("task_id")
    exec_date = context.get("execution_date")
    try_number = ti.try_number if ti else None
    err = context.get("exception")
    message = (
        f"[AIRFLOW][FAIL] dag={dag_id} task={task_id} exec_date={exec_date} try={try_number} error={err}"  # noqa: E501
    )
    logger.error(message)

    # Optional structured log file
    log_dir = os.path.join("monitoring")
    os.makedirs(log_dir, exist_ok=True)
    with open(os.path.join(log_dir, "failures.log"), "a", encoding="utf-8") as f:
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "dag_id": dag_id,
            "task_id": task_id,
            "execution_date": str(exec_date),
            "try": try_number,
            "error": str(err),
        }
        f.write(json.dumps(record) + "\n")

    webhook = os.getenv(SLACK_WEBHOOK_ENV)
    if webhook:
        _post_slack(webhook, message)


def task_success_callback(context: Dict[str, Any]) -> None:
    ti = context.get("ti")
    dag_id = context.get("dag_id")
    task_id = context.get("task_id")
    exec_date = context.get("execution_date")
    try_number = ti.try_number if ti else None
    message = (
        f"[AIRFLOW][SUCCESS] dag={dag_id} task={task_id} exec_date={exec_date} try={try_number}"  # noqa: E501
    )
    logger.info(message)
    webhook = os.getenv(SLACK_WEBHOOK_ENV)
    if webhook:
        _post_slack(webhook, message)
