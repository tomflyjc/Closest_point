##Vector=group
##CLosest_Point_V2=name
##Couche_de_Points=vector
##Couche_de_Lignes=vector

"""
This script intent to provide a count as for the SQL Funciton CLosestPoint
Ce script vise a recrÃ©er dans QGIS la Focntion SQL : CLosest Point
It rely on the solutions provided in "Nearest neighbor between a point layer and a line layer"
  http://gis.stackexchange.com/questions/396/nearest-pojected-point-from-a-point-                               layer-on-a-line-or-polygon-outer-ring-layer
V2 du  8 aout 2016
jean-christophe.baudin@onema.fr
"""
from qgis.core import *
from qgis.gui import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import os
import sys
import unicodedata 
from osgeo import ogr
from math import sqrt
from sys import maxint

from processing import *
 
def magnitude(p1, p2):
    if p1==p2: return 1
    else:
        vect_x = p2.x() - p1.x()
        vect_y = p2.y() - p1.y()
        return sqrt(vect_x**2 + vect_y**2)

def intersect_point_to_line(point, line_start, line_end):
    line_magnitude =  magnitude(line_end, line_start)
    u = ((point.x()-line_start.x())*(line_end.x()-line_start.x())+(point.y()-line_start.y())*(line_end.y()-line_start.y()))/(line_magnitude**2)
    # closest point does not fall within the line segment, 
    # take the shorter distance to an endpoint
    if u < 0.0001 or u > 1:
        ix = magnitude(point, line_start)
        iy = magnitude(point, line_end)
        if ix > iy:
            return line_end
        else:
            return line_start
    else:
        ix = line_start.x() + u * (line_end.x() - line_start.x())
        iy = line_start.y() + u * (line_end.y() - line_start.y())
        return QgsPoint(ix, iy)

layerP = processing.getObject(Couche_de_Points)
providerP = layerP.dataProvider()
fieldsP = providerP.fields()
inFeatP = QgsFeature()

layerL = processing.getObject(Couche_de_Lignes)
providerL = layerL.dataProvider()
fieldsL = providerL.fields()
inFeatL = QgsFeature()

counterP = counterL= nElement=0

for featP in layerP.selectedFeatures():
    counterP+=1
if counterP==0:
    QMessageBox.information(None,"information:","Choose at least one point from point layer_"+ str(layerP.name())) 
    
indexLine=QgsSpatialIndex()
for featL in layerL.selectedFeatures():
    indexLine.insertFeature(featL)
    counterL+=1
if counterL==0:
    QMessageBox.information(None,"information:","Choose at least one line from point layer_"+ str(layerL.name()))
    #QMessageBox.information(None,"DEBUGindex:",str(indexBerge))     
ClosestP=QgsVectorLayer("Point", "Projected_ Points_From_"+ str(layerP.name()), "memory")
QgsMapLayerRegistry.instance().addMapLayer(ClosestP)
prClosestP = ClosestP.dataProvider()

for f in fieldsP:
    znameField= f.name()
    Type= str(f.typeName())
    if Type == 'Integer': prClosestP.addAttributes([ QgsField( znameField, QVariant.Int)])
    if Type == 'Real': prClosestP.addAttributes([ QgsField( znameField, QVariant.Double)])
    if Type == 'String': prClosestP.addAttributes([ QgsField( znameField, QVariant.String)])
    else : prClosestP.addAttributes([ QgsField( znameField, QVariant.String)])
prClosestP.addAttributes([QgsField("DistanceP", QVariant.Double),
                                        QgsField("XDep", QVariant.Double),
                                        QgsField("YDep", QVariant.Double),
                                        QgsField("XProj", QVariant.Double),
                                        QgsField("YProj", QVariant.Double),
                                        QgsField("Xmed", QVariant.Double),
                                        QgsField("Ymed", QVariant.Double)])
featsP = processing.features(layerP)
nFeat = len(featsP)
"""
for inFeatP in featsP:
    progress.setPercentage(int(100 * nElement / nFeatL))
    nElement += 1
    # pour avoir l'attribut d'un objet/feat .... 
    attributs = inFeatP.attributes()
"""

for inFeatP in layerP.selectedFeatures():
    progress.setPercentage(int(100 * nElement / counterL))
    nElement += 1
    attributs=inFeatP.attributes()
    geomP=inFeatP.geometry()
    nearest_point = None
    minVal=0.0
    counterSelec=1
    first= True
    nearestsfids=indexLine.nearestNeighbor(geomP.asPoint(),counterSelec)
    #http://blog.vitu.ch/10212013-1331/advanced-feature-requests-qgis
    #layer.getFeatures( QgsFeatureRequest().setFilterFid( fid ) )
    request = QgsFeatureRequest().setFilterFids( nearestsfids )
    #list = [ feat for feat in CoucheL.getFeatures( request ) ]
    # QMessageBox.information(None,"DEBUGnearestIndex:",str(list))
    NBNodes=0
    Dist=DistT=minValT=Distance=0.0
    for featL in  layerL.getFeatures(request):
        geomL=featL.geometry()
        firstM=True
        geomL2=geomL.asPolyline()
        NBNodes=len(geomL2)
        for i in range(1,NBNodes):
            lineStart,lineEnd=geomL2[i-1],geomL2[i]
            ProjPoint=intersect_point_to_line(geomP.asPoint(),QgsPoint(lineStart),QgsPoint(lineEnd))
            Distance=magnitude(geomP.asPoint(),ProjPoint)
            toto=''
            toto=toto+ 'lineStart :'+ str(lineStart)+ '  lineEnd : '+ str(lineEnd)+ '\n'+ '\n'
            toto=toto+ 'ProjPoint '+ str(ProjPoint)+ '\n'+ '\n'
            toto=toto+ 'Distance '+ str(Distance)
            #QMessageBox.information(None,"DEBUG", toto)
            if firstM:
                minValT,nearest_pointT,firstM = Distance,ProjPoint,False
            else:
                if Distance < minValT:
                    minValT=Distance
                    nearest_pointT=ProjPoint
            #at the end of the loop save the nearest point for a line object
            #min_dist=magnitude(ObjetPoint,PProjMin)
            #QMessageBox.information(None,"DEBUG", " Dist min: "+ str(minValT))
        if first:
            minVal,nearest_point,first = minValT,nearest_pointT,False
        else:
            if minValT < minVal:
                minVal=minValT
                nearest_point=nearest_pointT
                #at loop end give the nearest Projected points on Line nearest Line
    PProjMin=nearest_point
    Geom= QgsGeometry().fromPoint(PProjMin)
    min_dist=minVal
    PX=geomP.asPoint().x()
    PY=geomP.asPoint().y()
    Xmed=(PX+PProjMin.x())/2
    Ymed=(PY+PProjMin.y())/2
    newfeat = QgsFeature()
    newfeat.setGeometry(Geom)
    Values=[]
    #Values.extend(attributs)
    fields=layerP.pendingFields()
    Values=[attributs[i] for i in range(len(fields))]
    Values.append(min_dist)
    Values.append(PX)
    Values.append(PY)
    Values.append(PProjMin.x())
    Values.append(PProjMin.y())
    Values.append(Xmed)
    Values.append(Ymed)
    newfeat.setAttributes(Values)
    ClosestP.startEditing()  
    prClosestP.addFeatures([ newfeat ])
    #prClosestP.updateExtents()
ClosestP.commitChanges()
iface.mapCanvas().refresh()            

