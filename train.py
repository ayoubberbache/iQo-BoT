"""Train EdgeChemNet (CPU, RAM-capped). Usage: python train.py [--epochs 20]"""
import argparse, gc, time
import numpy as np
import torch
import torch.nn.functional as F
from config import encode, SAFETY
from data_gen import generate
from model import EdgeChemNet, n_params

RAM_CAP = 80.0


def ram_pct():
    """RAM use as % of the container's cgroup limit if set (Docker --memory), else of host RAM."""
    for cur, lim in (("/sys/fs/cgroup/memory.current", "/sys/fs/cgroup/memory.max"),                 # cgroup v2
                     ("/sys/fs/cgroup/memory/memory.usage_in_bytes", "/sys/fs/cgroup/memory/memory.limit_in_bytes")):
        try:
            limit = open(lim).read().strip()
            if limit != "max" and int(limit) < 1 << 50:
                return 100.0 * int(open(cur).read()) / int(limit)
        except (OSError, ValueError):
            pass
    try:
        import psutil
        return psutil.virtual_memory().percent
    except ImportError:
        m = dict(l.split(":") for l in open("/proc/meminfo"))
        g = lambda k: float(m[k].split()[0])
        return 100.0 * (1 - g("MemAvailable") / g("MemTotal"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--batch", type=int, default=128)
    ap.add_argument("--per-topic", type=int, default=700)
    ap.add_argument("--lr", type=float, default=3e-3)
    a = ap.parse_args()
    torch.manual_seed(0)
    torch.set_num_threads(2)

    X, ys, ya, yi, yt = generate(a.per_topic, seed=1)
    ids = torch.from_numpy(np.concatenate([encode(t) for t in X]))
    Y = [torch.tensor(v) for v in (ys, ya, yi, yt)]
    n = len(ids); cut = int(n * 0.9)
    tr = slice(0, cut); va = slice(cut, n)

    net = EdgeChemNet()
    print(f"parameters: {n_params(net):,}  (~{n_params(net)*4/1e6:.2f} MB fp32)")
    opt = torch.optim.AdamW(net.parameters(), lr=a.lr, weight_decay=0.01)
    steps = a.epochs * ((cut + a.batch - 1) // a.batch)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, a.lr, total_steps=steps)
    w_safe = torch.tensor([1.0, 1.0, 1.5, 3.0])           # penalise missed CRITICAL

    step = 0
    for ep in range(a.epochs):
        net.train(); perm = torch.randperm(cut); t0 = time.time(); tot = 0.0
        for i in range(0, cut, a.batch):
            b = perm[i:i + a.batch]
            s, ar, it, _, tp = net(ids[b])
            loss = (F.cross_entropy(s, Y[0][b], weight=w_safe) + F.cross_entropy(ar, Y[1][b])
                    + F.cross_entropy(it, Y[2][b]) + F.cross_entropy(tp, Y[3][b]))
            opt.zero_grad(set_to_none=True); loss.backward()
            torch.nn.utils.clip_grad_norm_(net.parameters(), 1.0)
            opt.step(); sched.step(); tot += loss.item() * len(b); step += 1
            if step % 20 == 0 and ram_pct() > RAM_CAP:    # RAM guard (< 80 %)
                gc.collect()
                if ram_pct() > RAM_CAP:
                    torch.save(net.state_dict(), "edge_chem_net_partial.pt")
                    raise SystemExit(f"RAM {ram_pct():.0f}% > {RAM_CAP}%: stopped, checkpoint saved")
        net.eval()
        with torch.no_grad():
            out = net(ids[va])
        acc = [(o.argmax(-1) == y[va]).float().mean().item() for o, y in zip((out[0], out[1], out[2], out[4]), Y)]
        crit = (Y[0][va] == 3)
        rec = (out[0].argmax(-1)[crit] == 3).float().mean().item() if crit.any() else float("nan")
        print(f"ep {ep+1:02d} loss {tot/cut:.3f} | val acc safety {acc[0]:.3f} arm {acc[1]:.3f} "
              f"intent {acc[2]:.3f} topic {acc[3]:.3f} | CRITICAL recall {rec:.3f} | "
              f"{time.time()-t0:.0f}s RAM {ram_pct():.0f}%")
    torch.save(net.state_dict(), "edge_chem_net_weights.pt")
    print("saved edge_chem_net_weights.pt")


if __name__ == "__main__":
    main()
