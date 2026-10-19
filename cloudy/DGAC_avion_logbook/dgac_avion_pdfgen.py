"""
PDF generation for a DGAC Plane logbook.
"""

import time
from itertools import groupby

from reportlab.graphics.charts.textlabels import Label
from reportlab.graphics.shapes import Drawing, Line
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import (
    Image,
    Indenter,
    PageBreak,
    Paragraph,
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
    "totjeq": 0,
    "totneq": 0,
    "totmonojdbl": 0,
    "totmonojcdb": 0,
    "totmonondbl": 0,
    "totmononcdb": 0,
    "totmuljdbl": 0,
    "totmuljcdb": 0,
    "totmuljcplt": 0,
    "totmulndbl": 0,
    "totmulncdb": 0,
    "totmulncplt": 0,
    "totvaidbl": 0,
    "totvaiplt": 0,
    "simu": 0,
    "ifr": 0,
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
    """Draw all the cut lines."""
    cut_lines = Drawing(1, 1)
    cut_lines.add(gen_cut_line(-100, 385, 1000, 385))
    cut_lines.add(gen_cut_line(620, -150, 620, 500))
    cut_lines.add(gen_cut_line(-100, -8, 1000, -8))
    cut_lines.add(gen_cut_line(-10, -150, -10, 500))
    return cut_lines


def min_to_str(minutes):
    """Convert minutes to hh:mm"""
    minutes = int(minutes)
    if minutes == 0:
        return EMPTY_STR
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def gen_carnet_de_vol(http_response=None, title="", show_cuts=True, logs=[], reports={}):
    """
    Generate the logbook pdf
    Logs contains all log entries for the book
    """

    if http_response:
        doc = SimpleDocTemplate(http_response, showBoundary=False, bottomMargin=0, title=title)
    else:
        doc = SimpleDocTemplate("carner_de_vol.pdf", showBoundary=False, bottomMargin=0, title=title)

    # Our container for 'Flowable' objects
    elements = []
    prev_totals = default_totals.copy()

    # check for reported hours and update prev_totals if needed
    if reports:
        if "mbr_equipage_jour" in reports:
            prev_totals["totjeq"] = reports["mbr_equipage_jour"]
        if "mbr_equipage_nuit" in reports:
            prev_totals["totneq"] = reports["mbr_equipage_nuit"]
        if "mono_jdbl" in reports:
            prev_totals["totmonojdbl"] = reports["mono_jdbl"]
        if "mono_jcdb" in reports:
            prev_totals["totmonojcdb"] = reports["mono_jcdb"]
        if "mono_ndbl" in reports:
            prev_totals["totmonondbl"] = reports["mono_ndbl"]
        if "mono_ncdb" in reports:
            prev_totals["totmononcdb"] = reports["mono_ncdb"]
        if "mul_jdbl" in reports:
            prev_totals["totmuljdbl"] = reports["mul_jdbl"]
        if "mul_jcdb" in reports:
            prev_totals["totmuljcdb"] = reports["mul_jcdb"]
        if "mul_jcplt" in reports:
            prev_totals["totmuljcplt"] = reports["mul_jcplt"]
        if "mul_ndbl" in reports:
            prev_totals["totmulndbl"] = reports["mul_ndbl"]
        if "mul_ncdb" in reports:
            prev_totals["totmulncdb"] = reports["mul_ncdb"]
        if "mul_ncplt" in reports:
            prev_totals["totmulncplt"] = reports["mul_ncplt"]
        if "vai_dbl" in reports:
            prev_totals["totvaidbl"] = reports["vai_dbl"]
        if "vai_plt" in reports:
            prev_totals["totvaiplt"] = reports["vai_plt"]
        if "simu" in reports:
            prev_totals["simu"] = reports["simu"]
        if "ifr" in reports:
            prev_totals["ifr"] = reports["ifr"]

    # if we have some logs lets group them by year
    if logs:
        page_count = 1
        for year, year_group in groupby(logs, lambda log: log.date.year):
            logs_for_year = list(year_group)

            # add new page every 14 entries
            for i in range(0, len(logs_for_year), 14):
                # if not first page we add a break
                if page_count != 1:
                    elements.append(PageBreak())
                # keep track of the totals from the previous page
                bottom_totals = append_new_page(
                    year_str=year,
                    logs=logs_for_year[i : i + 14],
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
        tmp_totals["totjeq"] += int(log.mbr_equipage_jour)
        tmp_totals["totneq"] += int(log.mbr_equipage_nuit)

        tmp_totals["totmonojdbl"] += int(log.mono_jdbl)
        tmp_totals["totmonojcdb"] += int(log.mono_jcdb)
        tmp_totals["totmonondbl"] += int(log.mono_ndbl)
        tmp_totals["totmononcdb"] += int(log.mono_ncdb)

        tmp_totals["totmuljdbl"] += int(log.mul_jdbl)
        tmp_totals["totmuljcdb"] += int(log.mul_jcdb)
        tmp_totals["totmuljcplt"] += int(log.mul_jcplt)
        tmp_totals["totmulndbl"] += int(log.mul_ndbl)
        tmp_totals["totmulncdb"] += int(log.mul_ncdb)
        tmp_totals["totmulncplt"] += int(log.mul_ncplt)

        tmp_totals["totvaidbl"] += int(log.vai_dbl)
        tmp_totals["totvaiplt"] += int(log.vai_plt)
        tmp_totals["simu"] += int(log.simu)
        tmp_totals["ifr"] += int(log.ifr)

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

    elements.append(gen_header_left(prev_totals))

    # Inner lines for left page
    body_table_style = TableStyle(
        [
            ("LINEAFTER", (0, 0), (-2, -1), 0.7, DARK_GREY),
            ("LINEABOVE", (0, 0), (-1, 0), 0.7, DARK_GREY),
            ("LINEABOVE", (0, 1), (-1, -1), 0.2, DARK_GREY),
            ("LINEBEFORE", (0, 0), (0, -1), 0.9, DARK_GREY),
            ("LINEAFTER", (-1, 0), (-1, -1), 0.9, DARK_GREY),
            ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONT", (0, 0), (-1, -1), HAND_FONT, 8),
            ("FONT", (0, 0), (0, -1), HAND_FONT, 11),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("ALIGN", (5, 0), (-1, -1), "CENTER"),
            # ('LEFTPADDING', (5, 0),(-1, -1), 10),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )

    # build body data

    body_data = [[" ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " "] for _ in range(14)]
    for i, log in enumerate(logs):
        body_data[i][0] = time.strftime("%d/%m", log.date.timetuple())
        body_data[i][1] = _format_sting(log.aeronef_type, 6)
        body_data[i][2] = log.aeronef_imma
        body_data[i][3] = log.fctbrd
        body_data[i][4] = log.natvol
        body_data[i][5] = min_to_str(log.mbr_equipage_jour)
        body_data[i][6] = min_to_str(log.mbr_equipage_nuit)
        body_data[i][7] = min_to_str(log.mono_jdbl)
        body_data[i][8] = min_to_str(log.mono_jcdb)
        body_data[i][9] = min_to_str(log.mono_ndbl)
        body_data[i][10] = min_to_str(log.mono_ncdb)

    body_table = Table(
        body_data,
        style=body_table_style,
        colWidths=[
            1.7 * cm,
            1.51 * cm,
            1.7 * cm,
            2.02 * cm,
            5.86 * cm,
            1.59 * cm,
            1.59 * cm,
            1.2 * cm,
            1.59 * cm,
            1.2 * cm,
            1.62 * cm,
        ],
        rowHeights=[0.68 * cm] * 14,
    )
    body_table.hAlign = "LEFT"
    elements.append(body_table)

    # Footer left
    elements.append(gen_footer_left(cummul_totals))

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
    lab.x = 310
    lab.y = 400
    lab.setText("ANNÉE %s" % year_str)
    lab.fontName = "ARIALB"
    lab.fontSize = 12
    year.add(lab)
    elements.append(year)

    # Dashed cut lines: up right bottom left
    if show_cuts:
        elements.append(gen_cut_lines())

        # Cut image, a flowable so we position it using indenters and spacers ...
        elements.append(Indenter(left=-24.9 * cm))
        elements.append(Spacer(0, 35))
        elements.append(Image(ASSETS["CUT_IMG"], 30 / 2, 56 / 2.0))
        elements.append(Indenter(left=24.9 * cm))

    # Page break
    elements.append(PageBreak())

    #### RIGHT PAGE ####
    elements.append(gen_header_right(prev_totals))

    # Inner lines  RIGHT PAGE
    body_table_style = TableStyle(
        [
            ("LINEAFTER", (0, 0), (1, -1), 0.2, DARK_GREY),
            ("LINEAFTER", (2, 0), (2, -1), 0.7, DARK_GREY),
            ("LINEAFTER", (3, 0), (4, -1), 0.2, DARK_GREY),
            ("LINEAFTER", (5, 0), (5, -1), 0.7, DARK_GREY),
            ("LINEAFTER", (6, 0), (6, -1), 0.2, DARK_GREY),
            ("LINEAFTER", (7, 0), (9, -1), 0.7, DARK_GREY),
            ("LINEABOVE", (0, 0), (-1, 0), 0.7, DARK_GREY),
            ("LINEABOVE", (0, 1), (-1, -1), 0.2, DARK_GREY),
            ("LINEBEFORE", (0, 0), (0, -1), 0.9, DARK_GREY),
            ("LINEAFTER", (-1, 0), (-1, -1), 0.9, DARK_GREY),
            ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("ALIGN", (0, 0), (9, -1), "CENTER"),
            ("FONT", (0, 0), (-1, -1), HAND_FONT, 8),
            ("FONT", (10, 0), (10, -1), HAND_FONT, 5),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )

    body_data = [[" ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " "] for _ in range(14)]

    for i, log in enumerate(logs):
        obs = log.obs
        if len(obs) > LEN_MAX_OBS:
            obs = "%s.." % log.obs[: LEN_MAX_OBS - 2]

        body_data[i][0] = min_to_str(log.mul_jdbl)
        body_data[i][1] = min_to_str(log.mul_jcdb)
        body_data[i][2] = min_to_str(log.mul_jcplt)
        body_data[i][3] = min_to_str(log.mul_ndbl)
        body_data[i][4] = min_to_str(log.mul_ncdb)
        body_data[i][5] = min_to_str(log.mul_ncplt)
        body_data[i][6] = min_to_str(log.vai_dbl)
        body_data[i][7] = min_to_str(log.vai_plt)
        body_data[i][8] = min_to_str(log.simu)
        if log.ifr != 0:
            str_log_ifr = log.ifr
        else:
            str_log_ifr = ""
        body_data[i][9] = str_log_ifr

        body_data[i][10] = obs

    body_table = Table(
        body_data,
        style=body_table_style,
        colWidths=[
            1.2 * cm,
            1.59 * cm,
            1.59 * cm,
            1.2 * cm,
            1.59 * cm,
            1.59 * cm,
            1.2 * cm,
            1.2 * cm,
            1.61 * cm,
            1 * cm,
            7.87 * cm,
        ],
        rowHeights=[0.68 * cm] * 14,
    )

    body_table.hAlign = "LEFT"
    elements.append(body_table)
    elements.append(gen_footer_right(cummul_totals))

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
        elements.append(Indenter(left=-24.9 * cm))
        elements.append(Spacer(0, 35))
        elements.append(Image(ASSETS["CUT_IMG"], 30 / 2, 56 / 2.0))
        elements.append(Indenter(left=24.9 * cm))

    return cummul_totals


##################################### LEFT HEADER ##############################


def gen_header_left(prev_totals={}):
    """
    Table header for left page
    """
    if prev_totals == {}:
        prev_totals = default_totals.copy()

    # AERONEF, TYPE, IMMATRICULATION
    second_header_col_style = TableStyle(
        [
            ("SPAN", (0, 0), (1, 0)),
            ("LINEABOVE", (0, 1), (1, 1), 0.2, DARK_GREY),
            ("LINEBEFORE", (1, 1), (1, 1), 0.7, DARK_GREY),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONT", (0, 0), (-1, -1), "ARIAL", 9),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )

    second_col_data = [["AÉRONEF", ""], ["TYPE", "IMMATRI-\nCULATION"]]
    second_col_table = Table(
        second_col_data,
        style=second_header_col_style,
        colWidths=[1.5 * cm, 1.7 * cm],
        rowHeights=[1.475 * cm, 1.475 * cm],
    )

    # NATURE DU VOL, REPORTS. ARROW
    fourth_header_col_style = TableStyle(
        [
            ("VALIGN", (0, 1), (0, 1), "TOP"),
            ("RIGHTPADDING", (0, 1), (0, 1), 0),
            ("SPAN", (0, 0), (1, 0)),
            ("ALIGN", (0, 0), (1, 0), "CENTER"),
            ("VALIGN", (0, 0), (1, 0), "BOTTOM"),
            ("BOTTOMPADDING", (0, 0), (1, 0), 17),
            ("FONT", (0, 0), (1, 0), "ARIAL", 9),
            ("VALIGN", (1, 1), (1, 1), "BOTTOM"),
            ("BOTTOMPADDING", (1, 1), (1, 1), 5),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )

    img = Image(ASSETS["ARROW_IMG"], 0.65 * cm, 0.3 * cm)
    stylesheet = getSampleStyleSheet()
    para = Paragraph(
        """<para align=right spaceb=3 fontSize=7.5 fontName=BIBI color=(.3,.3,.3)><i>Reports.</i></para>""",
        stylesheet["BodyText"],
    )

    fourth_col_data = [["NATURE DU VOL"], [para, img]]
    fourth_col_table = Table(
        fourth_col_data,
        style=fourth_header_col_style,
        colWidths=[4.96 * cm, 1 * cm],
        rowHeights=[2.15 * cm, 0.65 * cm],
    )

    # MEMBRE EQUIPAGE, JOUR , NUIT
    fith_header_col_style = TableStyle(
        [
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("SPAN", (0, 0), (1, 0)),
            ("FONT", (0, 0), (1, 0), "ARIAL", 9),
            ("FONT", (0, 1), (1, 1), "ARIAL", 7.5),
            ("FONT", (0, 2), (1, 2), HAND_FONT, 9),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("INNERGRID", (0, 1), (-1, -1), 0.7, DARK_GREY),
            ("LINEABOVE", (0, 1), (1, 1), 0.2, DARK_GREY),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )

    fith_col_data = [
        ["MEMBRE\nD'ÉQUIPAGE"],
        ["JOUR", "NUIT"],
        [min_to_str(prev_totals["totjeq"]), min_to_str(prev_totals["totneq"])],
    ]

    fith_col_table = Table(
        fith_col_data,
        style=fith_header_col_style,
        colWidths=[1.59 * cm, 1.59 * cm],
        rowHeights=[1.4 * cm, 0.68 * cm, 0.68 * cm],
    )

    # PILOTE MONOMOTEUR, JOUR, NUIT, Double, Cdt de bord..
    sixth_header_col_style = TableStyle(
        [
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("SPAN", (0, 0), (3, 0)),
            ("SPAN", (0, 1), (1, 1)),
            ("SPAN", (2, 1), (3, 1)),
            ("FONT", (0, 0), (3, 1), "ARIAL", 9),
            ("FONT", (0, 2), (3, 2), "ARIAL", 7.2),
            ("FONT", (0, 3), (3, 3), HAND_FONT, 9),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LINEABOVE", (0, 1), (3, 1), 0.7, DARK_GREY),
            ("LINEABOVE", (0, 2), (3, 2), 0.2, DARK_GREY),
            ("INNERGRID", (0, 2), (3, 3), 0.7, DARK_GREY),
            ("INNERGRID", (1, 1), (2, 1), 0.7, DARK_GREY),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )

    sixth_col_data = [
        ["PILOTE MONOMOTEUR"],
        ["JOUR", "", "NUIT", ""],
        ["Double", "Cdt de bord", "Double", "Cdt de bord"],
        [
            min_to_str(prev_totals["totmonojdbl"]),
            min_to_str(prev_totals["totmonojcdb"]),
            min_to_str(prev_totals["totmonondbl"]),
            min_to_str(prev_totals["totmononcdb"]),
        ],
    ]

    sixth_col_table = Table(
        sixth_col_data,
        style=sixth_header_col_style,
        colWidths=[1.18 * cm, 1.59 * cm, 1.2 * cm, 1.6 * cm],
        rowHeights=[0.72 * cm, 0.68 * cm, 0.68 * cm, 0.68 * cm],
    )

    # Table styles
    header_table_style = TableStyle(
        [
            ("INNERGRID", (0, 0), (-1, -1), 0.7, DARK_GREY),
            ("LINEABOVE", (0, 0), (-1, 0), 0.9, DARK_GREY),
            ("LINEBEFORE", (0, 0), (0, 0), 0.9, DARK_GREY),
            ("LINEAFTER", (-1, 0), (-1, 0), 0.9, DARK_GREY),
            ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("FONT", (0, 0), (-1, -1), "ARIAL", 9),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )

    data = [
        [
            "DATE",
            second_col_table,
            "FUNCTION\nÀ\nBORD",
            fourth_col_table,
            fith_col_table,
            sixth_col_table,
        ],
    ]

    header_table = Table(
        data,
        colWidths=[1.7 * cm, 3.21 * cm, 2.02 * cm, 5.86 * cm, 3.18 * cm, 5.61 * cm],
        rowHeights=[
            2.8 * cm,
        ],
    )

    header_table.hAlign = "LEFT"
    header_table.setStyle(header_table_style)
    return header_table


###################################### LEFT FOOTER #############################


def gen_footer_left(cummul_totals={}):
    """
    Table Footer for left page
    """
    if cummul_totals == {}:
        cummul_totals = default_totals.copy()

    total_hm_style = TableStyle(
        [
            ("FONT", (0, 0), (-1, -1), "ARIAL", 7.1),
            ("ALIGN", (0, 0), (-1, 0), "LEFT"),
            ("LEFTPADDING", (0, 0), (0, 0), 2),
            ("BOTTOMPADDING", (0, 0), (0, 0), 2),
            ("LEFTPADDING", (2, 0), (2, 0), 70),
            # heures position
            ("LEFTPADDING", (1, 1), (1, 1), 10),
            ("BOTTOMPADDING", (0, 1), (0, 1), 1),
            # minutes. position
            ("LEFTPADDING", (3, 1), (3, 1), -10.5),
            ("BOTTOMPADDING", (1, 1), (3, 1), 1),
            ("FONT", (0, 1), (0, 1), HAND_FONT, 9),
            ("LEFTPADDING", (0, 1), (0, 1), 30),
            ("FONT", (2, 1), (2, 1), HAND_FONT, 9),
            ("LEFTPADDING", (2, 1), (2, 1), 20),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )

    # Total général des heures ... heures et minutes 14 elements
    total_m = (
        cummul_totals["totmonojdbl"]
        + cummul_totals["totmonojcdb"]
        + cummul_totals["totmonondbl"]
        + cummul_totals["totmononcdb"]
        + cummul_totals["totmuljdbl"]
        + cummul_totals["totmuljcdb"]
        + cummul_totals["totmuljcplt"]
        + cummul_totals["totmulndbl"]
        + cummul_totals["totmulncdb"]
        + cummul_totals["totmulncplt"]
    )

    thour, tmin = 0, 0
    if total_m != 0:
        thour, tmin = min_to_str(total_m).split(":")

    total_hm_data = [
        ["Total général des heures de vol comme pilote :", "", ""],
        [thour, "heures", tmin, "minutes."],
    ]

    total_hm_table = Table(
        total_hm_data,
        style=total_hm_style,
        colWidths=[1.7 * cm, 1.51 * cm, 1.7 * cm, 2.02 * cm],
        rowHeights=[
            0.4 * cm,
            0.46 * cm,
        ],
    )

    # Totaux à reporter and arrow
    total_report_arrow_style = TableStyle(
        [
            ("FONT", (0, 0), (-1, -1), "ARIAL", 7.1),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
            ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
            ("RIGHTPADDING", (1, 0), (1, 0), 3),
            ("BOTTOMPADDING", (-1, -1), (-1, -1), 0),
        ]
    )

    img = Image(ASSETS["ARROW_IMG"], 0.65 * cm, 0.3 * cm)
    total_report_arrow_data = [["Totaux à reporter", img]]
    total_report_arrow_table = Table(
        total_report_arrow_data,
        style=total_report_arrow_style,
        colWidths=[5.16 * cm, 0.7 * cm],
        rowHeights=[0.86 * cm],
    )

    # Footer table style
    footer_table_style = TableStyle(
        [
            ("INNERGRID", (1, 0), (-1, -1), 0.7, DARK_GREY),
            ("LINEABOVE", (0, 1), (-1, 1), 0.9, DARK_GREY),
            ("LINEABOVE", (0, 0), (-1, 0), 0.7, DARK_GREY),
            ("LINEBEFORE", (0, 0), (0, 0), 0.9, DARK_GREY),
            ("LINEAFTER", (-2, 0), (-1, 0), 0.9, DARK_GREY),
            ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("FONT", (0, 0), (-1, -1), HAND_FONT, 9),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )

    data = [
        [
            total_hm_table,
            total_report_arrow_table,
            min_to_str(cummul_totals["totjeq"]),
            min_to_str(cummul_totals["totneq"]),
            min_to_str(cummul_totals["totmonojdbl"]),
            min_to_str(cummul_totals["totmonojcdb"]),
            min_to_str(cummul_totals["totmonondbl"]),
            min_to_str(cummul_totals["totmononcdb"]),
        ],
    ]

    footer_table = Table(
        data,
        colWidths=[
            6.93 * cm,
            5.86 * cm,
            1.59 * cm,
            1.59 * cm,
            1.2 * cm,
            1.59 * cm,
            1.2 * cm,
            1.62 * cm,
        ],
        rowHeights=[
            0.86 * cm,
        ],
    )

    footer_table.hAlign = "LEFT"
    footer_table.setStyle(footer_table_style)
    return footer_table


##################################### RIGHT HEADER #############################


def gen_header_right(prev_totals={}):
    """
    Table header for right page
    """
    if prev_totals == {}:
        prev_totals = default_totals.copy()

    # PILOTE MULTIMOTEURS, JOUR NUIT ..
    first_header_col_style = TableStyle(
        [
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("SPAN", (0, 0), (-1, 0)),
            ("SPAN", (0, 1), (2, 1)),
            ("SPAN", (3, 1), (5, 1)),
            ("FONT", (0, 0), (-1, 1), "ARIAL", 9),
            ("FONT", (0, 2), (-1, 2), "ARIAL", 8),
            ("FONT", (0, 3), (-1, -1), HAND_FONT, 9),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LINEABOVE", (0, 1), (-1, 1), 0.7, DARK_GREY),
            ("LINEABOVE", (0, 2), (-1, 2), 0.7, DARK_GREY),
            ("INNERGRID", (0, 2), (-1, -1), 0.2, DARK_GREY),
            ("LINEABOVE", (0, 3), (-1, 3), 0.7, DARK_GREY),
            ("INNERGRID", (1, 1), (-1, 1), 0.7, DARK_GREY),
            ("LINEBEFORE", (3, 2), (3, 3), 0.7, DARK_GREY),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )

    first_col_data = [
        [
            "PILOTE MULTIMOTEURS",
        ],
        ["JOUR", "", "", "NUIT", "", ""],
        ["Double", "Cdt de bord", "Co-pilote", "Double", "Cdt de bord", "Co-pilote"],
        [
            min_to_str(prev_totals["totmuljdbl"]),
            min_to_str(prev_totals["totmuljcdb"]),
            min_to_str(prev_totals["totmuljcplt"]),
            min_to_str(prev_totals["totmulndbl"]),
            min_to_str(prev_totals["totmulncdb"]),
            min_to_str(prev_totals["totmulncplt"]),
        ],
    ]
    first_col_table = Table(
        first_col_data,
        style=first_header_col_style,
        colWidths=[1.2 * cm, 1.59 * cm, 1.59 * cm, 1.2 * cm, 1.59 * cm, 1.59 * cm],
        rowHeights=[0.7 * cm, 0.69 * cm, 0.71 * cm, 0.68 * cm],
    )

    # VOLS AUX INSTRUMENTS (1) Double Pilote
    second_header_col_style = TableStyle(
        [
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("SPAN", (0, 0), (-1, 0)),
            ("FONT", (0, 0), (-1, 0), "ARIAL", 7.3),
            ("FONT", (0, 1), (-1, -1), "ARIAL", 8.5),
            ("FONT", (0, 2), (-1, -1), HAND_FONT, 9),
            ("LINEABOVE", (0, 1), (-1, 1), 0.7, DARK_GREY),
            ("LINEABOVE", (0, 2), (-1, 2), 0.7, DARK_GREY),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("INNERGRID", (0, 1), (-1, -1), 0.2, DARK_GREY),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )

    second_col_data = [
        ["VOLS AUX\nINSTRUMENTS (1)"],
        ["Double", "Pilote"],
        [min_to_str(prev_totals["totvaidbl"]), min_to_str(prev_totals["totvaiplt"])],
    ]

    second_col_table = Table(
        second_col_data,
        style=second_header_col_style,
        colWidths=[1.2 * cm, 1.2 * cm],
        rowHeights=[1.39 * cm, 0.71 * cm, 0.68 * cm],
    )

    # SIMULATION
    third_head_col_style = TableStyle(
        [
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONT", (0, 0), (-1, 0), "ARIAL", 9),
            ("FONT", (0, 1), (-1, 1), HAND_FONT, 9),
            ("LINEABOVE", (0, 1), (-1, 1), 0.7, DARK_GREY),
            ("LINEAFTER", (0, 0), (0, 1), 0.7, DARK_GREY),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )

    # ARRIVÉES I.F.R
    ifr = Drawing(0, 0)
    lab = Label()
    lab.setOrigin(0, 0)
    lab.x = -1
    lab.y = 0
    lab.angle = 90
    lab.dx = 0
    lab.setText("ARRIVEES\n     I.F.R")
    lab.fontName = "ARIAL"
    lab.strokeColor = colors.Color(0.26, 0.26, 0.26, 0)
    lab.fillColor = colors.Color(0.26, 0.26, 0.26, 0.9)
    lab.fontSize = 9.5
    ifr.add(lab)

    ifr_total = prev_totals["ifr"]
    if ifr_total == 0:
        ifr_total = ""

    third_col_data = [["SIMU-\nLATION", ifr], [min_to_str(prev_totals["simu"]), ifr_total]]
    third_col_table = Table(
        third_col_data,
        style=third_head_col_style,
        colWidths=[
            1.61 * cm,
            1 * cm,
        ],
        rowHeights=[2.1 * cm, 0.68 * cm],
    )

    last_data = "OBSERVATIONS ET VISA\nDE L'AUTORITÉE HABILITÉE\nOU DE L'INSTRUCTEUR"

    data = [
        [first_col_table, second_col_table, third_col_table, last_data],
    ]

    header_table = Table(
        data,
        colWidths=[8.76 * cm, 2.4 * cm, 2.61 * cm, 7.87 * cm],
        rowHeights=[
            2.8 * cm,
        ],
    )

    # Table style
    header_table_style = TableStyle(
        [
            ("INNERGRID", (0, 0), (-1, -1), 0.7, DARK_GREY),
            ("LINEABOVE", (0, 0), (-1, 0), 0.9, DARK_GREY),
            ("LINEBEFORE", (0, 0), (0, 0), 0.9, DARK_GREY),
            ("LINEAFTER", (-1, 0), (-1, 0), 0.9, DARK_GREY),
            ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("FONT", (0, 0), (-1, -1), "ARIAL", 9.3),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )
    header_table.hAlign = "LEFT"
    header_table.setStyle(header_table_style)
    return header_table


##################################### RIGHT FOOTER #############################


def gen_footer_right(cummul_totals={}):
    """
    Table footer for right page
    """
    if cummul_totals == {}:
        cummul_totals = default_totals.copy()

    footer_table_style = TableStyle(
        [
            ("LINEAFTER", (0, 0), (1, -1), 0.2, DARK_GREY),
            ("LINEAFTER", (2, 0), (2, -1), 0.7, DARK_GREY),
            ("LINEAFTER", (3, 0), (4, -1), 0.2, DARK_GREY),
            ("LINEAFTER", (5, 0), (5, -1), 0.7, DARK_GREY),
            ("LINEAFTER", (6, 0), (6, -1), 0.2, DARK_GREY),
            ("LINEAFTER", (7, 0), (9, -1), 0.7, DARK_GREY),
            ("LINEABOVE", (0, 0), (-1, 0), 0.7, DARK_GREY),
            ("LINEBEFORE", (0, 0), (0, 0), 0.9, DARK_GREY),
            ("LINEABOVE", (0, 1), (-1, 1), 0.9, DARK_GREY),
            ("LINEAFTER", (-1, 0), (-1, -1), 0.9, DARK_GREY),
            ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
            # place (1) Ces ..
            ("LEFTPADDING", (10, 0), (10, 0), 15),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (10, 0), (10, 0), "BOTTOM"),
            ("FONT", (10, 0), (10, 0), "ARIAL", 7.1),
            ("FONT", (0, 0), (9, 0), HAND_FONT, 9),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )
    last_com = "(1) Ces heures sont comprises dans les heures de vol PILOTE."
    cummul_total_ifr = cummul_totals["ifr"]
    if cummul_total_ifr == 0:
        cummul_total_ifr = ""
    footer_data = [
        [
            min_to_str(cummul_totals["totmuljdbl"]),
            min_to_str(cummul_totals["totmuljcdb"]),
            min_to_str(cummul_totals["totmuljcplt"]),
            min_to_str(cummul_totals["totmulndbl"]),
            min_to_str(cummul_totals["totmulncdb"]),
            min_to_str(cummul_totals["totmulncplt"]),
            min_to_str(cummul_totals["totvaidbl"]),
            min_to_str(cummul_totals["totvaiplt"]),
            min_to_str(cummul_totals["simu"]),
            cummul_total_ifr,
            last_com,
        ]
    ]

    footer_table = Table(
        footer_data,
        style=footer_table_style,
        colWidths=[
            1.2 * cm,
            1.59 * cm,
            1.59 * cm,
            1.2 * cm,
            1.59 * cm,
            1.59 * cm,
            1.2 * cm,
            1.2 * cm,
            1.61 * cm,
            1 * cm,
            7.87 * cm,
        ],
        rowHeights=[0.86 * cm],
    )
    footer_table.hAlign = "LEFT"
    return footer_table


##################################### MAIN #############################

if __name__ == "__main__":
    gen_carnet_de_vol()
