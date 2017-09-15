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
import wx
from wx.lib.embeddedimage import PyEmbeddedImage


class config():
    """
    Configuration file that shares data between modules
    """
    def __init__(self):
        
        self.version = "1.0.1"
        self.links = {'home' : 'https://www.click2go.umip.com/i/s_w/ORIGAMI.html',
                      'github' : 'https://github.com/lukasz-migas/ORIGAMI',
                      'cite' : 'https://doi.org/10.1016/j.ijms.2017.08.014',
                      'newVersion' : 'https://github.com/lukasz-migas/ORIGAMI/releases'}

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
        self.wrensCMD = None
        
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
        # Global setting
        f.write("method " + str(self.iActivationMode)+ "\n")
        
        # Linear/Exponential/Boltzmann methods only
        if (self.iActivationMode == 'Linear' or
            self.iActivationMode == 'Exponential' or
            self.iActivationMode == 'Boltzmann'):
            f.write("spv " + str(self.iSPV)+ "\n")
            f.write("start " + str(self.iStartVoltage)+ "\n")
            f.write("end " + str(self.iEndVoltage)+ "\n")
            f.write("step " + str(self.iStepVoltage)+ "\n")
        else:
            f.write("spv " + "None"+ "\n")
            f.write("start " + "None"+ "\n")
            f.write("end " + "None"+ "\n")
            f.write("step " + "None"+ "\n")
        
        # Exponential method only
        if self.iActivationMode == 'Exponential':
            f.write("expIncrement " + str(self.iExponentIncre)+ "\n")
            f.write("expPercentage " + str(self.iExponentPerct)+ "\n")
        else:
            f.write("expIncrement " + "None"+ "\n")
            f.write("expPercentage " + "None"+ "\n")            
            
        # Boltzman method only
        if self.iActivationMode == 'Boltzmann':
            f.write("dx " + str(self.iBoltzmann)+ "\n")
        else:
            f.write("dx " + "None"+ "\n")
        
        # User-specified method only
        if self.iActivationMode == 'User-defined':
            f.write("SPVsList " + str(self.SPVsList)+ "\n")
            f.write("CVsList " + str(self.CVsList)+ "\n")
        else:
            f.write("SPVsList " + "None"+ "\n")
            f.write("CVsList " + "None"+ "\n")
            
        f.write("command " + str(self.wrensCMD)+ "\n")
            
        # Close file
        f.close()
                    
                    
class IconContainer:
    def __init__(self):
        
        self.icons()
        
    def icons(self):
        origamiLogo = PyEmbeddedImage(
            "iVBORw0KGgoAAAANSUhEUgAAAcoAAADgCAIAAAAMvrFvAAAABGdBTUEAALGPC/xhBQAAAAlw"
            "SFlzAAAOwwAADsMBx2+oZAAAN6BJREFUeF7tnQd8FGX+/7M7szW9Z5eiIF1ALFjwVOAnIiDH"
            "iR0Lilf+v5/e37Ocx+md/q/89Dz15annnVc8xX6CnhSRIkqTIkWKkEAIBNI2CWmbTXaTbf/P"
            "M8+TJSwpu8nO7iZ83xmGeZ4pzzMzz7z3O7Mzs5r6+voEgiAIItJoxf8EQRBERCG9EgRBqALp"
            "lSAIQhVIrwRBEKpAeiUIglAF0itBEIQqkF4JgiBUgfRKEAShCqRXgiAIVSC9EjGgqqpKDBFE"
            "/4X0SkSbtWvXvv3227t3766urhZZBNEfoXcOEFGluLh43rx5+fn5WVlZN998M4bz8vKys7PF"
            "aILoR5BeiWhzww03bNmyxe/3Y9hqtd5xxx233HJLenp6Tk4On4Ag+gfSwoULxSBBqE9VVZXb"
            "7V63bh3Xq8PRtG3bViQlScrNzcGoxMREPiVB9HUoeiWizb59+2688caamprx48cjYt28ebPL"
            "5YJeR44c+eMf/3jatGl6vZ4uFxD9AIpeiWiDuDU/P7+wsPCCCy545ZVXLr/88rq6utLSUpvN"
            "9sUXX2zZsiVdISUlRcxAEH0T0isRbZqbmzUazZo1a6qqqubOnXveeefNmjXrsssuw4kUJFtW"
            "VoZRu3fvTkxMTE1NdTqddLmA6KOQXoloA12Czz//vLq6KiMj4+KLL0am1Wq9/vrrL7rooj17"
            "9tTU1MCzq1atOnDgAPIxjclk4vMSRB+C9ErEAJ/PV1JSsmfPXpvNdvvtt2u17P5r9AcNGvSD"
            "H/wgLy/vxIkTkOzRo0dh4cLCQuTAsGazmc9OEH0C0isRAyBKyHTp0qV2ux0RK6wqRiQkGAyG"
            "Cy644Pvf/z6UCgVDsvn5+StWrCgvL8/NzbFaB4jpCCLuIb0SsQEaXb9+fUVFRVNT0+zZs/l9"
            "WgEwdsKECXPmzMnJyTl+/HhVVdX+/fuXL1+OqNZisWg0GrogS8Q/pFciNrhcLoSuW7dubWxs"
            "nD59enJyshjRBoSr1+sRyUKyubm5u3btwpR79+5dtmzZ0KFDx44dK6YjiHiF3jlAxAaEpVOm"
            "TElKSsLp/549exCQihGnA8nCvHfddRdCV1gYyZMnTy5duhR9MQVBxCukVyJmTJo0acKECV6v"
            "d9GiRS0tLSK3E6xWKxTMryEcPnyYHoch4h/SKxEzqqqqEJBKknTgwIFt27Z1FsByEORu3boV"
            "A5istLS0pKSE5xNE3EJ6JWJGTk7ONddck5GR0draun79+qBvt4J47bXX7Ha7wWCQZRmh7jff"
            "fEPXB4g4h/RKxJLc3NxJkyZhYNOmTU1NTTzzTAoKCj799FOfz3frrbeOGTMGIka0CymL0QQR"
            "l5BeiViCAPaGG2ZLkoTz/T179ojc03G5XK+++mpzc/PIkSMeffTRKVOmaDSaAwcONDY2iiki"
            "RJWCSBBEryG9EjHmoosuHDRoECLTpUuXwrMitx2FhYUbNmzAqPnz701MTBw7dqxer6+rq/v2"
            "228jZcOTJ08WFRWtWrXqq6++KisrE7kE0TtIr0SMSUtLmzp1KgY6+3mYt99+2+v1Dh06dObM"
            "mbDwuHHjMjMz3W73zp07xRQ9BXauqKiAu1988cWbbrrpkUce+elPf/rKK6+Ul5eLKQiiF5Be"
            "iRgDV06bNs1oNEJqy5Yt4+8f4GjYi7VWf/755xiYP38+f1IL00+cOBE527dvz+nRDxzwmHf/"
            "/v2LFy++//77582b9/rrrxcXF3sU3njjjeeff54MS/Qe0isRexCQDhs2DCEqztBFlkJra+ua"
            "NWsRqA4fPnzGjBkIXZGJ/oQJE6BXCJHfqhU6J0+e5HP96Ec/uvnmm3/1q19t27a1ubmZ37SA"
            "ZSKUxvIXLVr0+OOPFxUd4XMRRM8gvRKxx2Aw4MQfdlu3bl37G1p37Njx2WefYeDuu+9OSkri"
            "mVDhZZddZjabHQ7Hd999xzO7ALFqTU0NBnbv3v2Xv/wFsSrciri1srISTr/88isQq2IApWOx"
            "S5cuxQQYXrly5UMP/QwRLl8IQfQA0isRe7Kzs6dOnZqcnFxXV7dx40bYDZn8lVqIJUeOHAH5"
            "tr8rFjYcMWIEcr7++uva2lqR2xEIV2HhtWvXzlX405/+lJ+fjzD5/PPP/+EPf7h48UdvvfXW"
            "6NGjoWCtVgOJ5+Tk/PKXv7zzzjsx7+bNmx944AGEupH6Ao042yC9EnHB4MGDL7jgAsgUSoU3"
            "4VbEratXr5Yk7X33LTjz/Vj8+sC+ffs61Gt1dXVFRcWXX3757LPPzpkzB5bEsN1uh8e///3v"
            "//GPf3zvvfd+8YtfmExmlPWvf/2rsbFx8OBzrrjiCswryzJG3XXXXZIkIXp98MEHi4qKyLBE"
            "DyC9EnEBpDZr1iwY88iRI4WFhc3NzX//+99dLtfw4cOvv/769qErZ/z48cg88+nYmpoaOPed"
            "d95BKApFvvHGG5gAVr300kuffPLJ5cuXP/fcc7NnzzaZTPxK7qFDhyBx2Py+++4LvLULlVm4"
            "cCFmRz7cev/99+/YsYMMS4QLvZCQiAsQnxoMhhUrVjQ01MOlLS0tH374IULXn/3sYQSqZ+o1"
            "PT192bJlOPG3Wq04029qakIYu2bNmtdee+3FF19ctWoVoldMlpWVtWDBgt/85jfz58+HkVEE"
            "v/LAwWIx8d69e4cNG/bEE0/odDoxQrk0MWnSJCwfsnY4GtevX4/4GksQowkiBEivRLyAk/GD"
            "Bw8WFBQUFxdv27YNAeyIESNwnt7eegEQYK5cuRKxKjw4ZswYnOw/88wz6B84cACqTUlJgQp/"
            "+ctfPvroo5MnTzab2UUAMWc7YM8//OEPXq/3Zz/72UUXXRQ0DZZ8xRVX2O32/fv3ozIbN26U"
            "Zemcc84NfMlGEF1DeiXiBcgORsOpOkJXp9MJ2T3yyCMIXcXo04Fzcba+ffv28vLyTz75ZMuW"
            "LSdPnjQajbDktGnTfve73yFcPe+88xCudihWgDB2yZIlcDRE/PTTT/NrBUGgPldeeSU3rNvt"
            "3rJlK3KGDx9+5su/CeJMSK9EvJCoAN9BZ5Dd6NGj0TgRpYrRpwNppqenf/rpp62trZgY4er0"
            "6dN///vf/+QnP7nqqqtSU1PbXwTokMOHDyO29Xg8mKWL3z6ATwNXCfijYrA/4mWUKKYgiE6g"
            "r7aIOGLo0KEIP6FLSZLuu+++rn8aNiMjA+fp0N+MGTNWrVr13HPPwcjQbmfhahBvvvkmTvkR"
            "4d54440orgsQAj/xxBMIhzHs9XrfeOMNRLtBT0AQxJlo6K3vRPyQn59/2223njhRcv7557//"
            "/vs42RcjOgJiffjhh1esWHHvvfdCfyFalVNQUHD33XcjJj3nnHNwsh/KvMrFgS38LYgoeurU"
            "qS+88MK5557LxxLEmZBeiXihqqrqn//85/PPPw95wVyzZs3q2nqY7G9/+xumHDRokHKHbAdv"
            "2+oQRMf33HMPTvP58vllhO6GWS+QD/R6/UcffXT11VcjhyA6hPRKxAsHDx689dZbS0tLJ0yY"
            "sGjRoq5DV87evXtvu+225OTkd955Z9SoUSK3Ow4dOjRv3rympibErWlpaSI3HODZcePGPfbY"
            "Y1arVWQRxBmQXom4AKHr66+//tJLLyEIRUAa9BRsZ0CRMHJRUdGTTz6JgDSUWRB4Lly48JNP"
            "PrFYLB988EFeXp4YcQZYWBdfj3UxI0Fw6KstIi6AXnGuDfeNHTt26tSpoYgSJCUlXXLJJZh4"
            "9erVIc6Sn5+PiVHQ3LlzEXvCkp1hsYiBDhGLI4jOIb0SsQduXbx4cXl5uVarXbBgQSiXBQJM"
            "nDgR/QMHDoT4Vf5bb72FmBd+RNjbs9fFEkSIkF6J2GOz2RC6+ny+6dOnT5s2LcQ4FGDKiy66"
            "KD09vbW19cSJE4hJxYhOKCgoWLt2LSR+++23WywWkUsQ6kB6JWIMQtcPP/wAhjWbzffffz/c"
            "J0aERm5u7pgxYzwez5dfftn1zQP8lwgQulqt1ltuuYVCV0JtSK9EjCkrK/v4408QhyJuPf/8"
            "80VuyOj1+nHjxmHg4MGDXf927Lp161auXIkIF6Frdna2yCUI1SC9ErGEf6NVWVmZmJh47733"
            "itxw8Pl8//Vf/2U0Go8dO3b8+HGRewaw6ieffIKJBw0adPPNN5NeiShAeiViSWlpKayn0SRA"
            "kTjHF7nhgLA3Ly/PZDLhrP+bb77p7NpCQUHBjh07MPEdd9yRmZkpcglCTUivRCz54IMPqqur"
            "ExOT7rvvvm6/mOoM6PXSSy/FwLZt27xeL88M4l//+hf8O3jw4Llz51LoSkQH0isRM3bu3Pnp"
            "p//BwJQpU/jbWHh+DxgxYgTsXFRU5PF4RFYbyF+1atVnn32GwPbOO+elp6eLEQShMqRXIma8"
            "//77NTW1OK9fsGBBj0NX4PP5Jk+erNPpSktLoWyR2wbGvvXWW263G6HrD35wI4WuRNQgvRKx"
            "Yfv27fyHYHt2w0AQY8aMGTZsGELX8vLyIFNv3bq1sLAQmffccw+FrkQ0Ib0SseHdd9+tqanh"
            "Nwz05rIAR5KkmTNnwqH81iuRm5Dgcrn+9Kc/NTU1nXfeeXPmzKHQlYgmpFciBmzZsmXFihUY"
            "uPbaa0ePHs0ze8nAgQO1Wu2ePXuOHTvGc5Bct27dgQMHMIDQlX5fgIgypFciBrz33nt1dXUI"
            "XXtzw0B7EP9eddVVGRkZzc3NmzZt4rdnOZ3ON9980+fzDRkyZPbs2RS6ElGG9EpEm6+//vqz"
            "zz7DAELXUaNG9f7KAEeSJP6LsEVFRdArrL1u3Rf5+fkYde+999LPuxLRh/RKRJt33nmnoaEh"
            "OTmplzcMBIFYePLkyRg4dOgQYliErv/85xsej2fEiBE33HADha5E9CG9ElEFZ+6rVq2CVa+7"
            "bnqkrrpyELdOmzZNp9NBr2VlZV98wUJXhLHz58+HecVEBBFFSK9E9LDZbG+//bbdbsdZPKwX"
            "qcsCHCxt+PDhAwYMaGpq2rhx48qVK30+H0LXGTNmUOhKxATSKxElqqqqEFeuXr0a1rvuuutG"
            "jhwpRkSOzMxMGBYDL7/8MsJkSZIWLFhAoSsRK0ivRJSAVRctWoTQNSmJvWFA5EYUFMF/SAYB"
            "rNvtHjVq1MyZMyl0JWIF6ZWIEgcPHly7di0Gpk+fjnN2nhlZNBpNbm4u+kCW5bvuuluv14tx"
            "BBF1SK9ENLDZbAhdGxsbk5OT1QhdJUmqqKhYsmTJs88+iyT0CoNff/10+kkCIobQD3EToVJV"
            "VQVtiUSY7Nu3b/78+Q6H45Zbbvnf//3fiHypxSvjdrs3b9788ccf79y5s6GhwefzQbVZWVk/"
            "//nP58yZgwE+MUFEH9IrERJw6/r160tKSkQ6HLRa7dq1a7du3ZqUlPTBBx/wb596Axbo8Xj2"
            "7t27cePGNWvWFBcX8/cQJiUlXnDBhJkzZ06ePLn3r4khiF5CeiW6B27Nz8/HSX1dXR0PPJXA"
            "UXPmcBfAiXPnzkXoKtI9AgtBHVasWAGxbt++3eVyoXSNRjt06NBp06bxGxIQvdI1ASIeIL0S"
            "3VNaWvrggw9u3LjB52MOheMmTZoUuOEJJ+kBt545XFlZuWfPHsyC0PX999/vWejKw9VDhw69"
            "++67u3btPH78hM/nQ2Z6evpVV101a9asiy++ODk5GcWRWIn4gfRKdANC1yVLljz11FPQ2ezZ"
            "s9etW2e32xEqPv/882azWUzUOTh5f+CBBzBw0003hRu6QtDg+PHjKHT58uUYcDgccCjKHTFi"
            "BKw6ffr0vLw8UioRn5BeiW7YtWvX/PnzEcDOmDHj1VdfxVn5o48+imYzdepUGLbrm/Zh5N/+"
            "9rfvvPMOQsuwrrpiRmh97969q1atQokoDp5FptVqnTJlyo033jhy5EidTkf3tBLxDOmV6IqK"
            "iopf/epXH3/8MQLGRYsWjR8/Ho57+eWX//rXvyKKhGH/+Mc/dmHY4uLi2267DW0sxBsG4FCP"
            "x7N///5NmzZ9+umnKN3r9SIzKSlp4sSJiJ2vvPLKtLQ0CleJPgHplegUxI84K3/44YdbWlrm"
            "zp37zDPP8HwYEFZdvHhxc3MzDPvCCy90aFhM9thjj33++eeQ44cfftht6Hry5MnVq1d/9NFH"
            "kDJKRI4sy0OGDJk5cyYC53PPPQfxK4mV6EOQXolOKSwsvPvuuwsKCgYNGrRkyRKEjWKE8v6U"
            "r7/++vHHH6+rq7vmmmtefPHFMw1bVFR06623OhyOm2++ubOrruzaqkZz4MCBN998c8OGDXa7"
            "3efzIQcanTRpEpw+btw4BM5kVaIvQnolOgahK8LSf/zjH1qt9u9///v3vvc9ng/3IQeRKbx5"
            "//337927F5nXXntt0FUCTPbrX//63//+d4dXXTEWSygrK0NUu2fPnkOHDjU1NfHvrMaOHTt7"
            "9uyrr77aYrFgShIr0XchvRIdALd+++23P/rRjxBO3nPPPQsXLuQP79fU1OzatQs2PHr06Pbt"
            "26qrT8KJ/M7TyZMnP//880ltPwqACW677TYoOOheV6gZJ/6bN29etGhRfn4+mh9UK0naAQMG"
            "Tp8+/frrr4eIjUYjfWdF9ANIr0QHFBcX//jHP96xY8eIESNefvllNJIVK1Y0NDQgB4Z1u93K"
            "j61ohw0bduGFFxYVFe3cuRNzPfbYY5iL35H61FNPIXQN3OuKqYHNZvvoo4+2bduGiBULwSxp"
            "aWmXXXbZrFmzJk2axH9qkMJVot9AeiWCQej61ltv4WQfoszLy4P1CgsLMawEquxL/AkTJpx7"
            "7rk33HADvIkkQtRnn3128eLFOLX/zW9+M2fOHAj3jjvuQOR7++23P/300/Dy1q1bIejvvvuu"
            "srISy0EsjHlnzJhx7bXXDhkyBIWSVYn+B+mVCAan//PmzauuroZSeY4kSZmZmdOmTYMTp0yZ"
            "kpWVZTAY2r8tBbP88Ic/RMxrMpmeeOKJL7/88quvvsrIyHjppZf+85//bNq0CTEvrIqYNzc3"
            "7+qrr0a4CkdjYroIQPRjSK9EMAgzcY7f2toKh+L0f+LEiVdeeeWoUaNGjx4N53YoRAS85eXl"
            "Dz300L59+2RZ9ng8PNQ1Go1OpxMTJCYmXnjhhbNnz77qqquwBIylcJXo95BeiWBKS0uPHz/u"
            "9XqhV6vVin4oKoRhS0pKHnzwwYKCAtgTOVqtFmHv4MGDEfYiXIWpYV4KV4mzB9IrETFg2OLi"
            "4kcfffTAgQNpaWlXXHEFwlX0TSYTxarEWQjplYgwJ06c2LVr18CBAwcNGoQAlsRKnLWQXgmC"
            "IFSBfmuLIAhCFUivBEEQqkB6JQiCUAXSK0EQhCrE8qutjcdrfAkJcg9/2jkkTnq0E82tA/Jy"
            "RTpabDmx3+V36zWSkurxGvobvM5ZQy4XqShy8JujYy4dKhK9oKZ8t+yt8WlNIq0m/gR9xoBL"
            "RUI1agorZIffx95v0zVd7XS5yeeySNmD8kQ6WlRWVmg0vpycASIdDpWVttzcUCvcg4Kqq09k"
            "Zw8WiShiO37Y39pkGX6hSEeUmOl144ma/1OSVu7mAlILLP1HmU0/zXZE07DbSr77Scmbx1tr"
            "RLoXJGoNL1rvuH3YZJGOCluWHvxute3Hf5kq0j2lpmy3te5Bo+egSKtMqzzUOXa3SKhDTVGF"
            "9VOnsVI8K9wb7KPkyuuMOQOjZ1j4MStrc1LSYb8/7IOusXGk0zmgpSUvO3uQyOocFJSZuSUl"
            "pcDnC68gm21mWto4kYgKcKtz5WP68bcPuHKeyIoo0sKFC8VgFPmyuObB0rQyld0K/AkJ3zr1"
            "br9mjL8upe1deaqy+cTeB0rfKW49KdK9w+33bnAUWN1JYzPOFVkqA7d+9XqR3iRdOuc8kdUj"
            "FLc+YPTki7T6eLXpnpyfiIQKwK2WZS6TLQJuBYaTPl2DryrblZgSjWYJ5WVk7MjI2C7Lzh50"
            "ra0Zfr/BYKiuq9MlJqaKhXYECkpP35WZuVWSghfSbWc2n6iuzjCZonSjNHer99hG3ahZKYNV"
            "0XoMrr2uK655oDStVH23crwJCf+oSXylOqnMVimyVANu/e+St4+1Vot0JGj0uX5e/uGHR9aL"
            "tJpwt7qd2Ga9IvpuVRvh1orebpn2pBR4cte4qkptIq0aivJ2ZmZ+jRN2kdUjZNmRnHyourpE"
            "pM9AKWh3VtamnhWk19dbrUvr6g6ItJoE3CrS6hBtva46Vgu3Vnii5FYOdnUUDPvV8d3/XbKo"
            "xB2BawJBRMew5NbOUMOtnCgYFspLS4PyeutWTheGVQra02O3chTDLq+rU7fxRMetIKp6hVt/"
            "WpZqi65bOWobFm59oPTtEnetSEcatQ1Lbu0M9dzKUdWwivK+zc6G8iJW/w4Ni4JSU/dmZ2/o"
            "fUF6fS1i2NraApGONFFzK4ieXpcfZW6tjoVbOeoZdnXxjv8pWVTuVvdLQvUMS27tDLXdylHJ"
            "sIry9mVnb4ygWzlBhkVBKSnf5eREwK0cxbDLamsPiXTkiKZbQZT0uvxY7UNlaTF0K4cb9tWI"
            "GhZu/WnpOxWeBpFWE27Yf0fUsBFza/lua/2D/cmtJ6PiVg4z7NpIGrZNeV9F3K2c9oZNSTmY"
            "m/ulRuPhoyKCwXBSMexhkY4Eilt/HjW3gmjo9eOjdQ+VptV6o32dt0Ng2L9HzrArjm17sPTt"
            "Ko9dpNUHhn0scoaNpFvrHjS6o3QPVhSAW63RcisnJT9ihlXcmp+TA+WpWH9uWKfzi5ycdZF1"
            "K8dgqLZYltXUHBHp3tEWt24Q6aiguvKWHK17pCw1TtzKiZRhlx/b+n9L3632NIp0tIiUYSPp"
            "1tp+5daaqLuVEynDJifDrWu12sgrLwizuTg39wutlv0qpRoYjVVW69LeGzbK1wQCqGu9D47U"
            "w60N8eRWTu8N+8nRzQ+VvlvrdYh0dOm9YSPs1mg9OxAFonO9tTN6b9jm5g2K8lR3q15fk5RU"
            "FJEbErrAaKy0WJafPHlUpMMnVm4FKorv/SP1Py9PscefWzlthk3sgWE/Kdr0SNn7td4mkY4F"
            "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"
            "SEj4/08YXTiH8v1hAAAAAElFTkSuQmCC")
        self.getLogo = origamiLogo.GetBitmap()
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    