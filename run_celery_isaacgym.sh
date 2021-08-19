#!/bin/bash
exec celery --app pyrevolve.util.supervisor.rabbits.celery_queue worker --loglevel=INFO $@
