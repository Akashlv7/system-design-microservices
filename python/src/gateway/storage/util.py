import pika, json

def upload(f, fs, channel, access):
    # Store the file in MongoDB
    try:
        fid = fs.put(f)
    except Exception as err:
        print(err)
        return "internal server error", 500
    
    message = {
        "video_fid": str(fid),
        "mp3_fid": None,
        "username": access["username"],
    }


    # Put a message in the RabbitMQ for the downstream services
    try:
        channel.basic_publish(
            exchange="",
            routing_key='video',
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            )
        )
    except Exception as err:
        print(err)
        fs.delete(fid)
        return "internal server error", 500