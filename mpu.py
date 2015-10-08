'''Memory Protection Unit support.'''
import sys

class MPUException(Exception):
    '''Simple exception class for fatal errors.'''
    def __init__(self, errString):
        Exception.__init__(self)
        self.errString = errString

    def ShowAndExit(self):
        '''Show the error string and exit.'''
        sys.stderr.write("mpu: Error: " + self.errString)
        sys.exit(1)

class OrderedDict(object):
    '''Ordered dictionary'''
    # pylint: disable=too-few-public-methods
    # (all our work is in overloaded operators, which are basically public)

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

class MPUInfo(object):
    '''MPU information'''
    __instance = None
    __magic = object()
    def __init__(self, token):
        if token != MPUInfo.__magic:
            raise MPUException("Internal error")

        self.isEnabled = OrderedDict([('GRAM_READONLY', False), ('GRAM_NO_DCP', False),
                                      ('GRAM_EDC', False), ('GRAM_HOST', False),
                                      ('GRAM_MCP_0', False), ('GRAM_MCP_1', False), ('GRAM_MCP_2', False),
                                      ('GRAM_MCP_3', False), ('GRAM_MCP_4', False), ('GRAM_MCP_5', False),
                                      ('GRAM_FFT_0', False), ('GRAM_FFT_1', False), ('GRAM_FFT_2', False),
                                      ('GRAM_FFT_3', False), ('GRAM_FFT_4', False), ('GRAM_FFT_5', False),
                                      ('EXTRAM_READONLY', False), ('EXTRAM_NO_DCP', False),
                                      ('EXTRAM_EDC', False), ('EXTRAM_HOST', False),
                                      ('GRAM_MCU_ECU_HOLE', False), ('EXTRAM_MCU_ECU_HOLE', False)])

        #First boolean: if first argument exsits
        #Second boolean: if second argument exsits
        #protectedBuffers means the to be protected buffers defined in C
        self.protectedBuffers = {'GRAM_MCP_0':["", "", False, False], 'GRAM_MCP_1':["", "", False, False],
                                 'GRAM_MCP_2':["", "", False, False], 'GRAM_MCP_3':["", "", False, False],
                                 'GRAM_MCP_4':["", "", False, False], 'GRAM_MCP_5':["", "", False, False],
                                 'GRAM_FFT_0':["", "", False, False], 'GRAM_FFT_1':["", "", False, False],
                                 'GRAM_FFT_2':["", "", False, False], 'GRAM_FFT_3':["", "", False, False],
                                 'GRAM_FFT_4':["", "", False, False], 'GRAM_FFT_5':["", "", False, False],
                                 'GRAM_READONLY':["", "", False, False], 'GRAM_MCU_ECU_HOLE':["", "", False, False],
                                 'GRAM_NO_DCP':["", "", False, False], 'GRAM_EDC':["", "", False, False],
                                 'GRAM_HOST':["", "", False, False], 'EXTRAM_READONLY':["", "", False, False],
                                 'EXTRAM_MCU_ECU_HOLE':["", "", False, False], 'EXTRAM_NO_DCP':["", "", False, False],
                                 'EXTRAM_EDC':["", "", False, False], 'EXTRAM_HOST':["", "", False, False]}

        self.mask = 0x00000000

        self.enabledRegions = []

    @staticmethod
    def Get():
        '''Return the single instance of this class.'''
        if MPUInfo.__instance == None:
            MPUInfo.__instance = MPUInfo(MPUInfo.__magic)
        return MPUInfo.__instance

    def VerifyRegions(self, part, isGRAM):
        '''Verifing whether the enabled region has been defined or not'''

        gramEnabledRegions = []
        extramEnabledRegions = []
        #gram regions
        for key in self.isEnabled.keys[0:15] + ["GRAM_MCU_ECU_HOLE"]:
            if self.isEnabled[key]:
                gramEnabledRegions.append(key)

        #extram regions
        for key in self.isEnabled.keys[16:19] + ["EXTRAM_MCU_ECU_HOLE"]:
            if self.isEnabled[key]:
                extramEnabledRegions.append(key)

        noend = ["_noEnd_"]
        none = ["None"]

        #If the region enabled is not appended, throw exception
        if isGRAM:
            for gramEnabledRegion in gramEnabledRegions:
                if not self.protectedBuffers[gramEnabledRegion][MPU_START_ADDRESS] \
                in (part.dbl + part.cpx + part.sxt + part.pkd + none) \
                and not self.protectedBuffers[gramEnabledRegion][IF_START_PREDEFINED]:
                    raise MPUException("gram region start address " + "[" +
                                       str(self.protectedBuffers[gramEnabledRegion][MPU_START_ADDRESS]) +
                                       "]" + " not appended  ")

                if not self.protectedBuffers[gramEnabledRegion][MPU_END_ADDRESS] \
                in (part.dbl + part.cpx + part.sxt + part.pkd + noend + none) \
                and not self.protectedBuffers[gramEnabledRegion][IF_END_PREDEFINED]:
                    raise MPUException("gram region end address " + "[" +
                                       str(self.protectedBuffers[gramEnabledRegion][MPU_END_ADDRESS]) + "]" + " not appended  ")

        elif not isGRAM:
            for extramEnabledRegion in extramEnabledRegions:
                if not self.protectedBuffers[extramEnabledRegion][MPU_START_ADDRESS] \
                in (part.cached + part.uncached + none) \
                and not self.protectedBuffers[extramEnabledRegion][IF_START_PREDEFINED]:
                    raise MPUException("extram region start address " + "[" +
                                       str(self.protectedBuffers[extramEnabledRegion][MPU_START_ADDRESS]) + "]" +
                                       " not appended  ")

                if not self.protectedBuffers[extramEnabledRegion][MPU_END_ADDRESS] \
                in (part.cached + part.uncached + noend + none)\
                and not self.protectedBuffers[extramEnabledRegion][IF_END_PREDEFINED]:
                    raise MPUException("extram region end address " + "[" +
                                       str(self.protectedBuffers[extramEnabledRegion][MPU_END_ADDRESS]) + "]" +
                                       " not appended  ")

    def SetRegionAndMask(self):
        '''Return enabled buffers and mask'''
        i = 0
        #i is for generating mask
        for key in self.isEnabled.keys:
            if self.isEnabled[key]:
                self.enabledRegions.append(key)
                self.mask = self.mask | (1 << i)
            i += 1


def _enableRegion(region, start, end=None):
    '''Enable region'''
    mpuInfo = MPUInfo.Get()

    if start == None:
        mpuInfo.isEnabled[region] = True
        mpuInfo.protectedBuffers[region][MPU_START_ADDRESS] = "None"
        mpuInfo.protectedBuffers[region][MPU_END_ADDRESS] = "None"
        return

    if not region in mpuInfo.isEnabled.keys:
        sys.stderr.write("mpu: Error:Region "+ region + " not defined  ")
        exit(1)

    for existRegion in mpuInfo.isEnabled.keys:
        if mpuInfo.isEnabled[existRegion]:
            if mpuInfo.protectedBuffers[existRegion][MPU_START_ADDRESS] == start \
            or mpuInfo.protectedBuffers[existRegion][MPU_END_ADDRESS] == start:
                mpuInfo.protectedBuffers[region][IF_START_PREDEFINED] = True
                mpuInfo.protectedBuffers[region][MPU_START_ADDRESS] = existRegion

            if mpuInfo.protectedBuffers[existRegion][MPU_START_ADDRESS] == end \
            or mpuInfo.protectedBuffers[existRegion][MPU_END_ADDRESS] == end:
                mpuInfo.protectedBuffers[region][IF_END_PREDEFINED] = True
                mpuInfo.protectedBuffers[region][MPU_END_ADDRESS] = existRegion


    mpuInfo.isEnabled[region] = True

    if not mpuInfo.protectedBuffers[region][IF_END_PREDEFINED]:
        if not mpuInfo.protectedBuffers[region][IF_START_PREDEFINED]:
            if None == end:
                mpuInfo.protectedBuffers[region] = [start, "_noEnd_", False, False]
            else:
                mpuInfo.protectedBuffers[region] = [start, end, False, False]
        elif mpuInfo.protectedBuffers[region][IF_START_PREDEFINED]:
            if None == end:
                mpuInfo.protectedBuffers[region][MPU_END_ADDRESS] = "_noEnd_"
            else:
                mpuInfo.protectedBuffers[region][MPU_END_ADDRESS] = end

    elif mpuInfo.protectedBuffers[region][IF_END_PREDEFINED]:
        if not mpuInfo.protectedBuffers[region][IF_START_PREDEFINED]:
            mpuInfo.protectedBuffers[region][MPU_START_ADDRESS] = start


def setProtectedRegion(regions, sym=None, varibleName=None):
    '''Configure the memory protected region,
        regions mean enabledRegions'''
    mpuInfo = MPUInfo.Get()

    #varibale Name is None it means that it's for varibles start with "." (.dcpimage)
    if varibleName == None:
        varibleName = sym

    sectDef = ""
    for region in regions:
        #Iterate every region
        if not mpuInfo.protectedBuffers[region][IF_END_PREDEFINED]:
            if not mpuInfo.protectedBuffers[region][IF_START_PREDEFINED]:
                if sym in mpuInfo.protectedBuffers[region]:
                    if sym == mpuInfo.protectedBuffers[region][0]:
                        sectDef += "         _mpu_"+region + "_start = . ;\n"
                        sectDef += "        . = ALIGN({0:d});\n".format(4)
                        sectDef += "        *(" + varibleName + ")\n"
                        if "_noEnd_" == mpuInfo.protectedBuffers[region][MPU_END_ADDRESS]:
                            sectDef += "         _mpu_"+region + "_end = . ;\n"
                    elif sym == mpuInfo.protectedBuffers[region][MPU_END_ADDRESS]:
                        sectDef += "        . = ALIGN({0:d});\n".format(4)
                        sectDef += "        *(" + varibleName + ")\n"
                        sectDef += "         _mpu_"+region + "_end = . ;\n"

            elif mpuInfo.protectedBuffers[region][IF_START_PREDEFINED]:
                if sym == mpuInfo.protectedBuffers[region][MPU_END_ADDRESS]:
                    sectDef += "        . = ALIGN({0:d});\n".format(4)
                    sectDef += "        *(" + varibleName + ")\n"
                    sectDef += "         _mpu_"+region + "_end = . ;\n"

        if mpuInfo.protectedBuffers[region][IF_END_PREDEFINED]:
            if not mpuInfo.protectedBuffers[region][IF_START_PREDEFINED]:
                if sym in mpuInfo.protectedBuffers[region]:
                    if sym == mpuInfo.protectedBuffers[region][0]:
                        sectDef += "         _mpu_"+region + "_start = . ;\n"
                        sectDef += "        . = ALIGN({0:d});\n".format(4)
                        sectDef += "        *(" + varibleName + ")\n"
                        if "_noEnd_" == mpuInfo.protectedBuffers[region][MPU_END_ADDRESS]:
                            sectDef += "         _mpu_"+region + "_end = . ;\n"
                    elif sym == mpuInfo.protectedBuffers[region][MPU_END_ADDRESS]:
                        sectDef += "        . = ALIGN({0:d});\n".format(4)
                        sectDef += "        *(" + varibleName + ")\n"
                        sectDef += "         _mpu_"+region + "_end = . ;\n"

        if  sym == None:
            #If predefined
            if mpuInfo.protectedBuffers[region][IF_START_PREDEFINED]:
                sectDef += "         _mpu_" +region + "_start = _mpu_" + mpuInfo.protectedBuffers[region][0]+ "_start ;\n"
            if mpuInfo.protectedBuffers[region][IF_END_PREDEFINED]:
                sectDef += ("         _mpu_" +region + "_end = _mpu_" +
                            mpuInfo.protectedBuffers[region][MPU_END_ADDRESS]+ "_end ;\n")

            #When the addresses are defined as None
            if mpuInfo.protectedBuffers[region][MPU_START_ADDRESS] == "None" \
            and mpuInfo.protectedBuffers[region][MPU_END_ADDRESS] == "None":
                sectDef += "         _mpu_"+region + "_start = 0x0 ;\n"
                sectDef += "         _mpu_"+region + "_end = 0x0 ;\n"

    return sectDef
