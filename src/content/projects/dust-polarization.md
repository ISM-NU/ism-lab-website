---
title: "Measuring polarized dust"
code: "POL"
summary: "The methods under everything else: how to estimate polarization fraction and angle without bias, and how the Planck satellite and the PILOT balloon measure them."
order: 4
image: "/sky/comp-galactic_centre-960.webp"
instruments: ["Planck", "PILOT"]
papers:
  - "2015A&A...576A.104P"
  - "2015A&A...576A.105P"
  - "2015A&A...576A.106P"
  - "2015A&A...574A.135M"
  - "2015A&A...574A.136M"
  - "2016A&A...595A..57A"
  - "2019A&A...630A..74M"
  - "2017ExA....43..211M"
  - "2023ExA....56..197B"
  - "2023eas..conf.1537A"
  - "2015PhDT.......311A"
findings:
  # Abstract (Mangilli et al. 2019): "we infer a magnetic field orientation projected onto the plane of the sky that is
  # remarkably ordered over the full extent of the CMZ, with an average tilt angle of ~22 deg clockwise with respect to
  # the Galactic plane." Data: 240 um, 2.2' resolution, -2 < l < 2, -4 < b < 3 deg.
  - text: "PILOT mapped polarized dust emission at 240 µm over the whole central molecular zone. The plane-of-sky field it implies is ordered across the full CMZ and tilted clockwise from the Galactic plane."
    value: "average tilt ≃ 22°"
    bibcode: "2019A&A...630A..74M"
  # Abstract (Montier et al. 2015a): "We show that for low variations of the effective ellipticity between the Q and U
  # components around the symmetrical case the covariance matrix may be simplified as is usually done, with negligible
  # impact on the bias. For S/N on intensity lower than 10 the uncertainty on the total intensity is shown to
  # drastically increase the uncertainty of the polarization fraction but not the relative bias".
  - text: "The usual simplified noise covariance is safe when the Q and U noise is close to symmetric. When the intensity itself is noisy, its uncertainty greatly widens the uncertainty on the polarization fraction without changing the relative bias."
    value: "intensity S/N < 10"
    bibcode: "2015A&A...574A.135M"
  # Abstract (Montier et al. 2015b): "we show that the traditional estimators suffer from discontinuous distributions at
  # low S/N, while the asymptotic and Bayesian methods do not. Attention is given to the shape of the output
  # distribution of the estimators, and is compared with a Gaussian. In this regard, the new asymptotic method presents
  # the best performance".
  - text: "At low signal to noise the traditional estimators of polarization fraction have discontinuous output distributions; the asymptotic and Bayesian estimators do not, and the asymptotic one comes closest to a Gaussian."
    bibcode: "2015A&A...574A.136M"
  # Abstract (Alina et al. 2016): "We characterize, for the first time, the bias on the conventional estimator of the
  # polarization angle dispersion function (S hereafter) and show that it can be positive or negative depending on the
  # true value. [...] We show that in the case where the ellipticity of the noise in (Q, U) varies by less than 10
  # percent, one can use simplified, diagonal approximation of the noise covariance matrix."
  - text: "The conventional estimator of the polarization angle dispersion function is biased up or down depending on its true value. A diagonal noise covariance is adequate only while the Q-U noise ellipticity varies by less than 10 per cent."
    bibcode: "2016A&A...595A..57A"
---

Polarization fraction and angle are noisy, non-linear quantities, and naive
estimates are biased at low signal to noise. Part of the group's work is the
statistics needed to read such maps without bias, and part is the
instruments: the Planck all-sky survey and PILOT, a balloon that measured dust
polarization towards the Galactic centre.
