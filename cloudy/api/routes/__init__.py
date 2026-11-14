from ninja import Router

from . import account, aircraft, auth, logbooks, logs, payments, reports

router = Router()
router.add_router("", auth.router)
router.add_router("", account.router)
router.add_router("", logbooks.router)
router.add_router("", logs.router)
router.add_router("", reports.router)
router.add_router("", aircraft.router)
router.add_router("", payments.router)

__all__ = ["router"]
