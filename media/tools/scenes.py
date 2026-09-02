"""Scenario builders - all body creation goes through GravSim's own spin() tool."""
import math
import studio


def _fresh(width, height, seed, G, theta, max_radius):
    main = studio.load_sim(width, height, seed=seed)
    main.G = G
    main.BARNES_HUT_THETA = theta
    main.max_random_radius = max_radius
    return main


def galaxy(main, cx, cy, radius, n, spin_speed, layers=(1.0, 0.55, 0.3, 0.15)):
    """Filled rotating disk built from nested spin() annuli (GravSim's 'S' tool)."""
    weights = [l * l for l in layers]
    tot = sum(weights)
    for l, wgt in zip(layers, weights):
        k = max(1, int(round(n * wgt / tot)))
        main.spin(k, cx, cy, galaxy_radius=radius * l, spin_speed=spin_speed)


def build(width, height, seed, G, theta, max_radius, plan):
    """Two-pass build: measure each galaxy's own mass, then spin it at its own
    equilibrium speed so the disk is self-bound instead of flying apart."""
    speeds = []
    for spec in plan:
        probe = _fresh(width, height, seed, G, theta, max_radius)
        galaxy(probe, spec["cx"], spec["cy"], spec["r"], spec["n"], 0.0)
        m = sum(b.mass for b in probe.inbound if b.mass)
        v_edge = math.sqrt(G * m / spec["r"]) if m > 0 else 0.0
        speeds.append(v_edge / spec["r"] * spec.get("spin", 1.0) * spec.get("sign", 1))

    main = _fresh(width, height, seed, G, theta, max_radius)
    for spec, s in zip(plan, speeds):
        galaxy(main, spec["cx"], spec["cy"], spec["r"], spec["n"], s)
    return main, speeds


def zero_momentum(main):
    """Remove net drift so the cluster stays framed (an initial-condition tweak,
    equivalent to placing the galaxy with no bulk velocity)."""
    bodies = [b for b in main.inbound if b.mass]
    M = sum(b.mass for b in bodies)
    if not M:
        return
    vx = sum(b.vx * b.mass for b in bodies) / M
    vy = sum(b.vy * b.mass for b in bodies) / M
    for b in bodies:
        b.vx -= vx
        b.vy -= vy
