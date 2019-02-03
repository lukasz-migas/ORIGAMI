<h2><strong>What changed in ORIGAMI<sup>ANALYSE</sup></strong></h2>

## Documentation

<p><strong>[NEW]:</strong> Added online [documentation](https://lukasz-migas.github.io/ORIGAMI/)

<p><strong>[NEW]:</strong> Added several new videos to the [YouTube playlist](https://www.youtube.com/playlist?list=PLrPB7zfH4WXMYa5CN9qDtl-G-Ax_L6AK8)

## Document Tree

<p><strong>[FIXED]:</strong>Fixed typo: spectrun -> spectrum (grr)

<p><strong>[FIXED]:</strong>When loading mzml/mgf files, the individual scans will no longer be shown in the document tree as it caused some major issues. If you would like to see the individual spectra, please double-click on the header 'Tandem Mass Spectra'

<p><strong>[FIXED]:</strong>Fixed a problem when trying to plot waterfall plot from the Document Tree menu

<p><strong>[IMPROVED]:</strong> When loading any data into the INTERACTIVE document, you will be asked whether data should be duplicated, merged or duplicated

<p><strong>[IMPROVED]:</strong> When plotting a waterfall plot, data will be checked to ensure its not too big (e.g. not too many rows). If the value is above the threshold (set to 500), you will be asked if you would like to continue

## Main window

<p><strong>[NEW]:</strong> Added new menu: **Plugins**. This menu will hold all future mini-applications

<p><strong>[NEW]:</strong> Umder the menu **Plot settings** I've added a couple new options that allow modification of plot extra plot parameters.

<p><strong>[IMPROVED]:</strong> The help pages **(Help -> Help pages -> ...)** have now been replaced with links to the new documentation (opens in the browser). Where no documentation exists yet, old pages will be shown. Also available [online](https://origami.lukasz-migas.com)

## Annotations

<p><strong>[NEW]:</strong> you can now also easily 'duplicate/multiply' annotations. **Action -> Multiply annotations...** this will result in a copy of the selected annotation(s) with slight difference in the min-value (so they can be distinguished from its parent)

<p><strong>[NEW]:</strong> Text annotations can now be added to other plots (scatter, v-bar, h-bar, waterfall, multi-line/overlay). To added annotations, find it in the **Document Tree**, right-click on it and you should be presented with option **Show annotations panel...**. Then you can simply follow the standard annotations protocol. See [here](https://origami.lukasz-migas.com/user-guide/processing/mass-spectra-annotation.html) for more information

<p><strong>[NEW]:</strong> Annotations parameters can now be easily modified as they can be **dragged** on the plot. If an annotation is shown on your plot, you can simply drag it around in the plot area and once you let-go, new settings (e.g. position) will be updated in the ORIGAMI document.

<p><strong>[FIXED]:</strong>font size, weight and rotation will now be aplied when adding labels

<p><strong>[FIXED]:</strong>auto-label generator will now also create labels based purely on the charge state

<p><strong>[FIXED]:</strong>annotation parameters (e.g. size, weight, rotation) will be respected when replotting from the Document Tree

## Interactive panel

<p><strong>[NEW]:</strong> Made big progres in terms of copying/applying styles for plot elements. When you
double-click on any element in the file list a new window will appear where you can individually adjust plot parameters. When you finished, you can right-click on that same (or any other) item in the list and select 'Copy style..'. You can then select any other item in the list, right-click on it and select 'Apply style..'.

<p><strong>[NEW]:</strong> certain plot types (v-bar, h-bar, scatter, waterfall, multi-line/overlay) will now support addition of annotations (and their widgets). Annotations can correspond to anything you wish to say about specific region of a dataset.

<p><strong>[NEW]:</strong> Scatter plots that are created from datasets loaded through text files with added metadata can be enhanced with weblinks/URLs. See the [example](https://origami.lukasz-migas.com/interactive-examples/ccs-compendium.html) for more information.

<p><strong>[FIXED]:</strong>fixed sorting in the list (especilaly when using the 'Show selected' option) Lists are sorted using 'natural sorting' from now on, meaning they should be more logically sorted.

<p><strong>[FIXED]:</strong>fixed the show/hide table elements when you right-click on the table headers

<p><strong>[IMPROVED]:</strong> Colorbars:

* added loads of new settings users can control
* better behaviour when adding colorbars to plots

<p><strong>[CHANED]:</strong> removed tools/toolset from ORIGAMI - the new system of copy/apply style should work much better

<p><strong>[IMPROVED]:</strong> I've realised that using 'coffeescript' for widget exportation was a big mistake as it takes ~10x+ longer to compile that script than pure JavaScript. Adding widgets will be a lot faster from now on (a couple haven't been ported to JS yet).

## Plots

<p><strong>[IMPROVED]:</strong> Improved color handling in violin and waterfall plots. The line color (edge) and shade/fill-under can be independently controlled now.

## UVPD processing :star:

<p><strong>[NEW]:</strong> Added new plug that allows analysis and processing of UVPD datasets that were acquired with laser being constantly switched on/off. This is a user-specific plugin that will most likely have no use for anyone else apart from some Barran group members. To activate, click on the **Menu -> Plugins -> UVPD processing window...**.

## Tandem MS panel

<p><strong>[NEW]:</strong> You can now load .mzML files (haven't figured out how to add .mzIdentML files to them yet...)

<p><strong>[NEW]:</strong> MS/MS files can now be exported in an interactive format (.html document). This feature is still in development and I imagine will not be stable until v1.2.2 at the earliest. At the moment, individual scans of MS/MS file (.mgf only) can be annotated (e.g. fragments can be generated) and added to the file. Scans that have been user-annotated can be subsequently exported. This will be properly showcased in a tutorial.

<p><strong>[NEW]:</strong> Added two new options in the **Action menu** which permit improved population of the table by either excluding scans with PTMs and excluding scans without identification. Clicking on either of these will automatically trigger re-population of the table based on the selected options.

<p><strong>[NEW]:</strong> You can see what PTMs have been included in the scan by clicking on the **Modifications list**

<p><strong>[IMPROVED]:</strong> Scans that have multiple identification information will be separated into separae instances in the table (e.g. look at the column ID #)

<p><strong>[IMPROVED]:</strong> Fragment generator can now handle PTMs (at least those that have kept the mass information)

<p><strong>[IMPROVED]:</strong> Improved the way scans are loaded (faster and actually works...)

<p><strong>[IMPROVED]:</strong> Improved the way butterfly plots are shown. A horizontal line will be drawn from now on (at y=0)

<p><strong>[IMPROVED]:</strong> Added several new customisation parameters that permit better data visualisation. These are found under **Action -> Customise...**

<p><strong>[FIXED]:</strong>When selecting frag-all option, appropriate checkboxes will be ticked from now on

<p><strong>[FIXED]:</strong>Fixed fragment generator to stop overriding fragments with same name (e.g. y1+ was equal y_H2Ox11+...)

## Other data -> Annotated data

<p><strong>[NEW]:</strong> Added new keyword 'axis_url'/'axis_urls' to the data parser. These keywords can be used to provide web addresses which can be attached to the data (scatter points only for now). If valid URL address is provided, when you tap on a point you will be taken to a new tab in your browser which corresponds to the web address. This is only valid in the interactive plots

<p><strong>[CHANED]:</strong> Changed the poorly selected name of 'Other data' to 'Annotated data'


## Mailing list

If you would like to be added to the ORIGAMI mailing list where you will be notified of new releases, please contact lukasz.migas@manchester.ac.uk or visit https://origami.lukasz-migas.com/main/subscribe.html.

## How to update

A lot has changed in this version so the only way to update is to download the package and unpack it somewhere else on your PC. I've tried really hard not to break too many things :)

Many thanks,
Lukasz