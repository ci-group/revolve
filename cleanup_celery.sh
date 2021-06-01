#!/bin/bash
celery --app pyrevolve.util.supervisor.rabbits.celery_queue worker --loglevel=DEBUG
