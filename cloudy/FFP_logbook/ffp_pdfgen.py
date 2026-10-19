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

ASSETS = register_pdf_assets(pdfmetrics)

# colors
DARK_GREY = (0.25, 0.25, 0.25)
LIGHT_GREY = (0.5, 0.5, 0.5)
BLACK = (0, 0, 0)


HAND_FONT = "BLOK"
LEN_MAX_OBS = 50


NBR_LOGS_PER_PAGE = 6
EMPTY_STR = ""

# imgs
ARROW_IMG = "fleche.png"
CUT_IMG = "cut.png"

# Landscape mode
PAGE_HEIGHT = defaultPageSize[1]
PAGE_WIDTH = defaultPageSize[0]
styles = getSampleStyleSheet()


default_totals = {
    "jump_count": 1,
}


def truncchar(s, max_per_ligne=10, max_lines=2):
    if len(s) < max_per_ligne:
        return s
    lines = len(s) / max_per_ligne
    terminate = ""
    if lines > max_lines:
        lines = max_lines
        terminate = "..."
    result = ""
    index = max_per_ligne
    for line in range(1, max_lines):
        ss = s[:index] + "-\n" + s[index : index + max_per_ligne]
        result += ss

        index = index + max_per_ligne
    return result + terminate


def gen_cut_line(x, y, x1, y1, s=1.2):
    return Line(x, y, x1, y1, strokeColor=DARK_GREY, strokeWidth=s, strokeDashArray=[6, 3])


def gen_cut_lines():
    cut_lines = Drawing(1, 1)
    cut_lines.add(gen_cut_line(-100, 260, 1000, 260))
    cut_lines.add(gen_cut_line(405, -150, 405, 500))
    cut_lines.add(gen_cut_line(-100, -8, 1000, -8))
    cut_lines.add(gen_cut_line(-10, -150, -10, 500))
    return cut_lines


def gen_carnet_de_vol(http_response=None, title="", show_cuts=True, logs=[], reports={}):
    if http_response:
        doc = SimpleDocTemplate(http_response, showBoundary=False, bottomMargin=0)
    else:
        doc = SimpleDocTemplate("carner_de_vol.pdf", showBoundary=False, bottomMargin=0)
    page_count = 1
    base_count = 0
    prev_totals = default_totals.copy()
    # Our container for 'Flowable' objects

    elements = []

    if reports:
        prev_totals["jump_count"] = int(reports["jump_count"])

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


def append_new_page(elements=[], prev_totals={}, logs=[], show_cuts=True, year_str="2010", page_count=1):
    """
    Append a new page with 14 log entries and totals to the log book
    """
    # first page ? if so we set prev_totals to default_totals
    if not prev_totals:
        prev_totals = default_totals

    # Our container for 'Flowable' objects

    # Header left
    elements.append(gen_header_left())

    # Inner lines for left page
    BODY_TABLE_STYLE = TableStyle(
        [
            ("INNERGRID", (0, 0), (-1, -1), 0.5, DARK_GREY),
            ("BOX", (0, 0), (-1, -1), 0.4, DARK_GREY),
            ("LINEABOVE", (0, 0), (-1, 0), 0.8, DARK_GREY),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (2, -1), "CENTER"),
            ("ALIGN", (4, 0), (4, -1), "CENTER"),
            ("FONT", (0, 0), (-1, -1), "BLOK", 7),
            ("ALIGN", (3, 0), (3, -1), "LEFT"),
            ("ALIGN", (5, 0), (-1, -1), "LEFT"),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )

    body_data = [[" ", " ", " ", " ", " ", " ", " "] for x in range(6)]
    # let the first line empty
    for i, log in enumerate(logs):
        body_data[i][0] = prev_totals["jump_count"]
        body_data[i][1] = time.strftime("%d/%m/%y", log.date.timetuple())
        body_data[i][2] = log.place
        body_data[i][3] = truncchar(log.aircraft, 7)
        body_data[i][4] = log.altitude
        body_data[i][5] = truncchar(log.canopy, 8)
        body_data[i][6] = truncchar(log.perf_exercise, 26)

        prev_totals["jump_count"] += 1

    body_table = Table(
        body_data,
        style=BODY_TABLE_STYLE,
        colWidths=[1.2 * cm, 1.6 * cm, 1.6 * cm, 1.6 * cm, 1.6 * cm, 1.7 * cm, 4.7 * cm],
        rowHeights=[1.2 * cm] * 6,
    )
    body_table.hAlign = "LEFT"
    elements.append(body_table)

    # Footer left

    # Page number left
    page = Drawing(0, 0)
    lab = Label()
    lab.setOrigin(0, 0)
    lab.x = 420
    lab.y = -30
    lab.setText("p %s" % page_count)
    lab.fontName = "ARIAL"
    lab.fontSize = 9
    page.add(lab)
    elements.append(page)
    page_count = page_count + 1

    # Year
    year = Drawing(0, 0)
    lab = Label()
    lab.setOrigin(0, 0)
    lab.x = 195
    lab.y = 280
    lab.setText("ANNÉE %s" % year_str)
    lab.fontName = "ARIALB"
    lab.fontSize = 11
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
    elements.append(gen_header_right())

    # Inner lines  RIGHT PAGE
    BODY_TABLE_STYLE = TableStyle(
        [
            ("INNERGRID", (0, 0), (-1, -1), 0.5, DARK_GREY),
            ("BOX", (0, 0), (-1, -1), 0.5, DARK_GREY),
            ("LINEABOVE", (0, 0), (-1, 0), 0.8, DARK_GREY),
            ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONT", (0, 0), (-1, -1), "BLOK", 7),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )

    body_data = [[" ", " "] for x in range(6)]
    # let the first line empty
    for i, log in enumerate(logs):
        body_data[i][0] = truncchar(log.freefall_training, 40)
        body_data[i][1] = truncchar(log.canopy_piloting, 40)

        prev_totals["jump_count"] += 1
    body_table = Table(
        body_data, style=BODY_TABLE_STYLE, colWidths=[7 * cm, 7 * cm], rowHeights=[1.2 * cm] * 6
    )
    body_table.hAlign = "LEFT"
    elements.append(body_table)

    # Page number left
    page = Drawing(0, 0)
    lab = Label()
    lab.setOrigin(0, 0)
    lab.x = 420
    lab.y = -30
    lab.setText("p %s" % page_count)
    lab.fontName = "ARIAL"
    lab.fontSize = 9
    page.add(lab)
    elements.append(page)
    page_count = page_count + 1

    if show_cuts:
        # Dashed cut lines: up right bottom left
        cut_lines = gen_cut_lines()
        elements.append(cut_lines)
        # Cut image, a flowable so we position it using indenters and spacers ...
        elements.append(Indenter(left=-24.9 * cm))
        elements.append(Spacer(0, 35))
        elements.append(Image(ASSETS["CUT_IMG"], 30 / 2, 56 / 2.0))
        elements.append(Indenter(left=24.9 * cm))
    return prev_totals


##################################### LEFT HEADER ##############################


def gen_header_left():
    """
    Table header for left page
    """
    # SAUT
    SECOND_HEADER_COL_STYLE = TableStyle(
        [
            ("SPAN", (0, 0), (1, 0)),
            ("INNERGRID", (1, 0), (-1, -1), 0.5, DARK_GREY),
            ("BOX", (1, 0), (-1, -1), 0.4, DARK_GREY),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONT", (0, 0), (-1, 0), "ARIAL", 7.8),
            ("FONT", (0, -1), (-1, -1), "ARIAL", 6.5),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )

    # Table styles
    HEADER_TABLE_STYLE = TableStyle(
        [
            ("VALIGN", (0, 0), (1, 0), "BOTTOM"),
            ("INNERGRID", (1, 0), (-1, -1), 0.5, DARK_GREY),
            ("LINEABOVE", (0, 0), (0, 0), 0.5, DARK_GREY),
            ("LINEBEFORE", (0, 0), (0, -1), 0.5, DARK_GREY),
            ("BOX", (1, 0), (-1, -1), 0.5, DARK_GREY),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("VALIGN", (0, -1), (1, -1), "TOP"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("FONT", (0, 0), (-1, -1), "ARIAL", 7.8),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )

    data = [
        [
            "SAUT N*\nJump n*",
            "DATE\nDate",
            "LIEU\nPlace",
            "AÉRONEF\nAicraft",
            "HAUTEUR\nAltitude",
            "VOILURE\nPRINCIPALE\nMain Canopy",
            "PROGRAMME DU SAUT\nPerformed excercice",
        ],
    ]

    header_table = Table(
        data,
        colWidths=[1.2 * cm, 1.6 * cm, 1.6 * cm, 1.6 * cm, 1.6 * cm, 1.7 * cm, 4.7 * cm],
        rowHeights=[
            1.5 * cm,
        ],
    )

    header_table.hAlign = "LEFT"
    header_table.setStyle(HEADER_TABLE_STYLE)
    return header_table


##################################### RIGHT HEADER #############################


def gen_header_right():
    """
    Table header for right page
    """
    # OBSERVATIONS
    SECOND_HEADER_COL_STYLE = TableStyle(
        [
            ("SPAN", (0, 0), (1, 0)),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, DARK_GREY),
            ("BOX", (0, 0), (-1, -1), 0.5, DARK_GREY),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONT", (0, 0), (-1, 0), "ARIAL", 7.8),
            ("FONT", (0, -1), (-1, -1), "ARIAL", 6.5),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )

    second_col_data = [
        ["OBSERVATIONS DU MONITEUR -", ""],
        ["Exercise en chute - Freefall training", "Exercise sous voile - Canopy piloting"],
    ]
    second_col_table = Table(
        second_col_data,
        style=SECOND_HEADER_COL_STYLE,
        colWidths=[7 * cm, 7 * cm],
        rowHeights=[0.8 * cm, 0.6 * cm],
    )

    data = [
        [second_col_table],
    ]

    header_table = Table(
        data,
        colWidths=[14.0 * cm],
        rowHeights=[
            1.4 * cm,
        ],
    )
    # Table style
    HEADER_TABLE_STYLE = TableStyle(
        [
            ("INNERGRID", (0, 0), (-1, -1), 0.5, DARK_GREY),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("FONT", (0, 0), (-1, -1), "ARIAL", 9.3),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_GREY),
        ]
    )
    header_table.hAlign = "LEFT"
    header_table.setStyle(HEADER_TABLE_STYLE)
    return header_table


##################################### MAIN #############################
if __name__ == "__main__":
    gen_carnet_de_vol()
