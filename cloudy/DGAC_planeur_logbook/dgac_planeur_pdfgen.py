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

NBR_LOGS_PER_PAGE = 12

# Landscape mode
PAGE_HEIGHT = defaultPageSize[1]
PAGE_WIDTH = defaultPageSize[0]
styles = getSampleStyleSheet()


default_totals = {"total_flytime_dbl": 0, "total_flytime_cdb": 0, "total_flytime_ins": 0}


def gen_cut_line(coord_x, coord_y, coord_x1, coord_y1, width=1.2):
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
    cut_lines.add(gen_cut_line(-100, 345, 1000, 345))
    cut_lines.add(gen_cut_line(545, -150, 545, 500))
    cut_lines.add(gen_cut_line(-100, -8, 1000, -8))
    cut_lines.add(gen_cut_line(-10, -150, -10, 500))
    return cut_lines


def min_to_str(minutes):
    """Convert minutes to hh:mm"""
    if minutes == 0:
        return "--"
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def gen_carnet_de_vol(http_response=None, title="", show_cuts=True, logs=[], reports={}):
    """
    Generate the logbook pdf
    Logs contains all log entries for the book
    """

    if http_response:
        doc = SimpleDocTemplate(http_response, showBoundary=False, bottomMargin=0)
    else:
        doc = SimpleDocTemplate("carner_de_vol.pdf", showBoundary=False, bottomMargin=0)

    # Our container for 'Flowable' objects
    elements = []
    prev_totals = default_totals.copy()

    # check for reported hours and update prev_totals if needed
    if reports:
        if "flytime_cdb" in reports:
            prev_totals["total_flytime_cdb"] = reports["flytime_cdb"]
        if "flytime_dbl" in reports:
            prev_totals["total_flytime_dbl"] = reports["flytime_dbl"]
        if "flytime_ins" in reports:
            prev_totals["total_flytime_ins"] = reports["flytime_ins"]

    # if we have some logs lets group them by year
    if logs:
        page_count = 1
        for year, year_group in groupby(logs, lambda log: log.date.year):
            logs_for_year = list(year_group)

            # add new page every 12 entries
            for i in range(0, len(logs_for_year), NBR_LOGS_PER_PAGE):
                # if not first page we add a break
                if page_count != 1:
                    elements.append(PageBreak())
                # keep track of the totals from the previous page
                bottom_totals = append_new_page(
                    year_str=year,
                    logs=logs_for_year[i : i + NBR_LOGS_PER_PAGE],
                    prev_totals=prev_totals,
                    show_cuts=show_cuts,
                    elements=elements,
                    page_count=page_count,
                )
                # remember totals
                prev_totals = bottom_totals
                page_count += 1

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
        tmp_totals["total_flytime_dbl"] += log.flytime_dbl
        tmp_totals["total_flytime_cdb"] += log.flytime_cdb
        tmp_totals["total_flytime_ins"] += log.flytime_ins

    return tmp_totals


def _calculate_cumulated_totals(page_totals, prev_totals):
    """
    Sum previous totals + current page
    """
    cummul_totals = {}
    for k, _ in page_totals.items():
        cummul_totals[k] = page_totals[k] + prev_totals[k]

    return cummul_totals


def append_new_page(elements=[], prev_totals={}, logs=[], show_cuts=True, year_str="1111", page_count=1):
    """
    Append a new page with 12 log entries and totals to the log book
    """

    # First calculate totals
    page_totals = _calculate_page_totals(logs)
    cummul_totals = _calculate_cumulated_totals(prev_totals, page_totals)

    # Then build the page

    # Header left

    elements.append(gen_header_left(prev_totals, year_str))

    # Inner lines for left page
    body_table_style = TableStyle(
        [
            ("LINEABOVE", (0, 0), (-1, 0), 0.6, DARK_GREY),
            ("LINEABOVE", (0, 1), (-1, -1), 0.3, DARK_GREY),
            ("LINEBEFORE", (0, 0), (-4, -1), 0.6, DARK_GREY),
            ("LINEBEFORE", (-3, 0), (-2, -1), 0.3, DARK_GREY),
            ("LINEBEFORE", (-1, 0), (-1, -1), 0.6, DARK_GREY),
            ("LINEAFTER", (-1, 0), (-1, -1), 0.6, DARK_GREY),
            ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("ALIGN", (4, 0), (8, -1), "CENTER"),
            ("FONT", (0, 0), (-1, -1), HAND_FONT, 6),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )

    # build body data

    body_data = [[" ", " ", " ", " ", " ", " ", " ", " ", " ", " "] for _ in range(12)]
    for i, log in enumerate(logs):
        body_data[i][0] = time.strftime("%d/%m", log.date.timetuple())
        body_data[i][1] = log.glider_type
        body_data[i][2] = log.glider_imma
        body_data[i][3] = log.fctbrd
        body_data[i][4] = log.natvol
        body_data[i][5] = log.lmode
        body_data[i][6] = min_to_str(log.flytime_dbl)
        body_data[i][7] = min_to_str(log.flytime_cdb)
        body_data[i][8] = min_to_str(log.flytime_ins)
        body_data[i][9] = log.obs

    body_table = Table(
        body_data,
        style=body_table_style,
        colWidths=[
            1.52 * cm,
            1.52 * cm,
            1.52 * cm,
            2.02 * cm,
            1.52 * cm,
            1.132 * cm,
            1.32 * cm,
            1.32 * cm,
            1.32 * cm,
            5.62 * cm,
        ],
        rowHeights=[0.70 * cm] * 12,
    )
    body_table.hAlign = "LEFT"
    elements.append(body_table)

    # LABEL "REPORT"
    report = Drawing(0, 0)
    lab = Label()
    lab.setOrigin(0, 0)
    lab.x = 205
    lab.y = 242
    lab.setText("Report .......................................................")
    lab.fontName = "ARIAL"
    lab.strokeColor = colors.Color(0.1, 0.1, 0.1, 0)
    lab.fillColor = colors.Color(0.1, 0.1, 0.1, 0.9)
    lab.fontSize = 6
    report.add(lab)
    elements.append(report)

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
    lab.y = 360
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

    return cummul_totals


##################################### LEFT HEADER ##############################


def gen_header_left(prev_totals={}, year=""):
    """
    Table header for left page
    """
    if prev_totals == {}:
        prev_totals = default_totals.copy()

    # ANNÉE 20   DATE'
    first_header_col_style = TableStyle(
        [
            ("SPAN", (0, 0), (1, 0)),
            ("LINEABOVE", (0, 0), (-1, -1), 0.6, DARK_GREY),
            ("LINEBEFORE", (0, 0), (0, -1), 0.6, DARK_GREY),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONT", (0, 0), (-1, -1), "ARIAL", 7.9),
            ("FONT", (0, 1), (1, 1), "ARIAL", 6.5),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )

    first_col_data = [["ANNÉE\n %s   \nDATE" % (year), ""], [""]]
    first_col_table = Table(
        first_col_data,
        style=first_header_col_style,
        colWidths=[1.52 * cm, 0 * cm],
        rowHeights=[1.52 * cm, 0.7 * cm],
    )

    # PLANEUR, TYPE, IMMATRIC.
    second_header_col_style = TableStyle(
        [
            ("SPAN", (0, 0), (1, 0)),
            ("LINEABOVE", (0, 0), (-1, -1), 0.6, DARK_GREY),
            ("LINEBEFORE", (0, 0), (-1, -2), 0.6, DARK_GREY),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONT", (0, 0), (-1, -1), "ARIAL", 7.9),
            ("FONT", (0, 1), (1, 1), "ARIAL", 6.5),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )

    second_col_data = [["PLANEUR", ""], ["TYPE", "IMMATRIC."], [""]]
    second_col_table = Table(
        second_col_data,
        style=second_header_col_style,
        colWidths=[1.52 * cm, 1.52 * cm],
        rowHeights=[0.5 * cm, 1.02 * cm, 0.7 * cm],
    )

    # FUNCTION À BORD
    third_header_col_style = TableStyle(
        [
            ("SPAN", (0, 0), (1, 0)),
            ("LINEABOVE", (0, 0), (-1, -1), 0.6, DARK_GREY),
            ("LINEBEFORE", (0, 0), (0, 0), 0.6, DARK_GREY),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONT", (0, 0), (-1, -1), "ARIAL", 7.9),
            ("FONT", (0, 1), (1, 1), "ARIAL", 6.5),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )

    third_col_data = [["FUNCTION\nÀ\nBORD", ""], [""]]
    third_col_table = Table(
        third_col_data,
        style=third_header_col_style,
        colWidths=[2.02 * cm, 0 * cm],
        rowHeights=[1.52 * cm, 0.7 * cm],
    )

    # NATURE DU VOL
    fourth_header_col_style = TableStyle(
        [
            ("SPAN", (0, 0), (1, 0)),
            ("LINEABOVE", (0, 0), (-1, -1), 0.6, DARK_GREY),
            ("LINEBEFORE", (0, 0), (0, 0), 0.6, DARK_GREY),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONT", (0, 0), (-1, -1), "ARIAL", 7.9),
            ("FONT", (0, 1), (1, 1), "ARIAL", 6.5),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )

    fourth_col_data = [["NATURE\nDU\nVOL", ""], [""]]
    fourth_col_table = Table(
        fourth_col_data,
        style=fourth_header_col_style,
        colWidths=[1.52 * cm, 0 * cm],
        rowHeights=[1.52 * cm, 0.7 * cm],
    )

    # MODE DE LANCt
    fifth_header_col_style = TableStyle(
        [
            ("SPAN", (0, 0), (1, 0)),
            ("LINEABOVE", (0, 0), (-1, -1), 0.6, DARK_GREY),
            ("LINEBEFORE", (0, 0), (0, 0), 0.6, DARK_GREY),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONT", (0, 0), (-1, -1), "ARIAL", 7.9),
            ("FONT", (0, 1), (1, 1), "ARIAL", 6.5),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )

    fifth_col_data = [["MODE\nDE\nLANCt", ""], [""]]
    fifth_col_table = Table(
        fifth_col_data,
        style=fifth_header_col_style,
        colWidths=[1.13 * cm, 0 * cm],
        rowHeights=[1.52 * cm, 0.7 * cm],
    )

    # HEURES DE VOL, Double Commande, Cdt de Bord, Instructeur
    sixth_header_col_style = TableStyle(
        [
            ("SPAN", (0, 0), (-1, 0)),
            ("FONT", (0, 0), (1, 0), "ARIAL", 7.9),
            ("FONT", (0, 1), (1, 1), "ARIAL", 6.5),
            ("FONT", (0, 1), (-1, -1), "ARIAL", 6.5),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("INNERGRID", (0, 1), (-1, -1), 0.3, DARK_GREY),
            ("LINEABOVE", (0, 0), (-1, -1), 0.6, DARK_GREY),
            ("LINEBEFORE", (0, 0), (0, -1), 0.6, DARK_GREY),
            ("FONT", (0, 2), (-1, 2), HAND_FONT, 6),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )

    sixth_col_data = [
        ["HEURES DE VOL"],
        ["Double\nCommande", "Cdt\nde\nBord", "Instructeur"],
        [
            min_to_str(prev_totals["total_flytime_dbl"]),
            min_to_str(prev_totals["total_flytime_cdb"]),
            min_to_str(prev_totals["total_flytime_ins"]),
        ],
    ]

    sixth_col_table = Table(
        sixth_col_data,
        style=sixth_header_col_style,
        colWidths=[1.32 * cm, 1.32 * cm, 1.32 * cm],
        rowHeights=[0.5 * cm, 1.02 * cm, 0.7 * cm],
    )

    # Table styles
    header_table_style = TableStyle(
        [
            ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("FONT", (0, 0), (-1, -1), "ARIAL", 7.9),
            ("LINEABOVE", (-1, -1), (-1, -1), 0.6, DARK_GREY),
            ("LINEBEFORE", (-1, -1), (-1, -1), 0.6, DARK_GREY),
            ("LINEAFTER", (-1, -1), (-1, -1), 0.6, DARK_GREY),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )

    data = [
        [
            first_col_table,
            second_col_table,
            third_col_table,
            fourth_col_table,
            fifth_col_table,
            sixth_col_table,
            "OBSERVATIONS ET VISA\nDE L'AUTORITÉE HABILITÉE\nOU DE L'INSTRUCTEUR\nRESPONSABLE",
        ]
    ]
    header_table = Table(
        data,
        colWidths=[1.52 * cm, 3.04 * cm, 2.02 * cm, 1.52 * cm, 1.133 * cm, 3.96 * cm, 5.619 * cm],
        rowHeights=[
            2.25 * cm,
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
            ("FONT", (0, 0), (1, 0), "ARIALB", 6.5),
            ("FONT", (0, 1), (-1, -1), HAND_FONT, 7),
            ("ALIGN", (0, 0), (-1, 0), "LEFT"),
            ("LEFTPADDING", (0, 0), (0, 0), 7),
            ("BOTTOMPADDING", (0, 0), (0, 0), 2.5),
            ("LEFTPADDING", (2, 0), (2, 0), 50),
            # heures position
            ("LEFTPADDING", (1, 1), (1, 1), 5),
            # minutes position
            ("LEFTPADDING", (3, 1), (3, 1), 0),
            ("BOTTOMPADDING", (1, 1), (3, 1), 2),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )

    # Total général des heures ... heures et minutes
    total_m = (
        cummul_totals["total_flytime_dbl"]
        + cummul_totals["total_flytime_cdb"]
        + cummul_totals["total_flytime_ins"]
    )

    thour, tmin = 0, 0
    if total_m != 0:
        thour, tmin = min_to_str(total_m).split(":")

    total_hm_data = [
        ["TOTAL GÉNÉRAL DES HEURES DE VOL", "", ""],
        [thour, "heures", tmin, "minutes."],
    ]

    total_hm_table = Table(
        total_hm_data,
        style=total_hm_style,
        colWidths=[1.3 * cm, 1.03 * cm, 1.02 * cm, 1.02 * cm],
        rowHeights=[
            0.70 * cm,
            0.42 * cm,
        ],
    )

    # Totaux à reporter and arrow
    total_report_arrow_style = TableStyle(
        [
            ("FONT", (0, 0), (-1, -1), "ARIALB", 7.0),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
            ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, 0), "BOTTOM"),
            ("RIGHTPADDING", (1, 0), (1, 0), 5),
        ]
    )

    total_report_arrow_data = [["TOTAUX À REPORTER :", ""]]
    total_report_arrow_table = Table(
        total_report_arrow_data,
        style=total_report_arrow_style,
        colWidths=[5.13 * cm, 0.1 * cm],
        rowHeights=[1.05 * cm],
    )

    # Footer table style
    footer_table_style = TableStyle(
        [
            ("INNERGRID", (1, 0), (-1, -1), 0.6, DARK_GREY),
            ("LINEABOVE", (0, 1), (-1, 1), 0.6, DARK_GREY),
            ("LINEABOVE", (0, 0), (-1, 0), 0.6, DARK_GREY),
            ("LINEBEFORE", (0, 0), (0, 0), 0.6, DARK_GREY),
            ("LINEAFTER", (-2, 0), (-1, 0), 0.6, DARK_GREY),
            ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("FONT", (0, 0), (-1, -1), HAND_FONT, 6.5),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )

    data = [
        [
            total_hm_table,
            total_report_arrow_table,
            min_to_str(cummul_totals["total_flytime_dbl"]),
            min_to_str(cummul_totals["total_flytime_cdb"]),
            min_to_str(cummul_totals["total_flytime_ins"]),
            "",
        ]
    ]

    footer_table = Table(
        data,
        colWidths=[4.1 * cm, 5.13 * cm, 1.32 * cm, 1.32 * cm, 1.32 * cm, 5.62 * cm],
        rowHeights=[
            1.10 * cm,
        ],
    )

    footer_table.hAlign = "LEFT"
    footer_table.setStyle(footer_table_style)
    return footer_table


##################################### MAIN #############################


if __name__ == "__main__":
    gen_carnet_de_vol()
