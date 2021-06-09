import os, io
from google.cloud import vision
from google.cloud.vision_v1 import types
import pandas as pd
import boto3
import json
from multiprocessing import Pipe, Process

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'Token.json'

client = vision.ImageAnnotatorClient()

json_data = 0


def lambda_handler(event, context):
    ds=[]
    
    def img(i, conn):
        num=0
        
        if(json_data[i]['isAd']==False):
            json_imgurl=json_data[i]['imgUrl']
            json_id=json_data[i]['id']
        else:
            conn.send([0, 0])
            conn.close()
            return

        for b in reversed(json_imgurl):
            num=num+1
            img_url=b
            
            image=vision.Image()
            image.source.image_uri=img_url
            response=client.text_detection(image=image)
            texts=response.text_annotations
            

            df=pd.DataFrame(columns=['locale','description'])
            for text in texts:
                df=df.append(
                        dict(
                                locale=text.locale,
                                description=text.description
                        ),
                        ignore_index=True
                )

            count=0
            ds=list(df['description']) #update 5/13

            
            if "제공" in ds or "지원" in ds or "협찬" in ds or "지급" in ds:
                if "받아" in ds or "받았" in ds:
                    conn.send([1, json_id])
                    conn.close()
                    return 
                elif "않" in ds:
                    conn.send([0, 0])
                    conn.close()
                    return 
                else:
                    conn.send([1, json_id])
                    conn.close()
                    return
            if "제공받아" in ds or "지원받아" in ds:
                conn.send([1, json_id])
                conn.close()
                return
            if "원고료" in ds or "제작비" in ds or "수수료" in ds:
                if "소정" in ds or "지원" in ds or "받아" in ds or "지원받아" in ds or "지급" in ds or "지급받아" in ds:
                    conn.send([1, json_id])
                    conn.close()
                    return 
                else:
                    conn.send([0, 0])
                    conn.close()
                    return
            else:
                conn.send([0, 0])
                conn.close()
                return
            
        conn.send([0,0])
        conn.close()
        return
            
    __name__='__main__'
    if __name__=='__main__':
        json_data=event
        result=[]

        processes = []  
        parent_connections = []
        
        for i in range(len(json_data)):
            parent_conn, child_conn=Pipe()
            p=Process(target=img, args=(i, child_conn,))
            parent_connections.append(parent_conn)
            processes.append(p)

        for process in processes:
            process.start()
                
        for process in processes:
            process.join()    
        
        for parent_connection in parent_connections:
            result.append(parent_connection.recv())

        for res in result:
            if res[0]:
                i=0
                for i in range(len(json_data)):
                    if json_data[i]['id']==res[1]:
                        break
                json_data[i]['isAd']=True
                
        return json.dumps(json_data, indent=2)
                

            

