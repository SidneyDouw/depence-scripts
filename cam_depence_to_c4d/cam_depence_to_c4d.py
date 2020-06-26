import os
import xml.etree.ElementTree as ET
import string
import math

import c4d
from c4d import documents
from c4d import storage
from c4d.gui import GeDialog


class Dialog(GeDialog):

    document_fps = 30
    camera_fov = 55

    didPressOK = False

    def CreateLayout(self):

        self.SetTitle("Make VPad Camera")

        self.GroupBegin(111, c4d.BFH_SCALEFIT, cols=2)
        self.AddStaticText(1000, c4d.BFH_LEFT, name="Sequence FPS", initw=200)
        self.AddEditSlider(1001, c4d.BFH_SCALEFIT)
        self.SetInt32(1001, self.document_fps, min=12, max=60, step=1, min2=1, max2=200)
        self.GroupEnd()

        self.GroupBegin(112, c4d.BFH_SCALEFIT, cols=2)
        self.AddStaticText(1002, c4d.BFH_LEFT, name="Camera FOV", initw=200)
        self.AddEditSlider(1003, c4d.BFH_SCALEFIT)
        self.SetFloat(1003, self.camera_fov, min=0, max=200, step=1, max2=10000, format=c4d.FORMAT_FLOAT)
        self.GroupEnd()

        self.AddButton(9999, c4d.BFH_CENTER, name="OK", initw=100, inith=12)
        # self.AddButton(10000, c4d.BFH_CENTER, name = "Cancel", initw = 100, inith = 12)
        return True

    def Command(self, id, msg):

        if id == 9999:
            self.document_fps = self.GetInt32(1001)
            self.camera_fov = self.GetInt32(1003)
            self.didPressOK = True
            self.Close()

            return True

        return False


def main():

    dlg = Dialog()
    dlg.Open(c4d.DLG_TYPE_MODAL_RESIZEABLE, defaultw=500)

    if not dlg.didPressOK:
        return

    DOCUMENT_FPS = dlg.document_fps
    CAMERA_FOV = dlg.camera_fov

    path = storage.LoadDialog(flags=2)

    if not path:
        print "No path found"
        return

    camInfoArr = parseXML(path)
    lastEl = camInfoArr[len(camInfoArr) - 1]

    # Setup document
    doc = documents.GetActiveDocument()
    doc.SetFps(DOCUMENT_FPS)
    doc.SetMaxTime(c4d.BaseTime(lastEl['startTime'] + lastEl['length']))

    rd = doc.GetActiveRenderData()
    rd[c4d.RDATA_FRAMERATE] = DOCUMENT_FPS

    # Create, setup and insert Camera object
    camera = c4d.BaseObject(c4d.Ocamera)
    camera[c4d.CAMERAOBJECT_FOV_VERTICAL] = CAMERA_FOV * math.pi/180
    doc.InsertObject(camera)

    posXtrack = c4d.CTrack(camera, [c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_X])
    posYtrack = c4d.CTrack(camera, [c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Y])
    posZtrack = c4d.CTrack(camera, [c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Z])
    rotXtrack = c4d.CTrack(camera, [c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X])
    rotYtrack = c4d.CTrack(camera, [c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y])
    rotZtrack = c4d.CTrack(camera, [c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z])

    camera.InsertTrackSorted(posXtrack)
    camera.InsertTrackSorted(posYtrack)
    camera.InsertTrackSorted(posZtrack)
    camera.InsertTrackSorted(rotXtrack)
    camera.InsertTrackSorted(rotYtrack)
    camera.InsertTrackSorted(rotZtrack)

    posXcurve = posXtrack.GetCurve()
    posYcurve = posYtrack.GetCurve()
    posZcurve = posZtrack.GetCurve()
    rotXcurve = rotXtrack.GetCurve()
    rotYcurve = rotYtrack.GetCurve()
    rotZcurve = rotZtrack.GetCurve()

    previousTransform = [0, 0, 0, 0, 0, 0]

    for camInfo in camInfoArr:

        startTime = camInfo['startTime']
        length = camInfo['length']
        endTime = startTime + length

        curveType = camInfo['curveType']

        posXkeyStart = c4d.CKey()
        posYkeyStart = c4d.CKey()
        posZkeyStart = c4d.CKey()
        rotXkeyStart = c4d.CKey()
        rotYkeyStart = c4d.CKey()
        rotZkeyStart = c4d.CKey()

        # Set StartTime values
        posXkeyStart.SetTime(posXcurve, c4d.BaseTime(startTime))
        posXkeyStart.SetValue(posXcurve, previousTransform[0])
        posYkeyStart.SetTime(posYcurve, c4d.BaseTime(startTime))
        posYkeyStart.SetValue(posYcurve, previousTransform[1])
        posZkeyStart.SetTime(posZcurve, c4d.BaseTime(startTime))
        posZkeyStart.SetValue(posZcurve, previousTransform[2])
        rotXkeyStart.SetTime(rotXcurve, c4d.BaseTime(startTime))
        rotXkeyStart.SetValue(rotXcurve, previousTransform[3])
        rotYkeyStart.SetTime(rotYcurve, c4d.BaseTime(startTime))
        rotYkeyStart.SetValue(rotYcurve, previousTransform[4])
        rotZkeyStart.SetTime(rotZcurve, c4d.BaseTime(startTime))
        rotZkeyStart.SetValue(rotZcurve, previousTransform[5])

        if (curveType == "Sinus"):
            tangentLength = c4d.BaseTime(length * (4.0/15.0))
            nTangentLength = c4d.BaseTime(length * (4.0/15.0) * -1)

            # posXkeyStart.SetTimeLeft(posXcurve, nTangentLength)
            posXkeyStart.SetTimeRight(posXcurve, tangentLength)
            # posYkeyStart.SetTimeLeft(posYcurve, nTangentLength)
            posYkeyStart.SetTimeRight(posYcurve, tangentLength)
            # posZkeyStart.SetTimeLeft(posZcurve, nTangentLength)
            posZkeyStart.SetTimeRight(posZcurve, tangentLength)
            # rotXkeyStart.SetTimeLeft(rotXcurve, nTangentLength)
            rotXkeyStart.SetTimeRight(rotXcurve, tangentLength)
            # rotYkeyStart.SetTimeLeft(rotYcurve, nTangentLength)
            rotYkeyStart.SetTimeRight(rotYcurve, tangentLength)
            # rotZkeyStart.SetTimeLeft(rotZcurve, nTangentLength)
            rotZkeyStart.SetTimeRight(rotZcurve, tangentLength)

        posXcurve.InsertKey(posXkeyStart)
        posYcurve.InsertKey(posYkeyStart)
        posZcurve.InsertKey(posZkeyStart)
        rotXcurve.InsertKey(rotXkeyStart)
        rotYcurve.InsertKey(rotYkeyStart)
        rotZcurve.InsertKey(rotZkeyStart)

        # Set EndTime values
        posXkeyEnd = c4d.CKey()
        posYkeyEnd = c4d.CKey()
        posZkeyEnd = c4d.CKey()
        rotXkeyEnd = c4d.CKey()
        rotYkeyEnd = c4d.CKey()
        rotZkeyEnd = c4d.CKey()

        posXkeyEnd.SetTime(posXcurve, c4d.BaseTime(endTime))
        posXkeyEnd.SetValue(posXcurve, camInfo['transform'][0])
        posYkeyEnd.SetTime(posYcurve, c4d.BaseTime(endTime))
        posYkeyEnd.SetValue(posYcurve, camInfo['transform'][1])
        posZkeyEnd.SetTime(posZcurve, c4d.BaseTime(endTime))
        posZkeyEnd.SetValue(posZcurve, camInfo['transform'][2])
        rotXkeyEnd.SetTime(rotXcurve, c4d.BaseTime(endTime))
        rotXkeyEnd.SetValue(rotXcurve, camInfo['transform'][3])
        rotYkeyEnd.SetTime(rotYcurve, c4d.BaseTime(endTime))
        rotYkeyEnd.SetValue(rotYcurve, camInfo['transform'][4])
        rotZkeyEnd.SetTime(rotZcurve, c4d.BaseTime(endTime))
        rotZkeyEnd.SetValue(rotZcurve, camInfo['transform'][5])

        if (curveType == "Sinus"):
            tangentLength = c4d.BaseTime(length * (4.0/15.0))
            nTangentLength = c4d.BaseTime(length * (4.0/15.0) * -1)

            posXkeyEnd.SetTimeLeft(posXcurve, nTangentLength)
            # posXkeyEnd.SetTimeRight(posXcurve, tangentLength)
            posYkeyEnd.SetTimeLeft(posYcurve, nTangentLength)
            # posYkeyEnd.SetTimeRight(posYcurve, tangentLength)
            posZkeyEnd.SetTimeLeft(posZcurve, nTangentLength)
            # posZkeyEnd.SetTimeRight(posZcurve, tangentLength)
            rotXkeyEnd.SetTimeLeft(rotXcurve, nTangentLength)
            # rotXkeyEnd.SetTimeRight(rotXcurve, tangentLength)
            rotYkeyEnd.SetTimeLeft(rotYcurve, nTangentLength)
            # rotYkeyEnd.SetTimeRight(rotYcurve, tangentLength)
            rotZkeyEnd.SetTimeLeft(rotZcurve, nTangentLength)
            # rotZkeyEnd.SetTimeRight(rotZcurve, tangentLength)

        posXcurve.InsertKey(posXkeyEnd)
        posYcurve.InsertKey(posYkeyEnd)
        posZcurve.InsertKey(posZkeyEnd)
        rotXcurve.InsertKey(rotXkeyEnd)
        rotYcurve.InsertKey(rotYkeyEnd)
        rotZcurve.InsertKey(rotZkeyEnd)

        # Set previousTransform to endTime
        previousTransform = [
            camInfo['transform'][0],
            camInfo['transform'][1],
            camInfo['transform'][2],
            camInfo['transform'][3],
            camInfo['transform'][4],
            camInfo['transform'][5]
        ]


def parseXML(sequence):

    sequenceFile = os.path.join(sequence, 'fullsequence.xml')

    tree = ET.parse(sequenceFile)

    tracks = tree.find('tracks')
    sceneList = tree.find('SceneList')

    camInfoArr = []

    if tracks is None:
        print("No 'Tracks' tag found")
        return

    if sceneList is None:
        print("No 'SceneList' tag found")
        return

    for block in tracks[0][0]:
        startTime = float(safeGet(block, "StartTime"))
        length = float(safeGet(block, "Lenght"))
        fadeInTime = float(safeGet(block, "FadeInTime"))
        sceneGUID = safeGet(block, "MultiSceneGUID")

        scene = sceneList.find("scene[@GUID='" + sceneGUID + "']")
        items = scene[0]

        camInfo = {
            'startTime': startTime,
            'length': length,
            'fadeInTime': fadeInTime,
            'curveType': None,
            'transform': []
        }

        for i, item in enumerate(items):
            # Get transform value
            value = safeGet(item, "Phase")

            # Check for the curve type
            fadeType = None
            try:
                fadeType = safeGet(item, "FadeType")
            except:
                pass

            delayType = None
            try:
                delayType = safeGet(item, "DelayType")
            except:
                pass

            curveType = None

            if fadeType == "1" and delayType == "1":
                curveType = "Sinus"
            elif fadeType is None and delayType is None:
                curveType = "Linear"
            else:
                print "Weird case:\n"
                print "FadeType: " + str(fadeType) + ", DelayType: " + str(delayType)
                return

            camInfo['curveType'] = curveType

            # Cast value to number and remap them
            value = float(string.replace(value, ",", "."))
            if (i <= 2):
                value = value * 100
            if (i > 2):
                value = value * math.pi/180
            if (i == 2 or i == 3 or i == 4):
                value = value * -1
            value = round(value, 4)
            camInfo['transform'].append(value)

        camInfoArr.append(camInfo)

    return camInfoArr


def safeGet(elem, attrib):
    val = elem.get(attrib)
    if val is not None:
        return val
    else:
        raise Exception("Attribute '" + str(attrib) + "' not found in '" + str(elem.tag) + "'")


if __name__ == "__main__":
    main()
