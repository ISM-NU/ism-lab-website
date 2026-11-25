---
title: "Interstellar filaments and magnetic fields"
code: "FIL"
summary: "We study the relative orientation between magnetic fields and interstellar filaments, and the properties of the turbulence in filaments. We train neural networks for effective identification of filamentary structures and their position angles."
order: 2
image: "/sky/region-orion.webp"
field: orion
instruments: ["Planck", "Herschel", "Neural networks"]
keyPapers: ["2019MNRAS.485.2825A", "2025AJ....170..207U", "2026Galax..14...53A", "2026A&A...711A..97O"]
papers:
  - "2019MNRAS.485.2825A"
  - "2020IAUGA..30..104A"
  - "2026A&A...711A..97O"
  - "2026Galax..14...53A"
  - "2025AJ....170..207U"
  - "2025zndo..16647869U"
  - "2024IAUGA..32P.104A"
  - "2022arXiv220500683A"
  - "2021A&A...647A.121M"
findings:
  # Abstract: "We recover the previously observed trend for filaments in low column density environments to be aligned
  # parallel to the background magnetic field; however, we find that this trend is significant only for low contrast
  # filaments, whereas high contrast filaments tend to be randomly orientated with respect to the background magnetic
  # field. Filaments in high column density environments do not globally show any preferential orientation, although
  # low contrast filaments alone tend to have perpendicular relative orientation with respect to the background
  # magnetic field."
  - text: "In low column density surroundings only low-contrast filaments run parallel to the background field; high-contrast ones are randomly oriented. In high column density surroundings there is no global preference, although low-contrast filaments alone tend to be perpendicular."
    bibcode: "2019MNRAS.485.2825A"
  # Abstract: "For a subsample of nearby filaments, for which volume densities can be derived, we find a clear
  # transition in the relative orientation with increasing density, at n_H ~ 10^3 cm^-3, changing from mostly
  # parallel to mostly perpendicular in the off-clump portions of filaments and from even to bimodal in the clumps."
  - text: "In nearby filaments, where volume density can be derived, the parts away from clumps change from mostly parallel to mostly perpendicular to the field as density rises; inside the clumps the distribution changes from even to bimodal."
    value: "transition at n_H ≈ 10^3 cm^-3"
    bibcode: "2019MNRAS.485.2825A"
  # Abstract (Oers et al. 2026): "We find that low-N_H2 filaments tend to be roughly parallel to B_PoS at all scales,
  # while narrow high-N_H2 filaments do not have any preferred orientations and wide high-N_H2 filaments tend to be
  # roughly perpendicular. This change in preferred orientations occurs at a transition column density typically in
  # the range [0.8, 8] x 10^21 cm^-2".
  - text: "Across the 116 Herschel Galactic Cold Cores fields, filaments of low column density lie roughly parallel to the Planck field at all scales. At high column density, narrow filaments show no preferred orientation and wide ones tend to be perpendicular."
    value: "transition N(H_2) ≈ 0.8–8 × 10^21 cm^-2"
    bibcode: "2026A&A...711A..97O"
  # Abstract (MaLeFiSenta): "we trained different neural network models and discovered that a combination of the
  # Mask R-CNN and U-Net architecture is most appropriate for filament identification and determination of their
  # orientation angles. We showed that neural network training might be performed efficiently on a relatively small
  # training sample of only around 100 maps."
  - text: "For finding filaments and their orientation angles in Planck, Herschel and HI4PI maps, a combination of Mask R-CNN and U-Net worked best, and it trains on about 100 maps."
    bibcode: "2022arXiv220500683A"
---

For filaments hosting Planck cold clumps, the orientation relative to the field
depends on density. Low-contrast filaments in diffuse surroundings tend to run
parallel to the field. In nearby filaments, where volume density can be
estimated, the off-clump parts change from mostly parallel to mostly
perpendicular at about 10^3 cm^-3 (Alina et al. 2019). Measuring that angle in
large samples needs automatic detection, so we build neural networks,
trained on Planck, Herschel and HI4PI maps or on synthetic images, that find
filaments and return their position angle.
