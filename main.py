import os
import flet as ft
import requests
from datetime import datetime

APP_TITLE = "Piedmont Pool Status"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "piedmont123")
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
# CONFIG
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
            "is_open": bool(row.get("is_open", False)),
            "reason": row.get("reason", "") or "",
            "updated_at": row.get("updated_at", "") or "",
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
        "is_open": is_open,
        "reason": reason,
        "updated_at": datetime.utcnow().isoformat(),
    }
    headers = supabase_headers()
    headers["Prefer"] = "return=representation"
    response = requests.patch(url, headers=headers, json=payload, timeout=10)
    response.raise_for_status()
    return response.json()

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
        updated_text.value = f"Last updated: {updated_at}" if updated_at else ""
        page.update()

    # =========================================================
    # ADMIN PANEL COMPONENTS
    # =========================================================
    password_input = ft.TextField(
        label="Admin Password",
        password=True,
        can_reveal_password=True,
        width=280,
    )
    open_switch = ft.Switch(label="Pool Open", value=False)
    reason_input = ft.TextField(
        label="Reason for Closing",
        multiline=True,
        min_lines=2,
        max_lines=3,
        width=280,
    )
    admin_error = ft.Text("", color=ft.Colors.RED_700)

    def sync_reason_visibility():
        reason_input.visible = not open_switch.value

    def on_switch_change(e):
        sync_reason_visibility()
        page.update()

    open_switch.on_change = on_switch_change

    def close_dialog(e=None):
        admin_dialog.open = False
        page.update()

    def save_admin_changes(e):
        """Save admin changes to Supabase"""
        admin_error.value = ""
        password_input.error_text = None

        # Validate password
        if password_input.value != ADMIN_PASSWORD:
            password_input.error_text = "Incorrect password"
            page.update()
            return

        try:
            # Get values from UI
            is_open = open_switch.value
            closure_reason = reason_input.value or ""

            # Use the existing save_status function
            save_status(is_open, closure_reason)

            # Success feedback
            admin_error.value = "✅ Changes saved successfully!"
            admin_error.color = ft.Colors.GREEN_700
            page.update()

            # Close dialog and refresh after 1 second
            import time
            time.sleep(1)
            close_dialog()
            refresh_ui()

        except Exception as ex:
            admin_error.value = f"❌ Error: {str(ex)}"
            admin_error.color = ft.Colors.RED_700
            page.update()

    def open_admin_dialog(e):
        """Open the admin login dialog"""
        current = load_status()
        password_input.value = ""
        password_input.error_text = None
        admin_error.value = ""
        open_switch.value = current.get("is_open", False)
        reason_input.value = current.get("reason", "")
        sync_reason_visibility()
        admin_dialog.open = True
        page.update()

    admin_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Admin Control Panel"),
        content=ft.Column(
            [
                password_input,
                open_switch,
                reason_input,
                admin_error,
            ],
            tight=True,
            spacing=12,
        ),
        actions=[
            ft.TextButton("Cancel", on_click=close_dialog),
            ft.TextButton("Save", on_click=save_admin_changes),
        ],
    )
    page.overlay.append(admin_dialog)

    # =========================================================
    # MAIN UI
    # =========================================================
    refresh_button = ft.FilledButton(
        "Refresh Status",
        on_click=lambda e: refresh_ui(),
        width=220,
    )
    admin_button = ft.OutlinedButton(
        "Admin Login",
        on_click=open_admin_dialog,
        width=220,
    )

    page.add(
        ft.Column(
            [
                pool_icon,
                title,
                subtitle,
                ft.Container(height=10),
                status_card,
                ft.Container(height=20),
                refresh_button,
                admin_button,
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
