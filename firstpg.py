from tkinter import *
from tkinter import messagebox
import requests  # Required to talk to your FastAPI backend

top = Tk()
top.title("SkillSwap")
top.geometry("400x450")
top.configure(bg="#F4F8FB")

def clear():
    for widget in top.winfo_children():
        widget.destroy()

def show_login():
    clear()
    top.title("SkillSwap - Login")
    top.geometry("400x350")

    form = Frame(top, bg="#F4F8FB")
    form.place(relx=0.5, rely=0.5, anchor="center")      
    
    lbl1 = Label(form, text="SkillSwap", bg="#2E6F95", fg="white", height=1, width=10, bd=10, font=("Segoe UI", 20, "bold"))
    lbl1.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

    lbl2 = Label(form, text="Email", bg="light yellow", height=1, width=10, bd=10, font=("Segoe UI", 15))
    lbl2.grid(row=1, column=0, padx=10, pady=10)

    e1 = Entry(form, width=30)
    e1.grid(row=1, column=1)

    lbl3 = Label(form, text="Password", bg="light yellow", height=1, width=10, bd=10, font=("Segoe UI", 15))
    lbl3.grid(row=2, column=0, padx=10, pady=10)

    e2 = Entry(form, width=30, show="*", fg="red")
    e2.grid(row=2, column=1)

    def fun():
        email = e1.get()
        password = e2.get()
        if email and password:
            messagebox.showinfo("Success", "Login successful!")
        else:
            messagebox.showerror("Warning", "Fill all Fields!")

    btn1 = Button(form, text="Login", bg="sky blue", activebackground="yellow", command=fun)
    btn1.grid(row=3, column=0, columnspan=2, pady=10)
    
    btn2 = Button(form, text="Create an account", command=show_register)
    btn2.grid(row=4, column=0, columnspan=2, pady=5)


def show_register():
    clear()
    top.title("SkillSwap - Register")
    top.geometry("400x420")

    form = Frame(top, bg="#F4F8FB")
    form.place(relx=0.5, rely=0.5, anchor="center")      
    
    lbl1 = Label(form, text="Create Account", bg="#2E6F95", fg="white", height=1, width=14, bd=10, font=("Segoe UI", 20, "bold"))
    lbl1.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

    lbl2 = Label(form, text="Name : ", bg="light yellow", height=1, width=10, bd=5, font=("Segoe UI", 11))
    lbl2.grid(row=1, column=0, padx=5, pady=5)
    e1 = Entry(form, width=25)
    e1.grid(row=1, column=1)

    lbl3 = Label(form, text="Email : ", bg="light yellow", height=1, width=10, bd=5, font=("Segoe UI", 11))
    lbl3.grid(row=2, column=0, padx=5, pady=5)
    e2 = Entry(form, width=25)
    e2.grid(row=2, column=1)

    lbl_dept = Label(form, text="Department:", bg="light yellow", height=1, width=10, bd=5, font=("Segoe UI", 11))
    lbl_dept.grid(row=3, column=0, padx=5, pady=5)
    e_dept = Entry(form, width=25)
    e_dept.grid(row=3, column=1)

    lbl4 = Label(form, text="Password : ", bg="light yellow", height=1, width=10, bd=5, font=("Segoe UI", 11))
    lbl4.grid(row=4, column=0, padx=5, pady=5)
    e3 = Entry(form, width=25, show="*", fg="red")
    e3.grid(row=4, column=1)

    def fun():
        name = e1.get()
        email = e2.get()
        department = e_dept.get()
        password = e3.get()

        if name and email and department and password:
            payload = {
                "name": name,
                "email": email,
                "department": department,
                "availability": ["Mon-Evening"]  # Default or dynamic if you add a field
            }
            
            try:
                # Send data to FastAPI backend running locally
                response = requests.post("http://127.0.0.1:8000/users", json=payload)
                
                if response.status_code == 200:
                    messagebox.showinfo("Success", "Registered successfully in MySQL database!")
                    show_login()
                else:
                    error_msg = response.json().get("detail", "Registration failed")
                    messagebox.showerror("Error", error_msg)
            except requests.exceptions.ConnectionError:
                messagebox.showerror("Connection Error", "Is your FastAPI server running in the terminal?")
        else:
            messagebox.showerror("Warning", "Fill all fields!")

    btn1 = Button(form, text="Register", bg="sky blue", activebackground="yellow", command=fun)
    btn1.grid(row=5, column=0, columnspan=2, pady=10)
    
    btn2 = Button(form, text="Back to login", command=show_login)
    btn2.grid(row=6, column=0, columnspan=2)

show_login()   
top.mainloop()
