# Tasks that need completing

## Bug fixes

- [ ] add default views of the 3d plot to quickly set the camera orientation
- [ ] add update functions to each of the plot classes
- [ ] tidy-up the plotting classes
- [ ] add splash screen
- [ ] replace the old-style icons
- [ ] add controls to specify the number of threads running simultaneously
- [ ] fix a bug that removes the z-axis and label when updating data in the heatmap-3d plot
- [ ] improve how the matplotlib interaction displays user events
    - [ ] 1d plots should use horizontal box to highlight region of extraction
- [x] fix configuration file
- [ ] add documentation to each of the finished modules
- [ ] restructure documentation website
- [ ] fix contour plot x-axis scale as it does not display correct range (should start at 0.5)
- [ ] heatmap violin plot cuts off 1 value
- [ ] add a fix to the waterfall plot to prevent the erronous highlighting of regions (edge +1 bin)
- [x] add the resize/lock attributes to 3d plot
- [x] enable data extraction for multi-file raw files
- [ ] add support for embedded RAW data
- [ ] add support for copying RAW data to Document/Raw directory
- [ ] add option to update RAW directory in case it was moved away
- [ ] add option to extract mass spectrum from multi-file data when user extracts using heatmap
- [ ] add option to extract chromatogram from multi-file data when user extracts using ms heatmap plot
- [ ] add about Document popup view
- [x] add timer event to update plots whenever user changed settings in MS/heatmap processor
- [x] reduced amount of time between user interaction and update frequency in lesa/manual editor
- [x] add mixin to handle config load

## New features

- [ ] overlay panel overhaul
- [ ] ccs panel
- [ ] mobility peak picker
- [ ] batch data extraction
- [ ] custom data extraction
- [ ] complete overhaul of UniDec integration (start from scratch...)
- [ ] add some of the nice features of CIUSuite2