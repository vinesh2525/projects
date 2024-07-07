import sqlite3
from tkinter import *
from tkinter import messagebox
from datetime import date, datetime, timedelta


# Connect to the SQLite database
try:
    connection = sqlite3.connect("Harsha_Hospital2.db", isolation_level=None)
    cursor = connection.cursor()
except sqlite3.Error as e:
    messagebox.showerror("Database Error", f"An error occurred: {e}")

# Dropping the existing doctor table if it exists
try:
    cursor.execute('DROP TABLE IF EXISTS doctor')
except sqlite3.Error as e:
    messagebox.showerror("Database Error", f"An error occurred: {e}")

# Creating table for doctor 
try:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctor (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            gender TEXT,
            exp INTEGER,
            specialization TEXT NOT NULL
        )
    ''')
except sqlite3.Error as e:
    messagebox.showerror("Database Error", f"An error occurred: {e}")

try:
    cursor.execute('DROP TABLE IF EXISTS appointment')
except sqlite3.Error as e:
    messagebox.showerror("Database Error", f"An error occurred: {e}")

# Creating table for appointment
try:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id INTEGER NOT NULL,
            time_slot DATETIME NOT NULL,
            patient_name TEXT,
            isBooked INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (doctor_id) REFERENCES doctor(id)
        )
    ''')
except sqlite3.Error as e:
    messagebox.showerror("Database Error", f"An error occurred: {e}")

class Doctor:
    id_name_dict = {}
    logged_in_doctor = None
    def __init__(self, name, specialization, gender, exp):
        self.name = name
        self.specialization = specialization
        self.gender = gender
        self.exp = exp
        self.id = self.save_in_db()  # Save in DB after attributes are set

    def save_in_db(self):
        try:
            cursor.execute('''INSERT INTO doctor (name, specialization, gender, exp)
                              VALUES (?, ?, ?, ?)''', (self.name, self.specialization, self.gender, self.exp))
            id = cursor.lastrowid
            self.id_name_dict[id] = f"{id} Dr. {self.name}, {self.specialization} "
            start_date = date.today() 
            Appointment.define_slots(id, start_date)
            return id
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"An error occurred: {e}")

class Appointment:
    @staticmethod
    def define_slots(doctor_id, start_date):
        slots = []
        for i in range(9, 17):
            for j in [0, 30]:
                slot_time = datetime.combine(start_date, datetime.min.time()) + timedelta(hours=i, minutes=j)
                slots.append((doctor_id, slot_time))
        try:
            cursor.executemany('INSERT INTO appointment (doctor_id, time_slot, isBooked) VALUES (?, ?, 0)', slots)
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"An error occurred: {e}")

    @staticmethod
    def book_appointment(patient_name, doctor_id, time_slot):
        try:
            cursor.execute("SELECT isBooked FROM appointment WHERE doctor_id = ? AND time_slot = ?", (doctor_id, time_slot))
            value = cursor.fetchone()
            if value and value[0] == 0:
                cursor.execute("UPDATE appointment SET patient_name = ?, isBooked = 1 WHERE doctor_id = ? AND time_slot = ?", (patient_name, doctor_id, time_slot))
                return cursor.rowcount > 0
            return False
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"An error occurred: {e}")

    @staticmethod
    def view_all_appointments(doctor_id):
        try:
            cursor.execute("SELECT patient_name, time_slot FROM appointment WHERE doctor_id = ? AND isBooked != 0", (doctor_id,))
            tuples_list = cursor.fetchall()
            my_appointments = [f"\t\t\t\t\t\t{datetime.strptime(x[1], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M')} \t\t\t  {x[0]}" for x in tuples_list]
            my_appointments.insert(0, "\t\t\t\t\t\tTIME SLOT \t\t\t PATIENT NAME ")
            my_appointments.insert(1, "\t\t\t\t\t\t*********** \t\t\t ***********")
            return my_appointments
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"An error occurred: {e}")

    @staticmethod
    def view_free_slots(doctor_id):
        try:
            cursor.execute("SELECT time_slot FROM appointment WHERE doctor_id = ? AND isBooked == 0", (doctor_id,))
            free_slots = cursor.fetchall()
            return [datetime.strptime(slot[0], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M') for slot in free_slots]
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"An error occurred: {e}")

class Harsha_Hospital:
    def __init__(self):
        self.name = "Harsha Multi Speciality Hospital"
        self.shortname = "Harsha Hospital"
        self.address = "Doctors Lane, Nirmal, Telangana"
        self.owner = self.mainDoctor = "Dr. Prashanth Kokkula"

    @staticmethod
    def greetings():
        return "Welcome to Harsha MultiSpeciality Hospital"

    @staticmethod
    def get_doctors():
        return Doctor.id_name_dict
    
    @staticmethod
    def get_services():
        return ["Orthopaedic", "Gynaecology", "General physician"]

class Patient:
    def __init__(self, name):
        self.name = name

    def book_appointment(self, doctor_id, time_slot):
        success = Appointment.book_appointment(self.name, time_slot, doctor_id)
        if success:
            return f"Appointment successfully booked at {time_slot} with Dr. {Doctor.id_name_dict[doctor_id]}"
        else:
            return "Failed to book appointment. Please try another time slot."

class Admin:
    def __init__(self, name):
        self.name = name

    @staticmethod
    def add_doctor(name, specialization, gender, exp):
        try:
            cursor.execute("select name from doctor")
            existing_doctors = [x[0] for x in cursor.fetchall()]
            
            if name in existing_doctors:
                messagebox.showerror("doctor name exists", "Give different name")
                return False
            else:
                Doctor(name, specialization, gender, exp)
                return True
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"An error occurred: {e}")

    @staticmethod
    def delete_doctor(name):
        try:
            cursor.execute("DELETE FROM doctor WHERE name = ?", (name,))
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"An error occurred: {e}")

    @staticmethod
    def view_appointments_of_all_doctors():
        try:
            cursor.execute('''SELECT doctor.name AS doctor_name, appointment.patient_name, appointment.time_slot
                              FROM appointment
                              JOIN doctor ON appointment.doctor_id = doctor.id
                              WHERE appointment.isBooked != 0 ORDER BY time_slot''')
            app_list = cursor.fetchall()
            output_list = [f"{appointment[2]} \t\t\t {appointment[1]} \t\t\t Dr.{appointment[0]}" for appointment in app_list]
            output_list.insert(0, "TIME SLOT \t\t\t PATIENT NAME \t\t\t DOCTOR NAME")
            output_list.insert(1, "*********** \t\t\t *********** \t\t\t ***********")
            return output_list
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"An error occurred: {e}")

# $$$$$$$$$$$$$$$$$$$   CODE EXECUTION     $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

# Adding doctors
Admin.add_doctor("Prashanth", "Ortho", "Male", 4)
Admin.add_doctor("Rahul", "General", "Male", 5)
Admin.add_doctor("Rani", "Gyno", "Female", 1)
Admin.add_doctor("Raju", "Dentist", "Male", 2)
Admin.add_doctor("Laxmi", "Ortho", "Female", 3)
Admin.add_doctor("Salla Arvind", "neuro_Surgeon", "male",1)

# Creating patients and booking appointments


time_format = '%Y-%m-%d %H:%M'

Appointment.book_appointment("Naga", 3, datetime.strptime(str(date.today())+" 10:30", time_format))
Appointment.book_appointment("Vinesh", 1, datetime.strptime(str(date.today())+" 09:30", time_format))
Appointment.book_appointment("Rahul", 1, datetime.strptime(str(date.today())+" 11:30", time_format))
Appointment.book_appointment("Nani", 4, datetime.strptime(str(date.today())+" 12:00", time_format))
Appointment.book_appointment("Bujji", 2, datetime.strptime(str(date.today())+" 14:00", time_format))
Appointment.book_appointment("Rishi", 5, datetime.strptime(str(date.today())+" 10:00", time_format))




'''
        

# Fetch and print doctors from the database
cursor.execute("SELECT * FROM doctor")
print(cursor.fetchall())

# Fetch and print all appointments
hh = Harsha_Hospital()
print(Harsha_Hospital.get_doctors())
print(Harsha_Hospital.get_services())
list_of_all_appointments = Admin.view_appointments_of_all_doctors()
for appointment in list_of_all_appointments:
    print(f"At {appointment[2]} patient: {appointment[1]} has an appointment with: {appointment[0]}")

# Print all appointments of a specific doctor
print(Appointment.view_all_appointments(1))

'''#
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$    front end   $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$


root = Tk()
root.geometry("1210x900")
root.title("Harsha Multi Speciality Hospital")
root.configure(bg="#F0F8FF")

icon_ico_path = "C:\\Users\\vinesh\\Desktop\\Capstone_project\\Hospital_Icon.ico"

root.iconbitmap(icon_ico_path)

def view_doctors():
    doctors = "\n".join(list(Harsha_Hospital.get_doctors().values()))
    messagebox.showinfo("View Available Doctors", doctors)

def view_services():
    messagebox.showinfo("Available Services", "Orthopaedic\nGynaecology\nGeneral Physician")

menubar = Menu(root)

# Adding menu items
doctor_menu = Menu(menubar, tearoff=0)
doctor_menu.add_command(label= "\n".join(list(Harsha_Hospital.get_doctors().values())), command=view_doctors)

service_menu = Menu(menubar, tearoff=0)
service_menu.add_command(label="Available Services", command=view_services)

# Adding menu items to the menu bar
menubar.add_cascade(label="Doctors", menu=doctor_menu)
menubar.add_cascade(label="Services", menu=service_menu)

# Configuring the root window to use the menu bar
root.config(menu=menubar)

header_frame = Frame(root, bg="#3498db")
header_frame.pack(pady=5, padx=10,expand=True, fill='x')

Label_pageIntro1 = Label(header_frame, text="Welcome to ", font=("Times New Roman", 20), bg="#3498db", fg="mediumspringgreen")
Label_pageIntro1.pack()

Label_pageIntro2 = Label(header_frame, text="HARSHA MULTI SPECIALITY HOSPITAL", font=("Times New Roman", 35, "bold"), bg="#3498db", fg="mediumspringgreen")
Label_pageIntro2.pack(pady=10)

Label_pageIntro3 = Label(header_frame, text="24 X 7 EMERGENCY AVAILABILITY", font=("Times New Roman", 20), bg="#3498db", fg="mediumspringgreen")
Label_pageIntro3.pack()
# defining all the available frames 


Appointment_Booking_frame = Frame(root,bg="#F0F8FF")
Doctor_login_page_frame = Frame(root,bg="#F0F8FF")
Admin_login_page_frame = Frame(root,bg="#F0F8FF")
doctor_page_frame = Frame(root,bg="#F0F8FF")
admin_page_frame = Frame(root,bg="#F0F8FF")

# choosing which page to show and hiding other pages

def show_Page(Given_Page):
    global Home_page_frame,Appointment_Booking_frame,doctor_page_frame,Admin_login_page_frame,Doctor_login_page_frame,admin_page_frame
    for page in [Home_page_frame,Appointment_Booking_frame,doctor_page_frame,Admin_login_page_frame,Doctor_login_page_frame,admin_page_frame]:
        page.pack_forget()
    Given_Page.pack(expand=True, fill='both')

# Preparing Home_page_frame

# Home page frame
Home_page_frame = Frame(root, bg="#F0F8FF")
Home_page_frame.pack(pady=5, padx=20)

Label_pageIntro4 = Label(Home_page_frame, text="AVAILABLE SERVICES", font=("Times New Roman", 18, "bold"), fg="#3498db", bg="#F0F8FF")
Label_pageIntro4.pack(pady=20)

buttonframe = Frame(Home_page_frame, bg="#F0F8FF")
buttonframe.columnconfigure(0, weight=1)
buttonframe.columnconfigure(1, weight=1)
buttonframe.columnconfigure(2, weight=1)

services = ["Orthopaedic", "Gynaecology", "General Physician"]
for i, service in enumerate(services):
    label = Label(buttonframe, text=service, font=("Times New Roman", 16, "bold"), padx=15, pady=10, fg="#008000", bg="#F0F8FF")
    label.grid(row=0, column=i, padx=10, pady=10)

buttonframe.pack()

Book_Appointment_Button = Button(Home_page_frame, text="BOOK YOUR APPOINTMENT", font=("Times New Roman", 18, "bold"), bg="#008080", fg="white", bd=2, relief="raised", padx=20, pady=10, command=lambda: show_Page(Appointment_Booking_frame))
Book_Appointment_Button.pack(padx=50, pady=40)

Login_as_Admin_button = Button(Home_page_frame, text="Admin Login", font=("Times New Roman", 14, "bold"), fg="white", bg="#2980b9", bd=2, relief="raised", padx=15, pady=8, command=lambda: show_Page(Admin_login_page_frame))
Login_as_Admin_button.pack(pady=15)

Login_as_Doctor_button = Button(Home_page_frame, text="Doctor Login", font=("Times New Roman", 14, "bold"), fg="white", bg="#2980b9", bd=2, relief="raised", padx=15, pady=8, command=lambda: show_Page(Doctor_login_page_frame))
Login_as_Doctor_button.pack(pady=15)


#preparing appointment page frame 
#----------------------------------------------------------------------------------------------------

#Appointment_Booking_frame = Frame(root, bg="#F0F8FF")  # Light blue background for the frame
Appointment_Booking_frame.pack(expand=True, fill='both')  # Make the frame fill the entire window

# Title Label
Label_AppointmentPage1 = Label(Appointment_Booking_frame, text="Book Appointment", font=("Times New Roman", 23), bg="#F0F8FF", fg="#008080")  # Teal color text
Label_AppointmentPage1.pack(pady=40)

# Input frame for the form
text_Input_Frame = Frame(Appointment_Booking_frame, bg="#F0F8FF")
text_Input_Frame.columnconfigure(0, weight=1)
text_Input_Frame.columnconfigure(1, weight=1)

# Name entry
Label_Name = Label(text_Input_Frame, text="Name            :", font=("Times New Roman", 17), bg="#F0F8FF", fg="#006400")  # Dark green color text
Label_Name.grid(row=0, column=0, padx=10, pady=5, sticky=E)
Label_TextBox = Entry(text_Input_Frame, width=18, font=('Times New Roman', 16), bd=1, bg="#F0F8FF")
Label_TextBox.grid(row=0, column=1, padx=10, pady=5)

# Doctor selection
docter_choosed = StringVar(text_Input_Frame)
docter_choosed.set("choose the doctor")

Label_SelectDoctor = Label(text_Input_Frame, text="select Doctor    :", font=("Times New Roman", 17), bg="#F0F8FF", fg="#006400")  # Dark green color text
Label_SelectDoctor.grid(row=1, column=0, padx=10, pady=5, sticky=E)
Label_DropDown = OptionMenu(text_Input_Frame, docter_choosed, *(list(Harsha_Hospital.get_doctors().values())))
Label_DropDown.config(width=18, font=("Times New Roman", 15), bg="#F0F8FF" )
Label_DropDown.grid(row=1, column=1, padx=10, pady=5)

# Mapping doctor names to IDs
id_of_doctors = {v: k for k, v in Harsha_Hospital.get_doctors().items()}

# Time slot selection
Choosed_timeslot = StringVar(text_Input_Frame)
Choosed_timeslot.set("View Free Slots")
Label_Time_slot = Label(text_Input_Frame, text="select Time Slot :", font=("Times New Roman", 17), bg="#F0F8FF", fg="#006400")  # Dark green color text
Label_Time_slot.grid(row=2, column=0, padx=10, pady=5, sticky=E)

# Update time slots on doctor selection
def on_selection_change(*args):
    selected_value = docter_choosed.get()
    if selected_value != "choose the doctor":
        doctor_id = id_of_doctors[selected_value]
        free_slots = Appointment.view_free_slots(doctor_id)
        Label_timeSlotDropDown = OptionMenu(text_Input_Frame, Choosed_timeslot, *free_slots)
        Label_timeSlotDropDown.config(width=18, font=("Times New Roman", 15), bg="#F0F8FF")
        Label_timeSlotDropDown.grid(row=2, column=1, padx=10, pady=5)

selected_value = docter_choosed.get()
docter_choosed.trace('w', on_selection_change)

# Pack the input frame
text_Input_Frame.pack()

def show_confirmation_popup(patient_name, doctor_name, timeslot):
    messagebox.showinfo("Appointment Confirmation", f"Appointment successfully booked!\n\nName: {patient_name}\nDoctor: {doctor_name}\nTime Slot: {timeslot}")
    back_to_home_fromAppointment()

def back_to_home_fromAppointment():
    Label_TextBox.delete(0,END)
    docter_choosed.set("choose the doctor")
    show_Page(Home_page_frame)

# Function to book appointment
def book_appointment2():
    patient_name = Label_TextBox.get()
    selected_doctor = docter_choosed.get()
    selected_timeslot = Choosed_timeslot.get()
    if patient_name and selected_doctor != "choose the doctor" and selected_timeslot != "View Free Slots":
        doctor_id = id_of_doctors[selected_doctor]
        time_slot = datetime.strptime(selected_timeslot, '%Y-%m-%d %H:%M')
        if Appointment.book_appointment(patient_name, doctor_id, time_slot):
            connection.commit()
            show_confirmation_popup(patient_name, selected_doctor, selected_timeslot)
        else:
            messagebox.showerror("Booking Failed", "This time slot is already booked.")
    else:
        messagebox.showerror("Data required", "Fill all data")


# Submit button
Submit_Appointment_Button = Button(Appointment_Booking_frame, text="BOOK SLOT", font=("Times New Roman", 18), command=book_appointment2, bg="#008080", fg="white")  # Teal background, white text
Submit_Appointment_Button.pack(pady=40)

Back_Button = Button(Appointment_Booking_frame, text="Go Back", command=back_to_home_fromAppointment, font=("Times New Roman", 18), bg="black", fg="white")  # Black background, white text
Back_Button.pack(pady=20)


# Doctor_login_frame

Doctor_id_passwords = {y: str(x) * 8 for x, y in Doctor.id_name_dict.items()}

Label_Doctor_login_page1 = Label(Doctor_login_page_frame, text="Doctor Login Page", font=("Times New Roman", 23), bg="#F0F8FF", fg="#008080").pack(pady=30)

Doctor_login_Frame = Frame(Doctor_login_page_frame, bg="#F0F8FF")

Doctor_login_Frame.columnconfigure(0, weight=1)
Doctor_login_Frame.columnconfigure(1, weight=1)

Label_Name = Label(Doctor_login_Frame, text="Select Name       :", font=("Times New Roman", 17), bg="#F0F8FF").grid(row=0, column=0, padx=10, pady=5, sticky=E)

docter_choosed2 = StringVar(Doctor_login_Frame)
docter_choosed2.set("Select Your User name")

Label_DropDown = OptionMenu(Doctor_login_Frame, docter_choosed2, *(list(Doctor_id_passwords.keys())))
Label_DropDown.config(width=18, font=("Times New Roman", 15), bg="#F0F8FF" )
Label_DropDown.grid(row=0, column=1, padx=10, pady=5)

Label_Name = Label(Doctor_login_Frame, text="Enter Password  :", font=("Times New Roman", 17), bg="#F0F8FF").grid(row=1, column=0, padx=10, pady=5, sticky=E)
Password_Entry = Entry(Doctor_login_Frame, width=18, font=('Times New Roman', 16), bg="#F0F8FF", bd=1, show="*")
Password_Entry.grid(row=1, column=1, padx=10, pady=15)
Doctor_login_Frame.pack()

def set_logged_doctor(doctorUsername):
    Doctor.logged_in_doctor = doctorUsername



def clear_fields():
    docter_choosed2.set("Select Your User name")
    Password_Entry.delete(0, 'end')

# Login function
def login():
    username = docter_choosed2.get()
    password = Password_Entry.get()
    if username in Doctor_id_passwords and password == Doctor_id_passwords[username]:
        set_logged_doctor(username)
        # Show success message (optional)
        # messagebox.showinfo("Login Successful", "You have successfully logged in.")
        show_Page(doctor_page_frame)
        # Clear input fields after successful login
        clear_fields()
    else:
        messagebox.showerror("Login Failed", "Invalid username or password.")
        # Clear password field on login failure
        Password_Entry.delete(0, 'end')

# Back button command to clear fields and go back to Home page
def back_to_home():
    clear_fields()
    show_Page(Home_page_frame)

Login_Button = Button(Doctor_login_page_frame, text="Login", font=("Times New Roman", 18), command=login, fg="white", bg="#2980b9")
Login_Button.pack(pady=20)
Back_Button = Button(Doctor_login_page_frame, text="Go Back", command=back_to_home, font=("Times New Roman", 18), bg="black", fg="white")
Back_Button.pack(pady=20)

Doctor_login_page_frame.pack(expand=True, fill='both')



# preparing admin login frame

Admin_Id_password = {"Admin" : 00000000}

Label_Admin_login_page1 = Label(Admin_login_page_frame,text="Admin Login Page", font=("Times New Roman", 23), bg="#F0F8FF", fg="#008080").pack(pady=10)
admin_login_Frame = Frame(Admin_login_page_frame,bg="#F0F8FF")
admin_login_Frame.columnconfigure(0,weight=1)
admin_login_Frame.columnconfigure(1,weight=1)

def clearAdminLogin_fields():
    Admin_username.delete(0, 'end')
    Admin_Password.delete(0, 'end')

def back_to_homeFromAdmin():
    clearAdminLogin_fields()
    show_Page(Home_page_frame)


def admin_login():
    username = Admin_username.get()
    password = Admin_Password.get()
    if username == "Admin" and password == "00000000":
        #messagebox.showinfo("Login Successful", "You have successfully logged in.")
        clearAdminLogin_fields()
        show_Page(admin_page_frame)
    else:
        messagebox.showerror("Login Failed", "Invalid username or password.")
        clearAdminLogin_fields()

Label(admin_login_Frame,text="Enter User name :", font=("Times New Roman", 17), bg="#F0F8FF").grid(row=0, column=0, padx=10, pady=5, sticky=E)
Admin_username = Entry(admin_login_Frame,width=18,font=('Times New Roman', 16))
Admin_username.grid(row=0, column=1, padx=10, pady=15)

Label(admin_login_Frame,text="Enter Password  :", font=("Times New Roman", 17), bg="#F0F8FF").grid(row=1, column=0, padx=10, pady=5, sticky=E)
Admin_Password = Entry(admin_login_Frame,width=18,font=('Times New Roman', 16),show="*")
Admin_Password.grid(row=1, column=1, padx=10, pady=15)
admin_login_Frame.pack()
Login_Button = Button(Admin_login_page_frame,text="Login",font=("Times New Roman",18),command=admin_login, fg="white", bg="#2980b9").pack(pady=30)

Back_Button = Button(Admin_login_page_frame, text="Go Back", command=back_to_homeFromAdmin,font=("Times New Roman", 18), bg="black", fg="white")
Back_Button.pack(pady=20)

Admin_login_page_frame.pack(expand=True, fill='both')


# prepareing doctor page
name_id_dict = {x:y for y,x in Doctor.id_name_dict.items()}

def back_to_home_fromDoctor():
    text_output.config(state=NORMAL)
    text_output.delete(1.0, END)
    text_output.config(state=DISABLED)
    show_Page(Home_page_frame)

def view_Appointments():
    doctor_id = name_id_dict.get(Doctor.logged_in_doctor)  # Retrieve doctor's ID
    if doctor_id is not None:
        appointments = Appointment.view_all_appointments(doctor_id)
        appointment_text = "\n".join(appointments)  # Concatenate appointments with newline

        # Update the Text widget with the fetched appointments
        text_output.config(state=NORMAL)  
        text_output.delete(1.0, END)  
        text_output.insert(END, appointment_text)  
        text_output.config(state=DISABLED)  # Disable editing state again (read-only)

# Creating doctor page GUI components
Label_Doctor_page1 = Label(doctor_page_frame, text="Doctor Page", font=("Times New Roman", 23),bg="#F0F8FF", fg="#008080")
Label_Doctor_page1.pack()


label_result2 = Label(doctor_page_frame, text="Today's Appointments", font=("Times New Roman", 15), bg="#F0F8FF")
label_result2.pack()

# Creating a scrollbar
scrollbar = Scrollbar(doctor_page_frame, orient=VERTICAL)
scrollbar.pack(side=RIGHT, fill=Y)

# Text widget for displaying appointments
text_output = Text(doctor_page_frame, height=10, width=50, font=("Times New Roman", 12), wrap=WORD, yscrollcommand=scrollbar.set)
text_output.pack(fill=BOTH, expand=True)

# Configuring the scrollbar to work with the text widget
scrollbar.config(command=text_output.yview)

# Button to trigger fetching and displaying appointments
View_Appointments_button = Button(doctor_page_frame, text="View Appointments", font=("Times New Roman", 18), command=view_Appointments, bg="#008080",fg="white")
View_Appointments_button.pack(pady=20)
# Back button
Back_Button = Button(doctor_page_frame, text="Go Back", command=back_to_home_fromDoctor, font=("Times New Roman", 18), bg="black", fg="white")
Back_Button.pack(side="bottom")

# preparing admin page



Label_Admin_page1 = Label(admin_page_frame,text="Admin Page", font=("Times New Roman", 23), bg="#F0F8FF", fg="#008080").pack(pady=20)

Admin_choice_Frame = Frame(admin_page_frame,bg="#F0F8FF")
Admin_choice_Frame.columnconfigure(0,weight=1)
Admin_choice_Frame.columnconfigure(1,weight=1)

text_Input_Frame2 = Frame(admin_page_frame,bg="#F0F8FF")

text_Input_Frame2.columnconfigure(0,weight=1)
text_Input_Frame2.columnconfigure(1,weight=1)
text_Input_Frame2.columnconfigure(2,weight=1)

List_of_options = ["Add Doctor", "Delete Doctor","View Appointments of all doctors"]
option_Choosed = StringVar(text_Input_Frame2)
option_Choosed.set("What do you want to do")

Label_SelectOption = Label(Admin_choice_Frame,text="Choice    :", font=("Times New Roman", 17), bg="#F0F8FF").grid(row=0, column=0, padx=10, pady=5, sticky=E)
Label_DropDown = OptionMenu(Admin_choice_Frame,option_Choosed,*List_of_options)
Label_DropDown.config(font=("Times New Roman", 15), bg="#F0F8FF"  )
Label_DropDown.grid(row=0, column=1, padx=10, pady=5)

Admin_choice_Frame.pack()
admin_page_frame.pack(expand=True, fill="both")

def clear_previous_widgets():
    for widget in text_Input_Frame2.winfo_children():
        widget.destroy()

def onSelectionChange(*args):
    clear_previous_widgets()
    selected_value = option_Choosed.get()
    if selected_value == "Add Doctor":
        def addDoctor(name,specialization,gender,age):
            if Label_nameEntry.get() and Admin.add_doctor(name,specialization,gender,age):
                messagebox.showinfo("Doctor Added", f"Doctor successfully added!\n\nName: {name}\nspecialization: {specialization}\ngender: {gender}")
                show_Page(Home_page_frame)
            else:
                messagebox.showinfo("No Docter", f"Give Doctor details")

    
        Label(text_Input_Frame2,text="Enter doctor name     :", font=("Times New Roman", 17), bg="#F0F8FF").grid(row=1, column=0, padx=10, pady=5, sticky=E)
        Label(text_Input_Frame2,text="Enter doctor specilization :", font=("Times New Roman", 17), bg="#F0F8FF").grid(row=2, column=0, padx=10, pady=5, sticky=E)
        Label(text_Input_Frame2,text="Enter doctor Gender     :", font=("Times New Roman", 17), bg="#F0F8FF").grid(row=3, column=0, padx=10, pady=5, sticky=E)
        Label(text_Input_Frame2,text="Enter doctor experience    :", font=("Times New Roman", 17), bg="#F0F8FF").grid(row=4, column=0, padx=10, pady=5, sticky=E)
        Label_nameEntry = Entry(text_Input_Frame2,width=18,font=('Times New Roman', 16), bg="#F0F8FF", bd=1)
        Label_nameEntry.grid(row=1, column=1, padx=10, pady=15)
        Label_SpecializationEntry = Entry(text_Input_Frame2,width=18,font=('Times New Roman', 16), bd=1, bg="#F0F8FF")
        Label_SpecializationEntry.grid(row=2, column=1, padx=10, pady=15)
        Label_GenderEntry = Entry(text_Input_Frame2,width=18,font=('Times New Roman', 16), bd=1, bg="#F0F8FF")
        Label_GenderEntry.grid(row=3, column=1, padx=10, pady=15)
        Label_expEntry = Entry(text_Input_Frame2,width=18,font=('Times New Roman', 16), bd=1, bg="#F0F8FF")
        Label_expEntry.grid(row=4, column=1, padx=10, pady=15)
        Add_button = Button(text_Input_Frame2,text="Add Doctor",font=("Times New Roman",18), bg="#008080",fg="white",
                            command= lambda: addDoctor(Label_nameEntry.get(),
                                                        Label_SpecializationEntry.get(),
                                                        Label_GenderEntry.get(),
                                                        Label_expEntry.get()))
        Add_button.grid(row=5, column=0, padx=10, pady=15,columnspan=4)
        
       
    elif selected_value == "Delete Doctor":
        def delete_choosed_doctor():
            messagebox.showinfo("Deletion Stopped", "Impact on exiting appointments\n Hence deletion is not supported")
        
        docter_delete = StringVar(text_Input_Frame2)
        docter_delete.set("choose the doctor")
        Label_SelectDoctor = Label(text_Input_Frame2,text="select Doctor    :", font=("Times New Roman", 17), bg="#F0F8FF").grid(row=1, column=0, padx=10, pady=5, sticky=E)
        Label_DropDown = OptionMenu(text_Input_Frame2,docter_delete,*(list(Harsha_Hospital.get_doctors().values())))
        Label_DropDown.config(width=18,font=("Times New Roman", 15), bg="#F0F8FF" )
        Label_DropDown.grid(row=1, column=1, padx=10, pady=5)
        delete_button = Button(text_Input_Frame2,text="delete Doctor",font=("Times New Roman",18), bg="#008080",fg="white",command=delete_choosed_doctor)
        delete_button.grid(row=5, column=0,columnspan=4, padx=10, pady=15)
        
    elif selected_value == "View Appointments of all doctors":

        # Text widget for displaying appointments
        text_output2 = Text(text_Input_Frame2, height=10, width=80, font=("Times New Roman", 12), wrap=WORD)
        text_output2.pack(fill=BOTH, expand=True, padx=20, pady=10)  # Adjust padding and packing options for appearance

        # Function to fetch and display appointments
        def view_Appointments2():
            appointments = Admin.view_appointments_of_all_doctors()
            appointment_text = "\n".join(appointments)  # Concatenate appointments with newline

            # Updating the Text widget with the fetched appointments
            text_output2.config(state=NORMAL)  
            text_output2.delete(1.0, END)  
            text_output2.insert(END, appointment_text)  
            text_output2.config(state=DISABLED)  # Disable editing state again (read-only)

        # Button to trigger fetching and displaying appointments
        View_Appointments_button = Button(text_Input_Frame2, text="View Appointments", font=("Times New Roman", 18), command=view_Appointments2, bg="#008080",fg="white")
        View_Appointments_button.pack(pady=20)
        

    else:
        pass

    

option_Choosed.trace('w', onSelectionChange)
show_Page(Home_page_frame)
Back_Button = Button(admin_page_frame, text="Go Back", command=lambda :show_Page(Home_page_frame),font=("Times New Roman", 18), bg="black", fg="white")
Back_Button.pack(pady = 30,side="bottom")


text_Input_Frame2.pack()

root.mainloop()
# Close the connection
connection.close()
