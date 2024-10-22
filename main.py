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
import os
import sys

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
        self.reminder_interval = 300  # 5 minutes default
        self.messagebox_open = False

        self.blink_detection_running = False
        self.blink_count = 0
        self.blink_start_time = 0
        self.frames_counter = 0

        self.blink_data = {
            'total_blinks': 0,
            'total_minutes': 0,
            'current_blinks': 0
        }

        self.create_ui_components()
        self.setup_blink_detection()
        self.update_timer()

    def create_ui_components(self):
        self.create_stopwatch_label()
        self.create_reminder_input()
        self.create_buttons()
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

    def create_blink_detection_button(self):
        blink_frame = ttk.Frame(self)
        blink_frame.pack(side=TOP, pady=10)

        self.blink_detection_button = ttk.Button(blink_frame, text="Start Blink Detection", command=self.toggle_blink_detection, bootstyle="warning")
        self.blink_detection_button.pack(side=TOP)

        self.blink_info_label = ttk.Label(blink_frame, text="Will remind you to blink if you haven't blinked 15 times in 60 seconds")
        self.blink_info_label.pack(side=TOP, pady=(5, 0))

        self.blink_data_frame = ttk.LabelFrame(self, text="Blink Data")
        self.blink_data_frame.pack(side=TOP, pady=10, padx=10, fill=X)

        self.avg_blinks_label = ttk.Label(self.blink_data_frame, text="Average blinks per minute: 0")
        self.avg_blinks_label.pack(side=TOP, pady=5)

        self.current_blinks_label = ttk.Label(self.blink_data_frame, text="Current blinks: 0")
        self.current_blinks_label.pack(side=TOP, pady=5)

        self.blink_reset_button = ttk.Button(
            self.blink_data_frame, 
            text="Reset", 
            command=self.reset_blink_data, 
            bootstyle="secondary-outline",
            width=8
        )
        self.blink_reset_button.pack(side=TOP, padx=(0, 10), pady=5)

    def update_timer(self):
        if self.running:
            current_time = time.time()
            self.elapsed_time = current_time - self.start_time
            hours, remainder = divmod(self.elapsed_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.stopwatch_label.config(text=f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}")

            if self.elapsed_time >= self.reminder_interval:
                self.show_reminder()
                self.start_time = current_time  # Reset the timer

        self.after(1000, self.update_timer)

    def start(self):
        if not self.running:
            self.start_time = time.time() - self.elapsed_time
            self.running = True
            self.start_button.config(state="disabled")
            self.pause_button.config(state="normal")

    def pause(self):
        if self.running:
            self.running = False
            self.start_button.config(state="normal")
            self.pause_button.config(state="disabled")

    def reset(self):
        self.running = False
        self.elapsed_time = 0
        self.stopwatch_label.config(text="00:00:00")
        self.start_button.config(state="normal")
        self.pause_button.config(state="disabled")

    def show_reminder(self):
        if not self.messagebox_open:
            self.messagebox_open = True
            self.after(0, self._show_reminder_on_main_thread)

    def _show_reminder_on_main_thread(self):
        self.show_topmost_msg("Reminder", "Time to take a break!")
        self.messagebox_open = False

    def set_reminder_time(self):
        try:
            interval = int(self.reminder_input.get())
            if interval > 0:
                self.reminder_interval = interval * 60
                messagebox.showinfo("Reminder Set", f"Reminder set to {interval} minutes!")
            else:
                messagebox.showerror("Invalid Input", "Please enter a positive number.")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number.")

    def toggle_blink_detection(self):
        if not self.blink_detection_running:
            self.blink_detection_running = True
            self.blink_detection_button.config(text="Stop Blink Detection")
            self.blink_data['current_blinks'] = 0
            self.blink_count = 0
            self.blink_start_time = time.time()
            self.cap = cv2.VideoCapture(0)
            self.after(10, self.process_frame)
        else:
            self.blink_detection_running = False
            self.blink_detection_button.config(text="Start Blink Detection")
            if self.cap:
                self.cap.release()
            cv2.destroyAllWindows()

    def process_frame(self):
        if not self.blink_detection_running:
            return

        ret, frame = self.cap.read()
        if not ret:
            self.toggle_blink_detection()
            return

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.detector(gray, 0)

        eyes_detected = False

        for face in faces:
            shape = self.predictor(gray, face)
            shape = face_utils.shape_to_np(shape)

            left_eye = shape[self.lStart:self.lEnd]
            right_eye = shape[self.rStart:self.rEnd]

            left_ear = calculate_ear(left_eye)
            right_ear = calculate_ear(right_eye)

            ear = (left_ear + right_ear) / 2.0

            left_eye_hull = cv2.convexHull(left_eye)
            right_eye_hull = cv2.convexHull(right_eye)
            cv2.drawContours(frame, [left_eye_hull], -1, (0, 255, 0), 1)
            cv2.drawContours(frame, [right_eye_hull], -1, (0, 255, 0), 1)

            eyes_detected = True

            if ear < EAR_THRESHOLD:
                self.frames_counter += 1
            else:
                if self.frames_counter >= BLINK_CONSECUTIVE_FRAMES:
                    self.blink_count += 1
                self.frames_counter = 0

        elapsed_time = time.time() - self.blink_start_time

        if eyes_detected:
            status_text = "Eyes detected"
            status_color = (0, 255, 0)
        else:
            status_text = "No eyes detected"
            status_color = (0, 0, 255)

        cv2.putText(frame, f"Blinks: {self.blink_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(frame, f"Time: {int(elapsed_time)}s", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(frame, status_text, (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        cv2.putText(frame, f"Press q to stop", (10, 460), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.imshow("Eye Blink Detector", frame)

        if elapsed_time >= 60:
            if eyes_detected:
                self.blink_data['total_blinks'] += self.blink_count
                self.blink_data['total_minutes'] += 1
                if self.blink_count < 15:
                    self.show_blink_reminder()
            self.blink_count = 0
            self.blink_start_time = time.time()

        self.blink_data['current_blinks'] = self.blink_count
        self.update_blink_data()

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            self.toggle_blink_detection()
        else:
            self.after(10, self.process_frame)

    def update_blink_data(self):
        avg_blinks = self.blink_data['total_blinks'] / max(1, self.blink_data['total_minutes'])
        self.avg_blinks_label.config(text=f"Average blinks per minute: {avg_blinks:.2f}")
        self.current_blinks_label.config(text=f"Current blinks: {self.blink_data['current_blinks']}")

    def reset_blink_data(self):
        self.blink_data = {
            'total_blinks': 0,
            'total_minutes': 0,
            'current_blinks': 0
        }
        self.blink_count = 0
        self.update_blink_data()
        messagebox.showinfo("Blink Data Reset", "Blink data has been reset successfully!")

    def show_topmost_msg(self, title, message):
        tpm_w = tk.Toplevel(self)
        tpm_w.withdraw()
        tpm_w.attributes('-topmost', True)
        messagebox.showinfo(title, message, parent=tpm_w)
        tpm_w.destroy()

    def setup_blink_detection(self):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        predictor_path = os.path.join(base_path, "shape_predictor_68_face_landmarks.dat")

        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(predictor_path)

        (self.lStart, self.lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
        (self.rStart, self.rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

        self.cap = None
        self.frames_counter = 0

    def show_blink_reminder(self):
        if not self.messagebox_open:
            self.messagebox_open = True
            self.after(0, self._show_blink_reminder_on_main_thread)

    def _show_blink_reminder_on_main_thread(self):
        tpm_w = tk.Toplevel(self)
        tpm_w.withdraw()
        tpm_w.attributes('-topmost', True)
        messagebox.showinfo("Blink Reminder", "Please blink more frequently!", parent=tpm_w)
        tpm_w.destroy()
        self.messagebox_open = False

if __name__ == "__main__":
    app = ttk.Window(
        title="Screen Time Reminder",
        themename="cosmo",
        resizable=(False, False)
    )
    ScreenTimeReminder(app)
    app.mainloop()
