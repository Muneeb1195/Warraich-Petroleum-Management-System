from datetime import datetime, date

from kivy.uix.screenmanager import Screen
from libs.utils.theme import *
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.metrics import dp

from libs.models.employee import Employee, Attendance
from libs.models.payroll import Payroll
from libs.database.connection import get_connection
from libs.utils.formatting import curr


class StaffScreen(Screen):
    def on_enter(self):
        self._rebuild_employees()
        self._rebuild_attendance()
        self._rebuild_payroll()

    # ==================== EMPLOYEES ====================
    def _rebuild_employees(self):
        container = self.ids.employee_container
        container.clear_widgets()
        employees = Employee.get_all("name")
        if not employees:
            container.add_widget(Label(
                text="No employees yet. Tap + to add one.",
                color=TEXT_AMBER, size_hint_y=None, height=dp(40),
            ))
        else:
            for e in employees:
                container.add_widget(EmployeeCard(e, self))
        container.add_widget(Widget(size_hint_y=1))

    def filter_employees(self, text):
        container = self.ids.employee_container
        text = text.lower()
        for child in container.children:
            if hasattr(child, "emp_data"):
                d = child.emp_data
                match = text in d["name"].lower() or text in d.get("role", "").lower()
                child.opacity = 1 if match else 0.3
                child.disabled = not match

    def show_employee_form(self, employee=None):
        content = EmployeeForm(employee, self)
        popup = Popup(
            title="Edit Employee" if employee else "Add Employee",
            content=content,
            size_hint=(0.9, 0.85),
        )
        content.popup = popup
        popup.open()

    def toggle_employee(self, eid, current_status):
        Employee.update(eid, is_active=0 if current_status else 1)
        self._rebuild_employees()

    # ==================== ATTENDANCE ====================
    def _rebuild_attendance(self):
        date_val = self.ids.attendance_date.text.strip() or date.today().isoformat()
        shift = self.ids.attendance_shift.text
        container = self.ids.attendance_container
        container.clear_widgets()

        employees = Employee.get_active()
        attendance = {a["employee_id"]: a for a in Attendance.get_by_date(date_val) if a["shift"] == shift}

        if not employees:
            container.add_widget(Label(
                text="No active employees found.",
                color=TEXT_AMBER, size_hint_y=None, height=dp(40),
            ))
        else:
            for emp in employees:
                att = attendance.get(emp["id"])
                status = att["status"] if att else "Not Marked"
                container.add_widget(AttendanceRow(emp, status, date_val, shift, self))

        container.add_widget(Widget(size_hint_y=1))

    def mark_attendance(self, employee_id, date_val, shift, status):
        Attendance.mark(employee_id, date_val, shift, status)
        self._rebuild_attendance()

    def mark_all_present(self):
        date_val = self.ids.attendance_date.text.strip() or date.today().isoformat()
        shift = self.ids.attendance_shift.text
        employees = Employee.get_active()
        if not employees:
            return

        confirm = Popup(
            title="Mark All Present",
            content=BoxLayout(orientation="vertical", spacing=dp(8)),
            size_hint=(0.7, 0.35),
        )
        lbl = Label(
            text=f"Mark ALL {len(employees)} employees as Present for {date_val} ({shift})?\n"
                 "Existing marks (Absent, Half Day, etc.) will be overwritten.",
            color=TEXT_PRIMARY, font_size="12sp",
        )
        confirm.content.add_widget(lbl)
        btn_row = BoxLayout(orientation="horizontal", spacing=dp(12), size_hint_y=None, height=dp(40))
        btn_row.add_widget(Button(
            text="Cancel", background_normal="", background_color=BTN_CANCEL, color=TEXT_PRIMARY,
            on_press=confirm.dismiss,
        ))
        btn_row.add_widget(Button(
            text="Mark All", background_normal="", background_color=BTN_SECONDARY, color=TEXT_PRIMARY,
            on_press=lambda *a: (confirm.dismiss(), self._do_mark_all_present(date_val, shift, employees)),
        ))
        confirm.content.add_widget(btn_row)
        confirm.open()

    def _do_mark_all_present(self, date_val, shift, employees):
        for emp in employees:
            Attendance.mark(emp["id"], date_val, shift, "Present")
        self._rebuild_attendance()

    # ==================== PAYROLL ====================
    def _rebuild_payroll(self):
        container = self.ids.payroll_container
        container.clear_widgets()
        month = self._payroll_month()
        year = self._payroll_year()
        records = Payroll.get_by_month(month, year)

        if not records:
            container.add_widget(Label(
                text="No payroll records for this month. Tap Calculate to generate.",
                color=TEXT_AMBER, size_hint_y=None, height=dp(40),
            ))
        else:
            for r in records:
                container.add_widget(PayrollRow(r, self))

        container.add_widget(Widget(size_hint_y=1))
        self._update_payroll_summary(records)

    def _payroll_month(self):
        try:
            return int(self.ids.payroll_month.text or str(datetime.now().month))
        except ValueError:
            return datetime.now().month

    def _payroll_year(self):
        try:
            return int(self.ids.payroll_year.text or str(datetime.now().year))
        except ValueError:
            return datetime.now().year

    def _update_payroll_summary(self, records):
        total_gross = sum(r["gross_salary"] for r in records)
        total_net = sum(r["net_salary"] for r in records)
        paid = sum(1 for r in records if r["paid"])
        self.ids.payroll_summary.text = (
            f"Total Gross: {curr(total_gross)}  |  "
            f"Total Net: {curr(total_net)}  |  "
            f"Paid: {paid}/{len(records)}"
        )

    def calculate_payroll(self):
        month = self._payroll_month()
        year = self._payroll_year()
        employees = Employee.get_active()
        if not employees:
            self._show_error("No active employees to process.")
            return
        for emp in employees:
            Payroll.calculate(emp["id"], month, year)
        self._rebuild_payroll()
        self._show_info("Payroll", f"Payroll calculated for {len(employees)} employees.")

    def mark_paid(self, payroll_id):
        Payroll.mark_paid(payroll_id)
        self._rebuild_payroll()

    # ==================== SHARED ====================
    def show_error(self, msg):
        popup = Popup(
            title="Error",
            content=Label(text=msg, color=TEXT_ERROR),
            size_hint=(0.7, 0.3),
        )
        popup.open()

    def _show_error(self, msg):
        self.show_error(msg)

    def _show_info(self, title, msg):
        popup = Popup(
            title=title,
            content=Label(text=msg, color=TEXT_PRIMARY),
            size_hint=(0.8, 0.4),
        )
        popup.open()

    def go_back(self):
        self.manager.current = "main"


# ==================== EMPLOYEE WIDGETS ====================
class EmployeeCard(BoxLayout):
    def __init__(self, emp, screen, **kwargs):
        super().__init__(**kwargs)
        self.emp_data = emp
        self.screen = screen
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(64)
        self.spacing = dp(2)
        self.padding = [dp(10), dp(6)]

        is_active = emp["is_active"]
        status_text = "Active" if is_active else "Inactive"
        status_color = VAL_POSITIVE if is_active else TEXT_DIM

        top = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(26))
        top.add_widget(Label(
            text=emp["name"], bold=True, color=TEXT_PRIMARY,
            font_size="14sp", halign="left",
        ))
        top.add_widget(Label(
            text=curr(emp["salary_amount"]), color=VAL_POSITIVE,
            font_size="13sp", halign="right", size_hint_x=0.2,
        ))
        top.add_widget(Label(
            text=status_text, color=status_color,
            font_size="12sp", halign="center", size_hint_x=0.15,
        ))
        btn_row = BoxLayout(orientation="horizontal", size_hint_x=0.2, spacing=dp(4))
        edit_btn = Button(text="Edit", font_size="10sp", background_normal="",
                          background_color=BTN_INFO, color=TEXT_PRIMARY)
        edit_btn.bind(on_press=lambda *a: screen.show_employee_form(emp))
        toggle_btn = Button(
            text="Deact" if is_active else "Act",
            font_size="10sp", background_normal="",
            background_color=BTN_STAFF_TOGGLE if is_active else BTN_SECONDARY,
            color=TEXT_PRIMARY,
        )
        toggle_btn.bind(on_press=lambda *a: screen.toggle_employee(emp["id"], is_active))
        btn_row.add_widget(edit_btn)
        btn_row.add_widget(toggle_btn)
        top.add_widget(btn_row)
        self.add_widget(top)

        bot = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(22))
        role = emp.get("role", "")
        phone = emp.get("phone", "")
        sal_type = emp["salary_type"]
        bot.add_widget(Label(
            text=f"Role: {role}" if role else "",
            color=TEXT_SECONDARY, font_size="11sp", halign="left", size_hint_x=0.3,
        ))
        bot.add_widget(Label(
            text=f"Ph: {phone}" if phone else "",
            color=TEXT_SECONDARY, font_size="11sp", halign="left", size_hint_x=0.3,
        ))
        bot.add_widget(Label(
            text=sal_type, color=TEXT_DIM,
            font_size="11sp", halign="left", size_hint_x=0.2,
        ))
        self.add_widget(bot)


class EmployeeForm(BoxLayout):
    def __init__(self, employee, screen, **kwargs):
        super().__init__(**kwargs)
        self.employee = employee
        self.screen = screen
        self.orientation = "vertical"
        self.spacing = dp(6)
        self.padding = [dp(12), dp(6)]

        self.name_input = TextInput(
            text=employee["name"] if employee else "",
            hint_text="Name *", multiline=False,
            foreground_color=(1,1,1,1), background_color=(0.15, 0.15, 0.18, 1),
        )
        self.add_widget(self.name_input)

        self.role_spinner = Spinner(
            text=employee["role"] if employee else "Attendant",
            values=["Manager", "Cashier", "Attendant", "Supervisor", "Other"],
            size_hint_y=None, height=dp(36),
            background_color=(0.18, 0.18, 0.22, 1), color=(1,1,1,1),
        )
        self.add_widget(self.role_spinner)

        self.phone_input = TextInput(
            text=employee.get("phone", "") if employee else "",
            hint_text="Phone", multiline=False,
            foreground_color=(1,1,1,1), background_color=(0.15, 0.15, 0.18, 1),
        )
        self.add_widget(self.phone_input)

        self.address_input = TextInput(
            text=employee.get("address", "") if employee else "",
            hint_text="Address", multiline=False,
            foreground_color=(1,1,1,1), background_color=(0.15, 0.15, 0.18, 1),
        )
        self.add_widget(self.address_input)

        self.bank_input = TextInput(
            text=employee.get("bank_name", "") if employee else "",
            hint_text="Bank Name", multiline=False,
            foreground_color=(1,1,1,1), background_color=(0.15, 0.15, 0.18, 1),
        )
        self.add_widget(self.bank_input)

        self.acct_input = TextInput(
            text=employee.get("bank_account", "") if employee else "",
            hint_text="Bank Account", multiline=False,
            foreground_color=(1,1,1,1), background_color=(0.15, 0.15, 0.18, 1),
        )
        self.add_widget(self.acct_input)

        self.ifsc_input = TextInput(
            text=employee.get("ifsc_code", "") if employee else "",
            hint_text="IFSC Code", multiline=False,
            foreground_color=(1,1,1,1), background_color=(0.15, 0.15, 0.18, 1),
        )
        self.add_widget(self.ifsc_input)

        sal_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(36), spacing=dp(6))
        self.salary_type = Spinner(
            text=employee["salary_type"] if employee else "Fixed",
            values=["Fixed", "Daily"],
            size_hint_x=0.35,
            background_color=(0.18, 0.18, 0.22, 1), color=(1,1,1,1),
        )
        self.amount_input = TextInput(
            text=str(employee["salary_amount"]) if employee else "0",
            hint_text="Amount", input_filter="float", multiline=False,
            size_hint_x=0.6,
            foreground_color=(1,1,1,1), background_color=(0.15, 0.15, 0.18, 1),
        )
        sal_row.add_widget(Label(text="Salary:", size_hint_x=0.2, color=(0.8,0.8,0.8,1)))
        sal_row.add_widget(self.salary_type)
        sal_row.add_widget(self.amount_input)
        self.add_widget(sal_row)

        self.add_widget(Widget())
        btn_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(44), spacing=dp(10))
        save_btn = Button(text="Save", background_normal="",
                          background_color=BTN_PRIMARY, color=(1,1,1,1))
        save_btn.bind(on_press=self._save)
        cancel_btn = Button(text="Cancel", background_normal="",
                            background_color=BTN_CANCEL, color=(1,1,1,1))
        cancel_btn.bind(on_press=lambda *a: self.popup.dismiss())
        btn_row.add_widget(save_btn)
        btn_row.add_widget(cancel_btn)
        self.add_widget(btn_row)

    def _save(self, *args):
        name = self.name_input.text.strip()
        if not name:
            self.screen.show_error("Employee name is required.")
            return
        try:
            amount = float(self.amount_input.text or "0")
        except ValueError:
            amount = 0
        if self.employee:
            Employee.update(self.employee["id"],
                            name=name, role=self.role_spinner.text,
                            phone=self.phone_input.text, address=self.address_input.text,
                            bank_name=self.bank_input.text, bank_account=self.acct_input.text,
                            ifsc_code=self.ifsc_input.text,
                            salary_type=self.salary_type.text, salary_amount=amount)
        else:
            Employee.create(name, self.role_spinner.text,
                            self.phone_input.text, self.address_input.text,
                            self.bank_input.text, self.acct_input.text,
                            self.ifsc_input.text, self.salary_type.text, amount)
        self.popup.dismiss()
        self.screen._rebuild_employees()


# ==================== ATTENDANCE WIDGETS ====================
class AttendanceRow(BoxLayout):
    def __init__(self, emp, current_status, date_val, shift, screen, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(40)
        self.spacing = dp(4)
        self.padding = [dp(4), dp(2)]

        name_lbl = Label(text=emp["name"], size_hint_x=0.2, halign="left", color=(1,1,1,1), font_size="12sp")
        self.add_widget(name_lbl)

        role_lbl = Label(text=emp["role"], size_hint_x=0.12, halign="left", color=(0.8,0.8,0.8,1), font_size="12sp")
        self.add_widget(role_lbl)

        status_clr = {
            "Present": (0.4, 1, 0.4, 1),
            "Absent": (1, 0.4, 0.4, 1),
            "Half Day": (1, 0.8, 0.4, 1),
            "Leave": (0.6, 0.6, 0.6, 1),
            "Not Marked": (0.6, 0.6, 0.6, 1),
        }.get(current_status, (0.6, 0.6, 0.6, 1))

        status_lbl = Label(text=current_status, size_hint_x=0.15, halign="left", color=status_clr, font_size="12sp")
        self.add_widget(status_lbl)

        btn_row = BoxLayout(orientation="horizontal", size_hint_x=0.45, spacing=dp(4))
        for s in ["Present", "Absent", "Half Day", "Leave"]:
            b = Button(
                text=s, font_size="10sp", background_normal="",
                background_color=BTN_SECONDARY if s == "Present" else
                                (0.5, 0.15, 0.15, 1) if s == "Absent" else
                                (0.5, 0.4, 0.15, 1) if s == "Half Day" else
                                (0.3, 0.3, 0.35, 1),
                color=TEXT_PRIMARY,
            )
            if s == current_status:
                b.background_color = (0.1, 0.3, 0.6, 1)
            b.bind(on_press=lambda *a, eid=emp["id"], st=s: screen.mark_attendance(eid, date_val, shift, st))
            btn_row.add_widget(b)
        self.add_widget(btn_row)


# ==================== PAYROLL WIDGETS ====================
class PayrollRow(BoxLayout):
    def __init__(self, record, screen, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(40)
        self.spacing = dp(4)
        self.padding = [dp(4), dp(2)]

        paid_text = "Paid" if record["paid"] else "Pending"
        paid_color = (0.4, 1, 0.4, 1) if record["paid"] else (1, 0.6, 0.2, 1)

        for txt, sx, clr in [
            (record.get("employee_name", ""), 0.18, (1, 1, 1, 1)),
            (record.get("role", ""), 0.1, (1, 1, 1, 1)),
            (str(record["working_days"]), 0.08, (1, 1, 1, 1)),
            (curr(record["gross_salary"]), 0.12, (1, 1, 1, 1)),
            (curr(record["net_salary"]), 0.12, (0.6, 1, 0.6, 1)),
            (paid_text, 0.12, paid_color),
        ]:
            lbl = Label(text=txt, size_hint_x=sx, halign="left", color=clr, font_size="11sp")
            self.add_widget(lbl)

        if not record["paid"]:
            pay_btn = Button(
                text="Mark Paid", font_size="10sp",
                size_hint_x=0.2, background_normal="",
                background_color=BTN_PRIMARY, color=(1,1,1,1),
            )
            pay_btn.bind(on_press=lambda *a: screen.mark_paid(record["id"]))
            self.add_widget(pay_btn)
        else:
            spacer = Widget(size_hint_x=0.2)
            self.add_widget(spacer)
