import ttkbootstrap as ttk
import tkinter as tk
from tkinter import messagebox
from ttkbootstrap.constants import *
import time
import cv2
import dlib
import numpy as np
from scipy.spatial import distance as dist
from imutils import face_utils
import threading

# Blink detection constants and functions
EAR_THRESHOLD = 0.40
BLINK_CONSECUTIVE_FRAMES = 1

def calculate_ear(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    ear = (A + B) / C
    return ear

class ScreenTimeReminder(ttk.Frame):
    def __init__(self, master_window):
        super().__init__(master_window, padding=(20, 10))
        self.pack(fill=BOTH, expand=YES)

        self.running = False
        self.start_time = 0
        self.elapsed_time = 0
        self.reminder_job = None
        self.reminder_interval = 10
        self.messagebox_open = False
        self.tasks = []

        # Blink detection variables
        self.blink_detection_running = False
        self.blink_count = 0
        self.blink_start_time = 0

        self.blink_data = {
            'total_blinks': 0,
            'total_minutes': 0,
            'current_blinks': 0
        }

        self.create_ui_components()
        self.update_clock()

    def create_ui_components(self):
        self.create_stopwatch_label()
        self.create_reminder_input()
        self.create_buttons()
        self.create_task_input()
        self.create_task_tableview()
        self.create_blink_detection_button()

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
        self.reminder_input.insert(0, "5")

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
        self.task_frame = ttk.Frame(self)
        self.task_frame.pack(side=BOTTOM, fill=BOTH, expand=YES, padx=10, pady=10)

        self.scrollbar = ttk.Scrollbar(self.task_frame, orient=tk.VERTICAL)
        self.scrollbar.pack(side=RIGHT, fill=Y)

        self.task_tree = ttk.Treeview(self.task_frame, columns=("Index", "Task", "Status"), show='headings', height=5, yscrollcommand=self.scrollbar.set)
        self.task_tree.heading("Index", text="Index", anchor=tk.W)
        self.task_tree.heading("Task", text="Task", anchor=tk.W)
        self.task_tree.heading("Status", text="Status", anchor=tk.W)
        
        self.task_tree.column("Index", width=60)
        self.task_tree.column("Task", width=200)
        self.task_tree.column("Status", width=100)

        self.scrollbar.config(command=self.task_tree.yview)
        self.task_tree.pack(side=BOTTOM, fill=BOTH, expand=YES)

    def create_task_input(self):
        self.task_input_frame = ttk.Frame(self)
        self.task_input_frame.pack(side=BOTTOM, pady=10)

        self.task_label = ttk.Label(self.task_input_frame, text="Add Task:")
        self.task_label.pack(side=LEFT, padx=5)

        self.task_input = ttk.Entry(self.task_input_frame)
        self.task_input.pack(side=LEFT, padx=5)

        self.add_task_button = ttk.Button(self.task_input_frame, text="Add Task", command=self.add_task, bootstyle="info")
        self.add_task_button.pack(side=LEFT, padx=5)

        self.finish_task_button = ttk.Button(self.task_input_frame, text="Finish Task", command=self.finish_task, bootstyle="success")
        self.finish_task_button.pack(side=LEFT, padx=5)

        self.delete_task_button = ttk.Button(self.task_input_frame, text="Delete Task", command=self.delete_task, bootstyle="danger")
        self.delete_task_button.pack(side=LEFT, padx=5)

    def create_blink_detection_button(self):
        blink_frame = ttk.Frame(self)
        blink_frame.pack(side=TOP, pady=10)

        self.blink_detection_button = ttk.Button(blink_frame, text="Start Blink Detection", command=self.toggle_blink_detection, bootstyle="warning")
        self.blink_detection_button.pack(side=TOP)

        self.blink_info_label = ttk.Label(blink_frame, text="Will remind you to blink if you haven't blinked 15 times in 60 seconds")
        self.blink_info_label.pack(side=TOP, pady=(5, 0))

        # New frame for blink data
        self.blink_data_frame = ttk.LabelFrame(self, text="Blink Data")
        self.blink_data_frame.pack(side=TOP, pady=10, padx=10, fill=X)

        self.avg_blinks_label = ttk.Label(self.blink_data_frame, text="Average blinks per minute: 0")
        self.avg_blinks_label.pack(side=TOP, pady=5)

        self.current_blinks_label = ttk.Label(self.blink_data_frame, text="Current blinks: 0")
        self.current_blinks_label.pack(side=TOP, pady=5)

    def update_clock(self):
        if self.running:
            current_time = time.time()
            self.elapsed_time = current_time - self.start_time
            hours, remainder = divmod(self.elapsed_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.stopwatch_label.config(text=f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}")
        self.after(1000, self.update_clock)

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
                self.reminder_interval = interval
                messagebox.showinfo("Reminder Set", f"Reminder set to {interval} minutes!")
            else:
                messagebox.showerror("Invalid Input", "Please enter a positive number.")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number.")

    def add_task(self):
        task_text = self.task_input.get()
        if task_text:
            index = len(self.tasks) + 1
            self.task_tree.insert("", "end", values=(index, task_text, "Pending"))
            self.task_input.delete(0, tk.END)  
            self.tasks.append(task_text)

    def finish_task(self):
        selected_task = self.task_tree.selection()
        if selected_task:
            for task in selected_task:
                self.task_tree.item(task, values=(self.task_tree.item(task, 'values')[0], self.task_tree.item(task, 'values')[1], "Finished"))
        else:
            messagebox.showwarning("No Selection", "Please select a task to finish.")

    def delete_task(self):
        selected_task = self.task_tree.selection()
        if selected_task:
            for task in selected_task:
                self.task_tree.delete(task)
            for index, item in enumerate(self.task_tree.get_children(), start=1):
                task_values = self.task_tree.item(item, 'values')
                self.task_tree.item(item, values=(index, task_values[1], task_values[2]))
        else:
            messagebox.showwarning("No Selection", "Please select a task to delete.")

    def toggle_blink_detection(self):
        if not self.blink_detection_running:
            self.blink_detection_running = True
            self.blink_detection_button.config(text="Stop Blink Detection")
            self.blink_data['current_blinks'] = 0
            threading.Thread(target=self.run_blink_detection, daemon=True).start()
            self.update_blink_data()
        else:
            self.blink_detection_running = False
            self.blink_detection_button.config(text="Start Blink Detection")

    def run_blink_detection(self):
        detector = dlib.get_frontal_face_detector()
        predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

        (lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
        (rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

        cap = cv2.VideoCapture(0)
        frames_counter = 0
        self.blink_count = 0
        self.blink_start_time = time.time()

        while self.blink_detection_running:
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detector(gray, 0)

            for face in faces:
                shape = predictor(gray, face)
                shape = face_utils.shape_to_np(shape)

                left_eye = shape[lStart:lEnd]
                right_eye = shape[rStart:rEnd]

                left_ear = calculate_ear(left_eye)
                right_ear = calculate_ear(right_eye)

                ear = (left_ear + right_ear) / 2.0

                left_eye_hull = cv2.convexHull(left_eye)
                right_eye_hull = cv2.convexHull(right_eye)
                cv2.drawContours(frame, [left_eye_hull], -1, (0, 255, 0), 1)
                cv2.drawContours(frame, [right_eye_hull], -1, (0, 255, 0), 1)

                if ear < EAR_THRESHOLD:
                    frames_counter += 1
                else:
                    if frames_counter >= BLINK_CONSECUTIVE_FRAMES:
                        self.blink_count += 1
                    frames_counter = 0

            elapsed_time = time.time() - self.blink_start_time

            cv2.putText(frame, f"Blinks: {self.blink_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(frame, f"Time: {int(elapsed_time)}s", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(frame, f"Press q to stop", (10, 460), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2   )

            cv2.imshow("Eye Blink Detector", frame)

            if elapsed_time >= 60:
                self.blink_data['total_blinks'] += self.blink_count
                self.blink_data['total_minutes'] += 1
                if self.blink_count < 15:
                    self.show_topmost_msg("Blink Reminder", "Please blink more frequently!")
                self.blink_count = 0
                self.blink_start_time = time.time()

            self.blink_data['current_blinks'] = self.blink_count

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

    def update_blink_data(self):
        if self.blink_detection_running:
            avg_blinks = self.blink_data['total_blinks'] / max(1, self.blink_data['total_minutes'])
            self.avg_blinks_label.config(text=f"Average blinks per minute: {avg_blinks:.2f}")
            self.current_blinks_label.config(text=f"Current blinks: {self.blink_data['current_blinks']}")
            self.after(1000, self.update_blink_data)

if __name__ == "__main__":
    app = ttk.Window(
        title="Screen Time Reminder",
        themename="cosmo",
        resizable=(False, False)
    )
    ScreenTimeReminder(app)
    app.mainloop()
