from os import path

from reportlab.pdfbase.ttfonts import TTFont


def register_pdf_assets(pdfmetrics):
    """
    Register fonts for Reportlab
    """
    assets = {}
    # Fonts
    pdfgen_root = path.abspath(path.dirname(__file__))

    pdfmetrics.registerFont(TTFont("ARIAL", path.join(pdfgen_root, "../static/pdf/arial.ttf")))
    pdfmetrics.registerFont(TTFont("ARIALB", path.join(pdfgen_root, "../static/pdf/arial_mt_bold.ttf")))
    pdfmetrics.registerFont(
        TTFont("BIBI", path.join(pdfgen_root, "../static/pdf/Berthold_Imago_Book_Italic.ttf"))
    )
    pdfmetrics.registerFont(TTFont("RABIOHEAD", path.join(pdfgen_root, "../static/pdf/rabiohead.ttf")))
    pdfmetrics.registerFont(TTFont("BLOK", path.join(pdfgen_root, "../static/pdf/Blokletters-Balpen.ttf")))

    # Imgs
    assets["ARROW_IMG"] = path.join(pdfgen_root, "../static/pdf/fleche.png")
    assets["CUT_IMG"] = path.join(pdfgen_root, "../static/pdf/cut.png")
    return assets


def timestr_to_min(time_str, time_in_min):
    """
    Convert time string to minutes
    Formats: hh:mm  or mm
    """
    if time_str.strip() == "":
        return 0
    if time_in_min:
        return int(time_str)
    hours = 0
    if ":" in time_str:
        hours, mins = time_str.split(":")
    else:
        mins = time_str
    return int(hours) * 60 + int(mins)
