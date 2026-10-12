from datetime import datetime
from tkinter import *
from tkinter import ttk, messagebox
import requests  # used by Register, same as your firstpg.py
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
state = {"uid": 1}
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
        uid = next((i for i, u in MOCK_DB["users"].items() if u["email"].lower() == email), None)
        if not e2.get():
           messagebox.showerror("Warning", "Fill all Fields!")
        elif uid is None:
           messagebox.showerror("Login failed", "Unknown email. Try riya@college.edu or aman@college.edu")
        else:
          state["uid"] = uid
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
        name, email, department, password = e1.get(), e2.get(), e_dept.get(), e3.get()
        if name and email and department and password:
            payload = {"name": name, "email": email, "department": department, "availability": ["Mon-Evening"]}
            try:
                response = requests.post("http://127.0.0.1:8000/users", json=payload, timeout=5)
                if response.status_code == 200:
                   u = response.json()["user"]
                   MOCK_DB["users"][1000 + u["id"]] = {"name": u["name"], "email": u["email"], "credits": u["credits"], "rating": 0.0, "rating_count": 0}
                   messagebox.showinfo("Success", "Registered successfully in MySQL database!")
                   show_login()
                else:
                    messagebox.showerror("Error", response.json().get("detail", "Registration failed"))
            except requests.exceptions.ConnectionError:
                messagebox.showerror("Connection Error", "Is your FastAPI server running in the terminal?")
        else:
            messagebox.showerror("Warning", "Fill all fields!")

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
        for u, sid, typ, level in MOCK_DB["user_skills"]:
            if typ != "offered" or u == uid:
                continue
            sname = MOCK_DB["skills"][sid]
            if kw.get().strip() and kw.get().strip().lower() not in sname.lower():
                continue
            teacher = MOCK_DB["users"][u]
            if minr.get() != "Any" and teacher["rating"] < float(minr.get()):
                continue
            a = MOCK_DB["availability"].get(u, "-")
            if avail.get() != "Any" and avail.get() != a:
                continue
            iid = f"{u}-{sid}"
            rows_holder[iid] = (u, teacher["name"], sid, sname, level)
            t.insert("", "end", iid=iid, values=(teacher["name"], sname, level, teacher["rating"], a))
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
            date, tm = e_date.get().strip(), e_time.get().strip()
            try:
                when = datetime.strptime(f"{date} {tm}", "%Y-%m-%d %H:%M")
            except ValueError:
                return messagebox.showerror("Invalid", "Use date YYYY-MM-DD and time HH:MM.")
            if when < datetime.now():
                return messagebox.showerror("Invalid", "Choose a future date and time.")
            h = int(dur.get())
            bal = MOCK_DB["users"][uid]["credits"]
            if bal < h:
                return messagebox.showerror("Not enough credits", f"You have {bal} available.")
            for b in MOCK_DB["bookings"]:
                if b["status"] not in ("pending", "confirmed"):
                    continue
                if b["date"] == date and b["time"] == tm and (b["learner"] == uid or b["teacher"] == tid):
                    return messagebox.showerror("Conflict", "You or the tutor already have a booking at that time.")
            MOCK_DB["users"][uid]["credits"] -= h        # NEW: lock credits in escrow
            MOCK_DB["bookings"].append({"id": MOCK_DB["next_id"], "learner": uid, "teacher": tid, "skill": sid,
                                        "date": date, "time": tm, "hours": h, "status": "pending"})
            MOCK_DB["next_id"] += 1
            win.destroy()
            messagebox.showinfo("Booked", f"{h} credit(s) placed in escrow. Waiting for {tname} to confirm.")
            goto("browse", page_browse)
        Button(f, text="Book (places credits in escrow)", bg="sky blue", command=confirm).pack(fill="x", pady=(12, 4))
        Button(f, text="Cancel", command=win.destroy).pack(fill="x")
    Button(body, text="Book session", bg="sky blue", activebackground="yellow", command=request_session).pack(anchor="w")

# MY SKILLS 
def page_myskills():
    title_lbl.config(text="My skills")
    uid = state["uid"]
    f = Frame(body, bg=BG)
    f.pack(anchor="w", fill="x")
    Label(f, text="Skill", bg=BG, fg=MUTED).grid(row=0, column=0, sticky="w")
    cs = ttk.Combobox(f, values=[f"{k} - {v}" for k, v in MOCK_DB["skills"].items()], state="readonly", width=20)
    cs.grid(row=1, column=0, pady=(2, 10), sticky="w")
    Label(f, text="Type", bg=BG, fg=MUTED).grid(row=0, column=1, sticky="w", padx=(16, 0))
    ct = ttk.Combobox(f, values=["Offered", "Requested"], state="readonly", width=12)
    ct.set("Offered")
    ct.grid(row=1, column=1, pady=(2, 10), sticky="w", padx=(16, 0))
    Label(f, text="Level (if offered)", bg=BG, fg=MUTED).grid(row=0, column=2, sticky="w", padx=(16, 0))
    cl = ttk.Combobox(f, values=["Beginner", "Intermediate", "Expert"], state="readonly", width=14)
    cl.set("Intermediate")
    cl.grid(row=1, column=2, pady=(2, 10), sticky="w", padx=(16, 0))
    def add():
        if not cs.get():
            return messagebox.showwarning("Pick a skill", "Choose a skill first.")
        sid = int(cs.get().split(" - ")[0])
        typ = ct.get().lower()
        level = cl.get() if typ == "offered" else "-"
        if any(u == uid and s == sid and t == typ for u, s, t, _ in MOCK_DB["user_skills"]):
            return messagebox.showwarning("Already added", f"You already have this skill as {typ}.")
        MOCK_DB["user_skills"].append((uid, sid, typ, level))
        messagebox.showinfo("Added", f"Added to your {typ} skills.")
        goto("myskills", page_myskills)
    Button(body, text="Add", bg="sky blue", command=add).pack(anchor="w", pady=(0, 10))
    cols_frame = Frame(body, bg=BG)
    cols_frame.pack(fill="both", expand=True)
    offered = Frame(cols_frame, bg=BG)
    offered.pack(side="left", fill="both", expand=True, padx=(0, 10))
    Label(offered, text="Offered", bg=BG, fg=TEXT, font=FONT_B).pack(anchor="w")
    t1 = ttk.Treeview(offered, columns=("skill", "level"), show="headings", height=6)
    t1.heading("skill", text="Skill")
    t1.heading("level", text="Level")
    for i, (u, s, typ, lvl) in enumerate(MOCK_DB["user_skills"]):
        if u == uid and typ == "offered":
            t1.insert("", "end", iid=i, values=(MOCK_DB["skills"][s], lvl))
    t1.pack(fill="both", expand=True)
    requested = Frame(cols_frame, bg=BG)
    requested.pack(side="left", fill="both", expand=True)
    Label(requested, text="Requested (help needed)", bg=BG, fg=TEXT, font=FONT_B).pack(anchor="w")
    t2 = ttk.Treeview(requested, columns=("skill",), show="headings", height=6)
    t2.heading("skill", text="Skill")
    for i, (u, s, typ, lvl) in enumerate(MOCK_DB["user_skills"]):
        if u == uid and typ == "requested":
            t2.insert("", "end", iid=i, values=(MOCK_DB["skills"][s],))
    t2.pack(fill="both", expand=True)
# MY SESSIONS 
def page_sessions():
    title_lbl.config(text="My sessions")
    uid = state["uid"]
    rows = [s for s in MOCK_DB["bookings"] if uid in (s["learner"], s["teacher"])]
    rows.sort(key=lambda r: -r["id"])
    cols = ("learner", "teacher", "skill", "date", "time", "hours", "status")
    t = ttk.Treeview(body, columns=cols, show="headings", height=9)
    for c in cols:
        t.heading(c, text=c.title())
        t.column(c, width=95)
    for s in rows:
        t.insert("", "end", iid=s["id"], values=(MOCK_DB["users"][s["learner"]]["name"], MOCK_DB["users"][s["teacher"]]["name"],
                 MOCK_DB["skills"][s["skill"]], s["date"], s["time"], s["hours"], s["status"].title()))
    t.pack(fill="both", expand=True, pady=8)
    legend = Frame(body, bg=BG)
    legend.pack(anchor="w", pady=(0, 8))
    for s in STATUS_BG:
        Label(legend, text=f"  {s.title()}  ", bg=STATUS_BG[s], fg=STATUS_FG[s], font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 6))
    by_id = {s["id"]: s for s in rows}
    def act(fn):
        sel = t.selection()
        if not sel:
            return messagebox.showwarning("Pick a session", "Select a row first.")
        fn(by_id[int(sel[0])])
    def do_confirm(s):
        if s["teacher"] == uid and s["status"] == "pending":
            s["status"] = "confirmed"
            goto("sessions", page_sessions)
        else:
            messagebox.showwarning("Not allowed", "Only the teacher can confirm a pending session.")
    def do_complete(s):
        if s["learner"] != uid or s["status"] != "confirmed":
            return messagebox.showwarning("Not allowed", "Only the learner can complete a confirmed session.")
        MOCK_DB["users"][s["teacher"]]["credits"] += s["hours"]
        MOCK_DB["transactions"].append({"from": uid, "to": s["teacher"], "amount": s["hours"], "date": "today", "type": "escrow_release"})
        s["status"] = "completed"
        messagebox.showinfo("Done", f"{s['hours']} credit(s) released to {MOCK_DB['users'][s['teacher']]['name']}.")
        goto("sessions", page_sessions)
    def do_dispute(s):
        if s["status"] == "completed":
            return messagebox.showwarning("Not allowed", "Cannot dispute a completed session.")
        win = Toplevel(top, bg=PANEL)
        win.title("Report an issue")
        f = Frame(win, bg=PANEL, padx=20, pady=16)
        f.pack()
        Label(f, text=f"Session #{s['id']}", bg=PANEL, fg=TEXT, font=FONT_B).pack(anchor="w")
        Label(f, text="What happened?", bg=PANEL, fg=MUTED).pack(anchor="w", pady=(8, 2))
        reason = Text(f, width=34, height=4)
        reason.pack()
        def submit():
            r = reason.get("1.0", "end").strip()
            if not r:
                return messagebox.showerror("Invalid", "Describe the issue first.")
            MOCK_DB["disputes"].append({"booking_id": s["id"], "by": uid, "reason": r, "status": "open"})
            s["status"] = "disputed"
            win.destroy()
            messagebox.showinfo("Reported", "Dispute submitted. Credits stay in escrow until resolved.")
            goto("sessions", page_sessions)
        Button(f, text="Submit dispute", bg="sky blue", command=submit).pack(fill="x", pady=(10, 4))
        Button(f, text="Cancel", command=win.destroy).pack(fill="x")
    def do_review(s):
        if s["learner"] != uid or s["status"] != "completed":
            return messagebox.showwarning("Not allowed", "You can only review your own completed sessions.")
        if any(r["booking_id"] == s["id"] for r in MOCK_DB["reviews"]):
            return messagebox.showwarning("Already reviewed", "You already reviewed this session.")
        win = Toplevel(top, bg=PANEL)
        win.title("Rate your tutor")
        f = Frame(win, bg=PANEL, padx=20, pady=16)
        f.pack()
        Label(f, text=f"Rate {MOCK_DB['users'][s['teacher']]['name']}", bg=PANEL, fg=TEXT, font=FONT_B).pack(anchor="w")
        rating = ttk.Combobox(f, values=["1", "2", "3", "4", "5"], state="readonly", width=5)
        rating.set("5")
        rating.pack(anchor="w", pady=(8, 2))
        comment = Entry(f, width=34)
        comment.pack(anchor="w", pady=(4, 0))
        def submit():
            rt = int(rating.get())
            tutor = MOCK_DB["users"][s["teacher"]]
            tutor["rating"] = round((tutor["rating"] * tutor["rating_count"] + rt) / (tutor["rating_count"] + 1), 2)
            tutor["rating_count"] += 1
            MOCK_DB["reviews"].append({"booking_id": s["id"], "rating": rt, "comment": comment.get()})
            win.destroy()
            messagebox.showinfo("Thanks", "Review submitted.")
        Button(f, text="Submit review", bg="sky blue", command=submit).pack(fill="x", pady=(10, 4))
        Button(f, text="Cancel", command=win.destroy).pack(fill="x")
    def do_cancel(s):
        if s["learner"] != uid or s["status"] != "pending":
            return messagebox.showwarning("Not allowed", "Only the learner can cancel a pending session.")
        MOCK_DB["users"][uid]["credits"] += s["hours"]
        s["status"] = "cancelled"
        messagebox.showinfo("Cancelled", f"{s['hours']} credit(s) refunded.")
        goto("sessions", page_sessions)
    bar = Frame(body, bg=BG)
    bar.pack(anchor="w")
    Button(bar, text="Confirm", command=lambda: act(do_confirm)).pack(side="left", padx=(0, 6))
    Button(bar, text="Mark completed", bg="sky blue", command=lambda: act(do_complete)).pack(side="left", padx=(0, 6))
    Button(bar, text="Report issue", fg="#A8382E", command=lambda: act(do_dispute)).pack(side="left", padx=(0, 6))
    Button(bar, text="Review", command=lambda: act(do_review)).pack(side="left")
    Button(bar, text="Cancel", command=lambda: act(do_cancel)).pack(side="left", padx=(6, 0))
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
