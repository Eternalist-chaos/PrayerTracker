import flet as ft
from datetime import datetime, date, timedelta

# --- CONFIGURATION ---
PRAYER_NAMES = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Warm Islamic Aesthetic Palette
COLOR_PRIMARY = "#8B5A2B"     # Deep warm brown/bronze
COLOR_SECONDARY = "#D4AF37"   # Gold accent
COLOR_BG = "#FAF3E0"          # Warm cream
COLOR_CARD = "#FFFFFF"        # White for cards, maybe tinted
COLOR_CARD_TINT = "#FDFBF7"   # Slightly warm white for inner cards
COLOR_DANGER = "#9E3C3C"      # Warm, deep red
COLOR_TEXT_MAIN = "#4A3B32"   # Soft dark brown for primary text
COLOR_TEXT_MUTED = "#8C7A6B"  # Muted warm brown for secondary text


def main(page: ft.Page):
    page.title = "My Prayer Journey"
    page.scroll = "adaptive"
    page.theme_mode = ft.ThemeMode.LIGHT

        page.bgcolor = COLOR_BG
    page.padding = 0 # Remove page padding, apply to inner container instead

    # Set up custom fonts
    page.fonts = {
        "Cinzel": "https://raw.githubusercontent.com/google/fonts/main/ofl/cinzel/Cinzel-VariableFont_wght.ttf",
        "Lato": "https://raw.githubusercontent.com/google/fonts/main/ofl/lato/Lato-Regular.ttf"
    }
    page.theme = ft.Theme(font_family="Lato")

    # --- 1. DATA LOGIC ---
    def load_data():
        try:
            if not page.client_storage.contains_key("app_data"):
                return {
                    "missed_prayers": {p: 0 for p in PRAYER_NAMES},
                    "daily_status": {p: False for p in PRAYER_NAMES},
                    "last_opened": date.today().isoformat(),
                    "cleared_log": {}
                }
            return page.client_storage.get("app_data")
        except:
            return {
                "missed_prayers": {p: 0 for p in PRAYER_NAMES},
                "daily_status": {p: False for p in PRAYER_NAMES},
                "last_opened": date.today().isoformat(),
                "cleared_log": {}
            }

    def save_data(data):
        try:
            page.client_storage.set("app_data", data)
        except:
            pass

    # Initialize Data
    app_data = load_data()

    # --- 2. MIDNIGHT CHECK ---
    def check_new_day():
        today_str = date.today().isoformat()
        if today_str != app_data.get("last_opened"):
            for p in PRAYER_NAMES:
                if not app_data["daily_status"].get(p, False):
                    app_data["missed_prayers"][p] += 1
            for p in PRAYER_NAMES:
                app_data["daily_status"][p] = False
            app_data["last_opened"] = today_str
            save_data(app_data)
            page.update()

    check_new_day()

    # --- 3. CORE FUNCTIONS ---
    def get_grand_total():
        return sum(app_data["missed_prayers"].values())

    def update_missed_display():
        # Update text counters
        for p in PRAYER_NAMES:
            count = app_data["missed_prayers"][p]
            txt_counters[p].value = str(count)
            txt_counters[p].color = "red400" if count > 0 else "grey700"

        # Update Grand Total
        txt_grand_total.value = f"{get_grand_total()}"

        # Redraw buttons
        render_daily_buttons()
        page.update()

    def toggle_prayer(e):
        p_name = e.control.data
        app_data["daily_status"][p_name] = not app_data["daily_status"][p_name]
        save_data(app_data)
        update_missed_display()

    def make_up_prayer(e):
        p_name = e.control.data
        if not app_data["daily_status"][p_name]:
            app_data["daily_status"][p_name] = True
        elif app_data["missed_prayers"][p_name] > 0:
            app_data["missed_prayers"][p_name] -= 1
        save_data(app_data)
        update_missed_display()

    def render_daily_buttons():
        daily_row.controls.clear()
        for p in PRAYER_NAMES:
            is_done = app_data["daily_status"].get(p, False)
            bg_color = COLOR_PRIMARY if is_done else COLOR_CARD_TINT
            text_color = "white" if is_done else COLOR_TEXT_MAIN
            border_color = "transparent" if is_done else COLOR_SECONDARY

            btn = ft.Container(
                data=p,
                width=55,
                height=55,
                bgcolor=bg_color,
                border_radius=27.5, # Circular look
                border=ft.Border(
                    top=ft.BorderSide(2, border_color),
                    bottom=ft.BorderSide(2, border_color),
                    left=ft.BorderSide(2, border_color),
                    right=ft.BorderSide(2, border_color)
                ),
                alignment=ft.Alignment(0, 0),
                on_click=toggle_prayer,
                content=ft.Text(p[:3].upper(), font_family="Cinzel", weight="bold", size=12, color=text_color)
            )

            makeup_btn = ft.IconButton(
                icon=ft.Icons.ADD,
                icon_size=18,
                data=p,
                on_click=make_up_prayer,
                tooltip=f"Log make-up {p}",
                icon_color=COLOR_SECONDARY,
                bgcolor='#1A8B5A2B'
            )

            col = ft.Column([btn, ft.Container(height=5), makeup_btn], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)
            daily_row.controls.append(col)

    # --- 4. CALCULATOR LOGIC ---
    def calculate_historical(e):
        if not start_picker.value or not end_picker.value:
            page.snack_bar = ft.SnackBar(ft.Text("Please select Start and End dates."), open=True)
            page.update()
            return

        start_d = start_picker.value.date()
        end_d = end_picker.value.date()

        if start_d > end_d:
            page.snack_bar = ft.SnackBar(ft.Text("Start Date cannot be after End Date!"), open=True)
            page.update()
            return

        selected_day_name = dropdown_weekday.value
        target_weekday = WEEKDAYS.index(selected_day_name) if selected_day_name and selected_day_name != "Every Day" else -1

        selected_prayers = []
        if cb_fajr.value: selected_prayers.append("Fajr")
        if cb_dhuhr.value: selected_prayers.append("Dhuhr")
        if cb_asr.value: selected_prayers.append("Asr")
        if cb_mag.value: selected_prayers.append("Maghrib")
        if cb_isha.value: selected_prayers.append("Isha")

        if not selected_prayers:
            page.snack_bar = ft.SnackBar(ft.Text("Please select at least one prayer!"), open=True)
            page.update()
            return

        operation = rg_operation.value

        curr = start_d
        while curr <= end_d:
            if target_weekday == -1 or curr.weekday() == target_weekday:
                for p in selected_prayers:
                    if operation == "add":
                        app_data["missed_prayers"][p] += 1
                    elif operation == "remove":
                        if app_data["missed_prayers"][p] > 0:
                            app_data["missed_prayers"][p] -= 1
            curr += timedelta(days=1)

        save_data(app_data)
        update_missed_display()
        op_text = "Added to" if operation == "add" else "Removed from"
        page.snack_bar = ft.SnackBar(ft.Text(f"{op_text} counters from {start_d} to {end_d}"), open=True)
        page.update()

    # --- 5. RESET / WIPE LOGIC ---
    def perform_wipe(e):
        # 1. Clear Storage
        try:
            page.client_storage.clear()
        except:
            pass

        # 2. Reset Memory
        for p in PRAYER_NAMES:
            app_data["missed_prayers"][p] = 0
            app_data["daily_status"][p] = False
        app_data["cleared_log"] = {}

        # 3. Save Clean State
        save_data(app_data)

        # 4. Close Dialogs & Update UI
        page.close(dlg_confirm_2)
        update_missed_display()
        page.snack_bar = ft.SnackBar(ft.Text("All data has been wiped."), open=True)
        page.update()

    # Dialog 2: Final Warning
    dlg_confirm_2 = ft.AlertDialog(
        modal=True,
        title=ft.Text("FINAL WARNING", color=COLOR_DANGER, weight="bold"),
        content=ft.Text("This action cannot be undone. All your progress will be lost forever. Are you absolutely sure?"),
        actions=[
            ft.TextButton("Cancel", on_click=lambda e: page.close(dlg_confirm_2)),
            ft.TextButton("WIPE EVERYTHING", on_click=perform_wipe, style=ft.ButtonStyle(color=COLOR_DANGER)),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    # Dialog 1: First Confirmation
    dlg_confirm_1 = ft.AlertDialog(
        modal=True,
        title=ft.Text("Reset Data"),
        content=ft.Text("Are you sure you want to reset all counters and history?"),
        actions=[
            ft.TextButton("Cancel", on_click=lambda e: page.close(dlg_confirm_1)),
            ft.TextButton("Yes, Continue", on_click=lambda e: [page.close(dlg_confirm_1), page.open(dlg_confirm_2)]),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    # --- 6. UI COMPONENTS ---
    header = ft.Container(
        content=ft.Column([
            ft.Text("Prayer Tracker", size=28, weight="bold", color=COLOR_PRIMARY),
            ft.Text(date.today().strftime("%A, %B %d"), size=16, color="grey600"),
        ]),
        margin=ft.Margin(0, 0, 0, 15)
    )

    daily_row = ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    daily_card = ft.Card(
        elevation=2,
        content=ft.Container(
            padding=15, bgcolor=COLOR_CARD, border_radius=15,
            content=ft.Column([
                ft.Text("TODAY'S STATUS", size=14, weight="bold", color="grey700"),
                ft.Divider(color="grey200", height=5),
                daily_row
            ])
        )
    )

    txt_grand_total = ft.Text("0", size=45, weight="bold", color="red500")
    total_card = ft.Container(
        padding=15, bgcolor=COLOR_SECONDARY, border_radius=15, alignment=ft.Alignment(0, 0),
        content=ft.Column([
            ft.Text("TOTAL MISSED", size=12, weight="bold", color=COLOR_PRIMARY),
            txt_grand_total
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

    # Missed Stats Grid
    txt_counters = {}
    stat_items = []
    box_width = (page.window_width - 80) / 5 if hasattr(page, 'window_width') and page.window_width else 60

    for p in PRAYER_NAMES:
        txt_counters[p] = ft.Text(str(app_data["missed_prayers"][p]), size=22, weight="bold", color=COLOR_DANGER)
        stat_items.append(
            ft.Container(
                bgcolor=COLOR_CARD, padding=10, border_radius=15,
                border=ft.border.all(1, '#338B5A2B'),
                width=box_width, height=90, alignment=ft.Alignment(0, 0),
                content=ft.Column([
                    ft.Text(p[:3].upper(), font_family="Cinzel", size=11, color=COLOR_TEXT_MUTED, weight="bold"),
                    txt_counters[p]
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )
        )
    stats_grid = ft.Row(controls=stat_items, alignment=ft.MainAxisAlignment.CENTER, spacing=8)

    # Date Pickers
    start_picker = ft.DatePicker(first_date=datetime(2000, 1, 1), last_date=datetime.now())
    end_picker = ft.DatePicker(first_date=datetime(2000, 1, 1), last_date=datetime.now())
    page.overlay.extend([start_picker, end_picker])

    # Tools Controls
    rg_operation = ft.RadioGroup(
        content=ft.Row([
            ft.Radio(value="add", label="Mark as Missed (+)"),
            ft.Radio(value="remove", label="Mark as Prayed (-)")
        ]),
        value="add"
    )
    dropdown_weekday = ft.Dropdown(
        label="Day Filter",
        options=[ft.dropdown.Option("Every Day")] + [ft.dropdown.Option(d) for d in WEEKDAYS],
        value="Every Day",
        height=45,
        text_size=12
    )
    cb_fajr = ft.Checkbox(label="Fajr", value=True); cb_dhuhr = ft.Checkbox(label="Dhuhr", value=True)
    cb_asr = ft.Checkbox(label="Asr", value=False); cb_mag = ft.Checkbox(label="Maghrib", value=False); cb_isha = ft.Checkbox(label="Isha", value=False)

    tools_card = ft.Card(
        elevation=2,
        content=ft.Container(
            border_radius=15, bgcolor=COLOR_CARD,
            content=ft.ExpansionTile(
                title=ft.Text("Calculator & Tools", weight="bold", color="grey700"),
                controls=[
                    ft.Container(padding=15, content=ft.Column([
                        ft.Text("BULK MODIFY RANGE", size=12, weight="bold", color=COLOR_PRIMARY),
                        rg_operation,
                        ft.Row([
                            ft.ElevatedButton("Start", on_click=lambda _: setattr(start_picker, 'open', True) or page.update()),
                            ft.ElevatedButton("End", on_click=lambda _: setattr(end_picker, 'open', True) or page.update())
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        dropdown_weekday,
                        ft.Row([cb_fajr, cb_dhuhr, cb_asr, cb_mag, cb_isha], wrap=True),
                        ft.ElevatedButton("Apply to Tracker", on_click=calculate_historical, bgcolor=COLOR_PRIMARY, color="white", width=400),

                        ft.Divider(height=30),

                        # DANGER ZONE
                        ft.Text("DANGER ZONE", size=12, weight="bold", color=COLOR_DANGER),
                        ft.ElevatedButton(
                            "RESET ALL DATA",
                            icon=ft.Icons.DELETE_FOREVER,
                            bgcolor=COLOR_DANGER,
                            color="white",
                            width=400,
                            on_click=lambda e: page.open(dlg_confirm_1)
                        )
                    ]))
                ]
            )
        )
    )

    # Wrap everything in a main container with the pattern background
    main_content = ft.Container(
        padding=20,
        expand=True,
        content=ft.Column([
            header, total_card, ft.Container(height=15), stats_grid, ft.Container(height=20), daily_card, ft.Container(height=20), tools_card
        ], scroll="adaptive")
    )



    page.add(main_content)
    update_missed_display()

if __name__ == '__main__':
    ft.app(main)