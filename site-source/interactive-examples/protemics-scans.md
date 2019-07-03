# Interactive MS/MS spectra

## Some background

Somewhat inspired by [xiSPEC](https://spectrumviewer.org/) to bring proteomics data to the webbrowser, I've slowly been adding functionality to load and annotate MS/MS data. ORIGAMI can currently read .mgf and .mzml files as well as .mzid files. The mzIdentML files can be used as source of annotations (results) of the .mgf files (NOT .mzml...).

When you load load a .mgf file, it will typically include 100s to 1000s of scans, each of which will contain 10s to 100s of peaks. The .mgf file does not store any annotation information (apart from precursor m/z, charge and a couple of other software specific annotations) so it must be supplemented with a .mzid file.

In the example that I've used, the .mgf file contains ~4000 scans and when the .mzid file is loaded, each is annotated with appropriate peptide information and associated post-translational modification information.

I have randomly selected a couple of scans and annotated them using the built-in fragment predictor (based on user-defined parameters) and as you can see below, when you select a scan, each 'dataset' includes data about the precursor (charge, peptide sequence, start/end position) and protein (including accession ID and protein sequence). In the current implementation, PTM information is not displayed below the plot, however is considered when generating fragments.

Actions:

* Dropdown menu: Select dataset  you are interested in
* Drag: Zoom-in on any plot area
* Hover: Discover information about peak including m/z, intensity, charge, fragment label, error, peptide sequence, modification

[See figure in another tab](html-files/proteomics-scans.html)

## Interactive figure

<iframe
    width="800"
    frameborder="0"
    height="1100"
    src="html-files/proteomics-scans.html"
    style="background: #FFFFFF;">
</iframe>
