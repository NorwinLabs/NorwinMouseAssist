"""
NorwinMouseAssist - GUI Application
Helps people with Parkinson's or tremors use a computer by smoothing mouse movements.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from mouse_smoother import MouseRecorder, MouseSmoother
from tremor import TremorProfile, analyze_tremor

CALIBRATION_SECONDS = 15

# Dark theme palette
FONT = "Segoe UI"
BG = "#14171c"
CARD = "#1d2229"
BORDER = "#2a313b"
TEXT = "#e8ecf1"
MUTED = "#8b95a3"
GREEN = "#2ecc71"
RED = "#e5484d"
ACCENT = "#4c8dff"


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
        self.root.configure(bg=BG)

        # Header
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=24, pady=(20, 6))
        tk.Label(header, text="NorwinMouseAssist", bg=BG, fg=TEXT,
                 font=(FONT, 20, "bold")).pack(anchor="w")
        tk.Label(header, text="Steadier mouse control for hand tremors",
                 bg=BG, fg=MUTED, font=(FONT, 10)).pack(anchor="w")

        # Big on/off card
        power = self._card(self.root)
        self.toggle_canvas = tk.Canvas(power, width=240, height=84, bg=CARD,
                                       highlightthickness=0, cursor="hand2")
        self.toggle_canvas.pack(pady=(4, 8))
        self.toggle_canvas.bind("<Button-1>", lambda e: self._toggle_smoothing())
        self.status_label = tk.Label(power, bg=CARD, font=(FONT, 12, "bold"))
        self.status_label.pack()
        tk.Label(power, text="Click the switch or press Ctrl+E", bg=CARD,
                 fg=MUTED, font=(FONT, 9)).pack(pady=(2, 4))
        self._render_toggle()

        # Tremor cancellation card
        tremor = self._card(self.root, "Tremor Cancellation")
        self.calib_label = tk.Label(tremor, bg=CARD, font=(FONT, 10),
                                    justify="left", wraplength=340, anchor="w")
        self.calib_label.pack(fill="x")

        row = tk.Frame(tremor, bg=CARD)
        row.pack(fill="x", pady=8)
        tk.Button(row, text="Calibrate…", command=self._run_calibration,
                  bg=ACCENT, fg="white", activebackground="#6aa0ff",
                  activeforeground="white", relief="flat", bd=0,
                  font=(FONT, 10, "bold"), padx=14, pady=5,
                  cursor="hand2").pack(side="left")
        self.use_tremor_check = tk.Checkbutton(
            row, text="Use tremor cancellation", variable=self.use_tremor_var,
            command=self._on_use_tremor_toggled, bg=CARD, fg=TEXT,
            selectcolor=BG, activebackground=CARD, activeforeground=TEXT,
            disabledforeground=MUTED, font=(FONT, 10))
        self.use_tremor_check.pack(side="right")

        self.tremor_strength_var = tk.IntVar(value=5)
        self.tremor_strength_scale = self._slider(
            tremor, "Strength", self.tremor_strength_var, 1, 10,
            "Higher removes more tremor, adds lag")

        # General smoothing card
        general = self._card(self.root, "General Smoothing")
        self.smoothing_var = tk.IntVar(value=5)
        self._slider(general, "Smoothing Level", self.smoothing_var, 2, 10,
                     "Higher is smoother, with more lag")
        self.speed_var = tk.IntVar(value=50)
        self._slider(general, "Max Speed", self.speed_var, 20, 100,
                     "Limits rapid movements")
        self.jitter_var = tk.IntVar(value=3)
        self._slider(general, "Jitter Filter", self.jitter_var, 1, 10,
                     "Filters small shakes")

        tk.Label(self.root, text="Changes apply immediately. Used when tremor "
                 "cancellation is off.", bg=BG, fg=MUTED,
                 font=(FONT, 9)).pack(pady=(4, 16))

    # --- widget helpers ----------------------------------------------------

    def _card(self, parent, title=None):
        """A rounded-looking dark panel; returns the frame to fill."""
        outer = tk.Frame(parent, bg=CARD, highlightbackground=BORDER,
                         highlightthickness=1)
        outer.pack(fill="x", padx=24, pady=8)
        inner = tk.Frame(outer, bg=CARD)
        inner.pack(fill="x", padx=18, pady=14)
        if title:
            tk.Label(inner, text=title, bg=CARD, fg=TEXT,
                     font=(FONT, 11, "bold")).pack(anchor="w", pady=(0, 6))
        return inner

    def _slider(self, parent, label, var, low, high, hint):
        frame = tk.Frame(parent, bg=CARD)
        frame.pack(fill="x", pady=(4, 2))
        top = tk.Frame(frame, bg=CARD)
        top.pack(fill="x")
        tk.Label(top, text=label, bg=CARD, fg=TEXT,
                 font=(FONT, 10)).pack(side="left")
        tk.Label(top, textvariable=var, bg=CARD, fg=ACCENT,
                 font=(FONT, 10, "bold")).pack(side="right")
        scale = tk.Scale(frame, from_=low, to=high, orient="horizontal",
                         variable=var, command=self._update_settings,
                         showvalue=False, bg=ACCENT, fg=TEXT, troughcolor=BG,
                         activebackground="#6aa0ff", highlightthickness=0,
                         bd=0, sliderrelief="flat", sliderlength=22, width=10)
        scale.pack(fill="x")
        tk.Label(frame, text=hint, bg=CARD, fg=MUTED,
                 font=(FONT, 8)).pack(anchor="w")
        return scale

    def _render_toggle(self):
        """Draw the pill switch and status text for the current state."""
        c = self.toggle_canvas
        c.delete("all")
        on = self.is_running
        w, h, pad = 240, 84, 4
        color = GREEN if on else "#3a424d"
        r = (h - 2 * pad) / 2
        c.create_oval(pad, pad, pad + 2 * r, h - pad, fill=color, outline=color)
        c.create_oval(w - pad - 2 * r, pad, w - pad, h - pad, fill=color,
                      outline=color)
        c.create_rectangle(pad + r, pad, w - pad - r, h - pad, fill=color,
                           outline=color)
        knob_x = w - pad - 2 * r if on else pad
        c.create_oval(knob_x + 6, pad + 6, knob_x + 2 * r - 6, h - pad - 6,
                      fill="white", outline="")
        c.create_text(w * (0.32 if on else 0.68), h / 2,
                      text="ON" if on else "OFF", fill="white",
                      font=(FONT, 16, "bold"))
        if on:
            self.status_label.config(text="● Smoothing is ON", fg=GREEN)
        else:
            self.status_label.config(text="● Smoothing is OFF", fg=RED)

    def _toggle_smoothing(self):
        """Toggle the mouse smoothing on/off."""
        if not self.is_running:
            try:
                self.smoother.start()
                self.is_running = True
            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"Failed to start mouse smoothing:\n{str(e)}\n\n"
                    "Make sure you have the required permissions."
                )
        else:
            self.smoother.stop()
            self.is_running = False
        self._render_toggle()

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
                     "your tremor and cancel it out.", fg=MUTED)
        else:
            self.calib_label.config(
                text=f"Calibrated: {self.profile.frequency_hz:.1f} Hz tremor, "
                     f"about {self.profile.amplitude_px:.1f} px"
                     + ("  (active)" if active else "  (off)"),
                fg=GREEN if active else TEXT)

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
