---
title: "The Large Magellanic Cloud"
code: "LMC"
summary: "Mapping the magnetic field of the Large Magellanic Cloud from polarized dust and the motion of its atomic hydrogen, with careful foreground subtraction."
order: 1
image: "/sky/comp-lmc-field-960.webp"
instruments: ["Planck", "ASKAP", "Parkes"]
keyPapers: ["2023MNRAS.518.4466A"]
papers:
  - "2023MNRAS.518.4466A"
  - "2026IAUS..392..179A"
  - "2024IAUGA..32P.103A"
  - "2023MNRAS.524.2994H"
upcoming:
  - title: "Field from GASKAP-HI velocity gradients"
    note: "The same velocity-gradient method applied to GASKAP-HI 21 cm data, at 30 arcsecond resolution instead of the 16 arcminutes of GASS."
  - title: "Separating the cold neutral medium"
    note: "Gaussian decomposition of every H I spectrum (ROHSA) separates the cold neutral medium from the rest of the atomic gas."
findings:
  # Abstract: "After foreground removal, the geometry of the plane-of-the-sky magnetic field in the LMC tends to
  # follow the structure of the atomic gas in the LMC. This is notably the case along the molecular ridges
  # extending south and south-east of the 30 Doradus star-forming complex, and along more diffuse southern arm
  # extending towards the Small Magellanic Cloud."
  - text: "With the Milky Way foreground removed, the plane-of-sky field of the LMC tends to follow its atomic gas, notably along the molecular ridges south and south-east of 30 Doradus and along the southern arm that extends towards the Small Magellanic Cloud."
    bibcode: "2023MNRAS.518.4466A"
  # Abstract: "The median polarization fraction in the LMC is slightly lower than that observed for the MW [...]
  # Overall, polarization fraction distribution is similar to that observed in the MW." Sec. 4: "The median value
  # is pmed = 3.6 per cent while the original median polarization is 4 per cent." Table 1, MW column: median 5.3
  # (Planck Collaboration Int. XIX 2015).
  - text: "The median polarization fraction of the LMC after foreground removal is slightly lower than in the diffuse Milky Way, and the distribution as a whole is similar."
    value: "median p = 3.6% (4.0% before removal; 5.3% for the Milky Way, Planck Int. XIX)"
    bibcode: "2023MNRAS.518.4466A"
  # Sec. 4: "We take the 99th upper percentile as the conservative estimate of the lower limit of the maximum
  # polarization fraction [...] This value is p_max = 21.6%. [...] This value is close to the corresponding values
  # derived for the Milky Way of 19.8% (Planck Int. XIX) and the value of 22% (Planck 2018 XII)".
  - text: "The highest polarization fractions in the LMC, a conservative lower limit on the maximum, are close to those measured for the Milky Way."
    value: "p_max = 21.6% (99th percentile; Milky Way 19.8% and 22%)"
    bibcode: "2023MNRAS.518.4466A"
  # Abstract (Hu, Lazarian, Alina et al. 2023): "Our analysis shows that the thin channels are dominated by velocity
  # contribution, and velocity caustics mainly generate the HI striations. [...] Conversely, the alignment with the
  # magnetic field is the most prominent in thin channels."
  - text: "In simulated multiphase H I and in GALFA-HI data, thin velocity channels are dominated by the velocity contribution: the striations aligned with the field are mainly velocity caustics, and the alignment is strongest in the thinnest channels."
    bibcode: "2023MNRAS.524.2994H"
---

The LMC is 162 000 light years away and inclined by only 25 to 35 degrees, so
its whole disk fits in one map. Planck measured the polarized emission of its
dust at 353 GHz. Rotated by 90 degrees, the polarization angle gives the
plane-of-sky orientation of the magnetic field, but the map also contains the
polarized dust of the Milky Way in front of the LMC.

Alina et al. (2023) removed that foreground. Its polarization direction came
from velocity gradients in GASS H I and was checked against starlight
polarization; its intensity came from the dust-to-gas correlation around the
galaxy. After the subtraction the field follows the atomic gas, notably along
the molecular ridges south and south-east of 30 Doradus and along the southern
arm that extends towards the Small Magellanic Cloud. The maps on this site show
Planck before that correction.

The foreground direction comes from the velocity gradient technique. It
assumes that turbulent motions stretch the structures seen in thin velocity
channels of 21 cm data along the magnetic field, so the gradients run
perpendicular to it. In the published LMC work it gave the direction of the
Milky Way foreground, not the field of the LMC itself. The premise is debated:
some studies read the striations in channel maps as cold density filaments. Hu,
Lazarian, Alina et al. (2023) argued from simulated multiphase H I and GALFA-HI
data that thin channels are dominated by velocity fluctuations, so the
striations trace the turbulent velocity field and align with the field best in
the thinnest channels.

The same 21 cm spectra also separate the cold neutral medium from the rest of
the atomic gas. Molecular clouds form out of the cold phase.
