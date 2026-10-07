"""Small plotting helpers shared by the notebooks."""
import matplotlib.pyplot as plt

from src import config

# One colour per signal, used in every figure so slides look consistent
COLORS = {
    "stator_winding": "#b5562a",  # copper: our target
    "coolant": "#2d6fa3",
    "ambient": "#7a8794",
    "current": "#3a7d44",
    "speed": "#6b4fa0",
    "torque": "#c28a00",
    "voltage": "#8a5a44",
    "train": "#2d6fa3",
    "test": "#b5562a",
}

# Units for every measured column, for axis labels
UNITS = {
    "u_q": "V", "u_d": "V", "i_d": "A", "i_q": "A",
    "motor_speed": "rpm", "torque": "Nm",
    "coolant": "°C", "ambient": "°C", "stator_winding": "°C",
    "stator_tooth": "°C", "stator_yoke": "°C", "pm": "°C",
}


def use_style():
    """A clean, readable style for every figure."""
    plt.rcParams.update({
        "figure.dpi": 100,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "axes.titleweight": "bold",
        "axes.titlesize": 12,
        "axes.labelsize": 10,
        "legend.frameon": False,
    })


def save_figure(fig, name):
    """Save a figure as PNG (dpi=150) in outputs/figures/ and return its path."""
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    path = config.FIGURES_DIR / name
    fig.savefig(path, dpi=150, bbox_inches="tight")
    return path
