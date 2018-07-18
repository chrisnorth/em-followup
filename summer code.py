#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  3 09:56:42 2018

@author: lewis
"""
from __future__ import division
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as cm
from scipy import ndimage
from scipy import signal
import scipy.signal as sg
from astropy.io import fits
from PIL import Image
import astropy.stats
import numpy.ma
import importlib
importlib.import_module('mpl_toolkits.mplot3d').Axes3D
from skimage import img_as_bool, io, color, morphology
from skimage.morphology import skeletonize
from skimage import measure
from numpy import random
from scipy import signal
from skimage import measure
import copy
from astropy.wcs import WCS
from astropy.io import fits
from astropy.utils.data import get_pkg_data_filename
from astropy.coordinates import ICRS, Galactic
from astropy import units as u
import matplotlib.ticker as mticker
import math
from matplotlib.colors import LogNorm
from reproject import reproject_interp
import os


'''
--------------------------------------------------------------------
'''

#SECTION 1 - LOAD IN IMAGES AND EXTRACT COORDINATES
#REQUIREMENTS
#2 comparison images of single target
#within a folder named e.g. 'keyword'
#images must have same name keyword as folder i.e. 'keyword_1', 'keyword_2'
#'keyword' folder saved in folder named 'images'
#also, create 'new_images' & 'fits_images' folders at same level as 'images' folder
#make sure 'new_images' & 'fits_images' folders are empty to begin 


#path_images is the directory to 'images' folder 
#getimage function opens one 'keyword' folder in 'images'
#extracts fitsheader of the 2 comparison images  inside
#extracts word coordinate system (wcs)

def getimage(path_general,keyword):

    path=path_general+'/images/%s/%s_1.fits'%(keyword,keyword)
    hdu_list1=fits.open(path)
    hdu1 = fits.open(path)[0]
    wcs1 = WCS(hdu1.header)
    image_data1=hdu1.data
    hdu_list1.close()
    
    path=path_general+'/images/%s/%s_2.fits'%(keyword,keyword)
    hdu_list2=fits.open(path)
    hdu2 = fits.open(path)[0]
    wcs2 = WCS(hdu2.header)
    image_data2=hdu2.data
    hdu_list2.close()
    
    return hdu1,wcs1,image_data1,hdu2,wcs2,image_data2



#similar function used later for extracting new fits images 
def get_fitsimage(path_general,keyword):

    path=path_general+'/fits_images/%s_1.fits'%(keyword)
    hdu1 = fits.open(path)[0]
    wcs1 = WCS(hdu1.header)
    image_data1=hdu1.data
    
    path=path_general+'/fits_images/%s_2.fits'%(keyword)
    hdu2 = fits.open(path)[0]
    wcs2 = WCS(hdu2.header)
    image_data2=hdu2.data

    return image_data1,image_data2,hdu1,hdu2,wcs1,wcs2



#function which extracts coordinates 
def coords(data1,data2,system,system2): 
    x=data1.shape[1]
    y=data1.shape[0]
    grid=np.ones((y,x))
    points=np.where(grid==1)
    pointsy,pointsx=points[0],points[1]
    coords1=system.wcs_pix2world(pointsx,pointsy,1)
    coordsy,coordsx=coords1[1],coords1[0]
    c_join=(coordsy,coordsx)
    return c_join,points



#function which takes new fits files and saves them as .png files
def save_png(name,Vmin,Vmax,path_general,wcs,sub,title):
    if sub=='yes':
        fits_data = fits.getdata(path_general+'/subtraction/%s'%name)
        plt.subplot(projection=wcs)
        plt.imshow(fits_data,vmin=Vmin,vmax=Vmax, cmap='PuRd_r',logNorm=True)
        plt.grid(color='white', ls='solid')
        plt.colorbar()
        plt.title('%s'%title)
        imagename = name.replace('.fits', '.png')
        plt.savefig(path_general+'/subtraction/%s'%imagename)
    else:
        fits_data = fits.getdata(path_general+'/fits_images/%s'%name)
        plt.subplot(projection=wcs)
        plt.imshow(fits_data,vmin=Vmin,vmax=Vmax, cmap='PuRd_r',logNorm=True)
        plt.grid(color='white', ls='solid')
        plt.colorbar()
        plt.title('%s'%title)
        imagename = name.replace('.fits', '.png')
        plt.savefig(path_general+'/new_images/%s'%imagename)
        plt.close('all')
    



#'path_images' : path to imagaes folder containing multiple 'name' folders  
#'path_fits' : path to folder where new .fits images are saved
#'path_new' : path to folder where new .png images are to be saved 

#function that crops & rotates images, and re-sizes pixels, normalise brightness
#so that both images have same format
#save as fits images in folder 'fits_images'
def CPR(path_general):
    print('CPR')
    #for each file in 'images' folder, load data & wcs, get coordinates of pixels
    for filename in os.listdir(path_general+'/images'):
        if filename=='.DS_Store': #problematic folder that shows up sometimes
            print('.')
        else:
            hdu1,wcs1,image_data1,hdu2,wcs2,image_data2=getimage(path_general,filename)        
            coordinates1,points1 = coords(image_data1,image_data2,wcs1,wcs2)
            coordinates2,points2 = coords(image_data2,image_data1,wcs2,wcs1)
            
            #rough estimate of which image is bigger (only repormat the larger image)
            xrange1 = max(coordinates1[1])-min(coordinates1[1])
            xrange2 = max(coordinates2[1])-min(coordinates2[1])
            yrange1 = max(coordinates1[0])-min(coordinates1[0])
            yrange2 = max(coordinates2[0])-min(coordinates2[0])
            
            if xrange1>=xrange2 : 
                if  yrange1>= yrange2:
                    new_image_data1, footprint = reproject_interp(hdu1, hdu2.header)
                    new_image_data2=image_data2 #reproject reformats image to same format
                    wcs=wcs2
                else:
                    if np.abs(xrange1-xrange2)>np.abs(yrange1-yrange2):
                        new_image_data1, footprint = reproject_interp(hdu1, hdu2.header)
                        new_image_data2=image_data2 #reproject reformats image to same format
                        wcs=wcs2
                    else:
                        new_image_data2, footprint = reproject_interp(hdu2, hdu1.header)
                        new_image_data1=image_data1
                        wcs=wcs1
                        
            if xrange2>xrange1 :
                if  yrange2>=yrange1:
                    new_image_data2, footprint = reproject_interp(hdu2, hdu1.header)
                    new_image_data1=image_data1
                    wcs=wcs1
                
                else:
                    if np.abs(xrange1-xrange2)>np.abs(yrange1-yrange2):
                        new_image_data2, footprint = reproject_interp(hdu2, hdu1.header)
                        new_image_data1=image_data1 #reproject reformats image to same format
                        wcs=wcs1
                    
                    else:
                        new_image_data1, footprint = reproject_interp(hdu1, hdu2.header)
                        new_image_data2=image_data2 #reproject reformats image to same format
                        wcs=wcs2
                        
                    
                    
            if xrange2==xrange1:
                if  yrange2>yrange1:
                    new_image_data2, footprint = reproject_interp(hdu2, hdu1.header)
                    new_image_data1=image_data1
                    wcs=wcs1
                else:
                    if np.abs(xrange1-xrange2)>np.abs(yrange1-yrange2):
                        new_image_data2, footprint = reproject_interp(hdu2, hdu1.header)
                        new_image_data1=image_data1 #reproject reformats image to same format
                        wcs=wcs1
                        
            new_image_data1=ndimage.filters.gaussian_filter(new_image_data1,3)
            new_image_data2=ndimage.filters.gaussian_filter(new_image_data2,3)
            
            
            if os.path.exists(path_general+'/fits_images/%s_1.fits'%filename)==True:
                os.remove(path_general+'/fits_images/%s_1.fits'%filename)
                os.remove(path_general+'/fits_images/%s_2.fits'%filename)
            header=wcs.to_header()
            hdu = fits.PrimaryHDU(new_image_data1,header=header)
            hdul = fits.HDUList([hdu])
            hdul.writeto(path_general+'/fits_images/%s_1.fits'%filename)
            
            hdu = fits.PrimaryHDU(new_image_data2,header=header)
            hdul = fits.HDUList([hdu])
            hdul.writeto(path_general+'/fits_images/%s_2.fits'%filename)
            
            
            
            
#change brightness
def bright_diff(path_general):
    print('bright_diff')
    for filename in os.listdir(path_general+'/images'):
        print(filename)
        if filename=='.DS_Store': #problematic folder that shows up sometimes
            print('.')
        else:
            new_image_data1,new_image_data2,hdu1,hdu2,wcs1,wcs2=get_fitsimage(path_general,filename)
            new_image_data1=ndimage.filters.gaussian_filter(new_image_data1,3)
            new_image_data2=ndimage.filters.gaussian_filter(new_image_data2,3)
            
            pool1=new_image_data1[np.isfinite(new_image_data1)]
            pool2=new_image_data2[np.isfinite(new_image_data1)]
            
            pool2=pool2[~np.isnan(pool1)]
            pool1=pool1[~np.isnan(pool1)]
            
            pool1=pool1[np.isfinite(pool2)]
            pool2=pool2[np.isfinite(pool2)]
            
            pool1=pool1[~np.isnan(pool2)]
            pool2=pool2[~np.isnan(pool2)]
            wholepool1=copy.deepcopy(pool1)
            wholepool2=copy.deepcopy(pool2)
            
            #want to isolate bright objects, limit pool to 50-80 percentiles 
            
#            l1,u1=np.percentile(pool1,[25,75])
#            l2,u2=np.percentile(pool2,[25,75])
#            
#            pool1=pool1[np.where(pool1>l1)]
#            pool2=pool2[np.where(pool1>l1)]
#            
#            pool1=pool1[np.where(pool1<u1)]    
#            pool2=pool2[np.where(pool1<u1)]
#            
#            pool1=pool1[np.where(pool2>l2)]
#            pool2=pool2[np.where(pool2>l2)]
#                                 
#            pool1=pool1[np.where(pool2<u2)]                  
#            pool2=pool2[np.where(pool2<u2)] 
            
            
            rms1=np.std(pool1)
            mean1=np.mean(pool1)
            rms2=np.std(pool2)
            mean2=np.mean(pool2)
            print(rms1,mean1,rms2,mean2)
            
            new_image_data1=new_image_data1-mean1
            new_image_data1=new_image_data1/rms1
            
            new_image_data2=new_image_data2-mean2
            new_image_data2=new_image_data2/rms2
            
            new_image_data1[np.where(new_image_data1)<0]=0
            new_image_data2[np.where(new_image_data2)<0]=0
            
            
#            ave_bright1=np.mean(pool1)
#            ave_bright2=np.mean(pool2)
#            diff=np.mean(ave_bright1-ave_bright2)
           
                
            
#            diff_accum = 0
#            newpool=pool2
#            
#            for i in range (5):
#                newpool += diff
#                diff_accum += diff
#                diff=np.mean(pool1-newpool)

#            new_image_data2=new_image_data2+diff
            os.remove(path_general+'/fits_images/%s_2.fits'%filename) #remove old file
            os.remove(path_general+'/fits_images/%s_1.fits'%filename)
            wcs=wcs2
            header=wcs.to_header()
            hdu = fits.PrimaryHDU(new_image_data2,header=header) #write new file
            hdul = fits.HDUList([hdu])
            hdul.writeto(path_general+'/fits_images/%s_2.fits'%filename)
            
            header=wcs.to_header()
            hdu = fits.PrimaryHDU(new_image_data1,header=header) #write new file
            hdul = fits.HDUList([hdu])
            hdul.writeto(path_general+'/fits_images/%s_1.fits'%filename)
            
            
#function to make subtraction images 
def sub(path_general):
    print('sub')
    for filename in os.listdir(path_general+'/images'):
        if filename=='.DS_Store': #problematic folder that shows up sometimes
            print('.')
        else:
            new_image_data1,new_image_data2,hdu1,hdu2,wcs1,wcs2=get_fitsimage(path_general,filename)
            print(filename)
            subtraction=np.absolute(new_image_data1-new_image_data2)
#            subtraction[~np.isfinite(subtraction)]=0
#            subtraction[np.where(subtraction<20)]=0
#                subtraction=ndimage.filters.gaussian_filter(subtraction,3)
#                mask=np.zeros_like(subtraction)
#                mask[subtraction>np.percentile(subtraction,75)]=1
            #subtraction=ndimage.filters.gaussian_filter(subtraction,3)
            hdu = fits.PrimaryHDU(subtraction) #write new file
            hdul = fits.HDUList([hdu])
            hdul.writeto(path_general+'/subtraction/%s_sub.fits'%filename)
            
#loads files from 'fits_images'
#plots fits images and selects sensible limits 
#saves image as a png file into 'new_images' file 
def out_save(path_general,subtraction):
    print('out_save')
    for filename in os.listdir(path_general+'/images'):
        if filename=='.DS_Store': #problematic folder that shows up sometimes
            print('.')
        else:
            new_image_data1,new_image_data2,hdu1,hdu2,wcs1,wcs2=get_fitsimage(path_general,filename)
            
            #pool of real data (no NaNs)
            pool1=new_image_data1[np.isfinite(new_image_data1)]
            pool1=pool1[~np.isnan(pool1)]
            min1,max1=np.percentile(pool1,[50,95])
            
            
            pool2=new_image_data2[np.isfinite(new_image_data2)]
            pool2=pool2[~np.isnan(pool2)]
#            min2,max2=np.percentile(pool2,[50,95])
            max2,min2=max(pool2),min(pool2)
            max1,min1=max(pool1),min(pool1)
            
            if subtraction=='yes':
                path=path_general+'/subtraction/%s_sub.fits'%(filename)
                hdu_list=fits.open(path)
                hdu = fits.open(path)[0]
                subs=hdu.data
                
                hdu_list.close()
                pools=subs[np.isfinite(subs)]
                pools=pools[~np.isnan(pools)]
                mins,maxs=np.percentile(pools,[50,95])
                mins,maxs=0.5,2
                mins,maxs=min(pools),max(pools)
                print(mins,maxs)
                save_png('%s_sub.fits'%filename,mins,maxs,path_general,wcs1,'yes',filename)
                os.remove(path_general+'/subtraction/%s_sub.fits'%filename)
            
            plt.close('all')
            save_png('%s_1.fits'%filename,min1,max1,path_general,wcs1,'no',max(pools))
            os.remove(path_general+'/fits_images/%s_1.fits'%filename)
            plt.close('all')
            
            save_png('%s_2.fits'%filename,min2,max2,path_general,wcs2,'no',max(pools))
            os.remove(path_general+'/fits_images/%s_2.fits'%filename)
            plt.close('all')
            
            


#path_images='/Users/lewisprole/Documents/University/year3/summer_project/images'
#path_fits='/Users/lewisprole/Documents/University/year3/summer_project/fits_images'
#path_new='/Users/lewisprole/Documents/University/year3/summer_project/new_images'
path_general='/Users/lewisprole/Documents/University/year3/summer_project'
CPR(path_general)
bright_diff(path_general)
sub(path_general)
out_save(path_general,'yes')




