from tkinter import *
from tkinter import messagebox

top = Tk()
top.title("SkillSwap")
top.geometry("400x400")
top.configure(bg="#F4F8FB")

def clear():
    for widget in top.winfo_children():
        widget.destroy()

def show_login():
    clear()
    top.title("SkillSwap - Login")
    top.geometry("400x350")

    form = Frame(top)
    form.place(relx=0.5, rely=0.5, anchor="center")   
    top.configure(bg="#F4F8FB")      
    form.configure(bg="#F4F8FB")     
    lbl1 = Label(form, text="SkillSwap", bg="#2E6F95",fg="white", height=1, width=10, bd=10, font=("Segoe UI", 20, "bold"))
    lbl1.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

    lbl2 = Label(form, text="Email", bg="light yellow", height=1, width=10, bd=10, font=("Segoe UI", 15))
    lbl2.grid(row=1, column=0, padx=10, pady=10)

    e1 = Entry(form, width=30)
    e1.grid(row=1, column=1)
    lbl3 = Label(form, text="Password", bg="light yellow", height=1, width=10, bd=10, font=("Segoe UI", 15))
    lbl3.grid(row=2, column=0, padx=10, pady=10)

    e2 = Entry(form, width=30,show="*",fg="red")
    e2.grid(row=2, column=1)
    def fun():
        email=e1.get()
        password=e2.get()
        if email and password:
           chld=Toplevel(top)
        else:
            messagebox.showerror("Warning","Fill all Fields!")
    btn1=Button(form,text="Login",bg="sky blue",activebackground="yellow",command=fun)
    btn1.grid(row=3,column=0,columnspan=2)
    btn2 = Button(form, text="Create an account", command=show_register)
    btn2.grid(row=4, column=0, columnspan=2, pady=5)


def show_register():
    clear()
    top.title("SkillSwap - Register")
    top.geometry("400x350")

    form = Frame(top,bg="#F4F8FB")
    form.place(relx=0.5, rely=0.5, anchor="center")   
    top.configure(bg="#F4F8FB")       
    lbl1 = Label(form, text="Create Account", bg="#2E6F95",fg="white", height=1, width=14, bd=10, font=("Segoe UI", 20, "bold"))
    lbl1.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

    lbl2 = Label(form, text="Name : ", bg="light yellow", height=1, width=8, bd=5, font=("Segoe UI", 12))
    lbl2.grid(row=1, column=0, padx=10, pady=5)
    e1 = Entry(form, width=30)
    e1.grid(row=1, column=1)

    lbl3 = Label(form, text="Email : ", bg="light yellow", height=1, width=8, bd=5, font=("Segoe UI", 12))
    lbl3.grid(row=2, column=0, padx=10, pady=5)
    e2 = Entry(form, width=30)
    e2.grid(row=2, column=1)

    lbl4 = Label(form, text="Password : ", bg="light yellow", height=1, width=8, bd=5, font=("Segoe UI", 12))
    lbl4.grid(row=3, column=0, padx=10, pady=5)
    e3 = Entry(form, width=30,show="*",fg="red")
    e3.grid(row=3, column=1)

    def fun():
        name = e1.get()
        email = e2.get()
        password = e3.get()
        if name and email and password:
           messagebox.showinfo("Success", "You Have registered successfully!!")
        else:
            messagebox.showerror("Warning","Fill all fields")

    btn1 = Button(form, text="Register", bg="sky blue", activebackground="yellow", command=fun)
    btn1.grid(row=4, column=0, columnspan=2, pady=10)
    btn2 = Button(form, text="Back to login", command=show_login)
    btn2.grid(row=5, column=0, columnspan=2)

show_login()   
top.mainloop()