import ttkbootstrap as ttk
import tkinter as tk
from tkinter import messagebox
from ttkbootstrap.constants import *
import time

class ScreenTimeReminder(ttk.Frame):
    def __init__(self, master_window):
        super().__init__(master_window, padding=(20, 10))
        self.pack(fill=BOTH, expand=YES)
        
        self.running = False
        self.start_time = 0
        self.elapsed_time = 0
        self.reminder_job = None
        self.reminder_elapsed_time = 0
        self.reminder_interval = 5 #
        self.messagebox_open = False
        
        self.create_stopwatch_label()
        self.create_reminder_input()
        self.create_buttons()
        self.update_clock()
        
    def update_clock(self):
        if self.running:
            # Calculate elapsed time
            current_time = time.time()
            self.elapsed_time = current_time - self.start_time
            hours, remainder = divmod(self.elapsed_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            # Update the label with formatted time
            
            self.stopwatch_label.config(text=f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}")
        # Schedule the next 
        self.after(1000, self.update_clock)  

    def create_stopwatch_label(self):
        self.stopwatch_label = ttk.Label(
            master=self,
            font="-size 32",
            anchor=CENTER,
            text="00:00:00"  # Initialize with the correct text
        )
        self.stopwatch_label.pack(side=TOP, fill=X, padx=60, pady=20)


    def create_buttons(self):
        """
        primary: Blue (default for primary actions).
        secondary: Grey (secondary actions).
        success: Green (for success or confirmation).
        info: Light blue (informational actions).
        warning: Yellow (for warnings).
        danger: Red (for destructive actions).
        light: White/light grey.
        dark: Dark grey/black.
        """
        self.start_button = ttk.Button(self, text="Start", command=self.start, bootstyle="info")
        self.start_button.pack(side=LEFT, padx=20)

        self.pause_button = ttk.Button(self, text="Pause", command=self.pause)
        self.pause_button.pack(side=LEFT, padx=20)

        self.reset_button = ttk.Button(self, text="Reset", command=self.reset)
        self.reset_button.pack(side=LEFT, padx=20)

    def create_reminder_input(self):
        # Label and input for reminder interval
        self.reminder_label = ttk.Label(self, text="Set screen time reminder (seconds):")
        self.reminder_label.pack(side=TOP, pady=5)
        
        self.reminder_input = ttk.Entry(self)
        self.reminder_input.pack(side=TOP, pady=10)
        
        self.reminder_input.insert(0,"5")

        self.set_reminder_button = ttk.Button(self, text="Set Reminder Time", command=self.set_reminder_time)
        self.set_reminder_button.pack(side=TOP, pady=10)

    def start(self):
        if not self.running:
            # Set the start_time correctly
            self.start_time = time.time() - self.elapsed_time
            self.running = True
            self.schedule_reminder()


    def pause(self):
        if self.running:
            self.running = False
            self.cancel_reminder()

    def reset(self):
        self.running = False
        self.elapsed_time = 0
        self.stopwatch_label.config(text="00:00:00")
        self.cancel_reminder()
        self.messagebox_open = False

    def reminder(self):
        if not self.messagebox_open:
            self.messagebox_open = True
            messagebox.showinfo("提醒", "休息一下！")
            self.messagebox_open = False
            self.schedule_reminder()
    
    def schedule_reminder(self):
        if self.running and not self.messagebox_open:
            self.reminder_job = self.after(self.reminder_interval * 1000,
                                           self.reminder)

    def cancel_reminder(self):
        if self.reminder_job:
            self.after_cancel(self.reminder_job)
            self.reminder_job = None
    def set_reminder_time(self):
        try:
            interval = int(self.reminder_input.get())
            if interval > 0:
                self.reminder_interval = interval  # Set the new reminder time
                messagebox.showinfo("Reminder Set", f"Reminder set to {interval} seconds!")
            else:
                messagebox.showerror("Invalid Input", "Please enter a positive number.")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number.")
if __name__ == "__main__":
    app = ttk.Window(
        title="Screen Time Reminder",   
        themename="cosmo", 
        resizable=(False, False)
    )
    ScreenTimeReminder(app)
    app.mainloop()
