# NorwinMouseAssist

An open-source software that can help people with non-steady hands, particularly those with Parkinson's disease or tremors, to use a computer more easily.

## Features

- **Mouse Movement Smoothing**: Removes jitter and stutters from mouse movements using an advanced filtering algorithm
- **Rapid Movement Dampening**: Limits excessive speed to prevent overshooting targets
- **Jitter Filtering**: Filters out small tremors that don't represent intentional movements
- **Easy-to-Use GUI**: Simple interface with on/off toggle and adjustable settings
- **Real-Time Adjustment**: All settings can be changed while the application is running

## Installation

### Requirements
- Python 3.7 or higher
- pip (Python package installer)

### Setup

1. Clone this repository:
```bash
git clone https://github.com/NorwinLabs/NorwinMouseAssist.git
cd NorwinMouseAssist
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the application:
```bash
python main.py
```

### Controls

- **Enable/Disable Button**: Click to toggle mouse smoothing on or off
- **Smoothing Level** (2-10): Controls how much smoothing is applied
  - Lower values: Less lag, but less smoothing
  - Higher values: More smoothing, but slightly more lag
- **Max Speed** (20-100): Limits how fast the cursor can move
  - Lower values: Slower, more controlled movements
  - Higher values: Faster movements allowed
- **Jitter Filter** (1-10): Filters out small unintentional movements
  - Lower values: More responsive to small movements
  - Higher values: Filters out more tremors

### Tips

1. Start with the default settings and adjust based on your needs
2. If the cursor feels too sluggish, reduce the Smoothing Level
3. If you're overshooting targets, reduce the Max Speed
4. If small tremors are still causing issues, increase the Jitter Filter

## How It Works

NorwinMouseAssist uses a multi-layered approach to smooth mouse movements:

1. **Moving Average Filter**: Averages recent mouse positions to smooth out jittery movements
2. **Velocity Limiting**: Prevents rapid movements that might be unintentional
3. **Jitter Threshold**: Ignores movements below a certain size to filter micro-tremors

The application runs in the background and processes mouse movements in real-time, providing a smoother cursor experience.

## Platform Support

- **Windows**: Fully supported
- **macOS**: Supported (may require accessibility permissions)
- **Linux**: Supported (may require X11)

## Permissions

On some operating systems, you may need to grant the application permission to control the mouse:
- **macOS**: System Preferences → Security & Privacy → Privacy → Accessibility
- **Linux**: Ensure you have X11 input access

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you find this software helpful, please consider:
- ⭐ Starring this repository
- 🐛 Reporting bugs or issues
- 💡 Suggesting new features
- 🤝 Contributing code improvements
