import os
import tkinter as tk
from tkinter import filedialog, messagebox, Label
import subprocess
import cv2
from PIL import Image, ImageTk

rife_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ECCV2022-RIFE")

class VideoConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("영상 변환 및 재생 프로그램")
        self.root.geometry("600x500") 

        input_frame = tk.Frame(root)
        input_frame.pack(pady=5)

        self.input_label = tk.Label(input_frame, text="입력 파일: 없음", wraplength=400)
        self.input_label.pack(side=tk.LEFT, padx=5)

        self.select_input_button = tk.Button(input_frame, text="입력 파일 선택", command=self.select_input_file)
        self.select_input_button.pack(side=tk.RIGHT, padx=5)

        frame_setting = tk.Frame(root)
        frame_setting.pack(pady=5)

        self.exp_value = 1 
        self.frame_label = tk.Label(frame_setting, text=f"프레임 수: x{2**self.exp_value}")
        self.frame_label.pack(side=tk.LEFT, padx=5)

        self.frame_button = tk.Button(frame_setting, text="증가 프레임 수 변경", command=self.change_exp)
        self.frame_button.pack(side=tk.RIGHT, padx=5)

        button_frame = tk.Frame(root)
        button_frame.pack(pady=5)

        self.convert_button = tk.Button(button_frame, text="일반 변환", command=lambda: self.convert_video(montage=False), state=tk.DISABLED)
        self.convert_button.grid(row=0, column=0, padx=5)

        self.compare_button = tk.Button(button_frame, text="비교 변환", command=lambda: self.convert_video(montage=True), state=tk.DISABLED)
        self.compare_button.grid(row=0, column=1, padx=5)

        self.status_label = tk.Label(root, text="변환 상태: 대기 중", fg="blue")
        self.status_label.pack(pady=5)

        self.video_label = Label(root)
        self.video_label.pack(pady=10)

        self.input_file = None
        self.output_folder = None
        self.output_file = None
        self.cap = None
        self.playing = False 

    def select_input_file(self):
        """입력 파일 선택"""
        file_path = filedialog.askopenfilename(title="입력 영상 파일 선택",
                                               filetypes=[("Video Files", "*.mp4 *.avi *.mkv *.mov")])
        if file_path:
            self.input_file = file_path
            self.input_label.config(text=f"입력 파일: {os.path.basename(file_path)}")
            self.convert_button.config(state=tk.NORMAL)  
            self.compare_button.config(state=tk.NORMAL) 

    def change_exp(self):
        """프레임 수 변경 (exp 값을 1 → 2 → 3 → 4 → 1 순환)"""
        self.exp_value = self.exp_value + 1 if self.exp_value < 4 else 1
        self.frame_label.config(text=f"프레임 수: x{2**self.exp_value}")

    def get_output_filename(self, montage):
        """입력 폴더에 'output' 폴더를 만들고, output{n}.mp4 형식으로 저장"""
        input_folder = os.path.dirname(self.input_file) 
        self.output_folder = os.path.join(input_folder, "output") 

        os.makedirs(self.output_folder, exist_ok=True) 

        n = 1
        while True:
            suffix = "_montage" if montage else ""  
            output_file = os.path.join(self.output_folder, f"output{n}{suffix}.mp4")
            if not os.path.exists(output_file):
                return output_file
            n += 1

    def convert_video(self, montage=False):
        """subprocess.run()을 사용해 영상 변환 실행"""
        if not self.input_file:
            messagebox.showerror("오류", "입력 파일을 설정하세요.")
            return

        self.output_file = self.get_output_filename(montage)

        command = [
            "python", os.path.join(rife_path, "inference_video.py"),
            f"--exp={self.exp_value}", 
            f"--video={self.input_file}",
            f"--output={self.output_file}"
        ]

        if montage:
            command.append("--montage") 

        try:
            self.status_label.config(text="변환 중...", fg="red")
            self.root.update_idletasks()

            subprocess.run(command, capture_output=True, text=True, cwd=rife_path)

            self.status_label.config(text="변환 완료!", fg="green")

            if self.cap:
                self.cap.release()
                cv2.destroyAllWindows()
                self.cap = None

            self.play_video()

        except Exception as e:
            messagebox.showerror("오류", f"변환 중 오류 발생: {str(e)}")

    def play_video(self):
        if not self.output_file or not os.path.exists(self.output_file):
            messagebox.showerror("오류", "출력 영상이 존재하지 않습니다.")
            return

        if self.cap is not None:
            self.cap.release()

        self.cap = cv2.VideoCapture(self.output_file)

        if hasattr(self, "after_id"):
            self.root.after_cancel(self.after_id)

        self.playing = True

        fps = self.cap.get(cv2.CAP_PROP_FPS)

        frame_delay = int(1000 / fps) 

        # 비디오 재생 시작
        self.show_frame(frame_delay)

    def show_frame(self, frame_delay):
        if self.cap and self.playing:
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                img = img.resize((400, 300), Image.Resampling.LANCZOS)
                imgtk = ImageTk.PhotoImage(image=img)

                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)

                # 다음 프레임 예약 실행
                self.after_id = self.root.after(frame_delay, lambda: self.show_frame(frame_delay))
            else:
                # 영상 끝나면 처음으로 되감기 후 다시 재생
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.after_id = self.root.after(frame_delay, lambda: self.show_frame(frame_delay))


if __name__ == "__main__":
    root = tk.Tk()
    app = VideoConverterApp(root)
    root.mainloop()
