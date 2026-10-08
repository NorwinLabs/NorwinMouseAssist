"""
NorwinMouseAssist - GUI Application
Helps people with Parkinson's or tremors use a computer by smoothing mouse movements.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from mouse_smoother import MouseRecorder, MouseSmoother
from tremor import TremorProfile, analyze_tremor

CALIBRATION_SECONDS = 15


class CalibrationDialog:
    """
    Guides the user through recording a short sample of their hand movement,
    detects the tremor in it, and returns a TremorProfile via `self.result`.
    """

    def __init__(self, parent):
        self.parent = parent
        self.result = None
        self.recorder = MouseRecorder()
        self._after_id = None
        self._elapsed = 0.0

        self.win = tk.Toplevel(parent)
        self.win.title("Tremor Calibration")
        self.win.geometry("420x360")
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.protocol("WM_DELETE_WINDOW", self._cancel)

        tk.Label(self.win, text="Tremor Calibration",
                 font=("Arial", 16, "bold"), pady=8).pack()

        self.message = tk.Label(self.win, justify="left", wraplength=380,
                                font=("Arial", 10))
        self.message.pack(padx=20, pady=5)

        self.progress = ttk.Progressbar(self.win, length=360,
                                        maximum=CALIBRATION_SECONDS)
        self.detail = tk.Label(self.win, font=("Arial", 10), fg="gray")

        self.buttons = tk.Frame(self.win)
        self.buttons.pack(side="bottom", pady=15)

        self._show_intro()
        self.win.grab_set()

    def wait(self):
        """Block until the dialog is closed; returns the new profile or None."""
        self.parent.wait_window(self.win)
        return self.result

    # --- screens -----------------------------------------------------------

    def _set_buttons(self, *specs):
        for child in self.buttons.winfo_children():
            child.destroy()
        for text, command in specs:
            tk.Button(self.buttons, text=text, command=command,
                      font=("Arial", 11), padx=12, pady=4).pack(side="left", padx=6)

    def _show_intro(self):
        self.progress.pack_forget()
        self.detail.pack_forget()
        self.message.config(text=(
            f"This takes {CALIBRATION_SECONDS} seconds.\n\n"
            "1. Rest your hand on the mouse the way you normally would.\n"
            "2. Press Start, then keep holding the mouse. Don't try to hold "
            "it still or fight the shaking - just let it happen.\n"
            "3. If you like, move the mouse slowly around the screen. "
            "Slow, deliberate movement is ignored.\n\n"
            "Smoothing is paused during calibration."))
        self._set_buttons(("Start", self._start), ("Cancel", self._cancel))

    def _start(self):
        self._elapsed = 0.0
        self.message.config(text="Recording... keep your hand on the mouse.")
        self.progress.config(value=0)
        self.progress.pack(pady=10)
        self.detail.config(text="")
        self.detail.pack()
        self._set_buttons(("Cancel", self._cancel))
        self.recorder.start()
        self._tick()

    def _tick(self):
        self._elapsed += 0.1
        self.progress.config(value=self._elapsed)
        self.detail.config(text=f"{int(self._elapsed)} / {CALIBRATION_SECONDS} s   "
                                f"({len(self.recorder.samples)} movements captured)")
        if self._elapsed >= CALIBRATION_SECONDS:
            self._finish()
        else:
            self._after_id = self.win.after(100, self._tick)

    def _finish(self):
        samples = self.recorder.stop()
        profile = analyze_tremor(samples)
        self.progress.pack_forget()

        if profile.detected:
            self.message.config(text=(
                "Tremor detected.\n\n"
                f"Frequency: {profile.frequency_hz:.1f} Hz "
                f"({profile.frequency_hz * 60:.0f} cycles per minute)\n"
                f"Size: about {profile.amplitude_px:.1f} pixels\n\n"
                "Apply this to cancel the tremor from your mouse input?"))
            self.detail.config(text="")
            self._set_buttons(("Apply & Save", lambda: self._accept(profile)),
                              ("Redo", self._show_intro),
                              ("Cancel", self._cancel))
        else:
            reason = ("Not enough mouse movement was recorded. Try again and "
                      "keep your hand on the mouse." if len(samples) < 50 else
                      "No clear, repeating tremor was found. That can happen "
                      "if the shaking was irregular or very small. You can "
                      "still use the general Smoothing settings.")
            self.message.config(text=f"No tremor detected.\n\n{reason}")
            self.detail.config(text="")
            self._set_buttons(("Try Again", self._show_intro), ("Close", self._cancel))

    # --- outcomes ----------------------------------------------------------

    def _accept(self, profile):
        self.result = profile
        self._close()

    def _cancel(self):
        self._close()

    def _close(self):
        if self._after_id:
            self.win.after_cancel(self._after_id)
            self._after_id = None
        self.recorder.stop()
        self.win.grab_release()
        self.win.destroy()


class MouseAssistApp:
    """Main application window for mouse smoothing control."""

    def __init__(self, root):
        self.root = root
        self.root.title("NorwinMouseAssist")
        self.root.resizable(False, False)  # window sizes itself to its content

        # Initialize mouse smoother
        self.smoother = MouseSmoother()
        self.is_running = False

        # Saved tremor calibration (if any)
        self.profile = TremorProfile.load()
        self.use_tremor_var = tk.BooleanVar(
            value=bool(self.profile and self.profile.detected))

        # Set up UI
        self._create_menu()
        self._create_widgets()
        self._update_tremor_ui()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_menu(self):
        """Create the menu bar."""
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Enable / Disable Smoothing",
                              command=self._toggle_smoothing, accelerator="Ctrl+E")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_closing)
        menubar.add_cascade(label="File", menu=file_menu)

        calib_menu = tk.Menu(menubar, tearoff=False)
        calib_menu.add_command(label="Run Calibration...",
                               command=self._run_calibration, accelerator="Ctrl+K")
        calib_menu.add_checkbutton(label="Use Tremor Cancellation",
                                   variable=self.use_tremor_var,
                                   command=self._on_use_tremor_toggled)
        calib_menu.add_separator()
        calib_menu.add_command(label="View Calibration Results...",
                               command=self._show_profile)
        calib_menu.add_command(label="Reset Calibration",
                               command=self._reset_calibration)
        menubar.add_cascade(label="Calibration", menu=calib_menu)

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="How Calibration Works...",
                              command=self._show_help)
        help_menu.add_command(label="About", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)
        self.root.bind("<Control-e>", lambda e: self._toggle_smoothing())
        self.root.bind("<Control-k>", lambda e: self._run_calibration())
        self.calib_menu = calib_menu

    def _create_widgets(self):
        """Create and layout all UI widgets."""
        
        # Title
        title_label = tk.Label(
            self.root,
            text="NorwinMouseAssist",
            font=("Arial", 18, "bold"),
            pady=10
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            self.root,
            text="Mouse Smoothing for Steady Control",
            font=("Arial", 10),
            fg="gray"
        )
        subtitle_label.pack()
        
        # Status Frame
        status_frame = tk.LabelFrame(
            self.root,
            text="Status",
            font=("Arial", 11, "bold"),
            padx=20,
            pady=15
        )
        status_frame.pack(padx=20, pady=15, fill="x")
        
        self.status_label = tk.Label(
            status_frame,
            text="● Disabled",
            font=("Arial", 12),
            fg="red"
        )
        self.status_label.pack()
        
        # Control Button
        self.toggle_button = tk.Button(
            self.root,
            text="Enable Smoothing",
            font=("Arial", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            activebackground="#45a049",
            pady=10,
            command=self._toggle_smoothing
        )
        self.toggle_button.pack(padx=20, pady=10, fill="x")
        
        # Tremor Cancellation Frame
        tremor_frame = tk.LabelFrame(
            self.root,
            text="Tremor Cancellation",
            font=("Arial", 11, "bold"),
            padx=20,
            pady=10
        )
        tremor_frame.pack(padx=20, pady=5, fill="x")

        self.calib_label = tk.Label(tremor_frame, font=("Arial", 10),
                                    justify="left", wraplength=340)
        self.calib_label.grid(row=0, column=0, columnspan=2, sticky="w")

        tk.Button(
            tremor_frame,
            text="Calibrate...",
            font=("Arial", 10),
            command=self._run_calibration
        ).grid(row=1, column=0, sticky="w", pady=6)

        self.use_tremor_check = tk.Checkbutton(
            tremor_frame,
            text="Use tremor cancellation",
            variable=self.use_tremor_var,
            command=self._on_use_tremor_toggled
        )
        self.use_tremor_check.grid(row=1, column=1, sticky="e", padx=10)

        tk.Label(tremor_frame, text="Strength:", font=("Arial", 10)).grid(
            row=2, column=0, sticky="w")
        self.tremor_strength_var = tk.IntVar(value=5)
        self.tremor_strength_scale = tk.Scale(
            tremor_frame,
            from_=1,
            to=10,
            orient="horizontal",
            variable=self.tremor_strength_var,
            command=self._update_settings,
            length=200
        )
        self.tremor_strength_scale.grid(row=2, column=1, padx=10)
        tk.Label(
            tremor_frame,
            text="(Higher = removes more tremor, more lag)",
            font=("Arial", 8),
            fg="gray"
        ).grid(row=3, column=1, sticky="w", padx=10)

        # Settings Frame
        settings_frame = tk.LabelFrame(
            self.root,
            text="General Smoothing (used when tremor cancellation is off)",
            font=("Arial", 11, "bold"),
            padx=20,
            pady=15
        )
        settings_frame.pack(padx=20, pady=10, fill="both", expand=True)
        
        # Smoothing Level
        smoothing_label = tk.Label(
            settings_frame,
            text="Smoothing Level:",
            font=("Arial", 10)
        )
        smoothing_label.grid(row=0, column=0, sticky="w", pady=5)
        
        self.smoothing_var = tk.IntVar(value=5)
        smoothing_scale = tk.Scale(
            settings_frame,
            from_=2,
            to=10,
            orient="horizontal",
            variable=self.smoothing_var,
            command=self._update_settings,
            length=200
        )
        smoothing_scale.grid(row=0, column=1, pady=5, padx=10)
        
        smoothing_info = tk.Label(
            settings_frame,
            text="(Higher = smoother, more lag)",
            font=("Arial", 8),
            fg="gray"
        )
        smoothing_info.grid(row=1, column=1, sticky="w", padx=10)
        
        # Max Speed
        speed_label = tk.Label(
            settings_frame,
            text="Max Speed:",
            font=("Arial", 10)
        )
        speed_label.grid(row=2, column=0, sticky="w", pady=5)
        
        self.speed_var = tk.IntVar(value=50)
        speed_scale = tk.Scale(
            settings_frame,
            from_=20,
            to=100,
            orient="horizontal",
            variable=self.speed_var,
            command=self._update_settings,
            length=200
        )
        speed_scale.grid(row=2, column=1, pady=5, padx=10)
        
        speed_info = tk.Label(
            settings_frame,
            text="(Limits rapid movements)",
            font=("Arial", 8),
            fg="gray"
        )
        speed_info.grid(row=3, column=1, sticky="w", padx=10)
        
        # Jitter Filter
        jitter_label = tk.Label(
            settings_frame,
            text="Jitter Filter:",
            font=("Arial", 10)
        )
        jitter_label.grid(row=4, column=0, sticky="w", pady=5)
        
        self.jitter_var = tk.IntVar(value=3)
        jitter_scale = tk.Scale(
            settings_frame,
            from_=1,
            to=10,
            orient="horizontal",
            variable=self.jitter_var,
            command=self._update_settings,
            length=200
        )
        jitter_scale.grid(row=4, column=1, pady=5, padx=10)
        
        jitter_info = tk.Label(
            settings_frame,
            text="(Filters small tremors)",
            font=("Arial", 8),
            fg="gray"
        )
        jitter_info.grid(row=5, column=1, sticky="w", padx=10)
        
        # Info text
        info_text = tk.Label(
            self.root,
            text="Adjust settings to your comfort level.\nChanges apply immediately.",
            font=("Arial", 9),
            fg="gray",
            pady=10
        )
        info_text.pack()
        
    def _toggle_smoothing(self):
        """Toggle the mouse smoothing on/off."""
        if not self.is_running:
            try:
                self.smoother.start()
                self.is_running = True
                self.status_label.config(text="● Enabled", fg="green")
                self.toggle_button.config(
                    text="Disable Smoothing",
                    bg="#f44336",
                    activebackground="#da190b"
                )
            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"Failed to start mouse smoothing:\n{str(e)}\n\n"
                    "Make sure you have the required permissions."
                )
        else:
            self.smoother.stop()
            self.is_running = False
            self.status_label.config(text="● Disabled", fg="red")
            self.toggle_button.config(
                text="Enable Smoothing",
                bg="#4CAF50",
                activebackground="#45a049"
            )
            
    def _update_settings(self, _=None):
        """Update smoother settings when sliders change."""
        self.smoother.update_settings(
            smoothing_window=self.smoothing_var.get(),
            max_velocity=self.speed_var.get(),
            jitter_threshold=self.jitter_var.get(),
            tremor_strength=self.tremor_strength_var.get()
        )

    # --- tremor calibration ------------------------------------------------

    def _has_profile(self):
        return bool(self.profile and self.profile.detected)

    def _update_tremor_ui(self):
        """Sync the smoother and the calibration widgets with the current profile."""
        has_profile = self._has_profile()
        if not has_profile:
            self.use_tremor_var.set(False)
        active = has_profile and self.use_tremor_var.get()

        self.smoother.set_tremor_profile(
            self.profile if active else None,
            strength=self.tremor_strength_var.get())

        state = "normal" if has_profile else "disabled"
        self.use_tremor_check.config(state=state)
        self.tremor_strength_scale.config(state=state)
        self.calib_menu.entryconfig("Use Tremor Cancellation", state=state)
        self.calib_menu.entryconfig("View Calibration Results...", state=state)
        self.calib_menu.entryconfig("Reset Calibration", state=state)

        if not has_profile:
            self.calib_label.config(
                text="Not calibrated. Run calibration so the app can learn "
                     "your tremor and cancel it out.", fg="gray")
        else:
            self.calib_label.config(
                text=f"Calibrated: {self.profile.frequency_hz:.1f} Hz tremor, "
                     f"about {self.profile.amplitude_px:.1f} px"
                     + ("  (active)" if active else "  (off)"),
                fg="green" if active else "black")

    def _on_use_tremor_toggled(self):
        self._update_tremor_ui()

    def _run_calibration(self):
        """Pause smoothing, run the calibration dialog, then resume."""
        was_running = self.is_running
        if was_running:
            self._toggle_smoothing()
        try:
            profile = CalibrationDialog(self.root).wait()
        except Exception as e:
            messagebox.showerror(
                "Calibration Error",
                f"Could not record mouse movement:\n{e}\n\n"
                "Make sure the app has permission to monitor the mouse.")
            profile = None
        if profile:
            self.profile = profile
            try:
                profile.save()
            except OSError as e:
                messagebox.showwarning(
                    "Not Saved",
                    f"Calibration applied but could not be saved:\n{e}")
            self.use_tremor_var.set(True)
            self._update_tremor_ui()
        if was_running:
            self._toggle_smoothing()

    def _show_profile(self):
        p = self.profile
        messagebox.showinfo(
            "Calibration Results",
            f"Tremor frequency: {p.frequency_hz:.1f} Hz\n"
            f"Tremor size: about {p.amplitude_px:.1f} px\n"
            f"Signal clarity: {p.peak_ratio:.0f}x background\n"
            f"Recorded for: {p.duration_s:.0f} s")

    def _reset_calibration(self):
        if messagebox.askyesno("Reset Calibration",
                               "Delete your saved calibration?"):
            TremorProfile.delete()
            self.profile = None
            self._update_tremor_ui()

    def _show_help(self):
        messagebox.showinfo(
            "How Calibration Works",
            "Tremors are rhythmic shaking at a fairly steady speed "
            "(usually 4-12 times per second), while deliberate movement is "
            "slower and not repetitive.\n\n"
            "During calibration the app records your mouse movement and "
            "measures that rhythm. It then filters exactly that frequency "
            "out of your mouse input, so the cursor follows what you mean to "
            "do and ignores the shake.\n\n"
            "Recalibrate if your tremor changes, for example after taking "
            "medication or at a different time of day.")

    def _show_about(self):
        messagebox.showinfo(
            "About NorwinMouseAssist",
            "NorwinMouseAssist\nMouse assistance for hand tremors.\n\n"
            "Open source, MIT License.")
        
    def _on_closing(self):
        """Handle application close."""
        if self.is_running:
            self.smoother.stop()
        self.root.destroy()


def main():
    """Main entry point for the application."""
    root = tk.Tk()
    app = MouseAssistApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
