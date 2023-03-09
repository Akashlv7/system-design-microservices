import pika, tempfile, json, os
from bson.objectid import ObjectId
import moviepy.editor as editor


def start(message, fs_videos, fs_mp3s, channel):
    message = json.loads(message)

    # empty temp file
    tf = tempfile.NamedTemporaryFile()

    # video contents
    video_out = fs_videos.get(ObjectId(message["video_fid"]))

    # add video contents to temp file
    tf.write(video_out.read())
    
    # convert video to audio
    audio = editor.VideoFileClip(tf.name).audio
    tf.close()

    # write audio to a file
    audio_tf_path = tempfile.gettempdir() + f"/{message['video_fid']}.mp3"
    audio.write_audiofile(audio_tf_path)

    # save file to mongo
    f = open(audio_tf_path, 'rb')
    data = f.read()
    fid = fs_mp3s.put(data)
    f.close()
    os.remove(audio_tf_path)


    # update message and publish
    message["mp3_fid"] = str(fid)

    try:
        channel.basic_publish(
            exchange="",
            routing_key=os.environ.get("MP3_QUEUE"),
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ),
        )
    except Exception as err:
        print(str(err))
        fs_mp3s.delete(fid)
        return "failed to publish message"