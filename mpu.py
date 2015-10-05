import sys

class OrderedDict(object):
    '''Ordered dictionary'''
    def __init__(self, items):
        self.items = items
        self.keys = []
        for i in items:
            self.keys.append(i[0])

    def __getitem__(self, key):
        '''Overload the [] operator for reading.'''
        for item in self.items:
            if item[0] == key:
                return item[1]

    def __setitem__(self, key, value):
        '''Overload the [] operator for writing.'''
        found = False
        for x, item in enumerate(self.items):
            if item[0] == key:
                self.items[x] = (key, value)
                found = True
        if not found:
            self.items.append((key, value))
            self.keys.append(key)

    def __iter__(self):
        '''Return the keys when we iterate.'''
        return self.keys.__iter__()

MPU_START_ADDRESS = 0
MPU_END_ADDRESS = 1
IF_START_PREDEFINED = 2
IF_END_PREDEFINED = 3

class MPU_info(object):
    '''MPU information'''
    def __init__(self):
        self.isEnabled = OrderedDict ([('GRAM_READONLY', False), ('GRAM_NO_DCP', False),
                                      ('GRAM_EDC', False), ('GRAM_HOST', False),
                                      ('GRAM_MCP_0', False), ('GRAM_MCP_1', False), ('GRAM_MCP_2', False), 
                                      ('GRAM_MCP_3', False), ('GRAM_MCP_4', False), ('GRAM_MCP_5', False), 
                                      ('GRAM_FFT_0', False), ('GRAM_FFT_1', False), ('GRAM_FFT_2', False), 
                                      ('GRAM_FFT_3', False), ('GRAM_FFT_4', False ), ('GRAM_FFT_5', False),
                                      ('EXTRAM_READONLY', False), ('EXTRAM_NO_DCP', False), 
                                      ('EXTRAM_EDC', False), ('EXTRAM_HOST', False),
                                      ('GRAM_MCU_ECU_HOLE', False), ('EXTRAM_MCU_ECU_HOLE', False)])
                         
        #First boolean: if first argument exsits
        #Second boolean: if second argument exsits
        self.bufName = {'GRAM_MCP_0':["", "", False, False], 'GRAM_MCP_1':["", "", False, False], 
                        'GRAM_MCP_2':["", "", False, False], 'GRAM_MCP_3':["", "", False, False], 
                        'GRAM_MCP_4':["", "", False, False], 'GRAM_MCP_5':["", "", False, False],
                        'GRAM_FFT_0':["", "", False, False], 'GRAM_FFT_1':["", "", False, False], 
                        'GRAM_FFT_2':["", "", False, False], 'GRAM_FFT_3':["", "", False, False], 
                        'GRAM_FFT_4':["", "", False, False], 'GRAM_FFT_5':["", "", False, False],
                        'GRAM_READONLY':["", "", False, False], 'GRAM_MCU_ECU_HOLE':["", "", False, False], 
                        'GRAM_NO_DCP':["", "", False, False],  'GRAM_EDC':["", "", False, False], 
                        'GRAM_HOST':["", "", False, False] ,  'EXTRAM_READONLY':["", "", False, False], 
                        'EXTRAM_MCU_ECU_HOLE':["", "", False, False], 'EXTRAM_NO_DCP':["", "", False, False],
                        'EXTRAM_EDC':["", "", False, False], 'EXTRAM_HOST':["", "", False, False]}

        self.mask = 0x00000000

    #def getIsenabled(self, region):
        #return self.isEnabled[region]

mpu_info = MPU_info()

def enableRegion(region, start, end = None):
    '''Enable region'''
    global mpu_info

    #if not start in mpu_info.regionNames:
        #sys.stderr.write("mpu: Error:Names "+ start + " not defined  ")
        #exit(1)
    if start == None:
        mpu_info.isEnabled[region] = True
        mpu_info.bufName[region][MPU_START_ADDRESS] = "None"
        mpu_info.bufName[region][MPU_END_ADDRESS] = "None"

        return

    if not region in mpu_info.isEnabled.keys:
        sys.stderr.write("mpu: Error:Region "+ region + " not defined  ")
        exit(1)

    for existRegion in mpu_info.isEnabled.keys:
        if mpu_info.isEnabled[existRegion]:
            if mpu_info.bufName[existRegion][MPU_START_ADDRESS] == start \
            or mpu_info.bufName[existRegion][MPU_END_ADDRESS] == start:
                mpu_info.bufName[region][IF_START_PREDEFINED] = True
                mpu_info.bufName[region][MPU_START_ADDRESS] = existRegion
                   
            if mpu_info.bufName[existRegion][MPU_START_ADDRESS] == end \
            or mpu_info.bufName[existRegion][MPU_END_ADDRESS] == end:
                mpu_info.bufName[region][IF_END_PREDEFINED] = True
                mpu_info.bufName[region][MPU_END_ADDRESS] = existRegion


    mpu_info.isEnabled[region] = True
    #if region == "EXTRAM_READONLY":
        #sys.stderr.write("mpu: Error:"+ str(mpu_info.isEnabled) +"\n"+ str(mpu_info.bufName) + " not defined  ")
        #exit(1)

    if not mpu_info.bufName[region][IF_END_PREDEFINED]:
        if not mpu_info.bufName[region][IF_START_PREDEFINED]:
            if None == end:
                mpu_info.bufName[region] = [start, "_noEnd_", False, False]
            else:
                mpu_info.bufName[region] = [start, end, False, False]
        elif mpu_info.bufName[region][IF_START_PREDEFINED]:
            if None == end:
                mpu_info.bufName[region][MPU_END_ADDRESS] = "_noEnd_" 
            else:
                mpu_info.bufName[region][MPU_END_ADDRESS] = end 

    elif mpu_info.bufName[region][IF_END_PREDEFINED]:
        if not mpu_info.bufName[region][IF_START_PREDEFINED]:
            mpu_info.bufName[region][MPU_START_ADDRESS] = start     

def getEnabledRegions():
    '''Return enabled buffers and mask'''
    enabledRegions = []
    enabledBuffers = []
    gramEnabledRegions = []
    extramEnabledRegions = []
    i = 0

    #i is for generating mask
    for key in mpu_info.isEnabled.keys:
        if mpu_info.isEnabled[key]:
            enabledRegions.append(key)
            mpu_info.mask = mpu_info.mask | (1 << i)
        i += 1
   
    for region in enabledRegions:
        enabledBuffers.append(mpu_info.bufName[region])

    return enabledRegions, mpu_info.mask

def verifyRegion(p, isGRAM):
    '''Verifing whether the enabled region has been defined or not. If yes, it returns the buffers that have been enabled
       mask contains the enabledRegions information'''
    #enabledRegions = []
    #enabledBuffers = []
    gramEnabledRegions = []
    extramEnabledRegions = []
   
    #i is for generating mask
    '''for key in mpu_info.isEnabled.keys:
        if mpu_info.isEnabled[key]:
            enabledRegions.append(key)
            mpu_info.mask = mpu_info.mask | (1 << i)
        i += 1
   '''
    #gram regions
    for key in mpu_info.isEnabled.keys[0:15] + ["GRAM_MCU_ECU_HOLE"]:
        if mpu_info.isEnabled[key]:
            gramEnabledRegions.append(key)

    #if mpu_info.isEnabled["GRAM_MCU_ECU_HOLE"]:
        #gramEnabledRegions.append("GRAM_MCU_ECU_HOLE")
    #extram regions
    for key in mpu_info.isEnabled.keys[16:19] + ["EXTRAM_MCU_ECU_HOLE"]:
        if mpu_info.isEnabled[key]:
            extramEnabledRegions.append(key)

    #if mpu_info.isEnabled["EXTRAM_MCU_ECU_HOLE"]:
        #extramEnabledRegions.append("EXTRAM_MCU_ECU_HOLE")


    #for region in enabledRegions:
        #enabledBuffers.append(mpu_info.bufName[region])
    

    noend = ["_noEnd_"]
    none = ["None"]
    #print gramEnabledRegions
    #print mpu_info.bufName

    #If the region enabled is not appended, throw exception
    if isGRAM:
        for gramEnabledRegion in gramEnabledRegions:
            if not mpu_info.bufName[gramEnabledRegion][MPU_START_ADDRESS] \
            in (p.dbl + p.cpx + p.sxt + p.pkd + none ) \
            and not mpu_info.bufName[gramEnabledRegion][IF_START_PREDEFINED]:
                sys.stderr.write("mpu: Error:gram region start address"+ 
                str(mpu_info.bufName[gramEnabledRegion][MPU_START_ADDRESS]) + " not appended  ")
                exit(1)
            if not mpu_info.bufName[gramEnabledRegion][MPU_END_ADDRESS] \
            in (p.dbl + p.cpx + p.sxt + p.pkd + noend + none) \
            and not mpu_info.bufName[gramEnabledRegion][IF_END_PREDEFINED]:
                sys.stderr.write("mpu: Error:gram region end address"+ 
                str(mpu_info.bufName[gramEnabledRegion][MPU_END_ADDRESS]) + " not appended  ")
                exit(1)

    elif not isGRAM:
        for extramEnabledRegion in extramEnabledRegions:
            if not mpu_info.bufName[extramEnabledRegion][MPU_START_ADDRESS] \
            in (p.cached + p.uncached + none) \
            and not mpu_info.bufName[extramEnabledRegion][IF_START_PREDEFINED]:
                sys.stderr.write("mpu: Error:extram region start address"+ 
                str(mpu_info.bufName[extramEnabledRegion][MPU_START_ADDRESS]) + " not appended  ")
                exit(1)
            if not mpu_info.bufName[extramEnabledRegion][MPU_END_ADDRESS] \
            in (p.cached + p.uncached + noend + none)\
            and not mpu_info.bufName[extramEnabledRegion][IF_END_PREDEFINED]:
                sys.stderr.write("mpu: Error:extram region end address"+ 
                str(mpu_info.bufName[extramEnabledRegion][MPU_END_ADDRESS]) + " not appended  ")
                exit(1)

    #return enabledRegions, mpu_info.mask

def getBufName():
    '''Return the bufName'''
    return mpu_info.bufName

def setProtectedRegion(regions, sym = None, varibleName = None):
    '''Configure the memory protected region
        regions mean enabledRegions'''
    #print "mpu: Error: "+ str(regions)+"\n"+str(mpu_info.bufName) + " not appended  "
    #exit(1)
    #varibale Name is None means that it's for varibles start with "."
    if varibleName == None:
        varibleName = sym

    sectDef = ""
    for region in regions:
        #Iterate every region
        if not mpu_info.bufName[region][IF_END_PREDEFINED]:
            if not mpu_info.bufName[region][IF_START_PREDEFINED]:
                if sym in mpu_info.bufName[region]:
                    if sym == mpu_info.bufName[region][0]:
                        sectDef += "         _mpu_"+region + "_start = . ;\n"
                        sectDef += "        . = ALIGN({0:d});\n".format(4)
                        sectDef += "        *(" + varibleName + ")\n"
                        if "_noEnd_" == mpu_info.bufName[region][MPU_END_ADDRESS]:
                            sectDef += "         _mpu_"+region + "_end = . ;\n"
                    elif sym == mpu_info.bufName[region][MPU_END_ADDRESS]:
                        sectDef += "        . = ALIGN({0:d});\n".format(4)
                        sectDef += "        *(" + varibleName + ")\n"
                        sectDef += "         _mpu_"+region + "_end = . ;\n"

            elif mpu_info.bufName[region][IF_START_PREDEFINED]:
                if sym == mpu_info.bufName[region][MPU_END_ADDRESS]:
                    sectDef += "        . = ALIGN({0:d});\n".format(4)
                    sectDef += "        *(" + varibleName + ")\n"
                    sectDef += "         _mpu_"+region + "_end = . ;\n"

        if mpu_info.bufName[region][IF_END_PREDEFINED]:
            if not mpu_info.bufName[region][IF_START_PREDEFINED]:
                if sym in mpu_info.bufName[region]:
                    if sym == mpu_info.bufName[region][0]:
                        sectDef += "         _mpu_"+region + "_start = . ;\n"
                        sectDef += "        . = ALIGN({0:d});\n".format(4)
                        sectDef += "        *(" + varibleName + ")\n"
                        if "_noEnd_" == mpu_info.bufName[region][MPU_END_ADDRESS]:
                            sectDef += "         _mpu_"+region + "_end = . ;\n"
                    elif sym == mpu_info.bufName[region][MPU_END_ADDRESS]:
                        sectDef += "        . = ALIGN({0:d});\n".format(4)
                        sectDef += "        *(" + varibleName + ")\n"
                        sectDef += "         _mpu_"+region + "_end = . ;\n"

        if  sym == None:
            #If predefined
            #sys.stderr.write("mpu: Error: "+ str(regions)+"\n"+str(mpu_info.bufName) + " not appended  ")
            #exit(1)
            if mpu_info.bufName[region][IF_START_PREDEFINED]:
                sectDef += "         _mpu_"+region + "_start = _mpu_"+ mpu_info.bufName[region][0]+ "_start ;\n"
            if mpu_info.bufName[region][IF_END_PREDEFINED]:
                sectDef += "         _mpu_"+region + "_end = _mpu_"+ mpu_info.bufName[region][MPU_END_ADDRESS]+ "_end ;\n"

            #When the addresses are defined as None
            if mpu_info.bufName[region][MPU_START_ADDRESS] == "None" \
            and mpu_info.bufName[region][MPU_END_ADDRESS] == "None" :
                sectDef += "         _mpu_"+region + "_start = 0x0 ;\n"
                sectDef += "         _mpu_"+region + "_end = 0x0 ;\n"

    return sectDef
