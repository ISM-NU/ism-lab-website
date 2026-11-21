---
name: "Denis Andreyev"
role: "Undergraduate student"
focus: "LMC magnetic field, Milky Way foreground, cold gas"
order: 8
photo: "/people/denis-andreyev.webp"
links:
  - label: "GitHub"
    href: "https://github.com/unsound-mint"
lines: [lmc]
short: "Rewrote our velocity gradient code as a parallel Julia package and parallelised ROHSA. Uses both to separate the Milky Way foreground from the Large Magellanic Cloud and to study the LMC's magnetic field and cold atomic gas. Also builds this website."
work:
  - title: "VGT.jl"
    note: "The velocity gradient technique in Julia: a parallel rewrite with validated estimators, noise models and sky-frame angles, tested on synthetic cubes from MHD simulations. Private until publication."
  - title: "ROHSA-LMC"
    note: "ROHSA Gaussian decomposition of LMC H I cubes, with OpenMP speed-ups, velocity-layer cubes and disk de-rotation."
    href: "https://github.com/ISM-NU/ROHSA-LMC"
  - title: "LMC-shells"
    note: "Whether VGT and Planck field directions run along the rims of the LMC's supergiant shells, with field-free synthetic shells as the control."
    href: "https://github.com/ISM-NU/LMC-shells"
  - title: "Pull requests to ROHSA"
    note: "OpenMP parallelisation, a faster cost function and convolution, binary input, and an integer-overflow fix for large cubes, offered to the upstream ROHSA code."
    href: "https://github.com/antoinemarchal/ROHSA/pulls?q=author%3Aunsound-mint"
  - title: "Pull requests to CARTA"
    note: "FITS header fixes in the backend of CARTA, the image viewer for ALMA, the VLA and SKA pathfinders."
    href: "https://github.com/CARTAvis/carta-backend/pulls?q=author%3Aunsound-mint"
  - title: "Pull requests to FITSIO.jl"
    note: "Header-writing fixes in the Julia FITS library."
    href: "https://github.com/JuliaAstro/FITSIO.jl/pulls?q=author%3Aunsound-mint"
  - title: "Vesqira"
    note: "An open-source workspace for research data: register FITS cubes and VGT maps, browse them with sky coordinates, and build figures linked to their sources. Pre-release."
    href: "https://github.com/unsound-mint/vesqira"
  - title: "This website"
    note: "Static Astro site built on real sky data."
    href: "https://github.com/ISM-NU/ism-lab-website"
---
Rewrote our velocity gradient code, which turns H I and CO spectral cubes into magnetic-field maps, as a parallel Julia package tested on synthetic cubes from MHD simulations, and parallelised ROHSA, which splits H I spectra into Gaussian components. Uses both to separate the Milky Way foreground from the Large Magellanic Cloud, checking each against starlight and Planck polarization, and to study the LMC's magnetic field and cold atomic gas. Also builds this website.
