<h2><strong>What changed in ORIGAMI<sup>ANALYSE</sup>:</strong></h2>
<p><strong>Note</strong>&nbsp;</p>
<p><span style="color: #000000;">Again, this was meant to be a small-ish update but turned into a fairly significant revamp of ORIGAMI. Because of this, I have upgraded it to version 1.2.0.</span></p>
<p>&nbsp;</p>
<p><span style="text-decoration: underline;"><span style="color: #000000;"><strong>General:</strong></span></span></p>
<p><span style="color: #000000;"><strong>[IMPROVED]:</strong> The underlying codebase of ORIGAMI has been improved to make it more readable and more responsive</span></p>
<p><span style="color: #000000;"><strong>[IMPROVED]:</strong> Item font color will be automatically adjusted to ensure best contrast from the background color in various lists in the GUI</span></p>
<p><span style="color: #000000;"><strong>[CHANGED]</strong>: Modification of the table elements is now available by Right-clicking on the column name</span></p>
<p>&nbsp;</p>
<p><span style="text-decoration: underline;"><strong>Tandem MS [NEW]:</strong></span></p>
<p><span style="color: #000000;"><strong class="historyAdded">[NEW]:</strong></span> Added support to load .mgf and .mzIdentML file formats to visualise tandem mass spectrometry results. Menu -&gt; Open open-source files... to load .mgf files. You can then annotate the tandem MS with peptide fragments. See Figure 1 for example.</p>
<p>&nbsp;</p>
<p><span style="text-decoration: underline;"><span style="color: #000000;"><strong>Interactive panel:</strong></span></span></p>
<p><span style="color: #000000;"><strong class="historyAdded">[NEW]: </strong>Started adding support for individual modification of parameters for interactive plots (double-clicking on an item in the list)</span></p>
<p><span style="color: #000000;"><strong class="historyAdded">[NEW]: </strong>Interactive documents can now be visualised without access to internet. Just check the "Add offline support" checkbox</span></p>
<p><span style="color: #000000;"><strong class="historyAdded">[NEW]:</strong> Annotated mass spectra will now include label + arrow (if available)</span></p>
<p><span style="color: #000000;"><strong>[IMPROVED]</strong>: Legends now work with markers and shaded areas</span></p>
<p><strong>[FIXED]: </strong>Issue that prevent exporting interactive documents with legends has been removed</p>
<p><strong>[FIXED]:</strong> Issue that prevent proper showing of toolbar has been removed</p>
<p>&nbsp;</p>
<p><span style="text-decoration: underline;"><span style="color: #000000;"><strong>Peaklist panel:</strong></span></span></p>
<p><span style="color: #000000;"><strong class="historyAdded">[NEW]: </strong>Added 'Extract automatically' check tool (Peaklist -&gt; Toolbar -&gt; Extract...)</span></p>
<p><span style="color: #000000;"><strong class="historyAdded">[NEW]: </strong>Added 'Overlay automatically' check tool (Peaklist -&gt; Toolbar -&gt; Overlay...)</span></p>
<p><span style="color: #000000;"><strong>[IMPROVED]:</strong> Added a lot of new shortcuts for easier plotting</span></p>
<p>&nbsp;</p>
<p><span style="text-decoration: underline;"><span style="color: #000000;"><strong>Text file panel:</strong></span></span></p>
<p><span style="color: #000000;"><strong class="historyAdded">[NEW]: </strong>Added 'Extract automatically' check tool (Peaklist -&gt; Toolbar -&gt; Extract...)</span></p>
<p><span style="color: #000000;"><strong class="historyAdded">[NEW]: </strong>Added 'Show chromatogram' and 'Show mobiligram' for each viewed file (Right-click -&gt; Select appropriate)</span></p>
<p><span style="color: #000000;"><strong>[IMPROVED]:</strong> Added a lot of new shortcuts for easier plotting</span></p>
<p><strong>[FIXED]:</strong> Removed an issue that prevented loading certain text files</p>
<p><strong>[FIXED]:</strong> Removed an issue that would incorrectly remove documents from the text file list</p>
<p>&nbsp;</p>
<p><span style="text-decoration: underline;"><span style="color: #000000;"><strong>Multiple MS files panel:</strong></span></span></p>
<p><span style="color: #000000;"><strong><strong class="historyAdded">[NEW]</strong>:</strong> The average mass spectrum can be re-binned/re-processed based on new parameters (Process -&gt; Average mass spectra (current document))</span></p>
<p><span style="color: #000000;"><strong>[IMPROVED]:</strong> Item font color will be automatically adjusted to ensure best contrast from the background color</span></p>
<p><span style="color: #000000;"><strong>[IMPROVED]:</strong> Average mass spectrum will be automatically re-binned/re-processed when an item is added or deleted</span></p>
<p><strong>[FIXED]:</strong> Removed an issue that prevented typing-in numerical values in the 'variable' colument when using laptop keyboards. I have only ever encountered this issue once... Let me know if it still occurs!</p>
<p>&nbsp;</p>
<p><span style="text-decoration: underline;"><span style="color: #000000;"><strong>Document tree:</strong></span></span></p>
<p><span style="color: #000000;"><strong class="historyAdded">[NEW]: </strong>Double-clicking on the document header will now clear all plots and show the most basic plots for that document (e.g. MS, DT, RT, etc). You can also do this by Right-click -&gt; Refresh document.</span></p>
<p><span style="color: #000000;"><strong class="historyAdded">[NEW]: </strong>You can now change the x-/y-axis labels for chromatograms and mobiligrams. Right-click on the item and slect 'Change x/y-axis to...'. These changes will be taken into account when extracting data from the chromatogram/mobiligram windows</span></p>
<p><span style="color: #000000;"><strong class="historyAdded"><strong>[IMPROVED]</strong>: </strong>Significant improvements to the right-click menus (most notably for UniDec/Annotations)</span></p>
<p>&nbsp;</p>
<p><span style="text-decoration: underline;"><span style="color: #000000;"><strong>Plots panel</strong></span></span></p>
<p><span style="color: #000000;"><strong><strong class="historyAdded">[NEW]:</strong></strong> Some images can now be rotated by 90 degrees (mainly 2D)</span></p>
<p><span style="color: #000000;"><strong>[IMPROVED]</strong>: Significant improvements to the right-click menus.</span></p>
<p><span style="color: #000000;"><strong>[IMPROVED]:</strong> Wheel-zoom in the X-dimensions has been improved (works like on maps now)</span></p>
<p>&nbsp;</p>
<p><span style="text-decoration: underline;"><span style="color: #000000;"><strong>Data extraction:</strong></span></span></p>
<p><span style="color: #000000;"><strong class="historyAdded">[NEW]:</strong> You can now extract mass spectra from the '2D' panel. Hold CTRL on your keyboard and drag the mouse in the plot area. Only works when standard plot is shown (e.g. Drift time (bins) vs Scans/Time)</span></p>
<p><span style="color: #000000;"><strong>[IMPROVED]:</strong> Data extraction in the DT, RT, DT/MS panels now takes into account the plot labels/units.</span></p>
<p><span style="color: #000000;"><strong>[IMPROVED]:</strong> Extracted mass spectra extracted in the DT and RT windows will be now shown in an area beneath the extraction plot (for convenience)</span></p>
<p>&nbsp;</p>
<p><span style="text-decoration: underline;"><span style="color: #000000;"><strong>MS annotations:</strong></span></span></p>
<p><span style="color: #000000;"><strong class="historyAdded">[NEW]:</strong> Peaks can now be annotated with an arrow (also available when exporting in an interactive format)</span></p>
<p><span style="color: #000000;"><strong class="historyAdded">[NEW]:</strong> Added new customisation parameters window where you can change your visualisation preferences. Action -&gt; Customise other settings...</span></p>
<p><span style="color: #000000;"><strong>[IMPROVED]:</strong> Selection of a peak in the MS window using the mouse (Annotating: On) will automatically try to determine the charge state based on the peaks isotopic distribution. You can change the error tolerance in Action -&gt; Customise other settings -&gt; Charge prediction value (default: 0.05).</span></p>
<p>&nbsp;</p>
<p><span style="text-decoration: underline;"><span style="color: #000000;"><strong>UniDec settings:</strong></span></span></p>
<p><span style="color: #000000;"><strong><strong class="historyAdded">[NEW]</strong>:</strong> Plots can now be customised using settings editor. (Settings: UniDec -&gt; Customise plots...)</span></p>
<p><span style="color: #000000;"><strong><strong class="historyAdded">[NEW]</strong>:</strong> You can switch between tabbed view where each plot is in a separate tab OR continuous view where all plots are available on the same page (Customise plots... -&gt; Panel view)</span></p>
<p><span style="color: #000000;"><strong>[IMPROVED]:</strong> Deconvolution is now done in a multi-threaded mode. Should stop program from hanging</span></p>
<p>&nbsp;</p>
<p><span style="text-decoration: underline;"><span style="color: #000000;"><strong>MS comparison:</strong></span></span></p>
<p><span style="color: #000000;"><strong><strong class="historyAdded">[NEW]</strong>: </strong>You can now assign your own label to the plot.<br /></span></p>
<p><span style="color: #000000;"><strong>[IMPROVED]:</strong> You can now compare ALL available mass spectra and not just those that were hidden under 'Mass Spectra' tag. (This includes: Mass Spectra, Mass Spectrum, Mass Spectrum (processed)). To open comparison panel: Menu -&gt; View -&gt; Open MS comparison panel...)</span></p>
<p>&nbsp;</p>
<p><span style="text-decoration: underline;"><span style="color: #000000;"><strong>Peak detection:</strong></span></span></p>
<p><span style="color: #000000;"><strong>[IMPROVED]:</strong> Works in multi-threaded mode. Should stop program from hanging.</span></p>
<p>&nbsp;</p>
<p><strong>Mailing list</strong></p>
<p>If you would like to be added to a ORIGAMI mailing list where you will be notified of new releases, please contact <a href="mailto:lukasz.migas@manchester.ac.uk">lukasz.migas@manchester.ac.uk</a>.&nbsp;</p>
<p><strong>How to update</strong></p>
<p>Since the whole package was revamped, the only way to update ORIGAMI is to download the ORIGAMI_ANALYSE_v1.2.0.zip file, unpack it somewhere on your PC and it should work out of the box. :)</p>
<p>As you might notice, the size of the directory increased quite a bit, it is about 1 Gb when unpacked.</p>
<p>Many thanks,</p>
<p>Lukasz</p>