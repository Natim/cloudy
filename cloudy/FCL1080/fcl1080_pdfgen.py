"""
PDF generation for a DGAC Plane logbook.
"""

import time
from itertools import groupby

from reportlab.graphics.charts.textlabels import Label
from reportlab.graphics.shapes import Drawing, Line
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import (
    Image,
    Indenter,
    PageBreak,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.rl_config import defaultPageSize

from cloudy.logbooks.pdf_export import register_pdf_assets

# Register fonts, imgs
ASSETS = register_pdf_assets(pdfmetrics)

HAND_FONT = "BLOK"
LEN_MAX_OBS = 70
# colors
DARK_GREY = (0.25, 0.25, 0.25)
LIGHT_GREY = (0.5, 0.5, 0.5)
BLACK = (0, 0, 0)


EMPTY_STR = ""

# Landscape mode
PAGE_HEIGHT = defaultPageSize[1]
PAGE_WIDTH = defaultPageSize[0]

styles = getSampleStyleSheet()


default_totals = {
    "synthetic_time": 0,
    "pilot_time_dual": 0,
    "landing_day": 0,
    "landing_night": 0,
    "pilot_timpe_cop": 0,
    "single_pilot_time": 0,
    "take_off_night": 0,
    "multi_pilot_time": 0,
    "total_time_flight": 0,
    "op_time_ifr": 0,
    "op_time_night": 0,
    "pilot_time_in_cmd": 0,
    "take_off_day": 0,
    "pilot_time_inst": 0,
}


def gen_cut_line(coord_x, coord_y, coord_x1, coord_y1, width=1.2):
    """Draw a line with the cut symbol on it."""
    return Line(
        coord_x,
        coord_y,
        coord_x1,
        coord_y1,
        strokeColor=DARK_GREY,
        strokeWidth=width,
        strokeDashArray=[6, 3],
    )


def gen_cut_lines():
    cut_lines = Drawing(1, 1)
    cut_lines.add(gen_cut_line(-100, 410, 1000, 415))
    cut_lines.add(gen_cut_line(750, -150, 750, 500))
    cut_lines.add(gen_cut_line(-100, -8, 1000, -8))
    cut_lines.add(gen_cut_line(-10, -150, -10, 500))
    return cut_lines


def min_to_str(minutes):
    """Convert minutes to hh:mm"""
    minutes = int(minutes)
    if minutes == 0:
        return EMPTY_STR
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _min_format(minutes):
    minutes = int(minutes)
    if minutes < 10:
        return "0%d" % minutes
    return minutes


def gen_carnet_de_vol(http_response=None, title="", show_cuts=True, logs=[], reports={}):
    """
    Generate the logbook pdf
    Logs contains all log entries for the book
    """

    if http_response:
        doc = SimpleDocTemplate(
            http_response,
            showBoundary=False,
            title=title,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=0,
        )
    else:
        doc = SimpleDocTemplate("carner_de_vol.pdf", showBoundary=False, bottomMargin=0, title=title)

    # Our container for 'Flowable' objects
    elements = []
    prev_totals = default_totals.copy()

    # check for reported hours and update prev_totals if needed
    if reports:
        if "synthetic_time" in reports:
            prev_totals["synthetic_time"] = reports["synthetic_time"]
        if "pilot_time_dual" in reports:
            prev_totals["pilot_time_dual"] = reports["pilot_time_dual"]
        if "landing_day" in reports:
            prev_totals["landing_day"] = reports["landing_day"]
        if "pilot_timpe_cop" in reports:
            prev_totals["pilot_timpe_cop"] = reports["pilot_timpe_cop"]
        if "single_pilot_time" in reports:
            prev_totals["single_pilot_time"] = reports["single_pilot_time"]
        if "take_off_night" in reports:
            prev_totals["take_off_night"] = reports["take_off_night"]
        if "multi_pilot_time" in reports:
            prev_totals["multi_pilot_time"] = reports["multi_pilot_time"]
        if "total_time_flight" in reports:
            prev_totals["total_time_flight"] = reports["total_time_flight"]
        if "op_time_ifr" in reports:
            prev_totals["op_time_ifr"] = reports["op_time_ifr"]
        if "op_time_night" in reports:
            prev_totals["op_time_night"] = reports["op_time_night"]
        if "pilot_time_in_cmd" in reports:
            prev_totals["pilot_time_in_cmd"] = reports["pilot_time_in_cmd"]
        if "landing_night" in reports:
            prev_totals["landing_night"] = reports["landing_night"]
        if "take_off_day" in reports:
            prev_totals["take_off_day"] = reports["take_off_day"]
        if "pilot_time_inst" in reports:
            prev_totals["pilot_time_inst"] = reports["pilot_time_inst"]

    # if we have some logs lets group them by year
    if logs:
        page_count = 1
        for year, year_group in groupby(logs, lambda log: log.date.year):
            logs_for_year = list(year_group)

            # add new page every 14 entries
            for i in range(0, len(logs_for_year), 18):
                # if not first page we add a break
                if page_count != 1:
                    elements.append(PageBreak())
                # keep track of the totals from the previous page
                bottom_totals = append_new_page(
                    year_str=year,
                    logs=logs_for_year[i : i + 18],
                    prev_totals=prev_totals,
                    show_cuts=show_cuts,
                    elements=elements,
                    page_count=page_count,
                )
                # remember totals
                prev_totals = bottom_totals
                page_count += 2

    else:
        # no data
        append_new_page(show_cuts=show_cuts, elements=elements)

    doc.pagesize = landscape(A4)

    doc.build(elements)


def _calculate_page_totals(logs):
    """
    Sum page hours
    """
    tmp_totals = default_totals.copy()
    for log in logs:
        tmp_totals["synthetic_time"] += int(log.synthetic_time)
        tmp_totals["pilot_time_dual"] += int(log.pilot_time_dual)

        log_landing_day = 0
        if log.landing_day:
            log_landing_day = log.landing_day
        tmp_totals["landing_day"] += int(log_landing_day)
        log_landing_night = 0
        if log.landing_night:
            log_landing_night = log.landing_night
        tmp_totals["landing_night"] += int(log_landing_night)
        log_take_off_day = 0
        if log.take_off_day:
            log_take_off_day = log.take_off_day
        tmp_totals["take_off_day"] += int(log_take_off_day)
        log_take_off_night = 0
        if log.take_off_night:
            log_take_off_night = log.take_off_night
        tmp_totals["take_off_night"] += int(log_take_off_night)

        tmp_totals["pilot_timpe_cop"] += int(log.pilot_timpe_cop)
        tmp_totals["single_pilot_time"] += int(log.single_pilot_time)

        tmp_totals["multi_pilot_time"] += int(log.multi_pilot_time)
        tmp_totals["total_time_flight"] += int(log.total_time_flight)
        tmp_totals["op_time_ifr"] += int(log.op_time_ifr)
        tmp_totals["op_time_night"] += int(log.op_time_night)
        tmp_totals["pilot_time_in_cmd"] += int(log.pilot_time_in_cmd)

        tmp_totals["pilot_time_inst"] += int(log.pilot_time_inst)

    return tmp_totals


def _calculate_cumulated_totals(page_totals, prev_totals):
    """
    Sum previous totals + current page
    """
    cummul_totals = {}
    for k, _ in page_totals.items():
        cummul_totals[k] = page_totals[k] + prev_totals[k]

    return cummul_totals


def _format_sting(strg, max_length):
    """
    Truncate the given string if it is longer than max_length.
    """
    if len(strg) > max_length:
        return strg[:max_length] + ".."
    return strg


def append_new_page(elements=[], prev_totals={}, logs=[], show_cuts=True, year_str="2010", page_count=1):
    """
    Append a new page with 14 log entries and totals to the log book
    """

    # First calculate totals
    page_totals = _calculate_page_totals(logs)
    cummul_totals = _calculate_cumulated_totals(prev_totals, page_totals)

    # Then build the page

    # Header left
    for el in gen_header_left(prev_totals):
        elements.append(el)

    # Inner lines for left page
    BODY_TABLE_STYLE = TableStyle(
        [
            ("GRID", (0, 0), (-1, -1), 0.6, DARK_GREY),
            ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("BACKGROUND", (0, 2), (-1, 2), (0.9, 0.9, 0.9)),
            ("BACKGROUND", (0, 5), (-1, 5), (0.9, 0.9, 0.9)),
            ("BACKGROUND", (0, 8), (-1, 8), (0.9, 0.9, 0.9)),
            ("BACKGROUND", (0, 11), (-1, 11), (0.9, 0.9, 0.9)),
            ("BACKGROUND", (0, 14), (-1, 14), (0.9, 0.9, 0.9)),
            ("BACKGROUND", (0, 17), (-1, 17), (0.9, 0.9, 0.9)),
            ("FONT", (0, 0), (0, -1), HAND_FONT, 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("ALIGN", (2, 0), (2, -1), "CENTER"),
            ("ALIGN", (4, 0), (4, -1), "CENTER"),
            ("ALIGN", (7, 0), (7, -1), "CENTER"),
            ("ALIGN", (8, 0), (14, -1), "CENTER"),
            ("ALIGN", (16, 0), (-1, -1), "CENTER"),
            ("FONT", (1, 0), (-1, -1), HAND_FONT, 5),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
            ("FONT", (2, 0), (2, -1), HAND_FONT, 6),
            ("FONT", (4, 0), (4, -1), HAND_FONT, 6),
            ("FONT", (7, 0), (7, -1), HAND_FONT, 6),
            ("FONT", (8, 0), (14, -1), HAND_FONT, 6),
            ("FONT", (16, 0), (-1, -1), HAND_FONT, 6),
        ]
    )
    # build body data
    body_data = [
        ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""] for _ in range(18)
    ]
    for i, log in enumerate(logs):
        body_data[i][0] = time.strftime("%d/%m", log.date.timetuple())
        body_data[i][1] = _format_sting(log.departure_place, 8)
        body_data[i][2] = min_to_str(log.departure_time)
        body_data[i][3] = _format_sting(log.arrival_place, 8)
        body_data[i][4] = min_to_str(log.arrival_time)
        body_data[i][5] = _format_sting(log.aircraft_type, 20)
        body_data[i][6] = _format_sting(log.aircraft_imma, 20)
        if log.single_pilot_se:
            body_data[i][7] = "X"
        else:
            body_data[i][7] = " "

        if log.single_pilot_me:
            body_data[i][8] = "X"
        else:
            body_data[i][8] = " "
        # SINGLE PILOT TIME
        if log.single_pilot_time:
            h, m = min_to_str(log.single_pilot_time).split(":")
            body_data[i][9] = h
            body_data[i][10] = m
        else:
            body_data[i][9] = " "
            body_data[i][10] = " "
        # MULTI PILOT TIME
        if log.multi_pilot_time:
            h, m = min_to_str(log.multi_pilot_time).split(":")
            body_data[i][11] = h
            body_data[i][12] = m
        else:
            body_data[i][11] = " "
            body_data[i][12] = " "
        # TOTAL TIME
        if log.total_time_flight:
            h, m = min_to_str(log.total_time_flight).split(":")
            body_data[i][13] = h
            body_data[i][14] = m
        else:
            body_data[i][13] = " "
            body_data[i][14] = " "

        body_data[i][15] = _format_sting(log.name_pic, 20)
        body_data[i][16] = log.take_off_day
        body_data[i][17] = log.take_off_night
        body_data[i][18] = log.landing_day
        body_data[i][19] = log.landing_night

    body_table = Table(
        body_data,
        style=BODY_TABLE_STYLE,
        colWidths=[
            1.65 * cm,
            1.2 * cm,
            1.2 * cm,
            1.2 * cm,
            1.2 * cm,
            3 * cm,
            2.7 * cm,
            0.8 * cm,
            0.8 * cm,
            0.8 * cm,
            0.8 * cm,
            1.15 * cm,
            0.8 * cm,
            1.15 * cm,
            0.8 * cm,
            3.3 * cm,
            0.8 * cm,
            0.8 * cm,
            0.8 * cm,
            0.8 * cm,
        ],
        rowHeights=[0.53 * cm] * 18,
    )
    body_table.hAlign = "LEFT"
    elements.append(body_table)

    # Footer left
    if page_totals == {}:
        page_totals = default_totals.copy()
    if cummul_totals == {}:
        cummul_totals = default_totals.copy()
    if prev_totals == {}:
        prev_totals = default_totals.copy()
    elements.append(gen_footer_left(prev=prev_totals, page=page_totals, total=cummul_totals))

    # Page number left
    page = Drawing(0, 0)
    lab = Label()
    lab.setOrigin(0, 0)
    lab.x = 640
    lab.y = -30
    lab.setText("p %s" % page_count)
    lab.fontName = "ARIAL"
    lab.fontSize = 9
    page.add(lab)
    elements.append(page)

    # Year
    year = Drawing(0, 0)
    lab = Label()
    lab.setOrigin(0, 0)
    lab.x = 29
    lab.y = 415
    lab.setText("ANNÉE %s" % year_str)
    lab.fontName = "ARIALB"
    lab.fontSize = 9
    year.add(lab)
    elements.append(year)

    # Dashed cut lines: up right bottom left
    if show_cuts:
        elements.append(gen_cut_lines())

        # Cut image, a flowable so we position it using indenters and spacers ...
        elements.append(Indenter(left=-27.8 * cm))
        elements.append(Spacer(0, 35))
        elements.append(Image(ASSETS["CUT_IMG"], 30 / 2, 56 / 2.0))
        elements.append(Indenter(left=27.8 * cm))

    # Page break
    elements.append(PageBreak())

    #### RIGHT PAGE ####
    # Header right
    for el in gen_header_right(prev_totals):
        elements.append(el)

    # Inner lines  RIGHT PAGE
    BODY_TABLE_STYLE = TableStyle(
        [
            ("GRID", (0, 0), (-1, -1), 0.6, DARK_GREY),
            ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONT", (0, 0), (-1, -1), HAND_FONT, 5),
            ("FONT", (12, 0), (12, -1), HAND_FONT, 6),
            ("ALIGN", (0, 0), (11, -1), "CENTER"),
            ("ALIGN", (14, 0), (15, -1), "CENTER"),
            ("BACKGROUND", (0, 2), (-1, 2), (0.9, 0.9, 0.9)),
            ("BACKGROUND", (0, 5), (-1, 5), (0.9, 0.9, 0.9)),
            ("BACKGROUND", (0, 8), (-1, 8), (0.9, 0.9, 0.9)),
            ("BACKGROUND", (0, 11), (-1, 11), (0.9, 0.9, 0.9)),
            ("BACKGROUND", (0, 14), (-1, 14), (0.9, 0.9, 0.9)),
            ("BACKGROUND", (0, 17), (-1, 17), (0.9, 0.9, 0.9)),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )

    # build body data
    body_data = [["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""] for _ in range(18)]
    for i, log in enumerate(logs):
        # OP CONDITION NIGHT TIME
        if log.op_time_night:
            h, m = min_to_str(log.op_time_night).split(":")
            body_data[i][0] = h
            body_data[i][1] = m
        else:
            body_data[i][0] = " "
            body_data[i][1] = " "
        # OP CONDITION op_time_ifr
        if log.op_time_ifr:
            h, m = min_to_str(log.op_time_ifr).split(":")
            body_data[i][2] = h
            body_data[i][3] = m
        else:
            body_data[i][2] = " "
            body_data[i][3] = " "
        # PILOT IN COMMAND
        if log.pilot_time_in_cmd:
            h, m = min_to_str(log.pilot_time_in_cmd).split(":")
            body_data[i][4] = h
            body_data[i][5] = m
        else:
            body_data[i][4] = " "
            body_data[i][5] = " "
        # CO PILOT
        if log.pilot_timpe_cop:
            h, m = min_to_str(log.pilot_timpe_cop).split(":")
            body_data[i][6] = h
            body_data[i][7] = m
        else:
            body_data[i][6] = " "
            body_data[i][7] = " "
        # DUAL
        if log.pilot_time_dual:
            h, m = min_to_str(log.pilot_time_dual).split(":")
            body_data[i][8] = h
            body_data[i][9] = m
        else:
            body_data[i][8] = " "
            body_data[i][9] = " "
        # INS
        if log.pilot_time_inst:
            h, m = min_to_str(log.pilot_time_inst).split(":")
            body_data[i][10] = h
            body_data[i][11] = m
        else:
            body_data[i][10] = " "
            body_data[i][11] = " "
        # SYN DATE
        if log.synthetic_date:
            body_data[i][12] = time.strftime("%d/%m", log.synthetic_date.timetuple())
        else:
            body_data[i][12] = " "
        # SYN TYPE
        body_data[i][13] = _format_sting(log.synthetic_type, 20)
        # SYN TOTAL TIME SESSION
        if log.synthetic_time:
            h, m = min_to_str(log.synthetic_time).split(":")
            body_data[i][14] = h
            body_data[i][15] = m
        else:
            body_data[i][14] = " "
            body_data[i][15] = " "
        body_data[i][16] = _format_sting(log.obs, 30)

    body_table = Table(
        body_data,
        style=BODY_TABLE_STYLE,
        colWidths=[
            1.05 * cm,
            1.05 * cm,
            1.05 * cm,
            1.05 * cm,
            1.05 * cm,
            1.05 * cm,
            1.05 * cm,
            1.05 * cm,
            1.05 * cm,
            1.05 * cm,
            1.05 * cm,
            1.05 * cm,
            1.65 * cm,
            3.3 * cm,
            0.8 * cm,
            0.8 * cm,
            6.65 * cm,
        ],
        rowHeights=[0.50 * cm] * 18,
    )

    body_table.hAlign = "LEFT"
    elements.append(body_table)
    if prev_totals == {}:
        prev_totals = default_totals.copy()
    if page_totals == {}:
        page_totals = default_totals.copy()
    if cummul_totals == {}:
        cummul_totals = default_totals.copy()

    elements.append(gen_footer_right(prev=prev_totals, page=page_totals, total=cummul_totals))

    # Page number right
    page = Drawing(0, 0)
    lab = Label()
    lab.setOrigin(0, 0)
    lab.x = 640
    lab.y = -30
    lab.setText("p %s" % str(page_count + 1))
    lab.fontName = "ARIAL"
    lab.fontSize = 9
    page.add(lab)
    elements.append(page)

    # Dashed cut lines: up right bottom left
    if show_cuts:
        # Dashed cut lines: up right bottom left
        cut_lines = gen_cut_lines()
        cut_lines.add(
            gen_cut_line(
                390,
                -150,
                390,
                -10,
            )
        )
        cut_lines.add(
            gen_cut_line(
                390,
                385,
                390,
                500,
            )
        )
        elements.append(cut_lines)

        # Cut image, a flowable so we position it using indenters and spacers ...
        elements.append(Indenter(left=-27.8 * cm))
        elements.append(Spacer(0, 35))
        elements.append(Image(ASSETS["CUT_IMG"], 30 / 2, 56 / 2.0))
        elements.append(Indenter(left=27.8 * cm))

    return cummul_totals


##################################### LEFT HEADER ##############################
from reportlab.platypus.flowables import Flowable


class TTR(Flowable):  # TableTextRotate
    """Rotates a tex in a table cell."""

    def __init__(self, text):
        Flowable.__init__(self)
        self.text = text

    def draw(self):
        canvas = self.canv
        canvas.rotate(90)
        canvas.drawString(0, -1, self.text)

    def wrap(self, aW, aH):
        canv = self.canv
        return canv._leading - 8, canv.stringWidth(self.text)


def gen_header_left(prev_totals={}):
    """
    Table header for left page
    """
    # Date
    DATE_HEADER_STYLE = TableStyle(
        [
            ("LINEBEFORE", (0, 0), (-1, -1), 0.6, DARK_GREY),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONT", (0, 0), (-1, -1), "ARIALB", 7),
            ("FONT", (0, 1), (0, 1), "ARIALB", 6),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )
    date_data = Table(
        [["DATE"], ["(dd/mm/yy)"]],
        style=DATE_HEADER_STYLE,
        colWidths=[1.65 * cm],
        rowHeights=[0.4 * cm, 1.3 * cm],
    )
    # departure
    DEPARTURE_HEADER_STYLE = TableStyle(
        [
            ("SPAN", (0, 0), (1, 0)),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONT", (0, 0), (-1, -1), "ARIALB", 7),
            ("INNERGRID", (0, 1), (-1, 1), 0.6, DARK_GREY),
            ("LINEABOVE", (0, 1), (1, 1), 0.6, DARK_GREY),
            ("FONT", (0, 1), (-1, 1), "ARIAL", 6),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )
    departure_data = Table(
        [["DEPARTURE", ""], ["PLACE", "TIME"]],
        style=DEPARTURE_HEADER_STYLE,
        colWidths=[1.2 * cm, 1.2 * cm],
        rowHeights=[1.2 * cm, 0.5 * cm],
    )
    # Arrival
    arrival_data = Table(
        [["ARRIVAL", ""], ["PLACE", "TIME"]],
        style=DEPARTURE_HEADER_STYLE,
        colWidths=[1.2 * cm, 1.2 * cm],
        rowHeights=[1.2 * cm, 0.5 * cm],
    )
    # Aircraft
    aircraft_data = Table(
        [["AIRCRAFT", ""], ["MAKE, MODEL, VARIANT", "REGISTRATION"]],
        style=DEPARTURE_HEADER_STYLE,
        colWidths=[3 * cm, 2.7 * cm],
        rowHeights=[1.2 * cm, 0.5 * cm],
    )
    # SP MP
    SPMP_HEADER_STYLE = TableStyle(
        [
            ("SPAN", (0, 0), (3, 0)),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONT", (0, 0), (-1, -1), "ARIALB", 7),
            ("LINEAFTER", (3, 0), (3, -1), 0.6, DARK_GREY),
            ("INNERGRID", (0, 1), (-1, 1), 0.6, DARK_GREY),
            ("LINEABOVE", (0, 1), (3, 1), 0.6, DARK_GREY),
            ("FONT", (0, 1), (-1, 1), "ARIAL", 6),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )
    spmp_data = Table(
        [["SINGLE\nPILOT TIME", "", "", "", "MULTI-PILOT\nTIME"], ["SE", "ME", "", "", ""]],
        style=SPMP_HEADER_STYLE,
        colWidths=[0.8 * cm, 0.8 * cm, 0.8 * cm, 0.8 * cm, 1.95 * cm],
        rowHeights=[1.2 * cm, 0.5 * cm],
    )
    # Total time of flight
    TOTAL_TIME_HEADER_STYLE = TableStyle(
        [
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONT", (0, 0), (-1, -1), "ARIALB", 7),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )
    total_time_of_flight_data = Table(
        [["TOTAL TIME\nOF FLIGHT"]],
        style=TOTAL_TIME_HEADER_STYLE,
        colWidths=[1.95 * cm],
        rowHeights=[1.7 * cm],
    )
    # Name pic
    NAME_PIC_HEADER_STYLE = TableStyle(
        [
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONT", (0, 0), (-1, -1), "ARIALB", 7),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )
    name_pic = Table([["NAME PIC"]], style=NAME_PIC_HEADER_STYLE, colWidths=[3.3 * cm], rowHeights=[1.7 * cm])
    # Take offs Landings
    TOLA_HEADER_STYLE = TableStyle(
        [
            ("SPAN", (0, 0), (1, 0)),
            ("SPAN", (2, 0), (3, 0)),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("VALIGN", (0, 1), (-1, -1), "CENTER"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONT", (0, 0), (-1, -1), "ARIALB", 7),
            ("LINEAFTER", (1, 0), (1, 0), 0.6, DARK_GREY),
            ("LINEAFTER", (3, 0), (3, -1), 0.6, DARK_GREY),
            ("INNERGRID", (0, 1), (-1, 1), 0.6, DARK_GREY),
            ("LINEABOVE", (0, 1), (3, 1), 0.6, DARK_GREY),
            ("FONT", (0, 1), (-1, 1), "ARIAL", 6),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )
    tola_data = Table(
        [["TAKEOFFS", "", "LANDINGS", ""], [TTR("DAY"), TTR("NIGHT"), TTR("DAY"), TTR("NIGHT")]],
        style=TOLA_HEADER_STYLE,
        colWidths=[0.8 * cm, 0.8 * cm, 0.8 * cm, 0.8 * cm],
        rowHeights=[0.5 * cm, 1.2 * cm],
    )
    # second row
    SECOND_HEADER_ROW_STYLE = TableStyle(
        [
            ("INNERGRID", (0, 0), (-1, -1), 0.6, DARK_GREY),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONT", (0, 0), (-1, -1), "ARIALB", 7),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )

    second_row_data = [
        [
            date_data,
            departure_data,
            arrival_data,
            aircraft_data,
            spmp_data,
            total_time_of_flight_data,
            name_pic,
            tola_data,
        ]
    ]
    second_row_header = Table(
        second_row_data,
        style=SECOND_HEADER_ROW_STYLE,
        colWidths=[
            1.65 * cm,
            2.4 * cm,
            2.4 * cm,
            5.7 * cm,
            5.15 * cm,
            1.95 * cm,
            3.3 * cm,
            3.2 * cm,
        ],
        rowHeights=[1.7 * cm],
    )

    # First row
    FIRST_ROW_HEADER_TABLE_STYLE = TableStyle(
        [
            ("INNERGRID", (0, 0), (-1, -1), 0.6, DARK_GREY),
            ("BOX", (0, 0), (-1, -1), 0.6, DARK_GREY),
            ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("FONT", (0, 0), (-1, -1), "ARIAL", 7),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )

    first_row_header = Table(
        [["1", "2", "3", "4", "5", "6", "7", "8"]],
        style=FIRST_ROW_HEADER_TABLE_STYLE,
        colWidths=[
            1.65 * cm,
            2.4 * cm,
            2.4 * cm,
            5.7 * cm,
            5.15 * cm,
            1.95 * cm,
            3.3 * cm,
            3.2 * cm,
        ],
        rowHeights=[0.50 * cm],
    )
    first_row_header.hAlign = "LEFT"
    second_row_header.hAlign = "LEFT"

    # Second row
    return [first_row_header, second_row_header]


###################################### LEFT FOOTER #############################


def _footer_hmin_cell_helper(totals_list, report_val):
    """Split minutes into hour/minute cells. Hours must be ints (Python 3 `/` is float)."""
    minutes = int(report_val or 0)
    if minutes == 0:
        totals_list += ["", ""]
        return
    totals_list.append(minutes // 60)
    totals_list.append(_min_format(minutes % 60))


def gen_footer_left(prev={}, page={}, total={}):
    """
    Table Footer for left page
    total this page
    total from previous pages
    total time
    """

    FOOTER_TABLE_STYLE = TableStyle(
        [
            ("INNERGRID", (1, 0), (-1, -1), 0.6, DARK_GREY),
            ("LINEBEFORE", (1, 0), (1, -1), 0.6, DARK_GREY),
            ("BOX", (0, 0), (-1, -1), 0.6, DARK_GREY),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("LEFTPADDING", (0, 0), (0, -1), 225),
            ("FONT", (1, 0), (-1, -1), HAND_FONT, 6),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("FONT", (0, 0), (0, -1), "ARIALB", 7),
            ("VALIGN", (1, 0), (-1, -1), "MIDDLE"),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )

    # Total général des heures ... heures et minutes
    total_page_data = ["TOTAL THIS PAGE", "", ""]
    total_prev_data = ["TOTAL FROM PREVIOUS PAGES", "", ""]
    total_total_data = ["TOTAL TIME", "", ""]
    data = {
        "page": {"totals": total_page_data, "source": page},
        "prev": {"totals": total_prev_data, "source": prev},
        "total": {"totals": total_total_data, "source": total},
    }

    for k, v in data.items():
        _footer_hmin_cell_helper(totals_list=v["totals"], report_val=v["source"]["single_pilot_time"])
        _footer_hmin_cell_helper(totals_list=v["totals"], report_val=v["source"]["multi_pilot_time"])
        _footer_hmin_cell_helper(totals_list=v["totals"], report_val=v["source"]["total_time_flight"])
        v["totals"].append("")
        v["totals"].append(v["source"]["landing_day"])
        v["totals"].append(v["source"]["landing_night"])
        v["totals"].append(v["source"]["take_off_day"])
        v["totals"].append(v["source"]["take_off_night"])

    footer_data = [
        total_page_data,
        total_prev_data,
        total_total_data,
    ]

    footer_table = Table(
        footer_data,
        style=FOOTER_TABLE_STYLE,
        colWidths=[
            12.15 * cm,
            0.8 * cm,
            0.8 * cm,
            0.8 * cm,
            0.8 * cm,
            1.15 * cm,
            0.8 * cm,
            1.15 * cm,
            0.8 * cm,
            3.3 * cm,
            0.8 * cm,
            0.8 * cm,
            0.8 * cm,
            0.8 * cm,
        ],
        rowHeights=[0.83 * cm, 0.83 * cm, 0.83 * cm],
    )

    footer_table.hAlign = "LEFT"
    footer_table.setStyle(FOOTER_TABLE_STYLE)
    return footer_table


##################################### RIGHT HEADER #############################


def gen_header_right(prev_totals={}):
    """
    Table header for right page
    """

    # OPE COND TIME
    OP_COND_TIME_HEADER_STYLE = TableStyle(
        [
            ("SPAN", (0, 0), (1, 0)),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONT", (0, 0), (-1, -1), "ARIALB", 7),
            ("INNERGRID", (0, 1), (-1, 1), 0.6, DARK_GREY),
            ("LINEABOVE", (0, 1), (1, 1), 0.6, DARK_GREY),
            ("LINEBEFORE", (0, 0), (-1, -1), 0.6, DARK_GREY),
            ("FONT", (0, 1), (-1, 1), "ARIAL", 6),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )
    cond_time_data = Table(
        [["OPERATIONAL\nCONDITION TIME", ""], ["NIGHT", "IFR"]],
        style=OP_COND_TIME_HEADER_STYLE,
        colWidths=[2.1 * cm, 2.1 * cm],
        rowHeights=[1.2 * cm, 0.5 * cm],
    )
    # Pilot function time
    PIL_FUNC_TIME_HEADER_STYLE = TableStyle(
        [
            ("SPAN", (0, 0), (7, 0)),
            ("SPAN", (0, 1), (1, 1)),
            ("SPAN", (2, 1), (3, 1)),
            ("SPAN", (4, 1), (5, 1)),
            ("SPAN", (6, 1), (7, 1)),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONT", (0, 0), (-1, -1), "ARIALB", 7),
            ("INNERGRID", (0, 1), (-1, 1), 0.6, DARK_GREY),
            ("LINEABOVE", (0, 1), (7, 1), 0.6, DARK_GREY),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("VALIGN", (0, 1), (-1, -1), "MIDDLE"),
            ("FONT", (0, 1), (-1, 1), "ARIAL", 6),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )
    pil_time_data = Table(
        [
            ["PILOT FUNCTION TIME", "", "", "", "", "", "", ""],
            ["PILOT-IN\nCOMMAND", "", "CO-PILOT", "", "DUAL", "", "INSTRUCTOR", ""],
        ],
        style=PIL_FUNC_TIME_HEADER_STYLE,
        colWidths=[
            1.05 * cm,
            1.05 * cm,
            1.05 * cm,
            1.05 * cm,
            1.05 * cm,
            1.05 * cm,
            1.05 * cm,
            1.05 * cm,
        ],
        rowHeights=[1.2 * cm, 0.5 * cm],
    )
    # SYNTHETIC
    SYNTHETIC_TIME_HEADER_STYLE = TableStyle(
        [
            ("SPAN", (0, 0), (3, 0)),
            ("SPAN", (2, 1), (3, 1)),
            ("VALIGN", (0, 1), (-1, -1), "MIDDLE"),
            ("VALIGN", (0, 0), (0, 0), "TOP"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONT", (0, 0), (-1, -1), "ARIALB", 7),
            ("INNERGRID", (0, 1), (-1, 1), 0.6, DARK_GREY),
            ("LINEABOVE", (0, 1), (3, 1), 0.6, DARK_GREY),
            ("FONT", (0, 1), (-1, 1), "ARIAL", 6),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )
    synt_data = Table(
        [
            ["SYNTHETIC TRAINING DEVICES SESSION", "", "", ""],
            ["DATE\n(dd/mm/yy)", "TYPE", "TOTAL TIME\nOF SESSION", ""],
        ],
        style=SYNTHETIC_TIME_HEADER_STYLE,
        colWidths=[1.65 * cm, 3.3 * cm, 0.8 * cm, 0.8 * cm],
        rowHeights=[1.2 * cm, 0.5 * cm],
    )
    # Remarks and endoresements
    OBS_STYLE = TableStyle(
        [
            ("SPAN", (0, 0), (0, 0)),
            ("VALIGN", (0, 0), (0, 0), "TOP"),
            ("ALIGN", (0, 0), (0, 0), "CENTER"),
            ("FONT", (0, 0), (-1, -1), "ARIALB", 7),
            ("LINEAFTER", (0, 0), (1, -1), 0.6, DARK_GREY),
            ("INNERGRID", (0, 1), (-1, 1), 0.6, DARK_GREY),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )
    obs_data = Table(
        [["REMARKS\nAND ENDORSEMENTS"]],
        style=OBS_STYLE,
        colWidths=[6.65 * cm],
        rowHeights=[
            1.7 * cm,
        ],
    )
    # First row
    FIRST_ROW_HEADER_TABLE_STYLE = TableStyle(
        [
            ("INNERGRID", (0, 0), (-1, -1), 0.6, DARK_GREY),
            ("BOX", (0, 0), (-1, -1), 0.6, DARK_GREY),
            ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("FONT", (0, 0), (-1, -1), "ARIAL", 7),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )
    first_row_header = Table(
        [["9", "10", "11", "12"]],
        style=FIRST_ROW_HEADER_TABLE_STYLE,
        colWidths=[
            4.2 * cm,
            8.4 * cm,
            6.55 * cm,
            6.65 * cm,
        ],
        rowHeights=[0.50 * cm],
    )
    first_row_header.hAlign = "LEFT"
    # second row
    SECOND_HEADER_ROW_STYLE = TableStyle(
        [
            ("INNERGRID", (0, 0), (-1, -1), 0.6, DARK_GREY),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONT", (0, 0), (-1, -1), "ARIALB", 7),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )

    second_row_data = [[cond_time_data, pil_time_data, synt_data, obs_data]]
    second_row_header = Table(
        second_row_data,
        style=SECOND_HEADER_ROW_STYLE,
        colWidths=[
            4.2 * cm,
            8.4 * cm,
            6.55 * cm,
            6.65 * cm,
        ],
        rowHeights=[1.7 * cm],
    )

    second_row_header.hAlign = "LEFT"

    # Second row
    return [first_row_header, second_row_header]


##################################### RIGHT FOOTER #############################


def gen_footer_right(prev={}, page={}, total={}):
    """
    Table footer for right page
    """

    FOOTER_TABLE_STYLE = TableStyle(
        [
            ("INNERGRID", (0, 0), (15, -1), 0.6, DARK_GREY),
            ("LINEBEFORE", (1, 0), (16, -1), 0.6, DARK_GREY),
            ("BOX", (0, 0), (-1, -1), 0.6, DARK_GREY),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("FONT", (0, 0), (-1, -1), HAND_FONT, 6),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONT", (16, 2), (16, 2), "ARIALB", 7),
            ("VALIGN", (16, 2), (16, 2), "TOP"),
            ("VALIGN", (16, 1), (16, 1), "BOTTOM"),
            ("FONT", (16, 0), (16, 1), "ARIALB", 7),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )
    # Total général des heures ... heures et minutes
    total_page_data = []
    total_prev_data = []
    total_total_data = []
    data = {
        "page": {"totals": total_page_data, "source": page},
        "prev": {"totals": total_prev_data, "source": prev},
        "total": {"totals": total_total_data, "source": total},
    }

    for k, v in data.items():
        _footer_hmin_cell_helper(totals_list=v["totals"], report_val=v["source"]["op_time_night"])
        _footer_hmin_cell_helper(totals_list=v["totals"], report_val=v["source"]["op_time_ifr"])
        _footer_hmin_cell_helper(totals_list=v["totals"], report_val=v["source"]["pilot_time_in_cmd"])
        _footer_hmin_cell_helper(totals_list=v["totals"], report_val=v["source"]["pilot_timpe_cop"])
        _footer_hmin_cell_helper(totals_list=v["totals"], report_val=v["source"]["pilot_time_dual"])
        _footer_hmin_cell_helper(totals_list=v["totals"], report_val=v["source"]["pilot_time_inst"])
        v["totals"].append("")
        v["totals"].append("")
        _footer_hmin_cell_helper(totals_list=v["totals"], report_val=v["source"]["synthetic_time"])

    total_page_data.append("I certify that the entries in this log are true.")
    total_prev_data.append("________________________")
    total_total_data.append("PILOT'S SIGNATURE")

    footer_data = [
        total_page_data,
        total_prev_data,
        total_total_data,
    ]
    footer_table = Table(
        footer_data,
        style=FOOTER_TABLE_STYLE,
        colWidths=[
            1.05 * cm,
            1.05 * cm,
            1.05 * cm,
            1.05 * cm,
            1.05 * cm,
            1.05 * cm,
            1.05 * cm,
            1.05 * cm,
            1.05 * cm,
            1.05 * cm,
            1.05 * cm,
            1.05 * cm,
            1.65 * cm,
            3.3 * cm,
            0.8 * cm,
            0.8 * cm,
            6.65 * cm,
        ],
        rowHeights=[0.83 * cm, 0.83 * cm, 0.83 * cm],
    )
    footer_table.hAlign = "LEFT"
    return footer_table


##################################### MAIN #############################
if __name__ == "__main__":
    gen_carnet_de_vol()
