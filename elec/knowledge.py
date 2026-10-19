"""Offline circuit helpers (exact arithmetic the bot can call instead of trusting the LLM with maths)."""
import math

E12 = [10, 12, 15, 18, 22, 27, 33, 39, 47, 56, 68, 82]


def ohm(v=None, i=None, r=None):
    """Give any two of v (V), i (A), r (ohm); returns the dict with all three plus power (W)."""
    if v is None: v = i * r
    elif i is None: i = v / r
    elif r is None: r = v / i
    return dict(v=v, i=i, r=r, p=v * i)


def nearest_e12(x, up=True):
    """Standard E12 value at or above (up=True) / below x ohms."""
    dec = 10 ** math.floor(math.log10(x))
    cands = sorted(e * dec * m for e in E12 for m in (0.1, 1, 10))
    return min((c for c in cands if c >= x), default=cands[-1]) if up else max(c for c in cands if c <= x)


def led_resistor(vs, vf, i_ma):
    """Series resistor for an LED. Returns (exact_ohm, next_standard_e12_ohm, resistor_power_w)."""
    i = i_ma / 1000.0
    r = (vs - vf) / i
    std = nearest_e12(r, up=True)
    return r, std, i * i * std


def divider(vin, r1, r2):
    return vin * r2 / (r1 + r2)


def rc_tau(r_ohm, c_farad):
    tau = r_ohm * c_farad
    return dict(tau_s=tau, t_63pct_s=tau, t_99pct_s=5 * tau, fc_hz=1 / (2 * math.pi * tau))


if __name__ == "__main__":
    print(led_resistor(5, 2, 10))
