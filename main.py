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

        self.blink_data = {
            'total_blinks': 0,
            'total_minutes': 0,
            'current_blinks': 0
        }

        self.create_ui_components()
        self.update_timer()

    def create_ui_components(self):
        self.create_stopwatch_label()
        self.create_reminder_input()
        self.create_buttons()
        self.create_blink_detection_components()

    def create_stopwatch_label(self):
        self.stopwatch_label = ttk.Label(
            master=self,
            font="-size 32",
            anchor=CENTER,
            text="00:00:00"
        )
        self.stopwatch_label.pack(side=TOP, fill=X, padx=60, pady=20)

    def create_reminder_input(self):
        reminder_frame = ttk.Frame(self)
        reminder_frame.pack(side=TOP, fill=X, pady=5)

        self.reminder_label = ttk.Label(reminder_frame, text="Reminder interval (min):")
        self.reminder_label.pack(side=LEFT, padx=(0, 5))
        
        self.reminder_input = ttk.Entry(reminder_frame, width=5)
        self.reminder_input.pack(side=LEFT)
        self.reminder_input.insert(0, "5")

        self.set_reminder_button = ttk.Button(reminder_frame, text="Set", command=self.set_reminder_time, width=5)
        self.set_reminder_button.pack(side=LEFT, padx=5)

    def create_buttons(self):
        button_frame = ttk.Frame(self)
        button_frame.pack(side=TOP, pady=10)

        self.start_button = ttk.Button(button_frame, text="Start", command=self.start, bootstyle="success", width=10)
        self.start_button.pack(side=LEFT, padx=5)

        self.pause_button = ttk.Button(button_frame, text="Pause", command=self.pause, bootstyle="warning", width=10)
        self.pause_button.pack(side=LEFT, padx=5)

        self.reset_button = ttk.Button(button_frame, text="Reset", command=self.reset, bootstyle="danger", width=10)
        self.reset_button.pack(side=LEFT, padx=5)

    def create_blink_detection_components(self):
        blink_frame = ttk.LabelFrame(self, text="Blink Detection")
        blink_frame.pack(side=TOP, pady=10, padx=10, fill=X)

        self.blink_detection_button = ttk.Button(blink_frame, text="Start Blink Detection", command=self.toggle_blink_detection, bootstyle="info", width=20)
        self.blink_detection_button.pack(side=TOP, pady=5)

        self.blink_status = ttk.Label(blink_frame, text="Status: Not Running", foreground="red")
        self.blink_status.pack(side=TOP, pady=5)

        data_frame = ttk.Frame(blink_frame)
        data_frame.pack(side=TOP, fill=X, expand=True)

        self.avg_blinks_label = ttk.Label(data_frame, text="Avg blinks/min: 0.00")
        self.avg_blinks_label.pack(side=LEFT, expand=True)

        self.current_blinks_label = ttk.Label(data_frame, text="Current blinks: 0")
        self.current_blinks_label.pack(side=LEFT, expand=True)

        self.blink_reset_button = ttk.Button(data_frame, text="Reset", command=self.reset_blink_data, bootstyle="secondary-outline", width=8)
        self.blink_reset_button.pack(side=RIGHT, padx=5)

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

        if self.blink_detection_running:
            self.update_blink_data()

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
            threading.Thread(target=self.show_topmost_msg, args=("Reminder", "Time to take a break!"), daemon=True).start()

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
            self.blink_status.config(text="Status: Running", foreground="green")
            self.blink_data['current_blinks'] = 0
            threading.Thread(target=self.run_blink_detection, daemon=True).start()
        else:
            self.blink_detection_running = False
            self.blink_detection_button.config(text="Start Blink Detection")
            self.blink_status.config(text="Status: Not Running", foreground="red")

    def update_blink_data(self):
        avg_blinks = self.blink_data['total_blinks'] / max(1, self.blink_data['total_minutes'])
        self.avg_blinks_label.config(text=f"Avg blinks/min: {avg_blinks:.2f}")
        self.current_blinks_label.config(text=f"Current blinks: {self.blink_data['current_blinks']}")

    def reset_blink_data(self):
        self.blink_data = {
            'total_blinks': 0,
            'total_minutes': 0,
            'current_blinks': 0
        }
        self.blink_count = 0
        self.update_blink_data()

    def show_topmost_msg(self, title, message):
        tpm_w = tk.Tk()
        tpm_w.withdraw()
        tpm_w.attributes('-topmost', True)
        messagebox.showinfo(title, message, parent=tpm_w)
        tpm_w.destroy()
        self.messagebox_open = False

    def run_blink_detection(self):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        predictor_path = os.path.join(base_path, "shape_predictor_68_face_landmarks.dat")

        detector = dlib.get_frontal_face_detector()
        predictor = dlib.shape_predictor(predictor_path)

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

            eyes_detected = False

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

                eyes_detected = True

                if ear < EAR_THRESHOLD:
                    frames_counter += 1
                else:
                    if frames_counter >= BLINK_CONSECUTIVE_FRAMES:
                        self.blink_count += 1
                    frames_counter = 0

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
                        self.after(0, self.show_blink_reminder)
                self.blink_count = 0
                self.blink_start_time = time.time()

            self.blink_data['current_blinks'] = self.blink_count

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or not self.blink_detection_running:
                break

        cap.release()
        cv2.destroyAllWindows()
        self.blink_detection_running = False
        self.after(0, self.blink_detection_button.config(text="Start Blink Detection"))

    def show_blink_reminder(self):
        def show_message():
            tpm_w = tk.Tk()
            tpm_w.withdraw()
            tpm_w.attributes('-topmost', True)
            messagebox.showinfo("Blink Reminder", "Please blink more frequently!", parent=tpm_w)
            tpm_w.destroy()
            self.messagebox_open = False

        if not self.messagebox_open:
            self.messagebox_open = True
            threading.Thread(target=show_message, daemon=True).start()

if __name__ == "__main__":
    app = ttk.Window(
        title="Screen Time Reminder",
        themename="cosmo",
        resizable=(False, False)
    )
    ScreenTimeReminder(app)
    app.mainloop()
