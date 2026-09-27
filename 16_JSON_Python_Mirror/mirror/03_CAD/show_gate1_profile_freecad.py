"""Display the Gate 1 profile data in a FreeCAD Spreadsheet view."""

import gate1_profile


def run():
    try:
        import FreeCAD as App
        import FreeCADGui as Gui
    except ImportError as exc:
        raise RuntimeError(
            "Run this file with FreeCAD's Python console or freecadcmd."
        ) from exc

    document = App.ActiveDocument or App.newDocument("Gate1Profile")
    sheet = document.getObject("Gate1_Profile")
    if sheet is None:
        sheet = document.addObject("Spreadsheet::Sheet", "Gate1_Profile")

    sheet.clearAll()
    sheet.set("A1", "Gate 1 section profile")
    sheet.set("A2", "Channel")
    sheet.set("B2", "xi")
    sheet.set("C2", "x")
    sheet.set("D2", "A")
    sheet.set("E2", "P")
    sheet.set("F2", "Dh")

    columns = ("A", "B", "C", "D", "E", "F")
    row = 3
    for channel in ("CH05", "CH06"):
        for point in gate1_profile.DATA[channel]:
            values = (
                channel,
                point["xi"],
                point["x"],
                point["A"],
                point["P"],
                point["Dh"],
            )
            for column, value in zip(columns, values):
                sheet.set(column + str(row), str(value))
            row += 1

    sheet.setStyle("A1:F2", "bold", "add")
    sheet.setColumnWidth("A", 90)
    for column in "BCDEF":
        sheet.setColumnWidth(column, 110)

    document.recompute()
    Gui.activeDocument().getObject(sheet.Name).show()
    Gui.activeDocument().activeView()
    return sheet


if __name__ == "__main__":
    run()