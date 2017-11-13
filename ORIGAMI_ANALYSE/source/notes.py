            # Get height of the peak
            ms = document.massSpectrum
            ms = np.flipud(np.rot90(np.array([ms['xvals'], ms['yvals']])))
            mzYMax = self.view.getYvalue(msList=ms, mzStart=mzStart, mzEnd=mzEnd)
            mzList.SetStringItem(index=mz, col=2, label=str(mzYMax))
            tempArray = []
            driftList = []
            retTimeList = []
            for rt in xrange(rtList.GetItemCount()):
                # RT has to be in minutes to extract using Driftscope
                rtStart= str2num(rtList.GetItem(rt,0).GetText())
                rtEnd = str2num(rtList.GetItem(rt,1).GetText())
                retTimeList.append([int(rtStart), int(rtEnd)]) # create list of RTs to be saved with the document
                rtStart= round(rtStart*(scantime/60),2)
                rtEnd = round(rtEnd*(scantime/60),2)
                filename = rtList.GetItem(rt,4).GetText()
                driftVoltage = str2num(rtList.GetItem(rt,3).GetText())
                if driftVoltage == None: driftVoltage=0
                if filename != document.title: continue
                self.view.SetStatusText(''.join(['RT(s): ',str(rtStart),'-',str(rtEnd),', MS: ',str(mzStart),'-',str(mzEnd)]), 3)
                ml.rawExtract1DIMSdataOverRT(fileNameLocation=path, driftscopeLocation=self.config.driftscopePath,
                                             mzStart=mzStart, mzEnd=mzEnd, rtStart=rtStart, rtEnd=rtEnd)
                # Load output
                imsData1D =  ml.rawOpen1DRTdata(path=path, norm=self.config.normalize)
                # Append to output
                tempArray.append(imsData1D)
                driftList.append(driftVoltage)
                
            # Add data to document object  
            ims1Darray = np.array(tempArray) # combine
            imsData1D = np.sum(ims1Darray, axis=0)
            document.gotExtractedDriftTimes = True
            rangeName = ''.join([str(mzStart),'-',str(mzEnd)])
            document.IMS1DdriftTimes[rangeName] = {'xvals':xvals,
                                                   'yvals':ims1Darray,
                                                   'yvalsSum':imsData1D,
                                                   'xlabels':xlabel,
                                                   'charge':charge,
                                                   'driftVoltage':driftList,
                                                   'retTimes':retTimeList,
                                                   'xylimits':[mzStart,mzEnd,mzYMax]}