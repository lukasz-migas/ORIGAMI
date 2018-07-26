<h2><strong>Repository of example datasets that can be loaded with the new "Other data..." option. </strong></h2>
<hr />
<h3><strong>Loading of non-MS datasets ("other" data)</strong></h3>
<hr />
<p><strong>Disclaimer:</strong></p>
<p>This is only an experimental feature and might not work perfectly! I've tried to implement all tags into various plotting functions but it is likely I forgot. I know for a fact that specifying xlimits/ylimits might not work everywhere.</p>
<hr />
<p>Since version 1.1.2 it is possible to load a number of data formats that are not mass spectrometry related, for instance, molecular dynamics results, machine learning, HDX, cross-linking and many others that comply with the data format requirements.A bit like in OriginPro or Excel, data can be loaded from a comma-delimited file that has been appropriately labeled with some of the allowed tags. The list of tags is found below and you also have a look online <strong><a href="https://github.com/lukasz-migas/ORIGAMI/tree/master/ORIGAMI_ANALYSE/other_datasets">here</a> </strong>to see some example files for datasets previously published by myself or members of the Barran group. The file must have metadata (found at the top of the file) and plot data (below the metadata).</p>
<h4>Allowed tags in the metadata section:</h4>
<p><strong>title</strong> = dataset title</p>
<p><strong>plot_type</strong> = type of plot ORIGAMI should display. Allowed types: <em>line, </em><em>multi-line</em>, <em>scatter</em>, <em>vertical-bar, horizontal-bar, grid-line, waterfall</em></p>
<p><strong>x_label</strong> = x-axis label</p>
<p><strong>y_label</strong> = y-axis label</p>
<p><strong>label </strong>or <strong>labels</strong> = y-axis labels. In general, number of labels must match number of columns with the <strong>axis_y</strong> tag.</p>
<p><strong>color</strong> or <strong>colors</strong> = colors to be associated with dataset. Color must be in HEX representation (i.e. #000000). In general, number of colors must match number of columns with the <strong>axis_y</strong> tag.</p>
<p><strong>x</strong><strong>limits</strong> = specify the minimum and maximum values for x-axis of the dataset. Must have two values.</p>
<p><strong>ylimits</strong> = specify the minimum and maximum values for y-axis of the dataset. Must have two values.</p>
<p><strong>legend_labels</strong> = for certain datasets (i.e. vertical/horizontal bar) it is necessary to add legend. Just put the desired label in.</p>
<p><strong>legend_colors</strong> = associated with legend_labels. Must have same number of colors as number of labels. Color must be in HEX representation.</p>
<p><strong>hover_labels</strong> = labels associated with columns with the <strong>axis_label </strong>tag. The number of hover_labels must match number of columns with axis_label tag.</p>
<h4>Allowed tags in the plot data section:</h4>
<p><strong>axis_x</strong> = columns associated with x-axis data.</p>
<p><strong>axis_y</strong> = columns associated with y-axis data.</p>
<p><strong>axis_xerr</strong> = columns associated with x-axis error data. Only used for scatter plot types.</p>
<p><strong>axis_yerr</strong> = columns associated with y-axis error data. Only used for scatter plot types.</p>
<p><strong>axis_color</strong> = columns with colors for each item in the x/y-axis. Color must be in HEX representation (i.e. #000000). Only used for scatter plot types.</p>
<p><strong>axis_y_min </strong>= columns associated with x-axis data. Only used for vertical/horizontalbar plot types.</p>
<p><strong>axis_y_max </strong>= columns associated with x-axis data. Only used for vertical/horizontalbar plot types.</p>
<p><strong>axis_label </strong>= columns associated with x/y-axis data. Used in hover tooltip. Can add hover tooltip labels using the <strong>hover_labels</strong>.</p>
<p><strong>axis_note </strong>= columns associated with x/y-axis data.</p>
<p>Requirements on per=plot basis:</p>
<p><em>line </em>- should only have two columns with labels <strong>axis_x</strong>, <strong>axis_y</strong></p>
<p><em>multi-line </em>- should have as many columns as desired. You either provide one common column with the <strong>axis_x</strong> tag and multiple columns with <strong>axis_y</strong> (must have the same length as <strong>axis_x</strong>) or provide multiple combinations of <strong>axis_x</strong> and <strong>axis_y</strong>. There must be equal number of axis_x and axis_y columns in this case. You can specify colors and labels using the <strong>color/colors</strong> and <strong>label/labels</strong> tag in the metadata section.</p>
<p><em>scatter - </em>should have as many columns as desired. You either provide one common column with the <strong>axis_x</strong> tag and multiple columns with <strong>axis_y</strong> (must have the same length as <strong>axis_x</strong>) or provide multiple combinations of <strong>axis_x</strong> and <strong>axis_y</strong>. You can also specify colors for each dataset using the <strong>color/colors</strong> tag in the metadata section or by providing <strong>axis_color</strong> column where color is specified for each item in the list. Currently only supported for datasets of the same length.<em><br /></em></p>
<p><em>vertical-bar&nbsp; - </em>should have as many columns as desired. You either provide one common column with <strong>axis_x</strong> tag and multiple columns with <strong>axis_y_min</strong> and <strong>axis_y_max</strong> (must have the same length as <strong>axis_x</strong>) or provide multiple combinations of axis_x and axis_y_min and axis_y_max. You can specify colors for individual items using the <strong>axis_color</strong> tag or using the <strong>color/colors</strong> tag. You can also specify labels for individual datasets using the <strong>axis_label</strong>.</p>
<p><em>horizontal-bar </em>- same as above.</p>
<p><em>grid-line </em>- same as <em>multi-line</em> with different plot name.<em><br /></em></p>
<p><em>waterfall</em> - same as <em>multi-line </em>with different plot name<em>.<br /></em></p>
<p>&nbsp;</p>
<h4><strong>Example figures:</strong></h4>
<p><img src="images/other_data_examples.png" alt="" width="1485" height="1615" /></p>
<p>&nbsp;</p>
