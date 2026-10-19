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

# colors
DARK_GREY = (0.25, 0.25, 0.25)
LIGHT_GREY = (0.5, 0.5, 0.5)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Landscape mode
PAGE_HEIGHT = defaultPageSize[1]
PAGE_WIDTH = defaultPageSize[0]
styles = getSampleStyleSheet()

HAND_FONT = "BLOK"
LEN_MAX_OBS = 50


NBR_LOGS_PER_PAGE = 9
EMPTY_STR = ""


default_totals = {
    "total_flytime_dbl": 0,
    "total_flytime_cdb": 0,
}


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
    cut_lines.add(gen_cut_line(-100, 287, 1000, 287))
    cut_lines.add(gen_cut_line(492, -150, 492, 500))
    cut_lines.add(gen_cut_line(-100, -8, 1000, -8))
    cut_lines.add(gen_cut_line(-10, -150, -10, 500))
    return cut_lines


def min_to_str(minutes):
    """Convert minutes to hh:mm"""
    if minutes == 0:
        return "--"
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def gen_carnet_de_vol(http_response=None, title="", show_cuts=True, logs=[], reports={}):
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

    # if we have some logs lets group them by year
    if logs:
        page_count = 1
        for year, year_group in groupby(logs, lambda log: log.date.year):
            logs_for_year = list(year_group)

            # add new page every 9 entries (but 10 rows on the logbook)
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
    return tmp_totals


def _calculate_cumulated_totals(page_totals, prev_totals):
    """
    Sum previous totals + current page
    """
    cummul_totals = {}
    for k, _ in page_totals.items():
        cummul_totals[k] = page_totals[k] + prev_totals[k]

    return cummul_totals


def append_new_page(elements=[], prev_totals={}, logs=[], show_cuts=True, year_str="2010", page_count=1):
    """
    Append a new page with 14 log entries and totals to the log book
    """
    # first page ? if so we set prev_totals to default_totals
    if not prev_totals:
        prev_totals = default_totals

    # First calculate totals
    page_totals = _calculate_page_totals(logs)
    # cumulated totals (prev + sum logs) that we will pass to the footer
    cummul_totals = _calculate_cumulated_totals(prev_totals, page_totals)

    # Then build the page

    # Header
    elements.append(gen_header(prev_totals))

    # Body
    # Inner lines
    body_table_style = TableStyle(
        [
            ("LINEAFTER", (2, 0), (-2, -1), 0.3, DARK_GREY),
            ("LINEAFTER", (0, 0), (1, -1), 0.3, WHITE),
            ("LINEABOVE", (0, 0), (-1, -1), 0.3, DARK_GREY),
            ("LINEBEFORE", (0, 0), (0, -1), 0.7, DARK_GREY),
            ("LINEAFTER", (-1, 0), (-1, -1), 0.7, DARK_GREY),
            ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("ALIGN", (3, 0), (4, -1), "CENTER"),
            ("ALIGN", (-1, -1), (-1, -1), "LEFT"),
            ("FONT", (0, 0), (-1, -1), "BLOK", 7),
            ("FONT", (-1, 0), (-1, -1), "BLOK", 5.8),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )

    body_data = [["", "", "", "", "", ""] for _ in range(10)]
    # Report line
    body_data[0][3] = min_to_str(prev_totals["total_flytime_dbl"])
    body_data[0][4] = min_to_str(prev_totals["total_flytime_cdb"])

    # let the first line empty
    for i, log in enumerate(logs):
        j = i + 1

        obs = log.obs
        if len(obs) > LEN_MAX_OBS:
            obs = "%s.." % log.obs[: LEN_MAX_OBS - 2]

        body_data[j][0] = time.strftime("%d/%m/%y", log.date.timetuple())
        body_data[j][1] = log.ulm_type
        body_data[j][2] = log.ulm_imma
        body_data[j][3] = min_to_str(log.flytime_dbl)
        body_data[j][4] = min_to_str(log.flytime_cdb)
        body_data[j][5] = obs

    body_table = Table(
        body_data,
        style=body_table_style,
        colWidths=[1.9 * cm, 2.05 * cm, 2.75 * cm, 1.4 * cm, 1.5 * cm, 7.4 * cm],
        rowHeights=[0.6 * cm] * 10,
    )
    body_table.hAlign = "LEFT"
    elements.append(body_table)

    # LABEL "REPORT"
    report = Drawing(0, 0)
    lab = Label()
    lab.setOrigin(0, 0)
    lab.x = 151
    lab.y = 163
    lab.setText("Report _______")
    lab.fontName = "ARIAL"
    lab.strokeColor = colors.Color(0.1, 0.1, 0.1, 0)
    lab.fillColor = colors.Color(0.1, 0.1, 0.1, 0.8)
    lab.fontSize = 9
    report.add(lab)
    elements.append(report)

    # Footer left
    for elmt in gen_footer(cummul_totals):
        elements.append(elmt)
    # elements.append(gen_footer(cummul_totals))

    # Page number left
    page = Drawing(0, 0)
    lab = Label()
    lab.setOrigin(0, 0)
    lab.x = 480
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
    lab.x = 250
    lab.y = 310
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

    return cummul_totals


##################################### LEFT HEADER ##############################


def gen_header(prev_totals={}):
    """
    Table header
    """

    if prev_totals == {}:
        prev_totals = default_totals.copy()

    # HEURES DE VOL, DOUBLE, CDT DE BORD
    fourth_header_col_style = TableStyle(
        [
            ("SPAN", (0, 0), (1, 0)),
            ("LINEABOVE", (0, 1), (1, 1), 0.3, DARK_GREY),
            ("LINEBEFORE", (1, 1), (1, 1), 0.3, DARK_GREY),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONT", (0, 0), (-1, -1), "ARIAL", 9.3),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )

    fourth_col_data = [["HEURES DE VOL", ""], ["Double", "Cdt de\nbord"]]
    fourth_col_table = Table(
        fourth_col_data,
        style=fourth_header_col_style,
        colWidths=[1.4 * cm, 1.5 * cm],
        rowHeights=[0.75 * cm, 1.1 * cm],
    )

    # Table styles
    header_table_style = TableStyle(
        [
            ("INNERGRID", (0, 0), (-1, -1), 0.3, DARK_GREY),
            ("LINEABOVE", (0, 0), (-1, 0), 0.7, DARK_GREY),
            ("LINEBEFORE", (0, 0), (0, 0), 0.7, DARK_GREY),
            ("LINEAFTER", (-1, 0), (-1, 0), 0.7, DARK_GREY),
            ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("FONT", (0, 0), (-1, -1), "ARIAL", 9.3),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )

    data = [["Date", "Type", "Immatriculé", fourth_col_table, "Observations\nNature du vol"]]

    header_table = Table(
        data,
        colWidths=[1.9 * cm, 2.05 * cm, 2.75 * cm, 2.9 * cm, 7.4 * cm],
        rowHeights=[
            1.85 * cm,
        ],
    )

    header_table.hAlign = "LEFT"
    header_table.setStyle(header_table_style)
    return header_table


######################################  FOOTER #############################


def gen_footer(cummul_totals={}):
    """
    Table Footer
    Return a list of reportlab elements which form the footer
    """
    elements = []
    if cummul_totals == {}:
        cummul_totals = default_totals.copy()

    # Total cumulated sum
    total_m = cummul_totals["total_flytime_dbl"] + cummul_totals["total_flytime_cdb"]

    # footer  (Report)
    footer_left_style = TableStyle(
        [
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
            ("ALIGN", (0, 2), (0, 2), "RIGHT"),
            ("RIGHTPADDING", (0, 2), (0, 2), 41),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, DARK_GREY),
            ("FONT", (-2, 0), (-1, -1), "BLOK", 7.5),
            ("FONT", (0, 2), (0, 2), "ARIAL", 9),
        ]
    )
    footer_left_data = [
        [""],
        [""],
        [
            "Report",
            min_to_str(cummul_totals["total_flytime_dbl"]),
            min_to_str(cummul_totals["total_flytime_cdb"]),
        ],
    ]
    footer_left_table = Table(
        footer_left_data,
        style=footer_left_style,
        colWidths=[6.7 * cm, 1.4 * cm, 1.5 * cm],
        rowHeights=[0.6 * cm, 0.6 * cm, 0.7 * cm],
    )

    # footer right (Total ...)

    footer_right_style = TableStyle(
        [
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
            ("ALIGN", (0, 0), (0, 0), "CENTER"),
            ("LINEAFTER", (0, 0), (0, 0), 0.7, DARK_GREY),
            ("LINEBEFORE", (0, 0), (0, 0), 0.3, DARK_GREY),
            ("FONT", (0, 0), (-1, -1), "ARIAL", 9),
        ]
    )
    # min_to_str(total_m),
    # min_to_str(cummul_totals['tothcdb'])
    footer_right_data = [
        [
            "Total gal des h. de vol : \ndont                            H.Cdt de bord",
        ]
    ]
    footer_right_table = Table(
        footer_right_data,
        style=footer_right_style,
        colWidths=[7.4 * cm],
        rowHeights=[
            1.9 * cm,
        ],
    )

    # Total gal
    draw_canvas = Drawing(0, 0)
    lab = Label()
    lab.setOrigin(0, 0)
    lab.x = 452
    lab.y = -33
    lab.setText(min_to_str(total_m))
    lab.fontName = HAND_FONT
    lab.fontSize = 9
    lab.strokeColor = colors.Color(0.1, 0.1, 0.1, 0)
    lab.fillColor = colors.Color(0.1, 0.1, 0.1, 0.8)
    draw_canvas.add(lab)
    elements.append(draw_canvas)

    # Total cdb
    draw_canvas = Drawing(0, 0)
    lab = Label()
    lab.setOrigin(0, 0)
    lab.x = 357
    lab.y = -46
    lab.setText(min_to_str(cummul_totals["total_flytime_cdb"]))
    lab.fontName = HAND_FONT
    lab.fontSize = 9
    lab.strokeColor = colors.Color(0.1, 0.1, 0.1, 0)
    lab.fillColor = colors.Color(0.1, 0.1, 0.1, 0.8)
    draw_canvas.add(lab)
    elements.append(draw_canvas)

    # Footer table style
    footer_table_style = TableStyle(
        [
            ("INNERGRID", (1, 0), (-1, -1), 0.3, DARK_GREY),
            ("LINEABOVE", (0, 1), (-1, 1), 0.3, DARK_GREY),
            ("LINEABOVE", (0, 0), (-1, 0), 0.3, DARK_GREY),
            ("LINEBEFORE", (0, 0), (0, 0), 0.7, DARK_GREY),
            ("LINEBELOW", (0, -1), (-1, -1), 0.7, DARK_GREY),
            ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )

    data = [
        [footer_left_table, footer_right_table],
    ]

    footer_table = Table(data, colWidths=[9.6 * cm, 7.4 * cm], rowHeights=[1.9 * cm])

    footer_table.hAlign = "LEFT"
    footer_table.setStyle(footer_table_style)

    elements.append(footer_table)

    return elements


if __name__ == "__main__":
    gen_carnet_de_vol()
