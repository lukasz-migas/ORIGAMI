# Changelog

### v1.2.1 (n.a)
#### Documentation:
![](img/added.png) Added online [documentation](https://lukasz-migas.github.io/ORIGAMI/)

![](img/added.png) Added several new videos to the [YouTube playlist](https://www.youtube.com/playlist?list=PLrPB7zfH4WXMYa5CN9qDtl-G-Ax_L6AK8)

#### Document Tree:
![](img/fixed.png) Fixed typo: spectrun -> spectrum (grr)

![](img/fixed.png) When loading mzml/mgf files, the individual scans will no longer be shown in the document tree as it caused some major issues. If you would like to see the individual spectra, please double-click on the header 
'Tandem Mass Spectra'

![](img/improved.png) When loading any data into the INTERACTIVE document, you will be asked whether data should be duplicated, merged or duplicated

![](img/changed.png) When plotting a waterfall plot, data will be checked to ensure its not too big (e.g. too many rows). You will be asked if you would like to continue


#### Annotations:
![](img/fixed.png) font size, weight and rotation will now be aplied when adding labels

![](img/fixed.png) auto-label generator will now also create labels based purely on the charge state

![](img/fixed.png) annotation parameters (e.g. size, weight, rotation) will be respected when replotting from the Document Tree

#### Interactive panel:
![](img/added.png) Made big progres in terms of copying/applying styles for plot elements. When you double-click on any element in the file list a new window will appear where you can individually adjust plot parameters. When you finished, you can right-click on that same (or any other) item in the list and select 'Copy style..'. You can then select any other item in the list, right-click on it and select  'Apply style..'.  

![](img/fixed.png) fixed sorting in the list (especilaly when using the 'Show selected' option) Lists are sorted using 'natural sorting' from now on, meaning they should be more logically sorted. 

![](img/fixed.png) fixed the show/hide table elements when you right-click on the table headers

![](img/improved.png) Colorbars:
* added loads of new settings users can control
* better behaviour when adding colorbars to plots

![](img/changed.png) removed tools/toolset from ORIGAMI - the new system of copy/apply style should work much better

#### UVPD processing panel (widget)
![](img/added.png) new widget was added that allows processing of a *very specific* type of experiment. It can be activated by going to Menu -> Plugins -> UVPD processing...


### v1.2.0.3 (3/11/2018)
#### General:

![](img/improved.png) The underlying codebase of ORIGAMI has been improved to make it more readable and more responsive

![](img/improved.png) Item font color will be automatically adjusted to ensure best contrast from the background color in various lists in the GUI

![](img/changed.png) Modification of the table elements is now available by Right-clicking on the column name

![](img/changed.png) Logging of events was temporarily disabled as it appears to be causing some issues. I haven't been able to figure out why it crashes the program (yet).

#### Tandem MS :star:

![](img/added.png) Added support to load .mgf and .mzIdentML file formats to visualise tandem mass spectrometry results. Menu -> Open open-source files... to load .mgf files. You can then annotate the tandem MS with peptide fragments. See Figure 1 for example.

#### Interactive panel:

![](img/added.png) Started adding support for individual modification of parameters for interactive plots (double-clicking on an item in the list)

![](img/added.png) Interactive documents can now be visualised without access to internet. Just check the "Add offline support" checkbox

![](img/added.png) Annotated mass spectra will now include label + arrow (if available)

![](img/improved.png) Legends now work with markers and shaded areas

![](img/fixed.png) Issue that prevent exporting interactive documents with legends has been removed

![](img/fixed.png) Issue that prevent proper showing of toolbar has been removed

#### Peaklist panel:

![](img/added.png) Added 'Extract automatically' check tool (Peaklist -> Toolbar -> Extract...)

![](img/added.png) Added 'Overlay automatically' check tool (Peaklist -> Toolbar -> Overlay...)

![](img/improved.png) Added a lot of new shortcuts for easier plotting

#### Text file panel:

![](img/added.png) Added 'Extract automatically' check tool (Peaklist -> Toolbar -> Extract...)

![](img/added.png) Added 'Show chromatogram' and 'Show mobiligram' for each viewed file (Right-click -> Select appropriate)

![](img/improved.png) Added a lot of new shortcuts for easier plotting

![](img/fixed.png) Removed an issue that prevented loading certain text files

![](img/fixed.png) Removed an issue that would incorrectly remove documents from the text file list

#### Multiple MS files panel:

![](img/added.png) The average mass spectrum can be re-binned/re-processed based on new parameters (Process -> Average mass spectra (current document))

![](img/improved.png) Item font color will be automatically adjusted to ensure best contrast from the background color

![](img/improved.png) Average mass spectrum will be automatically re-binned/re-processed when an item is added or deleted

![](img/fixed.png) Removed an issue that prevented typing-in numerical values in the 'variable' colument when using laptop keyboards. I have only ever encountered this issue once... Let me know if it still occurs!

#### Document tree:

![](img/added.png) Double-clicking on the document header will now clear all plots and show the most basic plots for that document (e.g. MS, DT, RT, etc). You can also do this by Right-click -> Refresh document.

![](img/added.png) You can now change the x-/y-axis labels for chromatograms and mobiligrams. Right-click on the item and slect 'Change x/y-axis to...'. These changes will be taken into account when extracting data from the chromatogram/mobiligram windows

**![](img/improved.png)** Significant improvements to the right-click menus (most notably for UniDec/Annotations)

#### **Plots panel**

**![](img/added.png)** Some images can now be rotated by 90 degrees (mainly 2D)

![](img/improved.png) Significant improvements to the right-click menus.

![](img/improved.png) Wheel-zoom in the X-dimensions has been improved (works like on maps now)

#### Data extraction:

![](img/added.png) You can now extract mass spectra from the '2D' panel. Hold CTRL on your keyboard and drag the mouse in the plot area. Only works when standard plot is shown (e.g. Drift time (bins) vs Scans/Time)

![](img/improved.png) All data extraction will be carried out in a temporary\_data folder (found in the ORIGAMI directory). This **should** fix any issues where data was being extracted from network drives and should keep your HDDs a  little bit tidier. All files will be deleted at the end of the session.

![](img/improved.png) Data extraction in the DT, RT, DT/MS panels now takes into account the plot labels/units.

![](img/improved.png) Extracted mass spectra extracted in the DT and RT windows will be now shown in an area beneath the extraction plot (for convenience)

#### MS annotations:

![](img/added.png) Peaks can now be annotated with an arrow (also available when exporting in an interactive format)

![](img/added.png) Added new customisation parameters window where you can change your visualisation preferences. Action -> Customise other settings...

![](img/improved.png) Selection of a peak in the MS window using the mouse (Annotating: On) will automatically try to determine the charge state based on the peaks isotopic distribution. You can change the error tolerance in Action -> Customise other settings -> Charge prediction value (default: 0.05).

#### UniDec settings:

![](img/added.png) Plots can now be customised using settings editor. (Settings: UniDec -> Customise plots...)

![](img/added.png You can switch between tabbed view where each plot is in a separate tab OR continuous view where all plots are available on the same page (Customise plots... -> Panel view)

![](img/improved.png) Deconvolution is now done in a multi-threaded mode. Should stop program from hanging

![](img/improved.png) All deconvolution results will be now stored in a temporary_data folder (found in ORIGAMI directory). This should keep your HDDs a little bit tidier. All files will be deleted at the end of the session.

#### MS comparison:

![](img/added.png) You can now assign your own label to the plot.

![](img/improved.png) You can now compare ALL available mass spectra and not just those that were hidden under 'Mass Spectra' tag. (This includes: Mass Spectra, Mass Spectrum, Mass Spectrum (processed)). To open comparison panel: Menu -> View -> Open MS comparison panel...)

#### Peak detection:

![](img/improved.png) Works in multi-threaded mode. Should stop program from hanging.