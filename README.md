
<p align="center">
  <img width="460" height="300" src="/webpage_content/origami_analyse_logo.png">
</p>

# **ORIGAMI** - A Software Suite for Activated Ion Mobility Mass Spectrometry Applied To Multimeric Protein Assemblies
---
**ORIGAMI** is a two component software suite for faster acquisition of actived ion mobility mass spectrometry (IM-MS) datasets and analysis of MS and IM-MS data.<p>


The acquisition software (**ORIGAMI<sup>MS</sup>**) works by interfacing MassLynx and Waters Research Enabled Software (**WREnS**) to carry out a typically tedious task of increasing the collision or cone voltage prior to ion mobility separation. The program works by executing a set of commands that modify various DC potentials in Waters Synapt G2 (and above) family of instruments. There are four acquisition modes available (linear, exponential, Boltzmann and User-defined) which determine the activation ramp parameters.

**ORIGAMI<sup>MS</sup> requirements:**
- Installed WREnS on your instrument PC (please contact Waters Corp. for access to WREnS and installation instructions)
-  Download [ORIGAMI<sup>MS</sup>](https://github.com/lukasz-migas/ORIGAMI/releases/tag/v1.0.1) and associated WREnS scripts
- Read the [User Guide](https://github.com/lukasz-migas/ORIGAMI/blob/master/ORIGAMI_MS/UserGuide_MS.pdf) for more details or watch the YouTube [video](https://youtu.be/XNfM6F_MSb0)
- Installation instructions can be found in the [User Guide](https://github.com/lukasz-migas/ORIGAMI/blob/master/ORIGAMI_MS/UserGuide_MS.pdf)

---
The analysis software (**ORIGAMI<sup>ANALYSE</sup>**) can import single or multiple IM-MS Waters files (.raw) or a list of text files (.csv, .txt) to visualise and interrogate the ion mobility data. It provides an analysis platform to extract, process, visualise and export MS and IM-MS data to convenient image or text formats. The program was designed to handle activated IM-MS datasets, hence can easily manipulate large number of files to generate CIU or SID fingerprint maps; datasets can be compared and overlayed to produce high-quality images. All of the processed data can be also exported in an interactive format, to give a webpage-like behaviour with utility tools such as zooming, panning, data hovering and much more.

Some **ORIGAMI<sup>ANALYSE</sup>** features:
-	import single or multiple Waters raw files (requires Driftscope)
-	import single or multiple text files
-	batch data extraction from raw files
-	comparison and overlay of CIU/SID/UVPD datasets
-	export all data as static image or in an interactive webpage format
-	create and apply CCS calibration to proteins and small molecules
-	tools to analyse linear DTIMS datasets

**ORIGAMI<sup>ANALYSE</sup> requirements:**
- Driftscope (should be provided with your Waters instrument) - if Driftscope is not present, you will not be able to extract MS or IM-MS data
- Read the [User Guide](https://github.com/lukasz-migas/ORIGAMI/blob/master/ORIGAMI_ANALYSE/UserGuide.pdf)
- Installation instructions can be found in the [User Guide](https://github.com/lukasz-migas/ORIGAMI/blob/master/ORIGAMI_ANALYSE/UserGuide.pdf)

---
**Authors and contributors:**
- Lukasz G. Migas (lukasz.migas@manchester.ac.uk) - Software development and data acquisition
- Aidan France (aidan.france@manchester.ac.uk) - Data acquisition
- Perdita E. Barran (perdita.barran@manchester.ac.uk) - Supervision
- Bruno Bellina (bruno.bellina@manchester.ac.uk) - Supervision
- PB Research Group - Testing 😄
- Other users - bug reports 🐛
---
**Bug reports**<p>
If you encounter any errors or problems, would like to ask request new features or just have a chat about ORIGAMI or other MS and IM-MS topics, please contact Lukasz Migas (lukasz.migas@manchester.ac.uk).

---
**Citation**<p>
If you use either of the components of ORIGAMI, please consider citing it in your work:<p>
[L. G. Migas, A. P. France, B. Bellina, P. E. Barran, "ORIGAMI: A software suite for activated ion mobility mass spectrometry (aIM-MS) applied to multimeric protein assemblies”, Int. J. Mass Spectrom., 2017](https://doi.org/10.1016/j.ijms.2017.08.014)
