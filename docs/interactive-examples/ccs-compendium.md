# Interactive scatter plot

## Some background

I recently came across this nice paper from John McLean's lab at Vanderbilt which discusses how we can use a relatively large (~4000 values) database of measured standards in omics studies. They have created a *R Shiny* app which provides interactivity to explore the dataset. Since I have been recently improving ORIGAMI's interactive capabilities, I've decided to embed their dataset in ORIGAMI and export it as a self-sufficient HTML document. This took me about ~10 minutes altogether (mostly rearranging columns and annotating text document). I think the results are quite close to the original publication (Figure 2a).

[See figure in another tab](html-files/widgets-ccs-compendium.html)

## Interactive figure

<iframe
    width="650"
    frameborder="0"
    height="1100"
    src="html-files/widgets-ccs-compendium.html"
    style="background: #FFFFFF;">
</iframe>

## Formatted data

You can have a look at the way the data is structured below.

<iframe
    src="https://docs.google.com/spreadsheets/d/e/2PACX-1vRqOJpxBvUagahpBvQzM78FjHLRWnfVbkEYXJsUMYLtO_TnN-9cT2X9JlR1iS16K-2qfl4pr-iWS7dn/pubhtml?widget=true&amp;headers=false"
    width="650"
    height="400">
</iframe>

## Download formatted data

You can download the data used for this figure from [here](https://lukasz-migas.com/assets/post-22-12-2018-ccs-compendium/ccs_compendium.txt.zip).
