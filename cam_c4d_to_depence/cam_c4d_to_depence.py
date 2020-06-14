from __future__ import division

import c4d
from c4d import documents
from c4d import storage
from c4d import gui
from c4d.gui import GeDialog
from c4d.utils import MatrixToHPB

import string
import math
import uuid
import time
import os

DEBUG = False


class Dialog(GeDialog):

    keyFrameInterval = 6
    timeOffsetInFrames = 0
    sceneScale = 0.01
    frameSpaceInS = 0.033
    startFrame = 0
    endFrame = 1000
    targetFPS = 30

    didPressOK = False

    def CreateLayout(self):

        self.SetTitle("Make VPad Camera")

        self.GroupBegin(111, c4d.BFH_SCALEFIT, cols=2)
        self.AddStaticText(1000, c4d.BFH_LEFT, name="KeyFrame Interval", initw=200)
        self.AddEditSlider(1001, c4d.BFH_SCALEFIT)
        self.SetInt32(1001, self.keyFrameInterval, min=1, max=10, step=1, max2=10000)
        self.GroupEnd()

        self.GroupBegin(112, c4d.BFH_SCALEFIT, cols=2)
        self.AddStaticText(1002, c4d.BFH_LEFT, name="TimeOffset", initw=200)
        self.AddEditSlider(1003, c4d.BFH_SCALEFIT)
        self.SetInt32(1003, self.timeOffsetInFrames, min=-500, max=500, step=1, min2=-10000, max2=10000)
        self.GroupEnd()

        self.GroupBegin(113, c4d.BFH_SCALEFIT, cols=2)
        self.AddStaticText(1004, c4d.BFH_LEFT, name="Scene Scale", initw=200)
        self.AddEditSlider(1005, c4d.BFH_SCALEFIT)
        self.SetFloat(1005, self.sceneScale, min=0.0001, max=10, step=0.01,
                      format=c4d.FORMAT_FLOAT, max2=1000, quadscale=True)
        self.GroupEnd()

        self.GroupBegin(114, c4d.BFH_SCALEFIT, cols=2)
        self.AddStaticText(1006, c4d.BFH_LEFT, name="Space Between Blocks", initw=200)
        self.AddEditSlider(1007, c4d.BFH_SCALEFIT)
        self.SetFloat(1007, self.frameSpaceInS, min=0, max=1, step=0.01,
                      format=c4d.FORMAT_FLOAT, max2=100, quadscale=True)
        self.GroupEnd()

        self.GroupBegin(115, c4d.BFH_SCALEFIT, cols=2)
        self.AddStaticText(1008, c4d.BFH_LEFT, name="First Frame", initw=200)
        self.AddEditSlider(1009, c4d.BFH_SCALEFIT)
        self.SetInt32(1009, self.startFrame, min=0, max=1000, step=1, max2=99999)
        self.GroupEnd()

        self.GroupBegin(115, c4d.BFH_SCALEFIT, cols=2)
        self.AddStaticText(1012, c4d.BFH_LEFT, name="Last Frame", initw=200)
        self.AddEditSlider(1013, c4d.BFH_SCALEFIT)
        self.SetInt32(1013, self.endFrame, min=0, max=1000, step=1, max2=99999)
        self.GroupEnd()

        self.GroupBegin(116, c4d.BFH_SCALEFIT, cols=2)
        self.AddStaticText(1010, c4d.BFH_LEFT, name="Target FPS", initw=200)
        self.AddEditSlider(1011, c4d.BFH_SCALEFIT)
        self.SetFloat(1011, self.targetFPS, min=0, max=30, step=1, max2=10000)
        self.GroupEnd()

        self.AddButton(9999, c4d.BFH_CENTER, name="OK", initw=100, inith=12)
        # self.AddButton(10000, c4d.BFH_CENTER, name = "Cancel", initw = 100, inith = 12)
        return True

    def Command(self, id, msg):

        if id == 9999:
            self.keyFrameInterval = self.GetInt32(1001)
            self.timeOffsetInFrames = self.GetInt32(1003)
            self.sceneScale = self.GetFloat(1005)
            self.frameSpaceInS = self.GetFloat(1007)
            self.startFrame = self.GetInt32(1009)
            self.endFrame = self.GetInt32(1013)
            self.targetFPS = self.GetFloat(1011)
            self.didPressOK = True
            self.Close()

            return True

        return False


def d_print(msg):
    if DEBUG:
        print msg


def main():
    global path, rangeStart, rangeEnd

    doc = documents.GetActiveDocument()
    docFPS = doc[c4d.DOCUMENT_FPS]

    d_print("Document FPS: " + str(docFPS))

    try:
        cam = doc.GetSelection()[0]
        if not cam.GetType() == 5103:
            gui.MessageDialog("Please select a Camera to export")
            return
    except IndexError:
        gui.MessageDialog("Please select a Camera to export")
        return

    camTracks = []

    for i in range(903, 905):
        for j in range(1000, 1003):
            track = cam.FindCTrack(c4d.DescID(
                c4d.DescLevel(i), c4d.DescLevel(j)))
            camTracks.append(track)

    rangeStart = camTracks[0].GetCurve().GetKey(0).GetTime().GetFrame(docFPS)
    rangeEnd = camTracks[0].GetCurve().GetKey(camTracks[0].GetCurve().GetKeyCount()-1).GetTime().GetFrame(docFPS)

    dlg = Dialog()
    dlg.startFrame = rangeStart
    dlg.endFrame = rangeEnd
    dlg.Open(c4d.DLG_TYPE_MODAL_RESIZEABLE, defaultw=500)

    if not dlg.didPressOK:
        return

    keyFrameInterval = dlg.keyFrameInterval
    timeOffsetInFrames = dlg.timeOffsetInFrames
    sceneScale = dlg.sceneScale
    frameSpaceInS = dlg.frameSpaceInS
    startFrame = dlg.startFrame
    endFrame = dlg.endFrame
    targetFPS = dlg.targetFPS

    d_print("Keyframe Interval: " + str(keyFrameInterval))
    d_print("Time Offset: " + str(timeOffsetInFrames))
    d_print("Scene Scale: " + str(sceneScale))
    d_print("Frame Space: " + str(frameSpaceInS))
    d_print("Range Start: " + str(rangeStart))
    d_print("Range End: " + str(rangeEnd))
    d_print("Target FPS: " + str(targetFPS))

    path = storage.LoadDialog(flags=2)

    if not path:
        print "No path found"
        return

    if not os.path.exists(path + '/fullsequence_empty.xml'):
        os.rename(path + '/fullsequence.xml', path + '/fullsequence_empty.xml')

    f = open(path + '/fullsequence_empty.xml', 'r')
    xmlText = f.read()
    f.close()

    split1 = string.rfind(xmlText, "</Syncronorm_ShowSequence_V1.0>")
    split2 = string.rfind(xmlText, "</blocks>")

    string1 = xmlText[:split2-1]
    string2 = xmlText[split2:split1-1]
    string3 = xmlText[split1:]

    insertString1 = ""
    insertString2 = "<SceneList>"

    for frame in range(startFrame, endFrame+keyFrameInterval, keyFrameInterval):

        d_print("\n\n---------- Frame: " + str(frame) + ' ----------')

        ID = str(uuid.uuid4())

        startTime = (frame/targetFPS) + (timeOffsetInFrames /
                                         targetFPS) - (keyFrameInterval/targetFPS) + (1/docFPS)
        startTime = string.replace(str(startTime), ".", ",")

        d_print("Start Time: " + str(startTime))

        length = (keyFrameInterval/targetFPS) - frameSpaceInS
        length = string.replace(str(length), ".", ",")

        d_print("Length: " + str(length))

        doc.SetTime(c4d.BaseTime(frame, docFPS))

        c4d.DrawViews(c4d.DA_ONLY_ACTIVE_VIEW | c4d.DA_NO_THREAD |
                      c4d.DA_NO_REDUCTION | c4d.DA_STATICBREAK)
        c4d.GeSyncMessage(c4d.EVMSG_TIMECHANGED)

        posX = cam.GetMg().off.x * sceneScale
        posY = cam.GetMg().off.y * sceneScale
        posZ = -cam.GetMg().off.z * sceneScale
        rotX = -MatrixToHPB(cam.GetMg()).x * 180/math.pi
        rotY = -MatrixToHPB(cam.GetMg()).y * 180/math.pi
        rotZ = MatrixToHPB(cam.GetMg()).z * 180/math.pi

        if (rotX <= -180):
            rotX = rotX + 360
        if (rotX >= 180):
            rotX = rotX - 360

        if (rotY <= -180):
            rotY = rotY + 360
        if (rotY >= 180):
            rotY = rotY - 360

        if (rotZ <= -180):
            rotZ = rotZ + 360
        if (rotZ >= 180):
            rotZ = rotZ - 360

        # posX = round(posX, 6)
        # posY = round(posY, 6)
        # posZ = round(posZ, 6)
        rotX = round(rotX, 3)
        rotY = round(rotY, 3)
        rotZ = round(rotZ, 3)

        posX = string.replace(str(posX), ".", ",")
        posY = string.replace(str(posY), ".", ",")
        posZ = string.replace(str(posZ), ".", ",")
        rotX = string.replace(str(rotX), ".", ",")
        rotY = string.replace(str(rotY), ".", ",")
        rotZ = string.replace(str(rotZ), ".", ",")

        d_print(posX)
        d_print(posY)
        d_print(posZ)
        d_print(rotX)
        d_print(rotY)
        d_print(rotZ)

        insertString1 = (
            insertString1 + '\n<block Name="CamPos" StartTime="' + startTime + '" Lenght="' + length + '" FadeInTime="' + length + '" FadeOutTime="0" DelayInTime="0" DelayOutTime="0" BeatsPerMinute="120" UseACD="False" ACD_InDelay="0" ACD_InFade="0" ACD_OutDelay="0" ACD_OutFade="0" Mute="False" Freeze="False" Tracking="True" EffectSpeedOffset="0" MultiSceneGUID="' +
            ID + '" CueListGUID="" FadeCenter="True" FadeAmplitude="True" FadePhase="True" FadeRpM="False" UsedCenter="True" UsedAmplitude="True" UsedPhase="True" UsedRpM="True" InFadeRate="100" OutFadeRate="100" FadeType="0" DelayType="0" LightColor="-1">\n'
            + '  <LightColorX red="255" green="255" blue="255" amber="0" white="0" intensity="255" CellX="0" CellY="0"></LightColorX>\n'
            + '</block>'
        )

        insertString2 = (
            insertString2 + '<scene GroupGUID="" GUID="' + ID +
            '" AggTypeGUID="" InDelayTime="0" InFadeTime="0" Name="CamPos" OutDelayTime="0" OutFadeTime="0" IsUniqueBlockScene="False" UsedSplines="True">\n'
            + '  <Items>\n'
            + '    <Item UID="65500" PatternGUID="" Amplitude="0" Center="0" EffectGUID="" InDelayPoint="0" InFadePoint="100" Offset="0" OutDelayPoint="0" OutFadePoint="100" MaxPhase="0" Phase="' + posX +
            '" RpM="0" NumWaves="1" GoOut="0" CutAfter="1" SelectionIndex="0" Direction="0" TogleWinkelLeft="0" TogleWinkelRight="360" VisibleWaves="1" BNC_StartReverse="False" ValueOffset="0" FadeCenter="True" FadeAmplitude="True" FadePhase="True" FadeRpM="False" UsedCenter="True" UsedAmplitude="True" UsedPhase="True" UsedRpM="True" InFadeRate="100" OutFadeRate="100" FadeType="0" DelayType="0"></Item>\n'
            + '      <Item UID="65504" PatternGUID="" Amplitude="0" Center="0" EffectGUID="" InDelayPoint="0" InFadePoint="100" Offset="0" OutDelayPoint="0" OutFadePoint="100" MaxPhase="0" Phase="' + posY +
            '" RpM="0" NumWaves="1" GoOut="0" CutAfter="1" SelectionIndex="0" Direction="0" TogleWinkelLeft="0" TogleWinkelRight="360" VisibleWaves="1" BNC_StartReverse="False" ValueOffset="0" FadeCenter="True" FadeAmplitude="True" FadePhase="True" FadeRpM="False" UsedCenter="True" UsedAmplitude="True" UsedPhase="True" UsedRpM="True" InFadeRate="100" OutFadeRate="100" FadeType="0" DelayType="0"></Item>\n'
            + '      <Item UID="65508" PatternGUID="" Amplitude="0" Center="0" EffectGUID="" InDelayPoint="0" InFadePoint="100" Offset="0" OutDelayPoint="0" OutFadePoint="100" MaxPhase="0" Phase="' + posZ +
            '" RpM="0" NumWaves="1" GoOut="0" CutAfter="1" SelectionIndex="0" Direction="0" TogleWinkelLeft="0" TogleWinkelRight="360" VisibleWaves="1" BNC_StartReverse="False" ValueOffset="0" FadeCenter="True" FadeAmplitude="True" FadePhase="True" FadeRpM="False" UsedCenter="True" UsedAmplitude="True" UsedPhase="True" UsedRpM="True" InFadeRate="100" OutFadeRate="100" FadeType="0" DelayType="0"></Item>\n'
            + '      <Item UID="65512" PatternGUID="" Amplitude="0" Center="0" EffectGUID="" InDelayPoint="0" InFadePoint="100" Offset="0" OutDelayPoint="0" OutFadePoint="100" MaxPhase="0" Phase="' + rotX +
            '" RpM="0" NumWaves="1" GoOut="0" CutAfter="1" SelectionIndex="0" Direction="0" TogleWinkelLeft="0" TogleWinkelRight="360" VisibleWaves="1" BNC_StartReverse="False" ValueOffset="0" FadeCenter="True" FadeAmplitude="True" FadePhase="True" FadeRpM="False" UsedCenter="True" UsedAmplitude="True" UsedPhase="True" UsedRpM="True" InFadeRate="100" OutFadeRate="100" FadeType="0" DelayType="0"></Item>\n'
            + '      <Item UID="65516" PatternGUID="" Amplitude="0" Center="0" EffectGUID="" InDelayPoint="0" InFadePoint="100" Offset="0" OutDelayPoint="0" OutFadePoint="100" MaxPhase="0" Phase="' + rotY +
            '" RpM="0" NumWaves="1" GoOut="0" CutAfter="1" SelectionIndex="0" Direction="0" TogleWinkelLeft="0" TogleWinkelRight="360" VisibleWaves="1" BNC_StartReverse="False" ValueOffset="0" FadeCenter="True" FadeAmplitude="True" FadePhase="True" FadeRpM="False" UsedCenter="True" UsedAmplitude="True" UsedPhase="True" UsedRpM="True" InFadeRate="100" OutFadeRate="100" FadeType="0" DelayType="0"></Item>\n'
            + '      <Item UID="65520" PatternGUID="" Amplitude="0" Center="0" EffectGUID="" InDelayPoint="0" InFadePoint="100" Offset="0" OutDelayPoint="0" OutFadePoint="100" MaxPhase="0" Phase="' + rotZ +
            '" RpM="0" NumWaves="1" GoOut="0" CutAfter="1" SelectionIndex="0" Direction="0" TogleWinkelLeft="0" TogleWinkelRight="360" VisibleWaves="1" BNC_StartReverse="False" ValueOffset="0" FadeCenter="True" FadeAmplitude="True" FadePhase="True" FadeRpM="False" UsedCenter="True" UsedAmplitude="True" UsedPhase="True" UsedRpM="True" InFadeRate="100" OutFadeRate="100" FadeType="0" DelayType="0"></Item>\n'
            + '    </Items>\n'
            + '  <WayPoints PointData=""></WayPoints>\n'
            + '</scene>\n'
        )

    insertString1 = insertString1 + ""
    insertString2 = insertString2 + "</SceneList>"

    f = open(path + '/fullsequence.xml', 'w')
    f.write(string1 + insertString1 + string2 + insertString2 + string3)
    f.close()

    gui.MessageDialog("Camera Export Successful")


if __name__ == '__main__':
    main()
