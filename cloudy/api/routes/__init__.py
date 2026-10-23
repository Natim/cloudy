from ninja import Router

from . import aircraft, auth, logbooks, logs, reports

router = Router()
router.add_router("", auth.router)
router.add_router("", logbooks.router)
router.add_router("", logs.router)
router.add_router("", reports.router)
router.add_router("", aircraft.router)

__all__ = ["router"]
