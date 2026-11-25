---
title: "Machine learning techniques"
code: "ML"
summary: "Neural networks that find interstellar filaments in dust maps and measure their position angles, and that estimate the virial parameter of molecular clouds."
order: 7
image: "/sky/ml-card-960.webp"
imageCaption: "G202.3+2.5 · Herschel 250 µm, U-Net filament pixels in red"
field: filament_net
instruments: ["Herschel", "Planck", "Neural networks"]
keyPapers: ["2025AJ....170..207U"]
papers:
  - "2025AJ....170..207U"
  - "2025zndo..16647869U"
  - "2024IAUGA..32P.104A"
  - "2022arXiv220500683A"
upcoming:
  - title: "Virial parameter from a neural network"
    note: "A network trained to predict the virial parameter of molecular clouds, which says whether a cloud's internal motions can hold it up against its own gravity."
---

Large surveys hold more filaments than anyone can trace by hand. We
train neural networks, among them a U-Net, on Planck, Herschel and HI4PI maps
and on synthetic images to find filaments and return their position angles,
the input for comparing filaments with the magnetic field.
