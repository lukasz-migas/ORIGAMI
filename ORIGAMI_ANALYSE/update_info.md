<h2><strong>What changed in ORIGAMI<sup>ANALYSE&nbsp;</sup>:</strong></h2>
<p><strong>Note</strong>&nbsp;</p>
<p>This was meant to be a mini-update but it has spaned over several weeks and includes a fairly significant revamp of the <strong>Interactive output panel</strong> (with loads new features), addition of <strong>many</strong> new plot types, cleaner interface (in some places), bug fixes and more.</p>
<p>I have changed the way I compile ORIGAMI (switched from obsolete py2exe to pyinstaller) which increased the size of the directry (~2x) and made it less organised but it should result in better support. Overall, you should see similar performance and not notice the change.</p>
<p><strong>New in v1.1.2:</strong></p>
<ul>
<li>Added several new plotting methods:
<ul>
<li>Waterfall overlay</li>
<li>Violin</li>
<li>Scatter</li>
<li>Bar plot</li>
</ul>
</li>
<li>The document type (Type: Interactive) now supports addition of "Other..." data type. This is fairly versatile and can include any of the following: <em>line, multi-line, scatter, vertical-bar, horizontal-bar, grid-line, waterfall, grid-line and grid-scatter </em>and is mostly aimed at enabling exporting of more complex (and not necessarily MS related datasets) in an interactive format. To take advantage of its full potential I made a repository where you can see example files, but it basically requires specification of some meta-data (i.e. title, x/y-axis labels etc) and addition of data. You can learn more about it by going to <strong>Menu -&gt; Help -&gt; Help pages -&gt; Learn more: Other datasets (shortcut F1+9)</strong>. Check out the example files <a href="https://github.com/lukasz-migas/ORIGAMI/tree/master/ORIGAMI_ANALYSE/other_datasets">here</a>. I've also included a couple example files in folder 'example_files/other_data'. </li>
<li>Added new "Annotation" panel that enables you add annotations to mass spectra (i.e. charge state, protein name, any description). To enable it, plot the mass spectrum and right-click in the Documents Tree and select -&gt; Add/Show annotations (shown below). You can learn more about it going to <strong>Menu -&gt; Help pages -&gt; Learn more: Annotating mass spectra (shortcut F1+8)</strong></li>
<li>Added a proper version checker that will check whether new version of ORIGAMI is available online at each start of the program.</li>
<li>General changes to the Interactive Output panel:
<ul>
<li>Tried to reorganise several components to make it look less cluttered.</li>
<li>Added several new parameters that you can change</li>
<li>All generated plots can now benefit from using 'custom JavaScript' widgets and events. Events are currently limited to 'double-click in plot area will zoom-out' whereas widgets are much more versatile and include addition of buttons, sliders, toggles, radio buttons and few others. These can control the size of the labels, level of zoom, transparency or position of legend and many others. These are enabled by default and can be turned off in the <strong>Interactive Panel -&gt; Annotations -&gt; Add custom JS events/scripts when available</strong>. Addition of custom JS events/widgets slows down generation of interactive plots as these have to be compiled to JS. <strong>Note</strong>: First time you try this you will most likely be greeted with an error message. Follow the instructions there to solve it.</li>
<li>Expanded the list of available plots.</li>
<li>Interactive plots can be exprted in multi-threaded mode now, enabling you to do other tasks while they are being exported. <strong>Note: </strong>If you close the output window, the export process will stop.</li>
</ul>
</li>
<li>Overlay plots will not be added to overlay document by default. You first must toggle "Add overlay plots to document" in the menus of individual overlay panels.</li>
</ul>
<p><strong>Improvements in v1.1.2:</strong></p>
<ul>
<li>Loads of small improvements in the Interactive output pane</li>
<li>Improved and extended list of available labels</li>
<li>Reorganised the <strong>Plot parameters panel </strong></li>
<li>Some of the <strong>plot parameter</strong> options will take an immediate effected without the need to replot the data. Some will not!</li>
<li>General improvements to the Peak fitting/finding in the <strong>Processing panel</strong>.</li>
<li>General improvements to the Mass spectrum processing the <strong>Processing panel</strong>.</li>
<li>Usually at start of the program, ORIGAMI looks for Driftscope on your PC. If it doesn't find it, it usually notifies you of it. You can disable this behaviour now.</li>
<li>Configuration files are not saved automatically. You can disable this by going to <strong>Plot settings -&gt; Extra -&gt; Auto-save settings</strong> to off.</li>
<li>Added two new color palettes (cividis - colorblind friendly and winter)</li>
<li>Rearranged the UniDec panel and improved error messges.</li>
<li>Added label position optimisation (can be disabled if you don't like the results).</li>
</ul>
<p>&nbsp;<strong>Fixes in v1.1.2:</strong></p>
<ul>
<li>Many fixes that should improve the general usability and reliability of the analysis software</li>
<li>Fixed an issue where the colorbar wasn't displaying correct values</li>
<li>Fixed issues with the waterfall plots.</li>
<li>Fixed an issue which occurs when the size of the screen is not optimal. I've tested the software on screens with severan screen dimensions (1980x1080, 1680x1050, 1600x900, 1366x768, 1280x102 and 1280x800) and its looks pretty good.&nbsp; I would recommend using a decent sized screen for using ORIGAMI.</li>
</ul>
<p><strong>Planned features:</strong></p>
<ul style="list-style-type: square;">
<li>Interactive panel:
<ul style="list-style-type: square;">
<li>I don't like the current positiong of various settings and how they are actively enabled/disable upon selection in the list. I intend to add a separate window where when you double-click on an item it will open and you will only see relevant settings.</li>
<li>Widgets are awesome but still require a lot of work. A couple of really cool widgets I intend to add are toggles for colorblind mode, data selection dropdowns, comparison tools etc</li>
<li>I would like to add a number of neat plots, including circos-style plot for XL-MS, HDX-style grid plots etc</li>
</ul>
</li>
<li>Plots:
<ul style="list-style-type: square;">
<li>I have a couple of ideas for new plot types, especially for RMSD-type plots</li>
</ul>
</li>
<li>Main program:
<ul style="list-style-type: square;">
<li>Speed-up certain operations</li>
<li>Improve GUI</li>
<li>Add support for other vendor files. I intend to use <em>multiplierz </em>+ other open-source libraries</li>
</ul>
</li>
<li>Help pages:
<ul style="list-style-type: square;">
<li>Improve the text + add more examples</li>
</ul>
</li>
<li>Videos:
<ul style="list-style-type: square;">
<li>Record a couple of videos showing various features + usage</li>
</ul>
</li>
</ul>
<p>&nbsp;</p>
<p><strong>ORIGAMI-MS:</strong></p>
<p>There have been no changes to ORIGAMI<sup>MS</sup>, so please download it from release 1.0.1.</p>
<p><strong>Video tutorials:</strong></p>
<p>A couple of videos is available on YouTube. Will try to add more in future.</p>
<p><a title="ORIGAMI-MS: Setup Guide" href="https://www.youtube.com/watch?v=XNfM6F_MSb0&amp;list=PLrPB7zfH4WXMYa5CN9qDtl-G-Ax_L6AK8">ORIGAMI-MS: Setup Guide</a></p>
<p><a title="ORIGAMI-ANALYSE: Analysis of ORIGAMI-MS files" href="https://youtu.be/henWSN9tMgQ">ORIGAMI-ANALYSE: Analysis of ORIGAMI-MS files</a></p>
<p><strong>Mailing list</strong></p>
<p>If you would like to be added to a ORIGAMI mailing list where you will be notified of new releases, please contact <a href="mailto:lukasz.migas@manchester.ac.uk">lukasz.migas@manchester.ac.uk</a>.&nbsp;</p>
<p><strong>How to update</strong></p>
<p>Since the whole package was revamped, the only way to update ORIGAMI is to download the ORIGAMI_ANALYSE_v1.1.2.zip file, unpack it somewhere on your PC and it should work out of the box. :)</p>
<p>As you might notice, the size of the directory increased quite a bit, it is about 1 Gb when unpacked.</p>
<p>Many thanks,</p>
<p>Lukasz</p>
