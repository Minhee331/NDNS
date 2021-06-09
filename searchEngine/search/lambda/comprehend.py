import json
import boto3

#Using boto3 to call the Comprehend API
client = boto3.client('comprehend')

#Lambda function to work with Comprehend
def lambda_handler(event, context):
    
    json_data = event
    over = []
    result = []
    for i in json_data:
        body = i["body"]
        id = i['id']
        length = 0
        body_en = body.encode()
        allLen = len(body)
        negative = []
        positive = []
        lens = []
        while(length < allLen):
            sentiment = ''
            if (allLen < length + 1500):
                sentiment = client.detect_sentiment(Text = body[length:], LanguageCode = 'ko') #API call for sentiment analysis
                lens.append(allLen - length)
            else :
                sentiment = client.detect_sentiment(Text = body[length:length+1499], LanguageCode = 'ko') #API call for sentiment analysis
                lens.append(1500)
            sentRes = sentiment['Sentiment'] #Positive, Neutral, or Negative
            sentScore = sentiment['SentimentScore']
            # return sentScore
            negative.append(sentScore['Negative'])
            positive.append(sentScore['Positive'])
            length += 1500
        tNegative = 0
        tPositive = 0
        for idx in range(len(lens)):
            tNegative += (negative[idx] / allLen) * lens[idx] 
            tPositive += (positive[idx] / allLen) * lens[idx]
        result.append({"id": id, "Positive": tPositive,"Negative": tNegative})
        
    return {
        'body': result #body returned from our function
    }