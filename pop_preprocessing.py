import glob
import os
import rasterio
import gdal
import numpy as np
import osr 
import matplotlib.pyplot as plt


class tiffHandle(object):
    def __init__(self,in_filename,out_filename):
        self.input = in_filename
        self.output = out_filename
        self.readReprojRaster()

    def readReprojRaster(self):
        '''
        Read a geotiff in to RAM
        '''
        print("-- Reading in raster --")
        # open a dataset object
        self.ds = gdal.Warp(str(self.output), self.input, xRes=30, yRes=-30, dstSRS='EPSG:3857', outputType=gdal.GDT_Float32, srcNodata=np.nan, dstNodata=np.nan)
    
        # read data from geotiff object
        self.nX=self.ds.RasterXSize             # number of pixels in x direction
        self.nY=self.ds.RasterYSize             # number of pixels in y direction
        # geolocation tiepoint
        transform_ds = self.ds.GetGeoTransform()# extract geolocation information
        self.xOrigin=transform_ds[0]       # coordinate of x corner
        self.yOrigin=transform_ds[3]       # coordinate of y corner
        self.pixelWidth=transform_ds[1]    # resolution in x direction
        self.pixelHeight=transform_ds[5]   # resolution in y direction
        # read data. Returns as a 2D numpy array
        self.data=self.ds.GetRasterBand(1).ReadAsArray(0,0,self.nX,self.nY)
    
    def classRaster(self):
        """
            Reclassing extreme pixels to achieve a normal distribution
        """
        print('-- Cleaning raster --')
        self.p99 = np.nanpercentile(self.data, 99)

        # Reclass values above 99th percentile as 99th percentile 
        self.data[(self.data >= self.p99)] = self.p99

        # Reclass values below 0.1 as 0
        self.data[(self.data < 0.1)] = 0

        # Reclassing no data as 0
        self.data[(np.isnan(self.data))] = 0

    def norm(self,x,min,max):
        """
            Normalisation function
        """
        z = ((x-min)/(max-min))*255
        return z

    def normRaster(self):
        """
            Function to scale a raster 0-255
        """
        max_data = np.nanmax(self.data)
        min_data = np.nanmin(self.data)

        print('-- Normalising raster --')
        self.data_normalised = np.array([self.norm(x, min=min_data, max=max_data) for x in self.data])

    def writeTiff(self,epsg=3857):
        """
            Create output raster
        """
        # set geolocation information (note geotiffs count down from top edge in Y)
        geotransform = (self.xOrigin, self.pixelWidth, 0, self.yOrigin, 0, self.pixelHeight)

        # load data in to geotiff object
        dst_ds = gdal.GetDriverByName('GTiff').Create(self.output, self.nX, self.nY, 1, gdal.GDT_Float32)
        dst_ds.SetGeoTransform(geotransform)    # specify coords
        srs = osr.SpatialReference()            # establish encoding
        srs.ImportFromEPSG(epsg)                # set crs
        dst_ds.SetProjection(srs.ExportToWkt()) # export coords to file
        dst_ds.GetRasterBand(1).WriteArray(self.data_normalised)  # write image to the raster
        dst_ds.GetRasterBand(1).SetNoDataValue(np.nan)  # set no data value
        dst_ds.FlushCache()                     # write to disk
        dst_ds = None
        
        print("Image written to",self.output)

######### Processing POP layer ###########
# Finding and standardising each country scene file
pop_tif_obj = tiffHandle(in_filename='../../HRSL/MALAWI/malawi_hrsl_no_anom.tif',out_filename='../../HRSL/malawi_pop_4fill.tif')
pop_tif_obj.classRaster()
pop_tif_obj.normRaster()
pop_tif_obj.writeTiff()

print('Population preprocessed image written.')

