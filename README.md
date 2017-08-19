## ORIGAMI<sup>MS</sup>
Software suite for analysis of activated ion mobility mass spectrometry data

ORIGAMI<sup>MS</sup> (brief) User Guide:

ORIGAMI<sup>MS</sup> is a pretty straightforward software that utilises Waters Research Enabled (WREnS) and MassLynx to speed-up acquisition of typically cumbersome CIU/aIM-MS datasets. ORIGAMI<sup>MS</sup> operates on the principle of overriding collision voltage in either Trap or Cone of the instrument during the acquisition period. 

#### Pre-requisites:
---
<b> 1. A Waters Synapt G2/G2S/G2Si.</b><p>
<b> 2. Installed and running WREnS (in case you need assistance in installing it, please let me know and I can try to assist)</b><p>
 Thats it! You just have to make sure that WREnS is running on your machine. Usually can be done by using the `telnet epc` command.

#### How to install it:
---
The setup is rather simple. ORIGAMI<sup>MS</sup> is provided in a pre-compiled form (or as a source code that can be compiled locally). The main thing to remember is to make sure ORIGAMI<sup>MS</sup> knows where WREnS code is located and what are the names of the acquisition scripts. These are provided in two forms:
* Pre-compiled dll's - these have been compiled in WREnS and *should* work on any machine with WREnS. I would recommend compiling it from scratch using the WREnS compiler.
* C# source code  - uncompiled source code that can be inserted into an *appropriately labelled* script and compiled in the WREnS compiler. 

Before compling code, please copy each of the .cs scripts into the WREnS folder, typically: <p>
<b>C:\Users\ `USER_NAME_HERE`\Documents\Wrens\Scripts</b><p>
Once these were copied, start-up WREnS (with Administrator permissions) and load-up the WREnS scripts one-by-one. Press Build/Compile and watch out for the 'Created  : C:\Program Files (x86)\Wrens\Bin\ `YOUR_SCRIPT_NAME.dll`' message in the Log window. Repeat this for each of the 5 scripts. Please do not change the names of the scripts, as it you will just make more work for yourself later on. The source files can be found in *WREnS_source_code* folder on GitHub.

#### How to use it (GUI):
---
<b>1. Start ORIGAMI<sup>MS</sup> GUI.</b><p>
<b>2. Fill-in appropriate fields.</b><p>

* Linear mode: Ion polarity, Activation Zone, Scans per Voltage, Scan Time, Start Voltage, End Voltage and Step Voltage

* Exponential mode: All above + Exponential (%) and Exponential increment

* Boltzmann mode: All above (from Linear) + Boltzmann Offset

* User-defined: Scan time + Load list of SPV/CVs (example of one attached in Additional Files/aIM-MS_list_4-200-2V.csv)

<b>3. Compute the acquisition parameters and generate acquisition code. (Press Calculate in the GUI)</b><p>
<b>4. Start acquisition in MassLynx window ensuring the scan time is the same as what you inserted in ORIGAMI<sup>MS</sup>!.</b><p>
<b>5. Wait a second or two and press 'Start' in the GUI.</b><p>
<b>6. Wait for the collision voltage ramp to complete. In case of any issues (loss of spray, incorrect IM-MS settings or else) just press 'Stop' in the GUI.</b><p>
<b>7. Analyse your semi-indepenendly acquired dataset in ORIGAMI<sup>ANALYSE</sup>! :smile:</b><p>
