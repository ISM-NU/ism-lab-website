---
name: "Denis Andreyev"
role: "Student"
focus: "LMC magnetic field, velocity gradients, cold gas"
order: 8
photo: "/people/denis-andreyev.webp"
links:
  - label: "GitHub"
    href: "https://github.com/unsound-mint"
---
Rewrote our velocity gradient code, which turns H I and CO spectral cubes into magnetic-field maps, as a parallel Julia package tested on synthetic cubes from MHD simulations, and parallelised ROHSA, which splits H I spectra into Gaussian components. Uses both to map the field of the Large Magellanic Cloud and its Milky Way foreground against starlight and Planck polarization, and to find its cold atomic gas. Also builds this website.
