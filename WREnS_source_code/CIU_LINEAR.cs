//============================================================
// Collision Induced Unfolding (CIU) script that uses PROPERTY BANKS to
// ramp the Collision Energy in Trap or Cone to slowly unfold a protein.
// The script can go from 0-200V in any divisible increments.
//============================================================


// CONSTANTS (don't change...)
int waitTime = 100; // don't change 
int test = 1;
int multiplier = 1000; // it should be 1000, used for testing
int splitter = 20; // 
int startStopCounter = 3; // determines how many scans the start/stop should operate for
/// ******* \\\


public override void main()
{
   string[] userSettings=Argument.Split(',');
  
  string disclaimerText = 
    @"    
        ----------- MESSAGE FROM THE AUTHORS-----------
    This program is free software. Feel free to redistribute it and/or modify it 
    under the condition you cite and credit the authors whenever appropriate. 
    The program is distributed in the hope that it will be useful but is provided 
    WITHOUT ANY WARRANTY! 
                          
    If you encounter any problems, have questions or would like to send some
    love/hate, please send to Lukasz G. Migas (lukasz.migas@manchester.ac.uk)
    ----------- MESSAGE FROM THE AUTHORS -----------
    ";
                          
  print(disclaimerText);
  string parametersInfo = 
    @"    Available parameters:
    Activation type: 'TRAP' or 'CONE' [string]
    Ion polarity: 'POSITIVE' or 'NEGATIVE' [string]
    Scans per Voltage: [integer]
    Scan time: [float]
    Start voltage: [float]
    End voltage: [float]
    Step voltage: [float]
    Total acquisition time: [float]
    ";
  
  print(parametersInfo);
 
  
  // Split the text into parts 
  print("Your parameters:");
  string activationType=userSettings[0]; print("Activation Type:"+activationType);
  string ionPolarity=userSettings[1]; print("Ion Polarity:"+ionPolarity);
  string scanPerVoltageSt=userSettings[2]; print("Scans per Voltage:"+scanPerVoltageSt);
  string scantimeSt=userSettings[3]; print("Scan Time (s):"+scantimeSt);
  string startVoltageSt=userSettings[4]; print("Start Voltage (V):"+startVoltageSt);
  string endVoltageSt=userSettings[5]; print("End Voltage (V):"+endVoltageSt);
  string stepVoltageSt=userSettings[6]; print("Increment Voltage (V):"+stepVoltageSt);
  string totalAcqTimeSt=userSettings[7]; print("Total acquisition time (min):"+totalAcqTimeSt);
  
  // Extract the values and convert them to appropriate format
  int scanPerVoltage = Int32.Parse(scanPerVoltageSt); 
  int scantime = Int32.Parse(scantimeSt); 
  double startVoltage = Double.Parse(startVoltageSt); 
  double endVoltage = Double.Parse(endVoltageSt); 
  double stepVoltage = Double.Parse(stepVoltageSt); 
  double totalAcqTime = Double.Parse(totalAcqTimeSt); 
  
  if ((scantime < 1) || (scantime > 5))
  {
    print("Scan time has to be an integer between 1-5 seconds!");
    return;
  }

  int scanPerVoltageSave = scanPerVoltage;
  // Pre-calculate approximate time of execution
  double numberOfScans = (totalAcqTime*60)/scantime;
     


  print("------------------------------------------");
  print("Minimum (approx.) time of acqusition: "+Math.Round(totalAcqTime,2).ToString()+" minutes");
  print("Number of scans: "+Math.Round(numberOfScans,0).ToString());

  print("");
  print("----------- JUST IN CASE -----------"); 
  print("If you encounter problems, please run the StopWREnS script provided and Reinitilise MassLynx");
  print("----------- JUST IN CASE -----------");
  print("");
  
  // Blanks
  string wrensCMD;
  string startCMD;
  string resetCMD;
  string getValueFrom;

  if (activationType == "TRAP" || activationType == "trap")
  {
    if (ionPolarity == "POSITIVE")
    {
      wrensCMD = "addPropV,0,SOURCE_BIAS_SETTING,";
      startCMD = "addPropV,0,SOURCE_BIAS_SETTING,-20,false";
      resetCMD = "addPropV,0,SOURCE_BIAS_SETTING,4,false";
      getValueFrom = "SOURCE_BIAS_SETTING";
    }
    else if (ionPolarity == "NEGATIVE")
    {
      wrensCMD = "addPropV,0,SOURCE_BIAS_SETTING, -";
      startCMD = "addPropV,0,SOURCE_BIAS_SETTING,20,false";
      resetCMD = "addPropV,0,SOURCE_BIAS_SETTING,-4,false";
      getValueFrom = "SOURCE_BIAS_SETTING";
    }
    else
    {
      print("Make sure you either type in POSITIVE or NEGATIVE");
      wrensCMD = ""; startCMD = ""; resetCMD = ""; getValueFrom = "";
      return;
    }
  }
  else if (activationType == "CONE" || activationType == "cone")
  {
    if (ionPolarity == "POSITIVE")
    {
      wrensCMD = "addPropV,0,SAMPLE_CONE_VOLTAGE_SETTING,";
      startCMD = "addPropV,0,SAMPLE_CONE_VOLTAGE_SETTING,-20,false"; 
      resetCMD = "addPropV,0,SAMPLE_CONE_VOLTAGE_SETTING,30,false";
      getValueFrom = "SAMPLE_CONE_VOLTAGE_SETTING";
    }
    else if (ionPolarity == "NEGATIVE")
    {
      wrensCMD = "addPropV,0,SAMPLE_CONE_VOLTAGE_SETTING, -";
      startCMD = "addPropV,0,SAMPLE_CONE_VOLTAGE_SETTING,20,false"; 
      resetCMD = "addPropV,0,SAMPLE_CONE_VOLTAGE_SETTING,-30,false";
      getValueFrom = "SAMPLE_CONE_VOLTAGE_SETTING";
    }
    else
    {
      print("Make sure you either type in POSITIVE or NEGATIVE");
      wrensCMD = ""; startCMD = ""; resetCMD = ""; getValueFrom = "";
      return;
    }
  }
  else
  {
    print("Make sure you either type in TRAP or CONE");
    wrensCMD = "";  startCMD = ""; resetCMD = ""; getValueFrom = "";
    return;
  }

 if(connect("epc"))
 //if (test == 1)
 {
  {
    print("Ramping Collision Voltage in "+activationType+" in "+ionPolarity+" ionisation mode.");
    // Start data capture
    send_cmd("enableSyncWriteV");//initialises system to allow the banks to be used
    send_cmd("initPropertyArraysV");
    send_cmd(startCMD); // Stops flow of ions
    send_cmd("setSwitchCountV,0,"+startStopCounter.ToString()+ "");
    wait(multiplier);
    start_function("WrensStartScan","writePropertyBankV");
    wait(startStopCounter*multiplier);
    print("Starting ramping Collision Voltage");
    ///  START OF COLLIISON VOLTAGE RAMP ////
    // Start incrementing CE voltage
    for (double ce=startVoltage; ce<=endVoltage; ce+=stepVoltage)
    {
      // For some reason WREnS has a built-in timeout, so when the SPV is too large (above 23) then it will 
      // give an error. This while function prevents that from happening by restricting SPV to maximum
      // of the splitter. 
      while (scanPerVoltage > splitter)
      {
        int difference = scanPerVoltage-splitter;
        //print("Current trap CE (V): "+(get_setting(getValueFrom).ToString())+" Set CE: "+ce.ToString()+" SPV: "+splitter.ToString()+" remaining SPVs: "+difference.ToString());
        send_cmd("initPropertyArraysV");
        send_cmd(wrensCMD+ce.ToString()+",false");
        send_cmd("setSwitchCountV,0,"+splitter.ToString()+ "");
        wait(splitter*scantime*multiplier);
        print("Current trap CE (V): "+(get_setting(getValueFrom).ToString())+" Set CE: "+ce.ToString()+" SPV: "+splitter.ToString());
        scanPerVoltage = scanPerVoltage-splitter;
      }
      // Initilises property banks and clears previous ones
      //print("Current trap CE (V): "+(get_setting(getValueFrom).ToString())+" Set CE: "+ce.ToString()+" SPV: "+scanPerVoltage.ToString());
      send_cmd("initPropertyArraysV");
      send_cmd(wrensCMD+ce.ToString()+",false");
      send_cmd("setSwitchCountV,0,"+scanPerVoltage.ToString()+ "");
      wait(scanPerVoltage*scantime*multiplier);
      print("Current trap CE (V): "+(get_setting(getValueFrom).ToString())+" Set CE: "+ce.ToString()+" SPV: "+scanPerVoltage.ToString());
      scanPerVoltage = scanPerVoltageSave;
    }
    // Acquire last voltage
    while (scanPerVoltage > splitter)
    {
      int difference = scanPerVoltage-splitter;
      send_cmd("initPropertyArraysV");
      send_cmd(wrensCMD+endVoltage.ToString()+",false");
      send_cmd("setSwitchCountV,0,"+splitter.ToString()+ "");
      wait(scanPerVoltage*scantime*multiplier);
      scanPerVoltage = scanPerVoltage-splitter;
    }
    send_cmd("initPropertyArraysV");
    send_cmd(wrensCMD+endVoltage.ToString()+",false");
    send_cmd("setSwitchCountV,0,"+scanPerVoltage.ToString()+ "");
    wait(scanPerVoltage*scantime*multiplier);
    ///  END OF COLLIISON VOLTAGE RAMP ////

    // Reset the voltage using the startCMD
    send_cmd("initPropertyArraysV");
    send_cmd(startCMD); // Stops flow of ions
    send_cmd("setSwitchCountV,0,"+startStopCounter.ToString()+ "");
    wait(scantime*multiplier*startStopCounter);
    // Stop ion flow
    send_cmd("initPropertyArraysV");
    send_cmd(resetCMD); // Resets voltages
    send_cmd("setSwitchCountV,0,"+startStopCounter.ToString()+ "");
    wait(startStopCounter*scantime*multiplier);
    print("Final Collision Energy: "+(get_setting(getValueFrom).ToString()));
    disable_data_capture();
    send_cmd("initPropertyArraysV");//clears old property banks
    stop_function("WrensStartScan","writePropertyBankV");
    print("Finished ramping Collision Voltage."); 
  }
 }
 {
   print("Could not connect to the EPC");
 }
  print("======================================");
  print("Make sure you switch off the WREnS script before stopping your acqusition in MassLynx");
  print("If you encounter problems, please run the StopWREnS script provided and Reinitilise MassLynx");
  print("Thanks for using this script. Happy analysing!");
  print("======================================");
}