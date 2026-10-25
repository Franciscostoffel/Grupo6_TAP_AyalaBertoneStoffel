"""Sincronización periódica de las fuentes externas."""

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from backend.core.config import SYNC_INTERVAL_HOURS
from backend.db.repositories.session_repository import delete_expired_sessions
from backend.services.sync_service import sync_all_sources

scheduler = AsyncIOScheduler()


def start_scheduler():
    """Programa la sincronización cada SYNC_INTERVAL_HOURS horas."""
    scheduler.add_job(sync_all_sources, "interval", hours=SYNC_INTERVAL_HOURS)
    scheduler.add_job(delete_expired_sessions, "interval", hours=24)
    scheduler.start()


def stop_scheduler():
    scheduler.shutdown()
