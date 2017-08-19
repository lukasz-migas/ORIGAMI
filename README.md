# ORIGAMI<sup>MS</sup>
Software suite for analysis of activated ion mobility mass spectrometry data

ORIGAMI<sup>MS</sup> (brief) User Guide:

ORIGAMI<sup>MS</sup> is a pretty straightforward software that utilises Waters Research Enabled (WREnS) and MassLynx to speed-up acquisition of typically cumbersome CIU/aIM-MS datasets. ORIGAMI<sup>MS</sup> operates on the principle of overriding collision voltage in either Trap or Cone of the instrument during the acquisition period. 


How to use it (GUI):
<H4>1. Start ORIGAMI<sup>MS</sup> GUI.
<H4>2. Fill-in appropriate fields.

<b>Linear mode</b>: Ion polarity, Activation Zone, Scans per Voltage, Scan Time, Start Voltage, End Voltage and Step Voltage

<b>Exponential mode</b>: All above + Exponential (%) and Exponential increment

<b>Boltzmann mode</b>: All above (from Linear) + Boltzmann Offset

<b>User-defined</b>: Scan time + Load list of SPV/CVs (example of one attached in Additional Files/aIM-MS_list_4-200-2V.csv)

<H4>3. Compute the acquisition parameters and generate acquisition code. (Press Calculate in the GUI)
<H4>4. Start acquisition in MassLynx window ensuring the scan time is the same as what you inserted in ORIGAMI<sup>MS</sup>!.
<H4>5. Wait a second or two and press 'Start' in the GUI.
<H4>6. Wait for the collision voltage ramp to complete. In case of any issues (loss of spray, incorrect IM-MS settings or else) just press 'Stop' in the GUI.
<H4>7. Analyse your semi-indepenendly acquired dataset in ORIGAMI<sup>ANALYSE</sup>! :smile:
