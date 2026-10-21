from datetime import datetime, timedelta
from tkinter import *
from tkinter import ttk, messagebox
import requests  # used by Register

# Backend address
API_URL = "http://127.0.0.1:8000"

#THEME 
BG, PANEL, ACCENT, ACCENT2 = "#F4F8FB", "#FFFFFF", "#2E6F95", "#F0A868"
TEXT, MUTED = "#1B2B34", "#7A8B96"
FONT, FONT_B, FONT_H = ("Segoe UI", 10), ("Segoe UI", 10, "bold"), ("Segoe UI", 16, "bold")
STATUS_BG = {"pending": "#FCEEDD", "confirmed": "#E3EEF4", "completed": "#E5F2EA", "cancelled": "#FBEAE9", "disputed": "#FBEAE9"}
STATUS_FG = {"pending": "#B5762E", "confirmed": "#24567A", "completed": "#2F7A4C", "cancelled": "#A8382E", "disputed": "#A8382E"}
#MOCK DATA 
MOCK_DB = {
    "users": {
        1: {"name": "Riya Shah", "email": "riya@college.edu", "credits": 2, "rating": 4.6, "rating_count": 3},
        2: {"name": "Aman Verma", "email": "aman@college.edu", "credits": 9, "rating": 4.8, "rating_count": 5},
        3: {"name": "Neha Patil", "email": "neha@college.edu", "credits": 6, "rating": 4.3, "rating_count": 2},
    },
    "skills": {1: "Python", 2: "SQL", 3: "Guitar", 4: "Public Speaking", 5: "Excel"},
    # (user_id, skill_id, type, level) -- type is "offered" or "requested"
    "user_skills": [
        (2, 1, "offered", "Expert"), (2, 2, "offered", "Intermediate"),
        (3, 3, "offered", "Intermediate"), (3, 4, "offered", "Beginner"),
        (1, 5, "requested", "-"), (1, 3, "requested", "-"),
    ],
    "availability": {1: "Weekday evenings", 2: "Weekend mornings", 3: "Weekday afternoons"},
    "bookings": [
        {"id": 1, "learner": 1, "teacher": 2, "skill": 1, "date": "2026-10-12", "time": "18:00", "hours": 2, "status": "pending"},
        {"id": 2, "learner": 1, "teacher": 3, "skill": 3, "date": "2026-10-13", "time": "10:00", "hours": 1, "status": "confirmed"},
        {"id": 3, "learner": 1, "teacher": 2, "skill": 2, "date": "2026-10-05", "time": "19:00", "hours": 1, "status": "completed"},
    ],
    "transactions": [{"from": 1, "to": 2, "amount": 1, "date": "27 Sep", "type": "escrow_release"}],
    "disputes": [],
    "reviews": [],
    "next_id": 4,
}
state = {"uid": 1, "db_uid": None}
# ROOT WINDOW
top = Tk()
top.title("SkillSwap")
top.geometry("400x450")
top.configure(bg=BG)
style = ttk.Style(top)
style.theme_use("clam")
style.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=TEXT, rowheight=26, font=FONT)
style.configure("Treeview.Heading", background=BG, foreground=MUTED, font=FONT_B)
style.map("Treeview", background=[("selected", ACCENT)], foreground=[("selected", "#FFFFFF")])
def clear():
    for widget in top.winfo_children():
        widget.destroy()
def overlaps(date, tm, hours, b):
    """True if a new booking (date, tm, hours) overlaps existing booking b."""
    new_start = datetime.strptime(f"{date} {tm}", "%Y-%m-%d %H:%M")
    old_start = datetime.strptime(f"{b['date']} {b['time']}", "%Y-%m-%d %H:%M")
    return new_start < old_start + timedelta(hours=b["hours"]) and old_start < new_start + timedelta(hours=hours)
def credits_locked(uid):
    return sum(b["hours"] for b in MOCK_DB["bookings"]
               if b["learner"] == uid and b["status"] in ("pending", "confirmed", "disputed"))
# LOGIN 
def show_login():
    clear()
    top.title("SkillSwap - Login")
    top.geometry("400x350")

    form = Frame(top, bg=BG)
    form.place(relx=0.5, rely=0.5, anchor="center")

    Label(form, text="SkillSwap", bg="#2E6F95", fg="white", height=1, width=10, bd=10, font=("Segoe UI", 20, "bold")).grid(row=0, column=0, columnspan=2, padx=10, pady=10)
    Label(form, text="Email", bg="light yellow", height=1, width=10, bd=10, font=("Segoe UI", 15)).grid(row=1, column=0, padx=10, pady=10)
    e1 = Entry(form, width=30)
    e1.grid(row=1, column=1)
    Label(form, text="Password", bg="light yellow", height=1, width=10, bd=10, font=("Segoe UI", 15)).grid(row=2, column=0, padx=10, pady=10)
    e2 = Entry(form, width=30, show="*", fg="red")
    e2.grid(row=2, column=1)
    
    def fun():
        email = e1.get().strip().lower()
        password = e2.get()

        if not email or not password:
            messagebox.showerror("Warning", "Fill all fields!")
            return

        try:
            response = requests.post(
                f"{API_URL}/login",
                json={"email": email, "password": password},
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                user = data.get("user", data)

                db_user_id = int(user["id"])
                uid = 1000 + db_user_id

                MOCK_DB["users"][uid] = {
                    "name": user.get("name", ""),
                    "email": user.get("email", email),
                    "credits": user.get("credits", 5),
                    "rating": user.get("rating", 0.0),
                    "rating_count": user.get("rating_count", 0)
                }

                state["uid"] = uid
                state["db_uid"] = db_user_id
                show_main()

            else:
                try:
                    detail = response.json().get(
                        "detail", "Invalid email or password"
                    )
                except ValueError:
                    detail = "Invalid email or password"

                messagebox.showerror("Login failed", str(detail))

        except requests.exceptions.ConnectionError:
            messagebox.showerror(
                "Connection Error",
                f"Cannot reach the server at {API_URL}. Is it running?"
            )
        except requests.exceptions.Timeout:
            messagebox.showerror(
                "Timeout", "The server took too long to respond."
            )
        except requests.exceptions.RequestException as exc:
            messagebox.showerror("Request Error", str(exc))
        except (ValueError, KeyError, TypeError) as exc:
            messagebox.showerror(
                "Error", f"Unexpected server response: {exc}"
            )

        show_main()
    Button(form, text="Login", bg="sky blue", activebackground="yellow", command=fun).grid(row=3, column=0, columnspan=2, pady=10)
    Button(form, text="Create an account", command=show_register).grid(row=4, column=0, columnspan=2, pady=5)
# REGISTER 

def show_register():
    clear()
    top.title("SkillSwap - Register")
    top.geometry("400x420")
    form = Frame(top, bg=BG)
    form.place(relx=0.5, rely=0.5, anchor="center")

    Label(form, text="Create Account", bg="#2E6F95", fg="white", height=1, width=14, bd=10, font=("Segoe UI", 20, "bold")).grid(row=0, column=0, columnspan=2, padx=10, pady=10)
    Label(form, text="Name : ", bg="light yellow", height=1, width=10, bd=5, font=("Segoe UI", 11)).grid(row=1, column=0, padx=5, pady=5)
    e1 = Entry(form, width=25)
    e1.grid(row=1, column=1)

    Label(form, text="Email : ", bg="light yellow", height=1, width=10, bd=5, font=("Segoe UI", 11)).grid(row=2, column=0, padx=5, pady=5)
    e2 = Entry(form, width=25)
    e2.grid(row=2, column=1)

    Label(form, text="Department:", bg="light yellow", height=1, width=10, bd=5, font=("Segoe UI", 11)).grid(row=3, column=0, padx=5, pady=5)
    e_dept = Entry(form, width=25)
    e_dept.grid(row=3, column=1)

    Label(form, text="Password : ", bg="light yellow", height=1, width=10, bd=5, font=("Segoe UI", 11)).grid(row=4, column=0, padx=5, pady=5)
    e3 = Entry(form, width=25, show="*", fg="red")
    e3.grid(row=4, column=1)

    def fun():
        name = e1.get().strip()
        email = e2.get().strip().lower()
        department = e_dept.get().strip()
        password = e3.get()

        if not name or not email or not department or not password:
            messagebox.showerror("Warning", "Fill all fields!")
            return

        payload = {
            "name": name,
            "email": email,
            "department": department,
            "password": password,
            "availability": ["Mon-Evening"]
        }

        try:
            response = requests.post(
                f"{API_URL}/users",
                json=payload,
                timeout=5
            )

            if response.status_code in (200, 201):
                data = response.json()
                u = data.get("user", data)

                if "id" in u:
                    MOCK_DB["users"][1000 + int(u["id"])] = {
                        "name": u.get("name", name),
                        "email": u.get("email", email),
                        "credits": u.get("credits", 5),
                        "rating": 0.0,
                        "rating_count": 0
                    }

                messagebox.showinfo(
                    "Success",
                    "Registered successfully in MySQL database!"
                )
                show_login()

            else:
                try:
                    detail = response.json().get(
                        "detail", "Registration failed"
                    )
                except ValueError:
                    detail = f"Registration failed (server returned {response.status_code})"

                messagebox.showerror("Error", str(detail))

        except requests.exceptions.ConnectionError:
            messagebox.showerror(
                "Connection Error",
                f"Cannot reach the server at {API_URL}. Is it running?"
            )

        except requests.exceptions.Timeout:
            messagebox.showerror(
                "Timeout",
                "The server took too long to respond. Try again."
            )

        except requests.exceptions.RequestException as exc:
            messagebox.showerror("Request Error", str(exc))

        except (ValueError, KeyError, TypeError) as exc:
            messagebox.showerror("Error", f"Unexpected server response: {exc}")

    Button(form, text="Register", bg="sky blue", activebackground="yellow", command=fun).grid(row=5, column=0, columnspan=2, pady=10)
    Button(form, text="Back to login", command=show_login).grid(row=6, column=0, columnspan=2)

    Button(form, text="Register", bg="sky blue", activebackground="yellow", command=fun).grid(row=5, column=0, columnspan=2, pady=10)
    Button(form, text="Back to login", command=show_login).grid(row=6, column=0, columnspan=2)
# MAIN SHELL
body = None
title_lbl = None
credit_lbl = None
nav_btns = {}
def show_main():
    global body, title_lbl, credit_lbl, nav_btns
    clear()
    top.title("SkillSwap")
    top.geometry("1040x620")
    top.configure(bg=BG)
    side = Frame(top, bg=PANEL, width=190)
    side.pack(side="left", fill="y")
    side.pack_propagate(False)
    Label(side, text="SkillSwap", bg=PANEL, fg=TEXT, font=FONT_H, pady=20).pack()
    nav_btns = {}
    pages = [
        ("browse", "Find a peer", page_browse),
        ("sessions", "My sessions", page_sessions),
        ("myskills", "My skills", page_myskills),
        ("wallet", "Wallet", page_wallet),
        ("analytics", "Analytics", page_analytics),
        ("top", "Top teachers", page_top),
    ]
    for key, label, fn in pages:
        b = Button(side, text=label, bg=PANEL, fg=MUTED, activebackground="#E3EEF4", activeforeground=TEXT,
                  relief="flat", anchor="w", font=FONT, padx=18, pady=10, bd=0, command=lambda f=fn, k=key: goto(k, f))
        b.pack(fill="x")
        nav_btns[key] = b
    Button(side, text="Log out", bg=PANEL, fg="#A8382E", relief="flat", anchor="w", font=FONT,
          padx=18, pady=10, bd=0, command=show_login).pack(fill="x", side="bottom", pady=10)

    right = Frame(top, bg=BG)
    right.pack(side="left", fill="both", expand=True)
    bar = Frame(right, bg=BG)
    bar.pack(fill="x", padx=20, pady=16)
    title_lbl = Label(bar, bg=BG, fg=TEXT, font=FONT_H)
    title_lbl.pack(side="left")
    credit_lbl = Label(bar, bg=ACCENT2, fg="#4A2A0A", font=FONT_B, padx=12, pady=4)
    credit_lbl.pack(side="right")
    body = Frame(right, bg=BG)
    body.pack(fill="both", expand=True, padx=20)
    goto("browse", page_browse)
def goto(key, page_fn):
    for k, b in nav_btns.items():
        b.configure(bg=ACCENT if k == key else PANEL, fg="#FFFFFF" if k == key else MUTED)
    for w in body.winfo_children():
        w.destroy()
    u = MOCK_DB["users"][state["uid"]]
    locked = credits_locked(state["uid"])
    credit_lbl.config(text=f"{u['credits']} available  |  {locked} in escrow")
    page_fn()
# PEER MATCHER -- skill + availability + min rating filters
def page_browse():
    title_lbl.config(text="Find a peer")
    uid = state["uid"]

    bar = Frame(body, bg=BG)
    bar.pack(fill="x")
    Label(bar, text="Skill", bg=BG, fg=MUTED).grid(row=0, column=0, sticky="w")
    kw = Entry(bar, width=16)
    kw.grid(row=1, column=0, padx=(0, 10), ipady=3)
    Label(bar, text="Availability", bg=BG, fg=MUTED).grid(row=0, column=1, sticky="w")
    avail = ttk.Combobox(bar, values=["Any", "Weekday evenings", "Weekend mornings", "Weekday afternoons"], state="readonly", width=18)
    avail.set("Any")
    avail.grid(row=1, column=1, padx=(0, 10))
    Label(bar, text="Min rating", bg=BG, fg=MUTED).grid(row=0, column=2, sticky="w")
    minr = ttk.Combobox(bar, values=["Any", "3.0", "4.0", "4.5"], state="readonly", width=8)
    minr.set("Any")
    minr.grid(row=1, column=2, padx=(0, 10))
    rows_holder = {}
    cols = ("teacher", "skill", "level", "rating", "availability")
    t = ttk.Treeview(body, columns=cols, show="headings", height=8)
    for c in cols:
        t.heading(c, text=c.title())
        t.column(c, width=130)
    t.pack(fill="both", expand=True, pady=10)
    def load():
        for i in list(t.get_children()):
            t.delete(i)
        rows_holder.clear()
        try:
            params = {
                "skill_name": kw.get().strip(),
                "exclude_user_id": state.get("db_uid"),
                "min_rating": 0 if minr.get() == "Any" else float(minr.get()),
            }
            if avail.get() != "Any":
                params["availability"] = avail.get()
            response = requests.get(f"{API_URL}/matches", params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            for match in data.get("matches", []):
                teacher_id = int(match["user_id"])
                sid = int(match["skill_id"])
                sname = match["skill"]
                teacher_name = match["name"]
                level = match.get("level") or "Not set"
                rating = match.get("rating", 0)
                availability = ", ".join(match.get("availability", [])) or "-"
                iid = f"{teacher_id}-{sid}"
                rows_holder[iid] = (teacher_id, teacher_name, sid, sname, level)
                t.insert("", "end", iid=iid, values=(teacher_name, sname, level, rating, availability))
        except requests.exceptions.RequestException as exc:
            messagebox.showerror("Connection error", f"Could not load peers from the database.\n{exc}")
        except (ValueError, KeyError, TypeError) as exc:
            messagebox.showerror("Error", f"Unexpected peer response: {exc}")
    Button(bar, text="Search", command=load).grid(row=1, column=3, padx=(4, 0))
    load()
    def request_session():
        sel = t.selection()
        if not sel:
            return messagebox.showwarning("Pick a teacher", "Select a row first.")
        tid, tname, sid, sname, level = rows_holder[sel[0]]
        win = Toplevel(top, bg=PANEL)
        win.title("Book session")
        f = Frame(win, bg=PANEL, padx=20, pady=16)
        f.pack()
        Label(f, text=f"{tname} - {sname}", bg=PANEL, fg=TEXT, font=FONT_B).pack(anchor="w")
        Label(f, text="Date (YYYY-MM-DD)", bg=PANEL, fg=MUTED).pack(anchor="w", pady=(8, 2))
        e_date = Entry(f, width=16)
        e_date.insert(0, "2026-10-15")
        e_date.pack(anchor="w")
        Label(f, text="Start time (HH:MM)", bg=PANEL, fg=MUTED).pack(anchor="w", pady=(8, 2))
        e_time = Entry(f, width=16)
        e_time.insert(0, "17:00")
        e_time.pack(anchor="w")
        Label(f, text="Duration", bg=PANEL, fg=MUTED).pack(anchor="w", pady=(8, 2))
        dur = ttk.Combobox(f, values=["1", "2"], state="readonly", width=5)
        dur.set("1")
        dur.pack(anchor="w")
        
        def confirm():
            print("BOOK BUTTON CLICKED")
            date, tm = e_date.get().strip(), e_time.get().strip()
            try:
                when = datetime.strptime(f"{date} {tm}", "%Y-%m-%d %H:%M")
            except ValueError:
                return messagebox.showerror("Invalid", "Use date YYYY-MM-DD and time HH:MM.")

            if when < datetime.now():
                return messagebox.showerror("Invalid", "Choose a future date and time.")

            try:
                h = int(dur.get())
            except (ValueError, TypeError):
                return messagebox.showerror("Invalid", "Choose a valid duration.")

            if h <= 0:
                return messagebox.showerror("Invalid", "Duration must be greater than zero.")

            try:
                response = requests.post(
                    f"{API_URL}/bookings",
                    json={
                        "student_id": state["uid"] - 1000,
                        "tutor_id": tid,
                        "skill_id": sid,
                        "date": date,
                        "start_time": tm,
                        "duration": h
                    },
                    timeout=10
                )

                if response.status_code not in (200, 201):
                    try:
                        detail = response.json().get("detail", "Could not create booking.")
                    except ValueError:
                        detail = f"Booking failed (HTTP {response.status_code})."
                    return messagebox.showerror("Booking failed", str(detail))

                win.destroy()
                messagebox.showinfo(
                    "Booked",
                    f"{h} credit(s) reserved. Waiting for {tname} to confirm."
                )
                goto("browse", page_browse)

            except requests.exceptions.RequestException as exc:
                messagebox.showerror(
                    "Connection error",
                    f"Could not save the booking.\n{exc}"
                )

        Button(f, text="Book (places credits in escrow)", bg="sky blue", command=confirm).pack(fill="x", pady=(12, 4))
        Button(f, text="Cancel", command=win.destroy).pack(fill="x")
    Button(body, text="Book session", bg="sky blue", activebackground="yellow", command=request_session).pack(anchor="w")

# MY SKILLS 
def page_myskills():
    title_lbl.config(text="My skills")
    db_uid = state.get("db_uid")
    f = Frame(body, bg=BG)
    f.pack(anchor="w", fill="x")

    Label(f, text="Skill", bg=BG, fg=MUTED).grid(row=0, column=0, sticky="w")
    cs = ttk.Combobox(f, state="readonly", width=24)
    cs.grid(row=1, column=0, pady=(2, 10), sticky="w")

    Label(f, text="Type", bg=BG, fg=MUTED).grid(row=0, column=1, sticky="w", padx=(16, 0))
    ct = ttk.Combobox(f, values=["Offered", "Requested"], state="readonly", width=12)
    ct.set("Offered")
    ct.grid(row=1, column=1, pady=(2, 10), sticky="w", padx=(16, 0))

    Label(f, text="Level (if offered)", bg=BG, fg=MUTED).grid(row=0, column=2, sticky="w", padx=(16, 0))
    cl = ttk.Combobox(f, values=["Beginner", "Intermediate", "Expert"], state="readonly", width=14)
    cl.set("Intermediate")
    cl.grid(row=1, column=2, pady=(2, 10), sticky="w", padx=(16, 0))

    skill_lookup = {}
    def load_skills():
        try:
            response = requests.get(f"{API_URL}/skills", timeout=5)
            response.raise_for_status()
            rows = response.json()
            skill_lookup.clear()
            for row in rows:
                label = row["skill_name"]
                skill_lookup[label] = row
            cs["values"] = list(skill_lookup.keys())
            response = requests.get(f"{API_URL}/users/{db_uid}/skills", timeout=5)
            response.raise_for_status()
            user_skills = response.json()
            for widget in (t1, t2):
                for item in widget.get_children():
                    widget.delete(item)
            for i, row in enumerate(user_skills):
                label = row["skill_name"]
                if row["skill_type"] == "offered":
                    t1.insert("", "end", iid=f"offered-{i}", values=(label, row.get("level") or "Not set"))
                else:
                    t2.insert("", "end", iid=f"requested-{i}", values=(label,))
        except requests.exceptions.RequestException as exc:
            messagebox.showerror("Connection error", f"Could not load skills from the database.\\n{exc}")
        except (ValueError, KeyError, TypeError) as exc:
            messagebox.showerror("Error", f"Unexpected skills response: {exc}")

    def add():
        if not db_uid:
            return messagebox.showerror("Login required", "Please log in again.")
        if not cs.get():
            return messagebox.showwarning("Pick a skill", "Choose a skill first.")
        skill = skill_lookup.get(cs.get())
        if not skill:
            return messagebox.showerror("Error", "Please select a valid skill.")
        typ = ct.get().lower()
        payload = {"skill_name": skill["skill_name"], "skill_type": typ, "category": skill.get("category", "General"), "level": cl.get() if typ == "offered" else None}
        try:
            response = requests.post(f"{API_URL}/users/{db_uid}/skills", json=payload, timeout=5)
            if response.status_code in (200, 201):
                messagebox.showinfo("Added", f"Added to your {typ} skills and saved to the database.")
                load_skills()
            else:
                try:
                    detail = response.json().get("detail", "Could not add skill")
                except ValueError:
                    detail = f"Could not add skill (HTTP {response.status_code})"
                messagebox.showerror("Could not add skill", str(detail))
        except requests.exceptions.RequestException as exc:
            messagebox.showerror("Connection error", f"Could not save skill.\\n{exc}")

    Button(body, text="Add", bg="sky blue", command=add).pack(anchor="w", pady=(0, 10))
    cols_frame = Frame(body, bg=BG)
    cols_frame.pack(fill="both", expand=True)
    offered = Frame(cols_frame, bg=BG)
    offered.pack(side="left", fill="both", expand=True, padx=(0, 10))
    Label(offered, text="Offered", bg=BG, fg=TEXT, font=FONT_B).pack(anchor="w")
    t1 = ttk.Treeview(offered, columns=("skill", "level"), show="headings", height=6)
    t1.heading("skill", text="Skill")
    t1.heading("level", text="Level")
    t1.pack(fill="both", expand=True)

    requested = Frame(cols_frame, bg=BG)
    requested.pack(side="left", fill="both", expand=True)
    Label(requested, text="Requested (help needed)", bg=BG, fg=TEXT, font=FONT_B).pack(anchor="w")
    t2 = ttk.Treeview(requested, columns=("skill",), show="headings", height=6)
    t2.heading("skill", text="Skill")
    t2.pack(fill="both", expand=True)

    load_skills()
# MY SESSIONS 

def page_sessions():
    title_lbl.config(text="My sessions")
    db_uid = state.get("db_uid")

    if not db_uid:
        messagebox.showerror("Login required", "Please log in again.")
        return

    cols = ("learner", "teacher", "skill", "date", "time", "hours", "status")
    t = ttk.Treeview(body, columns=cols, show="headings", height=9)

    for c in cols:
        t.heading(c, text=c.title())
        t.column(c, width=110)

    t.pack(fill="both", expand=True, pady=8)

    legend = Frame(body, bg=BG)
    legend.pack(anchor="w", pady=(0, 8))

    for status in STATUS_BG:
        Label(
            legend,
            text=f"  {status.title()}  ",
            bg=STATUS_BG[status],
            fg=STATUS_FG[status],
            font=("Segoe UI", 9, "bold")
        ).pack(side="left", padx=(0, 6))

    rows_by_id = {}

    def load_sessions():
        for item in t.get_children():
            t.delete(item)
        rows_by_id.clear()

        try:
            response = requests.get(
                f"{API_URL}/users/{db_uid}/bookings",
                timeout=5
            )
            response.raise_for_status()
            rows = response.json()

            for s in rows:
                rows_by_id[s["id"]] = s
                t.insert(
                    "",
                    "end",
                    iid=str(s["id"]),
                    values=(
                        s["learner"],
                        s["tutor"],
                        s["skill"],
                        s["date"],
                        s["time"],
                        s["hours"],
                        s["status"].title()
                    )
                )

        except requests.exceptions.RequestException as exc:
            messagebox.showerror(
                "Connection error",
                f"Could not load sessions:\n{exc}"
            )
        except (ValueError, KeyError, TypeError) as exc:
            messagebox.showerror(
                "Error",
                f"Unexpected sessions response:\n{exc}"
            )

    def selected_session():
        selected = t.selection()
        if not selected:
            messagebox.showwarning(
                "Select session",
                "Please select a session first."
            )
            return None
        return rows_by_id.get(int(selected[0]))

    def post_action(session, action, payload):
        try:
            response = requests.post(
                f"{API_URL}/bookings/{session['id']}/{action}",
                json=payload,
                timeout=5
            )

            if response.ok:
                messagebox.showinfo(
                    "Success",
                    response.json().get("message", "Session updated.")
                )
                load_sessions()
                return True

            try:
                detail = response.json().get("detail", "Request failed")
            except ValueError:
                detail = f"Request failed (HTTP {response.status_code})"

            messagebox.showerror("Could not update session", str(detail))

        except requests.exceptions.RequestException as exc:
            messagebox.showerror("Connection error", str(exc))

        return False

    def confirm_session():
        s = selected_session()
        if not s:
            return
        if s["tutor_id"] != db_uid or s["status"] != "pending":
            return messagebox.showwarning(
                "Not allowed",
                "Only the tutor can confirm a pending session."
            )
        post_action(s, "confirm", {"user_id": db_uid})

    def complete_session():
        s = selected_session()
        if not s:
            return
        if s["learner_id"] != db_uid or s["status"] != "confirmed":
            return messagebox.showwarning(
                "Not allowed",
                "Only the learner can complete a confirmed session."
            )
        post_action(s, "complete", {"user_id": db_uid})

    def cancel_session():
        s = selected_session()
        if not s:
            return
        if s["status"] not in ("pending", "confirmed"):
            return messagebox.showwarning(
                "Not allowed",
                "Only pending or confirmed sessions can be cancelled."
            )
        post_action(s, "cancel", {"user_id": db_uid})

    def dispute_session():
        s = selected_session()
        if not s:
            return
        if s["status"] not in ("pending", "confirmed"):
            return messagebox.showwarning(
                "Not allowed",
                "This session cannot be disputed."
            )

        win = Toplevel(top, bg=PANEL)
        win.title("Report an issue")

        f = Frame(win, bg=PANEL, padx=20, pady=16)
        f.pack()

        Label(f, text="What happened?", bg=PANEL).pack(anchor="w")
        reason = Text(f, width=34, height=4)
        reason.pack()

        def submit():
            text = reason.get("1.0", "end").strip()
            if not text:
                return messagebox.showerror(
                    "Invalid", "Describe the issue first."
                )

            if post_action(
                s,
                "dispute",
                {"user_id": db_uid, "reason": text}
            ):
                win.destroy()

        Button(
            f, text="Submit dispute",
            command=submit, bg="sky blue"
        ).pack(fill="x", pady=8)

        Button(f, text="Cancel", command=win.destroy).pack(fill="x")

    def review_session():
        s = selected_session()
        if not s:
            return
        if s["learner_id"] != db_uid or s["status"] != "completed":
            return messagebox.showwarning(
                "Not allowed",
                "Only the learner can review a completed session."
            )
        if s.get("reviewed"):
            return messagebox.showwarning(
                "Already reviewed",
                "This session already has a review."
            )

        win = Toplevel(top, bg=PANEL)
        win.title("Rate your tutor")

        f = Frame(win, bg=PANEL, padx=20, pady=16)
        f.pack()

        Label(f, text=f"Rate {s['tutor']}", bg=PANEL).pack(anchor="w")

        rating = ttk.Combobox(
            f, values=["1", "2", "3", "4", "5"],
            state="readonly", width=5
        )
        rating.set("5")
        rating.pack(anchor="w", pady=6)

        comment = Entry(f, width=34)
        comment.pack(anchor="w")

        def submit():
            if post_action(
                s,
                "rating",
                {
                    "user_id": db_uid,
                    "rating": float(rating.get()),
                    "comment": comment.get().strip()
                }
            ):
                win.destroy()

        Button(
            f, text="Submit review",
            command=submit, bg="sky blue"
        ).pack(fill="x", pady=8)

        Button(f, text="Cancel", command=win.destroy).pack(fill="x")

    bar = Frame(body, bg=BG)
    bar.pack(anchor="w")

    Button(bar, text="Confirm", command=confirm_session).pack(side="left", padx=(0, 6))
    Button(bar, text="Mark completed", command=complete_session, bg="sky blue").pack(side="left", padx=(0, 6))
    Button(bar, text="Report issue", command=dispute_session).pack(side="left", padx=(0, 6))
    Button(bar, text="Review", command=review_session).pack(side="left")
    Button(bar, text="Cancel", command=cancel_session).pack(side="left", padx=(6, 0))

    load_sessions()

# WALLET 
def page_wallet():
    title_lbl.config(text="Wallet")
    uid = state["uid"]
    u = MOCK_DB["users"][uid]
    locked = credits_locked(uid)
    cards = Frame(body, bg=BG)
    cards.pack(fill="x", pady=(0, 12))
    for label, value, color in [("AVAILABLE", u["credits"], ACCENT), ("IN ESCROW", locked, ACCENT2)]:
        c = Frame(cards, bg=PANEL, padx=18, pady=14)
        c.pack(side="left", fill="x", expand=True, padx=(0, 10))
        Label(c, text=label, bg=PANEL, fg=MUTED, font=("Segoe UI", 8, "bold")).pack(anchor="w")
        Label(c, text=f"{value} credits", bg=PANEL, fg=color, font=("Segoe UI", 20, "bold")).pack(anchor="w")
    rows = [t for t in MOCK_DB["transactions"] if uid in (t["from"], t["to"])][::-1]
    t = ttk.Treeview(body, columns=("from", "to", "amount", "type", "date"), show="headings", height=8)
    for c in ("from", "to", "amount", "type", "date"):
        t.heading(c, text=c.title())
    for i, r in enumerate(rows):
        amt = f"-{r['amount']}" if r["from"] == uid else f"+{r['amount']}"
        t.insert("", "end", iid=i, values=(MOCK_DB["users"][r["from"]]["name"], MOCK_DB["users"][r["to"]]["name"], amt, r["type"], r["date"]))
    t.pack(fill="both", expand=True)
# EXCHANGE ANALYTICS -- hours taught vs received, simple bar chart
def page_analytics():
    title_lbl.config(text="Analytics")
    uid = state["uid"]
    taught = sum(b["hours"] for b in MOCK_DB["bookings"] if b["teacher"] == uid and b["status"] == "completed")
    received = sum(b["hours"] for b in MOCK_DB["bookings"] if b["learner"] == uid and b["status"] == "completed")
    cards = Frame(body, bg=BG)
    cards.pack(fill="x", pady=(0, 16))
    for label, value in [("HOURS TAUGHT", taught), ("HOURS RECEIVED", received), ("NET BALANCE", received - taught)]:
        c = Frame(cards, bg=PANEL, padx=18, pady=14)
        c.pack(side="left", fill="x", expand=True, padx=(0, 10))
        Label(c, text=label, bg=PANEL, fg=MUTED, font=("Segoe UI", 8, "bold")).pack(anchor="w")
        Label(c, text=str(value), bg=PANEL, fg=ACCENT, font=("Segoe UI", 20, "bold")).pack(anchor="w")
    canvas = Canvas(body, width=300, height=180, bg=PANEL, highlightthickness=0)
    canvas.pack(anchor="w", pady=10)
    maxv = max(taught, received, 1)
    bar_w = 80
    h1 = int((taught / maxv) * 130)
    h2 = int((received / maxv) * 130)
    canvas.create_rectangle(60, 150 - h1, 60 + bar_w, 150, fill=ACCENT, outline="")
    canvas.create_text(100, 165, text="Taught", fill=TEXT, font=FONT)
    canvas.create_rectangle(180, 150 - h2, 180 + bar_w, 150, fill=ACCENT2, outline="")
    canvas.create_text(220, 165, text="Received", fill=TEXT, font=FONT)
def page_top():
    title_lbl.config(text="Top teachers")
    counts = {}
    for s in MOCK_DB["bookings"]:
        if s["status"] == "completed":
            c = counts.setdefault(s["teacher"], {"n": 0, "h": 0})
            c["n"] += 1
            c["h"] += s["hours"]
    rows = sorted([{"name": MOCK_DB["users"][u]["name"], "rating": MOCK_DB["users"][u]["rating"], **v} for u, v in counts.items()], key=lambda r: -r["h"])[:5]
    t = ttk.Treeview(body, columns=("rank", "name", "sessions", "hours", "rating"), show="headings", height=6)
    for c in ("rank", "name", "sessions", "hours", "rating"):
        t.heading(c, text=c.title())
    if not rows:
        Label(body, text="No completed sessions yet.", bg=BG, fg=MUTED).pack(anchor="w", pady=10)
    for i, r in enumerate(rows):
        t.insert("", "end", iid=i, values=(i + 1, r["name"], r["n"], r["h"], r["rating"]))
    t.pack(fill="both", expand=True)
# START 
show_login()
top.mainloop()