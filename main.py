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
        self.reminder_interval = 10  # Default reminder interval 10min
        self.messagebox_open = False

        self.tasks = []

        # Create UI components
        self.create_stopwatch_label()
        self.create_reminder_input()
        self.create_reminder_input2()
        self.create_buttons()
        self.create_task_input()
        self.create_task_tableview()

        self.update_clock()

    def update_clock(self):
        if self.running:
            current_time = time.time()
            self.elapsed_time = current_time - self.start_time
            hours, remainder = divmod(self.elapsed_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.stopwatch_label.config(text=f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}")
        self.after(1000, self.update_clock)

    def create_stopwatch_label(self):
        self.stopwatch_label = ttk.Label(
            master=self,
            font="-size 32",
            anchor=CENTER,
            text="00:00:00"
        )
        self.stopwatch_label.pack(side=TOP, fill=X, padx=60, pady=20)

    def create_reminder_input(self):
        self.reminder_label = ttk.Label(self, text="Set screen time reminder (min):")
        self.reminder_label.pack(side=TOP, pady=5)
        
        self.reminder_input = ttk.Entry(self)
        self.reminder_input.pack(side=TOP, pady=10)
        
        self.reminder_input.insert(0, "5")  # Set default value to 5 seconds

        self.set_reminder_button = ttk.Button(self, text="Set Reminder Time", command=self.set_reminder_time)
        self.set_reminder_button.pack(side=TOP, pady=10)
    def create_reminder_input2(self):
        self.reminder_label = ttk.Label(self, text="Big break for 25 mins:")
        self.reminder_label.pack(side=TOP, pady=5)
        
        self.reminder_input = ttk.Entry(self)
        self.reminder_input.pack(side=TOP, pady=10)
        
        self.reminder_input.insert(0, "25")  # Set default value to 5 seconds

        self.set_reminder_button = ttk.Button(self, text="Set Reminder Time", command=self.set_reminder_time)
        self.set_reminder_button.pack(side=TOP, pady=10)

    def create_buttons(self):
        button_frame = ttk.Frame(self)
        button_frame.pack(side=TOP, pady=10)

        self.start_button = ttk.Button(button_frame, text="Start", command=self.start, bootstyle="info")
        self.start_button.pack(side=LEFT, padx=20)

        self.pause_button = ttk.Button(button_frame, text="Pause", command=self.pause)
        self.pause_button.pack(side=LEFT, padx=20)

        self.reset_button = ttk.Button(button_frame, text="Reset", command=self.reset)
        self.reset_button.pack(side=LEFT, padx=20)

    def create_task_tableview(self):
        #treeview
        self.task_frame = ttk.Frame(self)
        self.task_frame.pack(side=BOTTOM, fill=BOTH, expand=YES, padx=10, pady=10)

        #scrollbar for the task treeview
        self.scrollbar = ttk.Scrollbar(self.task_frame, orient=tk.VERTICAL)
        self.scrollbar.pack(side=RIGHT, fill=Y)

        #index column
        self.task_tree = ttk.Treeview(self.task_frame, columns=("Index", "Task", "Status"), show='headings', height=5, yscrollcommand=self.scrollbar.set)
        self.task_tree.heading("Index", text="Index", anchor=tk.W)
        self.task_tree.heading("Task", text="Task", anchor=tk.W)
        self.task_tree.heading("Status", text="Status", anchor=tk.W)
        
        self.task_tree.column("Index", width=60)
        self.task_tree.column("Task", width=200)
        self.task_tree.column("Status", width=100)

        # Attach the scrollbar to the treeview
        self.scrollbar.config(command=self.task_tree.yview)

        # Place task table at the bottom
        self.task_tree.pack(side=LEFT, fill=BOTH, expand=YES)

    def create_task_input(self):
        self.task_input_frame = ttk.Frame(self)
        self.task_input_frame.pack(side=BOTTOM, pady=10)

        self.task_label = ttk.Label(self.task_input_frame, text="Add Task:")
        self.task_label.pack(side=LEFT, padx=5)

        self.task_input = ttk.Entry(self.task_input_frame)
        self.task_input.pack(side=LEFT, padx=5)

        self.add_task_button = ttk.Button(self.task_input_frame, text="Add Task", command=self.add_task, bootstyle="info")
        self.add_task_button.pack(side=LEFT, padx=5)

        # Button to mark the task as finished
        self.finish_task_button = ttk.Button(self.task_input_frame, text="Finish Task", command=self.finish_task, bootstyle="success")
        self.finish_task_button.pack(side=LEFT, padx=5)

        # Button to delete the selected task
        self.delete_task_button = ttk.Button(self.task_input_frame, text="Delete Task", command=self.delete_task, bootstyle="danger")
        self.delete_task_button.pack(side=LEFT, padx=5)

    def start(self):
        if not self.running:
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

    def show_topmost_msg(self, title, message):
        tpm_w = tk.Tk()
        tpm_w.withdraw()
        tpm_w.attributes('-topmost', True)
        messagebox.showinfo(title, message, parent=tpm_w)
        tpm_w.destroy()

    def reminder(self):
        if not self.messagebox_open:
            self.messagebox_open = True
            self.show_topmost_msg("Reminder", "Time to take a break!")
            self.messagebox_open = False
            self.schedule_reminder()

    def schedule_reminder(self):
        if self.running and not self.messagebox_open:
            self.reminder_job = self.after(self.reminder_interval * 60000, self.reminder)

    def cancel_reminder(self):
        if self.reminder_job:
            self.after_cancel(self.reminder_job)
            self.reminder_job = None

    def set_reminder_time(self):
        try:
            interval = int(self.reminder_input.get())
            if interval > 0:
                self.reminder_interval = interval  # Set the new reminder time
                messagebox.showinfo("Reminder Set", f"Reminder set to {interval} minutes!")
            else:
                messagebox.showerror("Invalid Input", "Please enter a positive number.")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number.")

    def add_task(self):
        task_text = self.task_input.get()
        if task_text:
            # Insert the task into the treeview with "Pending" status and index
            index = len(self.tasks) + 1
            self.task_tree.insert("", "end", values=(index, task_text, "Pending"))
            self.task_input.delete(0, tk.END)  # Clear input after adding task
            self.tasks.append(task_text)  # Keep track of tasks for indexing

    def finish_task(self):
        selected_task = self.task_tree.selection()
        if selected_task:
            for task in selected_task:
                # Update the selected task's status to "Finished"
                self.task_tree.item(task, values=(self.task_tree.item(task, 'values')[0], self.task_tree.item(task, 'values')[1], "Finished"))
        else:
            messagebox.showwarning("No Selection", "Please select a task to finish.")

    def delete_task(self):
        selected_task = self.task_tree.selection()
        if selected_task:
            for task in selected_task:
                self.task_tree.delete(task)  # Remove the selected task from the treeview
            # Reindex the remaining tasks
            for index, item in enumerate(self.task_tree.get_children(), start=1):
                task_values = self.task_tree.item(item, 'values')
                self.task_tree.item(item, values=(index, task_values[1], task_values[2]))
        else:
            messagebox.showwarning("No Selection", "Please select a task to delete.")

if __name__ == "__main__":
    app = ttk.Window(
        title="Screen Time Reminder",
        themename="cosmo",
        resizable=(False, False)
    )
    ScreenTimeReminder(app)
    app.mainloop()
