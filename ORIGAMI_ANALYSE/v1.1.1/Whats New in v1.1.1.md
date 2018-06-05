
<h2><strong>What changed in ORIGAMI<sup>ANALYSE&nbsp;</sup>:</strong></h2>
<p><strong>Note</strong>&nbsp;</p>
<p>This is a major update, predominantly focusing on adding support for deconvolution of mass spectra using UniDec and introducing several new plotting options while also improving the Interactive Output documents.</p>
<p><strong>New in v1.1.1:</strong></p>
<ul>
<li>Added support for UniDec deconvolution in ORIGAMI. <br />
<ul>
<li>you can easily load MS and deconvolute using the well-established UniDec's Bayesian deconvolution algorithm</li>
<li>ORIGAMI generates nearly identical plots to those of UniDec</li>
<li>all deconvolution results can be exported in a HTML format</li>
<li>The results obtained in ORIGAMI are identical to those of UniDec</li>
<li>If you use this feature, please ensure to cite UniDec in your research!</li>
</ul>
</li>
<li>Can now export RGB plots in Interactive Format</li>
<li>Added two new overlay methods (Grid (2-&gt;1) and Grid (n x n))
<ul>
<li>The Grid (2-&gt;1) method allows viewing RMSD plot alongside its individual components</li>
<li>The Grid (n x n) allows viewing up to 16 species simultaneously</li>
</ul>
</li>
<li>Added Drag'n'Drop support for multiple data types
<ul>
<li>.raw files will be assumed to in an ORIGAMI format (it is compatible will all data processing tools)</li>
<li>.raw files dropped in the Multiple Files panel will be added to currently opened MANUAL document, if none present it will create a new one</li>
<li>.txt/.csv/.tab files are also supported. ORIGAMI will perform a test to see if its in a 2D IM-MS or MS format</li>
</ul>
</li>
<li>Added visualisation of MS using a waterfall-like plot
<ul>
<li>Right-click on Mass Spectra in the document window --&gt; Select Show mass spectra (waterfall). You can change waterfall settings in the Waterfall settings panel</li>
<li>By default it will try to sort files based on energy, if not available it will sort it by name</li>
</ul>
</li>
<li>MS comparison now supports files of different sizes</li>
<li>Added color palette option in the Settings -&gt; General panel</li>
<li>Added new document type (INTERACTIVE) which allows loading of MS, RT, DT and 2D datasets independent of the vendor (text format of course!). All of these can be exported in a .html format</li>
</ul>
<p><strong>Improvements in v1.1.1:</strong></p>
<ul>
<li>Interactive documents will now contain a watermark</li>
<li>Small improvements to the hover tool in the HTML viewer</li>
<li>small twaks to the 1D plots</li>
<li>Fixed an issue with the waterfall plots (incorrect ordering of the plot lines)</li>
<li>When extracting peaks in the MS window, ORIGAMI will try to determine the charge state automatically by examining the isotopic pattern</li>
</ul>
<p>&nbsp;</p>
<p><strong>Fixes in v1.1.1:</strong></p>
<ul>
<li>Many fixes that should improve the general usability and reliability of the analysis software</li>
<li>Minor problems when analysing multiple MassLynx files simultaneously</li>
<li>A couple of small issues when loading Linear DT files</li>
</ul>
<p>&nbsp;</p>
<p>&nbsp;<strong>Known issues:</strong></p>
<ul>
<li>The DT-IMS panel still lacks a lot of functions</li>
<li>The CCS panel is quite clunky and not intuitive - needs a revamp!</li>
<li>When zooming-in and the mouse cursor goes outside of the plot axes, the zoom tools get locked-up - kind of annoying</li>
</ul>
<p>&nbsp;</p>
<p><strong>Example images:</strong></p>
<p>&nbsp;</p>
<p><img src="https://github.com/lukasz-migas/ORIGAMI/blob/master/ORIGAMI_ANALYSE/v1.1.1/origami_unidec.gif" alt="UniDec GIF" width="600" height="340" /></p>
<p>Grid (2-&gt;1) overlay method</p>
<p><img src="https://github.com/lukasz-migas/ORIGAMI/blob/master/ORIGAMI_ANALYSE/v1.1.1/origami_grid2to1.png" alt="Grid (2-&gt;1)" width="600" height="340" /></p>
<p>Grid (n x n) overlay method</p>
<p><img src="https://github.com/lukasz-migas/ORIGAMI/blob/master/ORIGAMI_ANALYSE/v1.1.1/origami_gridNxN.png" alt="Grid (n x n)" width="600" height="340" /></p>
<p>MS waterfall method</p>
<p><img src="https://github.com/lukasz-migas/ORIGAMI/blob/master/ORIGAMI_ANALYSE/v1.1.1/origami_MS_waterfall.png" alt="MS Waterfall" width="600" height="340" /></p>
<p><strong>ORIGAMI-MS:</strong></p>
<p>There have been no changes to ORIGAMI<sup>MS</sup>, so please download it from release 1.0.1.</p>
<p><strong>Video tutorials:</strong></p>
<p>A couple of videos is available on YouTube. Will try to add more in future.</p>
<p><a title="ORIGAMI-MS: Setup Guide" href="https://www.youtube.com/watch?v=XNfM6F_MSb0&amp;list=PLrPB7zfH4WXMYa5CN9qDtl-G-Ax_L6AK8">ORIGAMI-MS: Setup Guide</a></p>
<p><a title="ORIGAMI-ANALYSE: Analysis of ORIGAMI-MS files" href="https://youtu.be/henWSN9tMgQ">ORIGAMI-ANALYSE: Analysis of ORIGAMI-MS files</a></p>
<p><strong>Mailing list</strong></p>
<p>If you would like to be added to a ORIGAMI mailing list where you will be notified of new releases, please contact <a href="mailto:lukasz.migas@manchester.ac.uk">lukasz.migas@manchester.ac.uk</a>.&nbsp;</p>
<p><strong>How to update</strong></p>
<p>Since the whole package was revamped, the only way to update ORIGAMI is to download the ORIGAMI_ANALYSE_v1.1.1.zip file, unpack it somewhere on your PC and it should work out of the box. :)</p>
<p>As you might notice, the size of the directory increased quite a bit, it is about 500 Mb when unpacked.</p>
<p>&nbsp;</p>
<p>Many thanks,</p>
<p>Lukasz</p>
