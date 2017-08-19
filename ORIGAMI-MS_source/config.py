# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#    Copyright (C) 2017 Lukasz G. Migas <lukasz.migas@manchester.ac.uk>

#    This program is free software. Feel free to redistribute it and/or 
#    modify it under the condition you cite and credit the authors whenever 
#    appropriate. 
#    The program is distributed in the hope that it will be useful but is 
#    provided WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE
# -------------------------------------------------------------------------

from toolbox import str2num, str2int
import os.path


class config():
    """
    Configuration file that shares data between modules
    """
    def __init__(self):
        self.iPolarity = None
        self.iActivationZone = None
        self.iActivationMode = None
        self.iSPV = None
        self.iScanTime = None
        self.iStartVoltage = None
        self.iEndVoltage = None
        self.iStepVoltage = None
        self.iExponentPerct = None
        self.iExponentIncre = None
        self.iBoltzmann = None
        
        self.CVsList = None
        self.SPVsList = None
        
        self.CSVFilePath = None
        self.startTime = None
        
        self.wrensRunnerPath = "C:/Program Files (x86)/Wrens/Bin/ScriptRunnerLight.exe"
        self.wrensLinearName = "CIU_LINEAR.dll"
        self.wrensLinearPath = "".join(['"',self.wrensRunnerPath,'" ',self.wrensLinearName,' "'])
        self.wrensExponentName = "CIU_EXPONENT.dll"
        self.wrensExponentPath = "".join(['"',self.wrensRunnerPath,'" ',self.wrensExponentName,' "'])
        self.wrensBoltzmannName = "CIU_FITTED.dll"
        self.wrensBoltzmannPath = "".join(['"',self.wrensRunnerPath,'" ',self.wrensBoltzmannName,' "'])
        self.wrensUserDefinedName = "CIU_LIST.dll"
        self.wrensUserDefinedPath = "".join(['"',self.wrensRunnerPath,'" ',self.wrensUserDefinedName,' "'])
        self.wrensResetName = "CIU_RESET.dll"
        self.wrensResetPath = "".join(['"',self.wrensRunnerPath,'" ',self.wrensResetName,' "'])
        
        


    def importConfig(self, fileName=None, e=None):
        """
        Imports config from a file
        """
        if not os.path.isfile(fileName): 
            print('not a path')
            return
        f = open(fileName, 'r')
        for line in f:
            if len(line.split()) > 1:
                if line.startswith("iPolarity "):
                    self.iPolarity = str(line.split()[1])
                if line.startswith("iActivationZone "):
                    self.iActivationZone = str(line.split()[1])
                if line.startswith("iActivationMode "):
                    self.iActivationMode = str(line.split()[1])
                if line.startswith("iSPV "):
                    self.iSPV = str2int(line.split()[1])
                if line.startswith("iScanTime "):
                    self.iScanTime = str2int(line.split()[1])
                if line.startswith("iStartVoltage "):
                    self.iStartVoltage = str2num(line.split()[1])
                if line.startswith("iEndVoltage "):
                    self.iEndVoltage = str2num(line.split()[1])
                if line.startswith("iStepVoltage "):
                    self.iStepVoltage = str2num(line.split()[1])
                if line.startswith("iExponentPerct "):
                    self.iExponentPerct = str2num(line.split()[1])  
                if line.startswith("iExponentIncre "):
                    self.iExponentIncre = str2num(line.split()[1])
                if line.startswith("iBoltzmann "):
                    self.iBoltzmann = str2num(line.split()[1])
                
#                 if line.startswith("wrensPath "):
#                     self.wrensPath = str(line.split(" ")[1::])
#                     print(self.wrensPath, os.path.isabs(self.wrensPath))  
                
                if line.startswith("wrensLinearName "):
                    self.wrensLinearName = str(line.split()[1])
                if line.startswith("wrensExponentName "):
                    self.wrensExponentName = str(line.split()[1])   
                if line.startswith("wrensBoltzmannName "):
                    self.wrensBoltzmannName = str(line.split()[1])  
                if line.startswith("wrensUserDefinedName "):
                    self.wrensUserDefinedName = str(line.split()[1])  
                if line.startswith("wrensResetName "):
                    self.wrensResetName = str(line.split()[1])  
                    
        self.wrensLinearPath = "".join(['"',self.wrensRunnerPath,'" ',self.wrensLinearName,' "'])
        self.wrensExponentPath = "".join(['"',self.wrensRunnerPath,'" ',self.wrensExponentName,' "'])
        self.wrensBoltzmannPath = "".join(['"',self.wrensRunnerPath,'" ',self.wrensBoltzmannName,' "'])
        self.wrensUserDefinedPath = "".join(['"',self.wrensRunnerPath,'" ',self.wrensUserDefinedName,' "'])
        self.wrensResetPath = "".join(['"',self.wrensRunnerPath,'" ',self.wrensResetName,' "'])
                    
                    
    def exportConfig(self, fileName=None, e=None):
        """
        Exports config to a file
        """
        
        print(''.join(["Exporting configuration file ", fileName]))
        f = open(fileName, 'w+')
        f.write('General config scheme\n')
        f.write('Property<space>Value\n')
        f.write('Please DO NOT change the property names\n')
        f.write('\n')    
        f.write('# === GENERAL SETTINGS === #\n')
        f.write("iPolarity " + str(self.iPolarity)+ "\n")
        f.write("iActivationZone " + str(self.iActivationZone)+ "\n")
        f.write("iActivationMode " + str(self.iActivationMode)+ "\n")
        f.write("iSPV " + str(self.iSPV)+ "\n")
        f.write("iScanTime " + str(self.iScanTime)+ "\n")
        f.write("iStartVoltage " + str(self.iStartVoltage)+ "\n")
        f.write("iEndVoltage " + str(self.iEndVoltage)+ "\n")
        f.write("iStepVoltage " + str(self.iStepVoltage)+ "\n")
        f.write("iExponentPerct " + str(self.iExponentPerct)+ "\n")
        f.write("iExponentIncre " + str(self.iExponentIncre)+ "\n")
        f.write("iBoltzmann " + str(self.iBoltzmann)+ "\n")
        f.write('# === PATHS === #\n')
        f.write("wrensLinearName " + str(self.wrensLinearName)+ "\n")
        f.write("wrensExponentName " + str(self.wrensExponentName)+ "\n")     
        f.write("wrensBoltzmannName " + str(self.wrensBoltzmannName)+ "\n")
        f.write("wrensUserDefinedName " + str(self.wrensUserDefinedName)+ "\n")
        f.write("wrensResetName " + str(self.wrensResetName)+ "\n")
        f.close()
                    
                    
    def exportOrigamiConfig(self, fileName=None, e=None):
        """
        Exports config to a file
        """
        
        print(''.join(["Exporting ORIGAMI configuration file ", fileName]))
        
        f = open(fileName, 'w+')
        f.write("method " + str(self.iActivationMode)+ "\n")
        f.write("spv " + str(self.iSPV)+ "\n")
        f.write("start " + str(self.iStartVoltage)+ "\n")
        f.write("end " + str(self.iEndVoltage)+ "\n")
        f.write("step " + str(self.iStepVoltage)+ "\n")
        f.write("expIncrement " + str(self.iExponentIncre)+ "\n")
        f.write("expPercentage " + str(self.iExponentPerct)+ "\n")
        f.write("dx " + str(self.iBoltzmann)+ "\n")
        f.write("SPVsList " + str(self.SPVsList)+ "\n")
        f.write("CVsList " + str(self.CVsList)+ "\n")
        f.close()
                    
                    
                    
                    
                    
                    