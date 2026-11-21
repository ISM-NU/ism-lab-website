// Directions where a student or visitor could contribute. Every entry rests on
// public facts: an open repository (checked with `gh repo list ISM-NU`,
// 2026-11-16) or a published record, and the public data it works with.
// Link only public repositories: VGT.jl is private, so its direction has none. No
// positions, funding or computing are implied. The PI confirms this list.
export interface Direction {
  title: string;
  /** What exists today. */
  exists: string;
  /** Where a contribution would go. */
  open: string;
  data: string;
  code?: { label: string; href: string };
  /** Research page the direction belongs to. */
  line: string;
}

export const directions: Direction[] = [
  {
    title: "Magnetic field from velocity gradients",
    exists: "Our velocity-gradient code turns H I and CO spectral-line cubes into plane-of-sky field orientation maps. The method gave the foreground direction in the LMC paper (Alina et al. 2023).",
    open: "Testing the method on more cubes, and checking its angles against dust and starlight polarization.",
    data: "GASS H I (Parkes), MAGMA CO (Mopra), Planck 353 GHz",
    line: "lmc",
  },
  {
    title: "Cold neutral gas in the LMC",
    exists: "ROHSA-LMC runs the ROHSA Gaussian decomposition (Marchal et al. 2019) on LMC H I cubes, with velocity-layer cubes and disk de-rotation.",
    open: "Interpreting the decomposed components, and separating the cold neutral medium from the rest of the atomic gas.",
    data: "GASS H I (Parkes)",
    code: { label: "ISM-NU/ROHSA-LMC", href: "https://github.com/ISM-NU/ROHSA-LMC" },
    line: "lmc",
  },
  {
    title: "Supergiant shells and the field",
    exists: "LMC-shells compares the rims of optical supergiant shells (DeMCELS Hα and [S II]) with the field directions from velocity gradients and from Planck, with synthetic controls.",
    open: "Extending the rim-tangency test and the controls to more shells.",
    data: "DeMCELS Hα and [S II], velocity-gradient maps, Planck 353 GHz",
    code: { label: "ISM-NU/LMC-shells", href: "https://github.com/ISM-NU/LMC-shells" },
    line: "lmc",
  },
  {
    title: "Filament angles with a neural network",
    exists: "A U-Net trained on synthetic images returns the position angle of filamentary structures without per-map tuning (Umetaliev et al. 2025). The model is open on Zenodo.",
    open: "Applying it to new Planck, Herschel and H I maps, and measuring filament orientation against the field in larger samples.",
    data: "Planck, Herschel and HI4PI maps; the synthetic training set",
    code: { label: "Zenodo 10.5281/zenodo.16647869", href: "https://doi.org/10.5281/zenodo.16647869" },
    line: "filaments",
  },
];
