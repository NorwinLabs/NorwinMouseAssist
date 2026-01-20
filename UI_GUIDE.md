# NorwinMouseAssist - Application Screenshots and UI Guide

## Main Application Window

The application provides a simple, user-friendly interface:

### Window Layout

```
┌─────────────────────────────────────┐
│      NorwinMouseAssist              │
│  Mouse Smoothing for Steady Control │
├─────────────────────────────────────┤
│                                     │
│  ┌─── Status ────────────────────┐ │
│  │      ● Disabled               │ │
│  └───────────────────────────────┘ │
│                                     │
│  ┌───────────────────────────────┐ │
│  │    Enable Smoothing          │ │
│  └───────────────────────────────┘ │
│                                     │
│  ┌─── Settings ──────────────────┐ │
│  │                               │ │
│  │ Smoothing Level:  ●────────  │ │
│  │ (Higher = smoother, more lag) │ │
│  │                               │ │
│  │ Max Speed:        ●────────  │ │
│  │ (Limits rapid movements)     │ │
│  │                               │ │
│  │ Jitter Filter:    ●────────  │ │
│  │ (Filters small tremors)      │ │
│  │                               │ │
│  └───────────────────────────────┘ │
│                                     │
│  Adjust settings to your comfort.   │
│  Changes apply immediately.         │
└─────────────────────────────────────┘
```

### When Enabled

When you click "Enable Smoothing", the interface changes:

- Status shows: **● Enabled** (in green)
- Button changes to: **Disable Smoothing** (red background)
- Mouse movements are now being smoothed in real-time

### Settings Controls

1. **Smoothing Level** (Slider: 2-10)
   - Default: 5
   - Lower = Less lag, less smoothing
   - Higher = More smoothing, slight lag
   - Best for: Adjust based on how much tremor reduction you need

2. **Max Speed** (Slider: 20-100)
   - Default: 50
   - Lower = Slower, more controlled cursor
   - Higher = Faster cursor movement allowed
   - Best for: Preventing overshooting when clicking buttons

3. **Jitter Filter** (Slider: 1-10)
   - Default: 3
   - Lower = More responsive to small movements
   - Higher = Filters out more micro-tremors
   - Best for: Reducing small unintentional movements

## How to Use

1. **Launch the Application**
   - Run `python main.py`
   - The window appears with smoothing disabled by default

2. **Enable Smoothing**
   - Click the "Enable Smoothing" button
   - Your mouse movements will now be smoothed
   - You should notice reduced jitter immediately

3. **Adjust Settings**
   - Move the sliders while smoothing is active
   - Changes apply immediately - no need to restart
   - Find the combination that feels most comfortable

4. **Tips for Finding Your Settings**
   - Start with defaults and adjust one setting at a time
   - If cursor feels slow: Decrease Smoothing Level
   - If you overshoot targets: Decrease Max Speed  
   - If small tremors persist: Increase Jitter Filter
   - If cursor feels unresponsive: Decrease Jitter Filter

5. **Disable When Not Needed**
   - Click "Disable Smoothing" to return to normal mouse behavior
   - The application stays open for easy re-enabling

## Visual Feedback

- **Red ● Disabled**: Mouse smoothing is off
- **Green ● Enabled**: Mouse smoothing is active
- **Green Button**: Click to enable
- **Red Button**: Click to disable

## Recommended Settings by Use Case

### Light Tremors
- Smoothing Level: 3-4
- Max Speed: 60-70
- Jitter Filter: 2-3

### Moderate Tremors  
- Smoothing Level: 5-6
- Max Speed: 50-60
- Jitter Filter: 3-5

### Severe Tremors
- Smoothing Level: 7-9
- Max Speed: 30-40
- Jitter Filter: 5-8

Remember: These are starting points. Everyone's needs are different, so experiment to find what works best for you!
