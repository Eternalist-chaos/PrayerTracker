import flet as ft
from datetime import datetime, date, timedelta

# --- CONFIGURATION ---
PRAYER_NAMES = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

COLOR_PRIMARY = "teal700"
COLOR_SECONDARY = "teal100"
COLOR_BG = "grey100"
COLOR_CARD = "white"
COLOR_DANGER = "red900"

def main(page: ft.Page):
    page.title = "My Prayer Journey"
    page.scroll = "adaptive"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = COLOR_BG
    page.padding = 20

    # --- 1. DATA LOGIC ---
    def load_data():
        if not page.client_storage.contains_key("app_data"):
            return {
                "missed_prayers": {p: 0 for p in PRAYER_NAMES},
                "daily_status": {p: False for p in PRAYER_NAMES},
                "last_opened": date.today().isoformat(),
                "cleared_log": {}
            }
        return page.client_storage.get("app_data")

    def save_data(data):
        page.client_storage.set("app_data", data)

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

    def render_daily_buttons():
        daily_row.controls.clear()
        for p in PRAYER_NAMES:
            is_done = app_data["daily_status"].get(p, False)
            bg_color = COLOR_PRIMARY if is_done else "white"
            text_color = "white" if is_done else COLOR_PRIMARY
            border_color = "transparent" if is_done else COLOR_PRIMARY

            btn = ft.Container(
                data=p,
                width=60,
                height=50,
                bgcolor=bg_color,
                border_radius=8,
                border=ft.Border(
                    top=ft.BorderSide(1, border_color),
                    bottom=ft.BorderSide(1, border_color),
                    left=ft.BorderSide(1, border_color),
                    right=ft.BorderSide(1, border_color)
                ),
                alignment=ft.Alignment(0, 0),
                on_click=toggle_prayer,
                content=ft.Text(p[:3].upper(), weight="bold", size=11, color=text_color)
            )
            daily_row.controls.append(btn)

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
        exc_idx = WEEKDAYS.index(selected_day_name) if selected_day_name else -1
        
        to_skip = []
        if cb_exc_fajr.value: to_skip.append("Fajr")
        if cb_exc_dhuhr.value: to_skip.append("Dhuhr")
        if cb_exc_asr.value: to_skip.append("Asr")
        if cb_exc_mag.value: to_skip.append("Maghrib")
        if cb_exc_isha.value: to_skip.append("Isha")

        curr = start_d
        while curr <= end_d:
            is_exc = (curr.weekday() == exc_idx)
            for p in PRAYER_NAMES:
                if not (is_exc and p in to_skip):
                    app_data["missed_prayers"][p] += 1
            curr += timedelta(days=1)
            
        save_data(app_data)
        update_missed_display()
        page.snack_bar = ft.SnackBar(ft.Text(f"Added prayers from {start_d} to {end_d}"), open=True)
        page.update()

    # --- 5. RESET / WIPE LOGIC ---
    def perform_wipe(e):
        # 1. Clear Storage
        page.client_storage.clear()
        
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
    box_width = (page.window_width - 80) / 5 if page.window_width else 60

    for p in PRAYER_NAMES:
        txt_counters[p] = ft.Text(str(app_data["missed_prayers"][p]), size=20, weight="bold", color="grey700")
        stat_items.append(
            ft.Container(
                bgcolor=COLOR_CARD, padding=5, border_radius=10,
                width=box_width, height=80, alignment=ft.Alignment(0, 0),
                content=ft.Column([
                    ft.Text(p[:3].upper(), size=10, color="grey500", weight="bold"),
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
    dropdown_weekday = ft.Dropdown(label="Day Offset", options=[ft.dropdown.Option(d) for d in WEEKDAYS], height=45, text_size=12)
    cb_exc_fajr = ft.Checkbox(label="Fajr", value=True); cb_exc_dhuhr = ft.Checkbox(label="Dhuhr", value=True)
    cb_exc_asr = ft.Checkbox(label="Asr", value=False); cb_exc_mag = ft.Checkbox(label="Maghrib", value=False); cb_exc_isha = ft.Checkbox(label="Isha", value=False)

    tools_card = ft.Card(
        elevation=2,
        content=ft.Container(
            border_radius=15, bgcolor=COLOR_CARD,
            content=ft.ExpansionTile(
                title=ft.Text("Calculator & Tools", weight="bold", color="grey700"),
                controls=[
                    ft.Container(padding=15, content=ft.Column([
                        ft.Text("BULK ADD RANGE", size=12, weight="bold", color=COLOR_PRIMARY),
                        ft.Row([
                            ft.ElevatedButton("Start", on_click=lambda _: setattr(start_picker, 'open', True) or page.update()), 
                            ft.ElevatedButton("End", on_click=lambda _: setattr(end_picker, 'open', True) or page.update())
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        dropdown_weekday,
                        ft.Row([cb_exc_fajr, cb_exc_dhuhr, cb_exc_asr, cb_exc_mag, cb_exc_isha], wrap=True),
                        ft.ElevatedButton("Run Calculation", on_click=calculate_historical, bgcolor=COLOR_PRIMARY, color="white", width=400),
                        
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

    page.add(header, total_card, ft.Container(height=15), stats_grid, ft.Container(height=20), daily_card, ft.Container(height=20), tools_card)
    update_missed_display()

ft.app(main)