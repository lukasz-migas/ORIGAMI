//=====================================
//  Demonstration of two alternating settings 
//=====================================
public override void main()
{
  connect("epc");
  send_cmd("initPropertyArraysV");//clears old property banks
  //add properties to banks
  //send_cmd("addPropV,0,CAPILLARY_VOLTAGE_SETTING,1.5,false");
  //send_cmd("addPropV,0,CAMERA_LED_OFF_COMMAND,1,true");
  //send_cmd("addPropV,1,CAPILLARY_VOLTAGE_SETTING,2.5,false");
  //send_cmd("addPropV,1,CAMERA_LED_ON_COMMAND,1,true");
  //use false for settings and true for commands, 
  //value for commands can be set to anything as they are ignored.
  
  send_cmd("enableSyncWriteV");//initialises system to allow the banks to be used

  //send_cmd("setSwitchCountV,0,4"); //bank 0 is used for 4 scans
  //send_cmd("setSwitchCountV,1,1"); //bank 1 is used for 1 scan
  
  start_function("WrensStartScan","writePropertyBankV");//start the banks running
  //wait(20000);//runs for 20 seconds
  stop_function("WrensStartScan","writePropertyBankV");//stops the banks running
}