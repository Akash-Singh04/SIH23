import os
from fastapi import FastAPI
from pydantic import BaseModel
import boto3
import botocore
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configure CORS settings
origins = [
    "http://localhost:3000",
      "http://localhost:3000/input"  # Add your frontend origin(s) here
    # Add more origins if needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # You can restrict HTTP methods if needed
    allow_headers=["*"],  # You can restrict headers if needed
)

class inputParameters(BaseModel):
    amplification_factor: int
    fl: float
    fh: float
    fs: float
    n_filter_tap: int
    filter_type: str
    temporal : bool
    selectedVideo: str

def upload_file_to_s3(file_name,bucket,object_name):
    print("Uploading video to S3...")
    s3 = boto3.client('s3',aws_access_key_id='AKIAVAHZBIOLFULVDWVC',aws_secret_access_key='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')

    if object_name is None:
        object_name = os.path.basename(file_name)
    try:
        s3.upload_file(file_name, bucket, object_name, ExtraArgs={'ContentType': 'video/mp4'})
        print(f"File '{file_name}' uploaded to S3 bucket '{bucket}' as '{object_name}'")
        return True
    except Exception as e:
        print(f"Error uploading file to S3: {str(e)}")
        return False

def download_video_from_s3(bucket_name,key, download_path):
    print("Downloading video from S3...")
    s3 = boto3.resource('s3',aws_access_key_id='AKIAVAHZBIOLFULVDWVC',aws_secret_access_key='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')
    try:
        s3.Bucket(bucket_name).download_file(key, download_path)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print("The object does not exist.")
        else:
            raise

@app.post("/upload/")
async def get(json: inputParameters):
    BUCKET_NAME = "skillissuevid"
    obj = json.selectedVideo.split("/")[-1]
    download_video_from_s3(BUCKET_NAME,obj,f"model/{obj}")
    object = obj.split(".")[0]
    os.mkdir(f"model/data/vids/{object}")
    com= f"ffmpeg -i model/{obj} model/data/vids/{object}"+"/%06d.png"
    os.system(com)
    if json.temporal:
        command = (
        f"python3 model/main.py --config_file=model/configs/o3f_hmhm2_bg_qnoise_mix4_nl_n_t_ds3.conf --phase=run_temporal --vid_dir=model/data/vids/{object} --out_dir=/ --amplification_factor={json.amplification_factor} --fl={json.fl} --fh={json.fh} --fs={json.fs} --n_filter_tap={json.n_filter_tap} --filter_type={json.filter_type}")
    else:
        command = (
        f"python3 model/main.py  --config_file=model/configs/o3f_hmhm2_bg_qnoise_mix4_nl_n_t_ds3.conf --phase=run --vid_dir=model/data/vids/{object} --out_dir=/ --amplification_factor={json.amplification_factor}"
        )
    os.system(command)
    upload_file_to_s3(f"model/data/output/{object}_o3f_hmhm2_bg_qnoise_mix4_nl_n_t_ds3/{object}_fl0.04_fh0.4_fs30.0_n2_differenceOfIIR_259002.mp4",BUCKET_NAME,f"{object}_output.mp4")
    return {"link": f"https://d175wanlbunlv0.cloudfront.net/{object}_output.mp4"}

if __name__ == '__main__':
    print("Starting server...")
    os.system("uvicorn model.api:app --host localhost --port 8080")
