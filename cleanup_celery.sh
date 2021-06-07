#!/bin/bash
source .venv/bin/activate
exec celery --app pyrevolve.util.supervisor.rabbits.celery_queue worker --loglevel=DEBUG
