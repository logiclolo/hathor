#comment
#comment This is the template of the history.txt
#comment Only change this file when you know what you are doing!!!
#comment
#######################################################################
Name:         <$HATHOR_FIRMWARE_NAME>
Path:         <$HATHOR_FIRMWARE_PATH>
File:         <$HATHOR_FIRMWARE_FILE>
DCR No:       </* PLEASE FILL IN */>
Start Date:   </* PLEASE FILL IN */>
Release Date: <$HATHOR_FIRMWARE_END_DATE>
Author:       <$HATHOR_AUTHOR>
--------------------------------------------------------------------
Firmware type:              <$HATHOR_FIRMWARE_TYPE>
Firmware version:           <$HATHOR_FIRMWARE_VERSION>
#ifdef $HATHOR_WINDOW_PLUGIN
New2 Viewer Plugin version: <$HATHOR_WINDOW_PLUGIN_VERSION>
#endif 
#ifdef $HATHOR_WINDOWLESS_PLUGIN
NP-Plugin:                  <$HATHOR_NP_PLUGIN_VERSION> (npVivotekInstallerMgt.xpi/crx)
IE-Plugin:                  <$HATHOR_IE_PLUGIN_VERSION
VNDPWrapper:                <$HATHOR_VNDP_WRAPPER_VERSION>
#endif 
#comment Check if both window and windowless plugin version is not defined
#if !defined($HATHOR_WINDOWLESS_PLUGIN) && !defined($HATHOR_WINDOW_PLUGIN)
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
              UNABLE TO FIND PLUGIN VERSION
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#endif
Web page language:          <$HATHOR_WEBPAGE_LANGUAGE>
#ifdef $HATHOR_COMMONBUG_LIST
Verify major bug fixed:     <$HATHOR_COMMONBUG_LIST>
#else
Verify major bug fixed:     </* PLEASE FILL IN */>
#endif
-----------------------------------------------------------------------
#include "module-versions.txt"

#include "svn-log.txt"

1. New features:
    /* Fill description of the new feature here */

2. Changed features:
    /* Fill description of the changed feature here */

3. Known bugs and issues
    /* Fill description of the known issue here */

4. Bugs fixed:
#include "fixed-bugs.txt"

6. Unfixed stable common bugs:
    /* Fill unfixed common bug here */

7. Untranslated string:
    /* Fill untranslated strings here */

8. Test scope about this release:
    /* Fill test scope request here */

#comment #include "history-previous.txt" 
