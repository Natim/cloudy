from cloudy.DGAC_avion_logbook.models import DGACAvionLogBook
from cloudy.DGAC_ballon_logbook.models import DGACBallonLogBook
from cloudy.DGAC_planeur_logbook.models import DGACPlaneurLogBook
from cloudy.FCL1080.models import FCL1080LogBook
from cloudy.FFP_logbook.models import FFPLogBook
from cloudy.FFPLUM_ulm_logbook.models import FFPLUMUlmLogBook

MAP = {
    "plane_dgac": DGACAvionLogBook,
    "glider_dgac": DGACPlaneurLogBook,
    "plane_fcl1080": FCL1080LogBook,
    "helicopter_dgac": DGACAvionLogBook,  # WHAT THE HELL IS THAT? COPTER=PLANE?
    "ulm_ffplum": FFPLUMUlmLogBook,
    "balloon_dgac": DGACBallonLogBook,
    "parachute_cloudy": FFPLogBook,
}
