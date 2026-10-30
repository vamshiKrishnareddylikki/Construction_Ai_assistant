"""
Tool 7 helper: creates a small, fictional architectural drawing set as a PDF.
It contains deliberate problems (missing sheets, missing NOAs, vague notes) so we know
exactly what the drawing reviewer SHOULD find. That makes the reviewer testable.
"""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle

OUT_PDF = "data/drawings/palmetto_bay_townhomes.pdf"
OUT_TRUTH = "data/drawings/palmetto_bay_townhomes_expected.json"
PROJECT = "PALMETTO BAY TOWNHOMES - BUILDING 2"
W, H = 17, 11  # 11x17 inch landscape sheet


def new_sheet(pdf, number, title):
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
    ax.add_patch(Rectangle((0.3, 0.3), W - 0.6, H - 0.6, fill=False, lw=2))
    # Title block (bottom-right)
    ax.add_patch(Rectangle((12.2, 0.3), 4.5, 2.4, fill=False, lw=1.5))
    tb = [("PROJECT:", PROJECT), ("ARCHITECT:", "Seabreeze Design Studio (fictional)"),
          ("SHEET TITLE:", title), ("DATE:", "2026-09-15   REV: 2  (Issued for Bid)"),
          ("SCALE:", "1/4\" = 1'-0\"" if number.startswith("A-1") else "AS NOTED")]
    for i, (k, v) in enumerate(tb):
        ax.text(12.35, 2.45 - i * 0.33, k, fontsize=7, weight="bold")
        ax.text(13.35, 2.45 - i * 0.33, v, fontsize=7)
    ax.text(15.6, 0.55, number, fontsize=22, weight="bold", ha="center")
    return fig, ax


def table(ax, x, y, headers, rows, widths, title):
    ax.text(x, y + 0.35, title, fontsize=11, weight="bold")
    cx = x
    for h, w in zip(headers, widths):
        ax.add_patch(Rectangle((cx, y - 0.3), w, 0.3, fill=False))
        ax.text(cx + 0.05, y - 0.2, h, fontsize=7, weight="bold")
        cx += w
    for r, row in enumerate(rows, start=1):
        cx = x
        for val, w in zip(row, widths):
            ax.add_patch(Rectangle((cx, y - 0.3 - r * 0.3), w, 0.3, fill=False))
            ax.text(cx + 0.05, y - 0.2 - r * 0.3, val, fontsize=7)
            cx += w


def notes(ax, x, y, lines, title="GENERAL NOTES"):
    ax.text(x, y, title, fontsize=10, weight="bold")
    for i, line in enumerate(lines, start=1):
        ax.text(x, y - 0.3 * i, f"{i}. {line}", fontsize=7.5)


def build():
    with PdfPages(OUT_PDF) as pdf:
        # ---- G-001 Cover sheet with sheet index ----
        fig, ax = new_sheet(pdf, "G-001", "COVER SHEET & SHEET INDEX")
        ax.text(W / 2, 9.3, PROJECT, fontsize=26, weight="bold", ha="center")
        ax.text(W / 2, 8.7, "14 two-story townhome units | 17800 SW 87th Ave (fictional), Miami-Dade County, FL",
                fontsize=12, ha="center")
        ax.text(W / 2, 8.3, "Code: Florida Building Code 8th Ed. | High-Velocity Hurricane Zone (HVHZ)",
                fontsize=11, ha="center")
        table(ax, 1.0, 7.0, ["SHEET", "TITLE"],
              [["G-001", "Cover Sheet & Sheet Index"], ["A-101", "First Floor Plan"],
               ["A-201", "Exterior Elevations"], ["A-601", "Door & Window Schedules"],
               ["S-101", "Foundation Plan"], ["S-201", "Roof Framing & Hurricane Strap Details"]],
              [1.2, 4.5], "SHEET INDEX")
        notes(ax, 8.5, 7.3, [
            "Owner: Palmetto Bay Holdings LLC (fictional).",
            "Contractor shall verify all existing conditions prior to bid.",
            "MEP drawings to be issued under separate cover (date TBD).",
        ], "PROJECT NOTES")
        pdf.savefig(fig); plt.close(fig)

        # ---- A-101 Floor plan ----
        fig, ax = new_sheet(pdf, "A-101", "FIRST FLOOR PLAN")
        rooms = [(1, 4, 4, 4, "LIVING"), (5, 4, 3, 4, "KITCHEN"), (8, 4, 2.5, 4, "DINING"),
                 (1, 2, 3, 2, "GARAGE"), (4, 2, 2, 2, "LAUNDRY"), (6, 2, 2, 2, "BATH 1"), (8, 2, 2.5, 2, "STAIR")]
        for x, y, w, h, name in rooms:
            ax.add_patch(Rectangle((x, y), w, h, fill=False, lw=2))
            ax.text(x + w / 2, y + h / 2, name, fontsize=9, ha="center")
        for x, y, tag in [(2, 8.05, "W1"), (4, 8.05, "W1"), (6.5, 8.05, "W2"), (9.2, 8.05, "W3"), (10.6, 6, "W4")]:
            ax.text(x, y, tag, fontsize=8, weight="bold", bbox=dict(boxstyle="round", fc="white"))
        for x, y, tag in [(3, 3.9, "D1"), (2.5, 1.85, "D2"), (6.8, 3.9, "D3"), (5, 1.85, "D4")]:
            ax.text(x, y, tag, fontsize=8, weight="bold", bbox=dict(boxstyle="circle", fc="white"))
        notes(ax, 11.5, 9.5, [
            "All dimensions to face of stud unless noted.",
            "All exterior openings to be impact-rated per HVHZ requirements.",
            "Kitchen cabinets and countertops by others.",
            "Hurricane straps at all trusses, see S-201.",
            "Flooring finish TBD by owner.",
            "Waterproofing at garage slab: see spec.",
        ])
        pdf.savefig(fig); plt.close(fig)

        # ---- A-201 Elevations ----
        fig, ax = new_sheet(pdf, "A-201", "EXTERIOR ELEVATIONS")
        for x0, label in [(1, "FRONT (NORTH) ELEVATION"), (7, "REAR (SOUTH) ELEVATION")]:
            ax.add_patch(Rectangle((x0, 4), 5, 4, fill=False, lw=2))
            ax.plot([x0, x0 + 2.5, x0 + 5], [8, 9.3, 8], color="black", lw=2)
            for wx in (x0 + 0.6, x0 + 3.4):
                ax.add_patch(Rectangle((wx, 6), 1, 1.2, fill=False))
            ax.text(x0 + 2.5, 3.5, label, fontsize=10, weight="bold", ha="center")
        notes(ax, 1, 2.8, ["Roofing: standing seam metal roof, manufacturer TBD.",
                           "Stucco finish color per owner selection."], "ELEVATION NOTES")
        pdf.savefig(fig); plt.close(fig)

        # ---- A-601 Schedules ----
        fig, ax = new_sheet(pdf, "A-601", "DOOR & WINDOW SCHEDULES")
        table(ax, 0.8, 9.6,
              ["MARK", "SIZE", "TYPE", "IMPACT", "PRODUCT APPROVAL", "QTY"],
              [["W1", "3'-0\" x 5'-0\"", "Single Hung", "YES", "Miami-Dade NOA 23-0412.05", "28"],
               ["W2", "4'-0\" x 4'-0\"", "Horizontal Roller", "YES", "Miami-Dade NOA 22-1108.11", "14"],
               ["W3", "6'-0\" x 8'-0\"", "Fixed", "YES", "", "14"],
               ["W4", "2'-0\" x 3'-0\"", "Awning", "NO", "", "14"],
               ["W5", "8'-0\" x 7'-0\"", "Sliding Glass Door", "YES", "FL# TBD", "14"]],
              [0.7, 1.4, 1.5, 0.8, 2.4, 0.5], "WINDOW SCHEDULE")
        table(ax, 0.8, 6.2,
              ["MARK", "SIZE", "TYPE", "LOCATION", "IMPACT", "PRODUCT APPROVAL"],
              [["D1", "3'-0\" x 8'-0\"", "Fiberglass Entry", "Exterior", "YES", "Miami-Dade NOA 21-0930.02"],
               ["D2", "16'-0\" x 8'-0\"", "Overhead Garage", "Exterior", "YES", ""],
               ["D3", "2'-8\" x 6'-8\"", "Solid Core Wood", "Interior", "N/A", "N/A"],
               ["D4", "2'-6\" x 6'-8\"", "Hollow Core Wood", "Interior", "N/A", "N/A"]],
              [0.7, 1.4, 1.6, 1.0, 0.7, 2.4], "DOOR SCHEDULE")
        notes(ax, 10.2, 9.6, [
            "All exterior windows and doors shall carry a valid",
            "Miami-Dade NOA (HVHZ). Submit with shop drawings.",
            "Hardware sets per spec section 08 71 00.",
            "Garage door wind load rating: verify with engineer.",
        ], "SCHEDULE NOTES")
        pdf.savefig(fig); plt.close(fig)

        # ---- S-101 Foundation plan (S-201 listed in index but NOT included) ----
        fig, ax = new_sheet(pdf, "S-101", "FOUNDATION PLAN")
        ax.add_patch(Rectangle((1, 2), 10, 7, fill=False, lw=2, ls="--"))
        ax.text(6, 5.5, "MONOLITHIC SLAB ON GRADE\n4\" SLAB W/ 6x6 W1.4xW1.4 WWF", fontsize=10, ha="center")
        notes(ax, 11.8, 9.5, ["Concrete: 3000 psi min @ 28 days.",
                              "Soil bearing capacity: per geotechnical report (not provided).",
                              "Termite pretreatment required."], "STRUCTURAL NOTES")
        pdf.savefig(fig); plt.close(fig)

    expected = {
        "sheets_in_set": ["G-001", "A-101", "A-201", "A-601", "S-101"],
        "sheets_listed_but_missing": ["S-201"],
        "missing_disciplines": ["M", "E", "P"],
        "openings_missing_approval": ["W3", "W4", "W5", "D2"],
        "openings_not_impact_rated": ["W4"],
        "long_lead_keywords": ["impact window", "sliding glass door", "garage door", "metal roof"],
        "rfi_candidates_should_mention": ["S-201", "geotechnical", "roof", "flooring", "waterproofing",
                                          "garage door", "W4"],
    }
    with open(OUT_TRUTH, "w") as f:
        json.dump(expected, f, indent=2)
    print(f"Saved {OUT_PDF} (5 sheets) and answer key {OUT_TRUTH}")


if __name__ == "__main__":
    build()
