The following instructions should be used in conjunction with the [MERlin documentation](https://emanuega.github.io/MERlin/)

# Overview
1. Upload data to Google bucket
2. Create Filestore fileshare instance
3. Deploy cluster
4. SSH into VM
5. Install software on VM
6. Prepare to run MERlin
7. Run MERlin
8. Analyze results, either on UGER or GCP VM instance
9. Move output from mounted fileshare to Google bucket

# 1. Storage on Google Bucket practices
In gs://merlintest/test, there is a dataset currently labelled `data` with 7 or 8 FOVs that you can run with the test_parameters given in the GitHub.

Ideally, each project should have it's own bucket associated with it, for ease of changing storage class and permissions as appropriate. Each bucket will contain the data and the output once MERlin is run. Permissions can be set for individual objects within each bucket, or the bucket as a whole. For projects currently in use, create a bucket that is in the 'standard' default storage class. Once you are done, you can change the bucket to an 'archive' storage class or whatever class is appropriate for your needs. Going down in storage class means that accesses will be more expensive, but storage will be cheaper. The "lower" storage classes may also have a minimum amount of time an object must stay in that class, so beware if you move down in storage classes and access the data frequently.

# 2. Create Filestore Fileshare Instance.
In the top left corner of the GCP console, click the navigation menu, navigate to Filestore, and click Create an Instance. Choose us-east1 as the region and us-east-1b as the zone. Use default settings for everything else, choosing whatever file share name and instance ID. Once you create, note the `server_ip`:`/fileshare_name` that is shown. 

### How much capacity?
The filestore instance will hold the analysis output of MERlin. When deciding how much capacity to assign your Filestore instance, provide about as much space as your data takes. A 2.3 TB dataset will produce a 1.7 TB output. You can also increase the size of your instance by editing the instance afterwards if you run out. 

# 3. Deploy Cluster 

Clone the repository using `git clone https://github.com/clearylab/gcp_merlin.git`. Inside the slurm_gcp directory are .yaml files.

If you plan on running hundreds or fewer of FOVs such as for using the example dataset, edit slurm-cluster.yaml. If you plan on running thousands or more of FOVs, edit slurm-cluster-2.yaml which has a second partition of high memory nodes, and change the CLUSTER_DEPLOY_NAME below to "slurm-cluster-2".

Replace the network_storage `server_ip` with the `server_ip` of your filestore instance. Replace the remote_mount with the `/fileshare_name`. 

In the `debug` partition, change the max_node_count to 55 or the number of fields of view (FOVs) + 5, whichever is higher to assure you have enough nodes to avoid queues. 

If you are running on Broad's UGER system, run `use Google-Cloud-SDK` before running the following lines, otherwise you must install the Google Cloud SDK.

```
export CLUSTER_DEPLOY_NAME="slurm-cluster"
export CLUSTER_NAME="merlin-cluster"
export CLUSTER_REGION="us-east1"
export CLUSTER_ZONE="us-east1-b"

cd slurm_gcp

gcloud deployment-manager deployments     --project="$(gcloud config get-value core/project)"     create $CLUSTER_DEPLOY_NAME     --config ${CLUSTER_DEPLOY_NAME}.yaml
```

You should now see the deployment listed under Deployment Manager in the console.
You may see a warning about disk sizes not matching, but it is fine to ignore the warning. 


# 4. SSH

There are two options to SSH into a VM

### 1.To SSH into a VM instance from the console:
1. Go to Compute Engine under navigation > VM instances
2. Select the controller and login VMs and press Start/Resume
3. Once started, press the SSH button to launch an SSH session 

### 2.To SSH into a VM instance using gcloud command-line tool
The following commands are to SSH into the login node using the Google Cloud SDK.
```
gcloud compute ssh ${CLUSTER_NAME}-controller     --command "sudo journalctl -fu google-startup-scripts.service"     --zone $CLUSTER_ZONE

export CLUSTER_LOGIN_NODE=$(gcloud compute instances list \
        --zones ${CLUSTER_ZONE} \
        --filter="name ~ .*login." \
        --format="value(name)" | head -n1)

gcloud compute ssh ${CLUSTER_LOGIN_NODE}     --zone $CLUSTER_ZONE
```

## Tips
You may see a error message about a group ID, this is fine to ignore.

If you attempt to SSH into a VM instance immediately, you will be warned that slurm is currently being installed and a message will be deployed when it is finished. Wait for that message before continuing.

**Remember to suspend VM instances when not using to avoid incurring charges**

### Check mounted disk
I hae been having issues with the mounted filestore instance so make sure that this works, otherwise there's not enough space to write the results of MERlin.
1. Run ```df``` when SSH'ed into the _controller_ VM instance, you should see `/mnt/disks/sec` listed somewhere. If you do not see this, skip to 3. If you do, proceed to 2.
2. If the above works, try writing something to /mnt/disks/sec. For instance, try ```touch a.txt``` . If that works, everything's good. If not, run ```sudo chmod 777 /mnt/disks/sec``` and try to touch a text file again.
3. If 1 does not work, try running `gcloud filestore instances list`. Do you see the fileshare name you created earlier listed? If you do, try step 1 again. I don't know why but sometimes this fixes it. If not, check that you have actually created the filestore instance and put the correct IP and name in the .yaml file.

# 5. Install necessary software
If this is the first time using the instance, you will have to install the necessary software. `installstuff.sh` in the repo contains everything you need to install. You can run the lines below to clone this directory into the home directory and run installstuff.sh

```
cd ~
git clone https://github.com/clearylab/gcp_merlin.git
cd gcp_merlin
bash installstuff.sh
```

`installstuff.sh` installs the necessary software and also creates two directories `snake_outputs` and `slurm_outputs` that MERlin will write standard output to. 

# 6. Prepare to run MERlin
### Configure .merlinenv
Create a .merlinenv file in your home directory as below
```
DATA_HOME=gs://merlintest/test
ANALYSIS_HOME=/mnt/disks/sec
PARAMETERS_HOME=/home/zheng/gcp_merlin/test_parameters
```

Your data should be in a Google bucket. Set the DATA_HOME in the .merlinenv to point to the bucket address of the parent directory of the data folder. In our example, the .dax files of our data are in gs://merlintest/test/data. `data` is the name of our dataset, and `gs://merlintest/test` will be our DATA_HOME. 
If you have installed MERlin from my (zheng-broad) fork as in the installstuff.sh script I have provided, then this should not be a problem. Currently, the official version of MERlin is not configured to accept gs:// addresses.

ANALYSIS_HOME should be in /mnt/disks/sec to use the filestore instance. 

PARAMETERS_HOME if you are using the test_parameters provided and cloned the repo as in step 5, will be in your home directory inside gcp_merlin. Change the path above to have the correct home directory. (Run `pwd` in your home directory to get the path)

### Configure parameters. 
#### Analysis parameters
The test_parameters supplied work for running the data in gs://merlintest/test/data. If you are running your own data, you will need to supply your own dataorganization and codebook, and likely make adjustments to the analysis folder.

I have provided two example json's, `nosegment.json` does not run MERlin's segmentation tasks, `segmentanddecode.json` does. 

I recommend these values for the analysis folder of the parameters, avoiding writing unnecessary images to save space.
a. Decode: "write_decoded_images": false,
b. FiducialCorrelationWarp: "write_aligned_images": false,
c. GenerateMosaic: "separate_files":true 

d. To prevent z-duplicates, I recommend setting the parameters in decode to
* "remove_z_duplicated_barcodes": true,
* "z_duplicate_xy_pixel_threshold": 3

#### Correct paths
In the snakemake folder in the test_parameters, you will use either snake.json and clusterconfig.json if you have 100s of FOVs, and snake-2.json and clusterconfig-2.json if you have 1000s of FOVs. **You must edit** the snake json's `cluster_config` to point to the corresponding clusterconfig json in the same folder.

The clusterconfig jsons also have parameters for where to write the output of the snakemake jobs, currently to snake_outputs in the home directory. You do not need to change this as this if that is where you want the outputs to go.

# 7. Run MERlin 
## If you have 100s of FOVs
runmerlin.sh
```
#!/bin/bash
#SBATCH -n 1
#SBATCH -N 1
#SBATCH -t 7-00:00:00
#SBATCH --mem 2000
#SBATCH --open-mode=append
#SBATCH --output="/home/zheng/slurm_outputs/slurm-%A.out"

source ~/.bash_profile
conda activate merlin_env

cd ~

merlin -a nosegment.json -m VizgenAlpha.json -o dataorganization.csv -c codebook_M22E1.csv -k snake.
json data
```
The merlin command above uses files from the test_parameters folder with the corresponding codebook for the test data given. 

You **must** change the output folder to an appropriate path. To use the slurm_outputs in your home directory, just change the prefix /home/zheng to your home directory.

If you are running multiple jobs at once with different data and analysis paths, you can specify those with -e and -s respecively in the MERlin command. You can NOT specify different parameter paths from the .merlinenv, so maintain one parameters directory and change the names of the files as appropriate if you are running multiple MERlin jobs with different parameters.

Submit the job to slurm using `sbatch runmerlin.sh`
Use `squeue` to check current job statuses and `scancel job_id` to cancel a job. See slurm documentation for more commands.

## If you have many FOVs (>1000)
Running MERlin on 1500 FOVs will increase the memory requirements for certain tasks (PlotPerformance, GenerateMosaic and potentially ExportBarcodes) beyond the 7.5GB available to each node in the default `debug` partition, or require more time to run than the preemptible `debug` nodes will allow. If you have deployed your yaml using 2 partitions as in `slurm-cluster-2.yaml`, you will want those tasks to use the `partition2` partition with higher memory, non-preemptible machines. This can be done by editing the `clusterconfig.json` and `snake.json` file as in `clusterconfig-2.json` and `snake-2.json`, specifying which partition each task should use.

## Other issues

### Potential issue reading data
You will likely not have this issue if you are using the default service account, but sometimes merlin does not allow me to read directly from the bucket without using gsutil to download without exporting the `GOOGLE_APPLICATION_CREDENTIALS` See here for more information if you get this issue https://cloud.google.com/docs/authentication/getting-started

### Windows error
If you see the following error:
`sbatch: error: Batch script contains DOS line breaks (\r\n) 
sbatch: error: instead of expected UNIX line breaks (\n)`
See https://wikis.ovgu.de/hpc/doku.php?id=guide:dos_unix_linebreaks for how to resolve it.


# 8. Analysis
Once you are done, move the output from /mnt/disks/sec to the Google Bucket where the data is using `gsutil -m cp -r current_dir gs://bucket_dir`. You can analyze results either on the VM instance or on UGER by downloading the data from the Google Bucket.

To generate "mosaics" from the barcodes.csv, change the variables at the top of make_merfish_mosaics.py and run.

# 9. Done with everything
Shut down the filestore instance and deployment, deleting all VMs created by it. Do *NOT* individually delete VMs. Go to the Deployment Manager on the console and delete the deployment along with all resources. 

If you no longer plan on accessing the Google bucket, change its storage level to Archive for future uploads. To change the storage class of objects already in the bucket run
`gsutil rewrite -s STORAGE_CLASS gs://PATH_TO_OBJECT`


    
