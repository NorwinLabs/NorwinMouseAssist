"""
NorwinMouseAssist - GUI Application
Helps people with Parkinson's or tremors use a computer by smoothing mouse movements.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import sys
from mouse_smoother import MouseSmoother


class MouseAssistApp:
    """Main application window for mouse smoothing control."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("NorwinMouseAssist")
        self.root.geometry("400x450")
        self.root.resizable(False, False)
        
        # Initialize mouse smoother
        self.smoother = MouseSmoother()
        self.is_running = False
        
        # Set up UI
        self._create_widgets()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
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
        
        # Settings Frame
        settings_frame = tk.LabelFrame(
            self.root,
            text="Settings",
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
            jitter_threshold=self.jitter_var.get()
        )
        
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
