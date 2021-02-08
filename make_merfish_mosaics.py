import numpy as np
import pandas as pd
import imageio
import matplotlib.pyplot as plt
import os.path
from os import path

#modify these variables as necessary
ANALYSIS_HOME = '/broad/clearylab/Users/zheng/microglia_control/MicrogliaDay1Output' #Merlin output folder
DATASET = 'slice1side1' #dataset name
CODEBOOK_NAME='codebook_0_VZG114_codebook.csv' #Name of codebook in the analysis folder
LIST_GENES = [0] #List gene indices to plot
DOWNSAMPLE_FACTOR = 1 #Produce images that are the the size of the mosaic divided by the downsample_factor on each dimension
SQUARE_3PX=False #Whether you want to plot spots as a 3x3 pixel square, otherwise it is just 1 pixel

if path.exists(ANALYSIS_HOME+"/"+DATASET+"/merfish_mosaics/new_barcodes.csv"):
    barcodes = pd.read_csv(ANALYSIS_HOME+"/"+DATASET+"/merfish_mosaics/new_barcodes.csv")
else:
    #read files
    barcodes = pd.read_csv(ANALYSIS_HOME+"/"+DATASET+'/ExportBarcodes/barcodes.csv')
    codebook = pd.read_csv(ANALYSIS_HOME+"/"+DATASET+'/'+CODEBOOK_NAME)
    m= pd.read_csv(ANALYSIS_HOME+"/"+DATASET+'/GenerateMosaic/micron_to_mosaic_pixel_transform.csv', index_col=None, header=None, sep = ' ')

    #perform transformation
    m.columns=["global_x","global_y","one"]
    barcodes["one"]=np.ones((len(barcodes),1))
    barcodes[["newx","newy","newh"]]=barcodes[["global_x","global_y","one"]]@m.T 

    #save new barcodes
    barcodes.to_csv(ANALYSIS_HOME+"/"+DATASET+'/merfish_mosaics/new_barcodes.csv')

#get mosaic size
#You can get the shape from any mosaic, so change the image being read as necessary if you don't have this
try:
    gm = imageio.imread(ANALYSIS_HOME+"/"+DATASET+"/GenerateMosaic/images/mosaic_DAPI_0.tif")
except:
    print("no DAPI mosaic at this location")
mosaic_shape = gm.shape
new_mosaic_shape = [x//DOWNSAMPLE_FACTOR for x in mosaic_shape]

#create images
for gene_id in LIST_GENES:
    barcodes_gene = barcodes.loc[barcodes['barcode_id']==gene_id]
    blank_np = np.zeros(new_mosaic_shape, dtype=np.uint8)
    for row in barcodes_gene.iterrows():
        x = int(row[1]['newx']//DOWNSAMPLE_FACTOR)
        y = int(row[1]['newy']//DOWNSAMPLE_FACTOR)
        if SQUARE_3PX:
            for i in range(-1,2):
                for j in range(-1,2):
                    new_x = x+i
                    new_y = y+j
                    blank_np[new_y,new_x]=255
        else:
            blank_np[y,x]=255
    #write
    #gene_name = codebook.iloc[gene_id]['name'] #conversion to save images with names instead of IDs
    imageio.imwrite(ANALYSIS_HOME+"/"+DATASET+"/merfish_mosaics/mask_"+str(gene_id)+".tif", blank_np)