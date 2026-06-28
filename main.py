import os
import flet as ft
import flet as ft
import urllib.request
import csv
from io import StringIO

# =========================================================
# CONFIG
# =========================================================
SHEET_URL = "[docs.google.com](https://docs.google.com/spreadsheets/d/1-V1jtdTDTYHFcLuLLJvD6P4pGZ3Lv20MCR95Z8OjxcE/edit?usp=sharing)"


def get_csv_url(sheet_url: str) -> str:
    sheet_url = sheet_url.strip()

    # If a markdown-style link ever gets pasted in, strip it
    if sheet_url.startswith("[") and "](" in sheet_url and sheet_url.endswith(")"):
        sheet_url = sheet_url.split("](", 1)[1][:-1]

    base = sheet_url.split("?", 1)[0]
    if "/edit" in base:
        base = base.split("/edit", 1)[0]

    return f"{base}/export?format=csv"


def get_pool_data():
    try:
        csv_url = get_csv_url(SHEET_URL)
        print("CSV URL:", repr(csv_url))

        with urllib.request.urlopen(csv_url, timeout=10) as response:
            content = response.read().decode("utf-8", errors="replace")

        rows = list(csv.reader(StringIO(content)))
        print("ROWS:", rows)

        if len(rows) < 2:
            return False, "No updates posted yet.", None

        header = [h.strip().lower() for h in rows[0]]
        row = rows[1]

        status_idx = header.index("status") if "status" in header else 0
        reason_idx = header.index("reason") if "reason" in header else 1

        status = row[status_idx].strip() if len(row) > status_idx else "Closed"
        reason = row[reason_idx].strip() if len(row) > reason_idx else ""

        return status.lower() == "open", reason, None

    except Exception as e:
        print("READ ERROR:", repr(e))
        return False, "", str(e)


def main(page: ft.Page):
    page.title = "Piedmont Pool Status"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20

    page.window_width = 400
    page.window_height = 800

    icon = ft.Text("🏊", size=56)
    title = ft.Text("Piedmont Pool", size=28, weight=ft.FontWeight.BOLD)
    subtitle = ft.Text("Huntsville, AL", size=16, color=ft.Colors.GREY_700)

    status_text = ft.Text(
        size=26,
        weight=ft.FontWeight.BOLD,
        text_align=ft.TextAlign.CENTER,
    )

    detail_text = ft.Text(
        size=16,
        text_align=ft.TextAlign.CENTER,
    )

    error_text = ft.Text(
        size=12,
        color=ft.Colors.RED_700,
        text_align=ft.TextAlign.CENTER,
    )

    status_card = ft.Container(
        width=320,
        padding=20,
        border_radius=20,
        content=ft.Column(
            [
                status_text,
                detail_text,
                error_text,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        ),
    )

    def refresh_status(e=None):
        status_text.value = "Refreshing..."
        detail_text.value = ""
        error_text.value = ""
        status_card.bgcolor = ft.Colors.BLUE_GREY_100
        page.update()

        is_open, reason, err = get_pool_data()

        if err:
            status_card.bgcolor = ft.Colors.GREY_400
            status_text.value = "STATUS UNAVAILABLE"
            detail_text.value = "Could not read the pool status sheet."
            error_text.value = err
        elif is_open:
            status_card.bgcolor = ft.Colors.GREEN_400
            status_text.value = "POOL IS OPEN"
            detail_text.value = "Come on in, the water's fine!"
            error_text.value = ""
        else:
            status_card.bgcolor = ft.Colors.RED_400
            status_text.value = "POOL IS CLOSED"
            detail_text.value = f"Reason: {reason}" if reason else "Check back later."
            error_text.value = ""

        page.update()

    page.add(
        ft.Column(
            [
                icon,
                title,
                subtitle,
                ft.Container(height=10),
                status_card,
                ft.Container(height=20),
                ft.FilledButton(
                    "Refresh Status",
                    on_click=refresh_status,
                    width=220,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        )
    )

    refresh_status()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8550))
    ft.run(
        main,
        view=ft.AppView.WEB_BROWSER,
        port=port,
        host="0.0.0.0",
    )
