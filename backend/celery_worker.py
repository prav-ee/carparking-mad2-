#!/usr/bin/env python3
"""
Celery worker script for running background tasks
"""

from tasks import celery

if __name__ == '__main__':
    celery.start() 