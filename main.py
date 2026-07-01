import os
import flet as ft
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

APP_TITLE = "Piedmont Pool Status"
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://jvkeepbtrkkevrlfimhy.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_856m_EwS_TeYlbze04OXgw_i5gNDuiY")
TABLE_NAME = "pool_status"
ROW_ID = 1

def supabase_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }

# =========================================================
# DATA FUNCTIONS
# =========================================================
def load_status():
    try:
        url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?id=eq.{ROW_ID}&select=*"
        response = requests.get(url, headers=supabase_headers(), timeout=10)
        response.raise_for_status()
        rows = response.json()
        if not rows:
            return {
                "is_open": False,
                "reason": "No status row found.",
                "updated_at": "",
                "error": None,
            }
        row = rows[0]
        return {
            "is_open": bool(row.get("is open", False)),  # FIX: "is open" with space
            "reason": row.get("reason", "") or "",
            "updated_at": row.get("updated _at", "") or "",  # FIX: "updated _at" with space
            "error": None,
        }
    except Exception as e:
        return {
            "is_open": False,
            "reason": "",
            "updated_at": "",
            "error": str(e),
        }

def save_status(is_open: bool, reason: str):
    url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?id=eq.{ROW_ID}"
    payload = {
        "is open": is_open,  # FIX: "is open" with space
        "reason": reason,
        "updated _at": datetime.utcnow().isoformat(),
    }
    headers = supabase_headers()
    headers["Prefer"] = "return=representation"
    response = requests.patch(url, headers=headers, json=payload, timeout=10)
    response.raise_for_status()
    return response.json()

def format_datetime(iso_string: str) -> str:
    """Convert a stored UTC ISO timestamp into a friendly local time string."""
    if not iso_string:
        return ""
    try:
        dt = datetime.fromisoformat(iso_string)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        local_dt = dt.astimezone(ZoneInfo("America/Chicago"))
        return local_dt.strftime("%b %d, %Y at %I:%M %p").replace(" 0", " ")
    except Exception:
        return iso_string

# =========================================================
# APP
# =========================================================
def main(page: ft.Page):
    page.title = APP_TITLE
    page.theme_mode = ft.ThemeMode.LIGHT
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20
    page.window_width = 400
    page.window_height = 800

    title = ft.Text("Piedmont Pool", size=28, weight=ft.FontWeight.BOLD)
    subtitle = ft.Text("Huntsville, AL", size=16, color=ft.Colors.GREY_700)
    pool_icon = ft.Text("🏊", size=56)
    status_text = ft.Text(size=26, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)
    reason_text = ft.Text(size=16, text_align=ft.TextAlign.CENTER)
    updated_text = ft.Text(size=12, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER)
    error_text_main = ft.Text("", color=ft.Colors.RED_700, text_align=ft.TextAlign.CENTER)

    status_card = ft.Container(
        width=320,
        padding=20,
        border_radius=20,
        content=ft.Column(
            [
                status_text,
                reason_text,
                updated_text,
                error_text_main,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        ),
    )

    # =========================================================
    # TOGGLE CONTROLS
    # =========================================================
    toggle_switch = ft.Switch(label="Pool Open", value=False)
    reason_input = ft.TextField(
        label="Reason for Closing",
        multiline=True,
        min_lines=2,
        max_lines=3,
        width=280,
        visible=False,
    )
    toggle_error = ft.Text("", size=12, text_align=ft.TextAlign.CENTER)

    def refresh_ui():
        data = load_status()
        if data["error"]:
            status_card.bgcolor = ft.Colors.GREY_400
            status_text.value = "STATUS UNAVAILABLE"
            reason_text.value = "Could not connect to Supabase."
            updated_text.value = ""
            error_text_main.value = data["error"]
            page.update()
            return

        is_open = data["is_open"]
        reason = data["reason"]
        updated_at = data["updated_at"]
        error_text_main.value = ""

        if is_open:
            status_card.bgcolor = ft.Colors.GREEN_400
            status_text.value = "POOL IS OPEN"
            reason_text.value = "Come on in, the water's fine!"
        else:
            status_card.bgcolor = ft.Colors.RED_400
            status_text.value = "POOL IS CLOSED"
            reason_text.value = f"Reason: {reason}" if reason else "Check back later."

        updated_text.value = f"Last updated: {format_datetime(updated_at)}" if updated_at else ""

        # Keep toggle control in sync with actual saved state
        toggle_switch.value = is_open
        reason_input.value = reason
        reason_input.visible = not is_open

        page.update()

    def on_toggle_change(e):
        """Immediately save the new status when the switch is flipped."""
        toggle_error.value = ""
        reason_input.visible = not toggle_switch.value
        page.update()

        try:
            save_status(toggle_switch.value, reason_input.value or "")
            refresh_ui()
        except Exception as ex:
            toggle_error.value = f"❌ Error: {str(ex)}"
            toggle_error.color = ft.Colors.RED_700
            page.update()

    def on_reason_submit(e):
        """Save an updated closing reason when Enter is pressed in the field."""
        try:
            save_status(toggle_switch.value, reason_input.value or "")
            toggle_error.value = "✅ Reason updated"
            toggle_error.color = ft.Colors.GREEN_700
            refresh_ui()
        except Exception as ex:
            toggle_error.value = f"❌ Error: {str(ex)}"
            toggle_error.color = ft.Colors.RED_700
            page.update()

    toggle_switch.on_change = on_toggle_change
    reason_input.on_submit = on_reason_submit

    # =========================================================
    # LAYOUT
    # =========================================================
    page.add(
        ft.Column(
            [
                pool_icon,
                title,
                subtitle,
                ft.Container(height=10),
                status_card,
                ft.Container(height=20),
                toggle_switch,
                reason_input,
                toggle_error,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        )
    )

    refresh_ui()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8550))
    ft.run(
        main,
        view=ft.AppView.WEB_BROWSER,
        host="0.0.0.0",
        port=port,
    )
