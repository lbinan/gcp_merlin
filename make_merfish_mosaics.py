import numpy as np
import pandas as pd
import imageio
import matplotlib.pyplot as plt
import os
from os import path
from glob import glob

def merfish_mosaic(
    DATASET= '/broad/clearylab/Users/zheng/microglia_control/MicrogliaDay1Output/slice1side1/' ,#dataset name
    CODEBOOK_NAME='codebook_0_VZG114_codebook.csv',
    LIST_GENES = [0],
    DOWNSAMPLE_FACTOR = 1,
    SQUARE_3PX=False,
    Z=None
    ):
    """
    Parameters:
    DATASET - path to dataset
    CODEBOOK_NAME - name of codebook file
    LIST_GENES - list of gene indices to make mosaics from
    DOWNSAMPLE_FACTOR = produce image that has the dimensions of the original image divided by the DOWNSAMPLE_FACTOR
    SQUARE_3PX - make each spot a 3 pixel square, if false then each spot is 1 pixel
    Z = number of z slices, leave None if you want a 2D image of all spots across Z-planes
    
    
    Output: writes image files inside the DATASET/merfish_mosaics folder
    """
    #add slash to DATASET if none
    if DATASET[-1]!="/":
        DATASET += "/"
        
    if path.exists(DATASET+"merfish_mosaics/new_barcodes.csv"):
        barcodes = pd.read_csv(DATASET+"merfish_mosaics/new_barcodes.csv")
        codebook = pd.read_csv(DATASET+CODEBOOK_NAME)
        #DELETE OLD FILES
        #mydir = DATASET+"merfish_mosaics/"
        #filelist = [ f for f in os.listdir(mydir) if f.endswith(".tif") ]
        #for f in filelist:
        #    os.remove(os.path.join(mydir, f))
    else:
        #read files
        barcodes = pd.read_csv(DATASET+'ExportBarcodes/barcodes.csv')
        codebook = pd.read_csv(DATASET+CODEBOOK_NAME)
        m= pd.read_csv(DATASET+'GenerateMosaic/micron_to_mosaic_pixel_transform.csv', index_col=None, DATASET=None, sep = ' ')

        #perform transformation
        m.columns=["global_x","global_y","one"]
        barcodes["one"]=np.ones((len(barcodes),1))
        barcodes[["newx","newy","newh"]]=barcodes[["global_x","global_y","one"]]@m.T 

        #save new barcodes
        barcodes.to_csv(DATASET+'merfish_mosaics/new_barcodes.csv')

    #get mosaic size
    #You can get the shape from any mosaic, so change the image being read as necessary if you don't have this
    try:
        gm = imageio.imread(DATASET+"GenerateMosaic/images/mosaic_DAPI_0.tif")
    except:
        print("no DAPI mosaic at this location")
    mosaic_shape = gm.shape
    new_mosaic_shape = [x//DOWNSAMPLE_FACTOR for x in mosaic_shape]

    #create images
    if Z == None:
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
            gene_name = codebook.iloc[gene_id]['name'] #conversion to save images with names instead of IDs
            imageio.imwrite(DATASET+"merfish_mosaics/mask_"+str(gene_name)+".tif", blank_np)
    else:
        for gene_id in LIST_GENES:
            for z in range(Z):
                barcodes_gene =barcodes.loc[np.logical_and(barcodes['barcode_id']==gene_id ,barcodes['global_z']==z)]
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
                gene_name = codebook.iloc[gene_id]['name'] #conversion to save images with names instead of IDs
                imageio.imwrite(DATASET+"merfish_mosaics/"+str(gene_name)+"_"+str(z)+".tif", blank_np)
