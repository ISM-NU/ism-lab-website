"""Checks for the helpers every render script shares (render_lmc.py).

They need no survey data and no network: python3 scripts/test_render_lmc.py.
The site build does not need the pipeline's Python packages, so without them
this says so loudly and exits 0. Set REQUIRE_PY_TESTS=1 to make that a failure.
"""

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("LMC_DATA", tempfile.gettempdir())  # paths are only read when a script runs
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    import numpy as np
    import render_lmc as rl
    import composites as comp
    from astropy.io import fits
except ModuleNotFoundError as e:
    required = os.environ.get("REQUIRE_PY_TESTS") == "1"
    print(
        f"{'FAILED' if required else 'SKIPPED'}: python module '{e.name}' is not installed, "
        "so test_render_lmc.py did NOT run" + ("" if required else " (REQUIRE_PY_TESTS=1 makes this an error)"),
        file=sys.stderr,
    )
    sys.exit(1 if required else 0)


def test_tan_grid_is_north_up_east_left():
    n, pix = 101, 0.02
    w = rl.tan_wcs("icrs", (81.0, -68.0), n, pix)
    ra, dec = w.wcs_pix2world([[(n - 1) / 2, (n - 1) / 2]], 0)[0]
    assert abs(ra - 81.0) < 1e-9 and abs(dec + 68.0) < 1e-9
    up = w.wcs_pix2world([[(n - 1) / 2, (n - 1) / 2 + 10]], 0)[0]
    assert up[1] > dec and abs(up[1] - dec - 10 * pix) < 1e-4
    left = w.wcs_pix2world([[(n - 1) / 2 - 10, (n - 1) / 2]], 0)[0]
    assert left[0] > ra


def test_tan_header_reproduces_the_site_grid():
    g = rl.GRID
    h = rl.tan_header("icrs", (g["CRVAL1"], g["CRVAL2"]), g["NAXIS1"], g["CDELT2"], crpix=g["CRPIX1"])
    for k, v in g.items():
        assert h[k] == v, k


def test_tan_header_leaves_the_system_unset_on_request():
    assert "RADESYS" not in rl.tan_header("icrs", (81.0, -68.0), 10, 0.1, radesys=None)


def test_tan_header_frames():
    gal = rl.tan_header("galactic", (202.5, 2.0), 900, 8.0 / 900)
    assert (gal["CTYPE1"], gal["CTYPE2"]) == ("GLON-TAN", "GLAT-TAN") and "RADESYS" not in gal
    assert gal["CRPIX1"] == 450.5 and gal["CDELT1"] == -gal["CDELT2"]
    try:
        rl.tan_header("fk4", (0, 0), 10, 1)
    except ValueError:
        return
    raise AssertionError("unknown frame accepted")


def test_cosmo_to_iau_recovers_the_field_angle():
    psi = np.radians(np.array([10.0, 30.0, 75.0, 120.0]))  # IAU polarization angles
    q, u_iau = np.cos(2 * psi), np.sin(2 * psi)
    u_cosmo = -u_iau  # what the Planck maps store
    back = 0.5 * np.arctan2(rl.cosmo_to_iau(u_cosmo), q)
    assert np.allclose(np.mod(back, np.pi), psi)
    assert not np.allclose(np.mod(0.5 * np.arctan2(u_cosmo, q), np.pi), psi)


def test_cosmo_to_iau_flips_the_qu_covariance_only():
    rng = np.random.default_rng(0)
    q = rng.normal(size=200000)
    u = 0.6 * q + 0.8 * rng.normal(size=q.size)
    cqu_iau = np.cov(q, rl.cosmo_to_iau(u))[0, 1]
    assert abs(cqu_iau + np.cov(q, u)[0, 1]) < 1e-12
    assert abs(np.var(rl.cosmo_to_iau(u)) - np.var(u)) < 1e-12


def test_grid_angle_convention():
    n = 201
    w = rl.tan_wcs("icrs", (81.0, -68.5), n, 0.06)
    pa = np.zeros((n, n))
    tilt = rl.grid_angle(w, (n, n), pa)
    c = n // 2
    assert abs(tilt[c, c]) < 1e-3
    assert np.allclose(tilt, -tilt[:, ::-1], atol=1e-3)  # mirror about the vertical axis
    assert 15 < np.degrees(np.abs(tilt).max()) < 25  # "up to ~20 deg" at the corners of the 12 deg LMC grid
    east = rl.grid_angle(w, (n, n), np.full((n, n), np.pi / 2))
    assert abs(east[c, c] - np.pi / 2) < 1e-3  # east is image-left, 90 deg from +y towards -x


def test_atomic_keeps_the_old_file_when_the_write_fails():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "out.json"
        with rl.atomic(f) as tmp:
            tmp.write_text("old")
        try:
            with rl.atomic(f) as tmp:
                tmp.write_text("par")
                raise RuntimeError
        except RuntimeError:
            pass
        assert f.read_text() == "old"
        assert [p.name for p in Path(d).iterdir()] == ["out.json"]
        with rl.atomic(f) as tmp:
            assert tmp.suffix == ".json"
            tmp.write_text("new")
        assert f.read_text() == "new"


def test_input_key_follows_the_inputs():
    a = rl.input_key("spire", 7, [10.0, -20.0], 5.5)
    assert a == rl.input_key("spire", 7, [10.0, -20.0], 5.5)
    assert a != rl.input_key("spire", 7, [10.0, -20.0], 6.5)


def test_hips_cache_is_refetched_when_its_inputs_change():
    calls = []
    real = comp.sample_hips
    comp.sample_hips = lambda url, order, wcs, n: calls.append(n) or np.ones((n, n))
    try:
        with tempfile.TemporaryDirectory() as d:
            comp.CACHE = Path(d)
            r = dict(comp.REGIONS["galactic_centre"], n=16)
            comp.fetch("t", "spire250", r, comp.target_wcs(r))
            comp.fetch("t", "spire250", r, comp.target_wcs(r))
            assert len(calls) == 1  # second call came from the cache
            wide = dict(r, fov=2 * r["fov"])
            comp.fetch("t", "spire250", wide, comp.target_wcs(wide))
            assert len(calls) == 2  # same name and survey, other field: not the stale grid
            fits.writeto(Path(d) / "t_spire250.fits", np.ones((16, 16), np.float32), overwrite=True)
            comp.fetch("t", "spire250", wide, comp.target_wcs(wide))
            assert len(calls) == 3  # a file with no key is not trusted
    finally:
        comp.sample_hips = real


def test_env_path_exits_with_the_variable_name_when_unset():
    os.environ.pop("ISM_TEST_UNSET", None)
    try:
        rl.env_path("ISM_TEST_UNSET", "somewhere")
    except SystemExit as e:
        assert "ISM_TEST_UNSET" in str(e)
        return
    raise AssertionError("unset variable accepted")


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"{len(tests)} passed")
