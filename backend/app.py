from flask import Flask, request
from flask_restful import Resource, Api
import os
import marshmallow
from supabase import create_client, Client
from pymongo import MongoClient
from dotenv import load_dotenv
import datetime
from bson import ObjectId


from schemas import imageSchema, imagesSchema

load_dotenv()

app = Flask(__name__)
api = Api(app)


url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)


client = MongoClient(os.environ.get("MONGO"))
db = None
images_data = None


try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB! now retrieving database...")
    db = client["wastesegregator"]
    images_data = db["images"]
    print("data base loaded...")

except Exception as e:
    print('error occured during bd init...', e)

if not os.path.exists('img_files'):
    print("Create a folder called img_files")
    os.mkdir('img_files')
else:
    print("Ignoring folder creation since folder already exists...")


class HelloWorld(Resource):
    def get(self):

        return {'hello': 'no world', 'collections': 'nono'}


class Image(Resource):

    # get all images...
    def get(self):
        if 'userid' not in request.form:
            return {"message": "userid required !!"}

        userId: str = request.form['userid']
        images = list(images_data.find({"userid": userId}))

        return {'images': imagesSchema.dump(images)}

    def delete(self):
        if 'userid' not in request.form:
            return {"message": "userid required !!"}

        imgid: str = request.form['imgid']
        try:
            dele = images_data.find_one_and_delete({"_id": ObjectId(imgid)})
            return {"message": "deleted successfully", "deleted_document": imageSchema.dump(dele)}
        except Exception:
            return {"message": "Unknown error while deleting"}

    def patch(self):
        if 'userid' not in request.form:
            return {"message": "missing data !!!"}
        imgid: str = request.form['imgid']
        userId: str = request.form['userid']
        userAddress: str = request.form['userAddress']
        userName: str = request.form['userName']
        weightOfWaste = request.form['weightOfWaste']
        if 'file' in request.files:
            file = request.files['file']

            if file.filename == '':
                return {"message": "no file was selected"}, 401

            file.save(os.path.join('img_files', file.filename))
            response = supabase.storage.from_("userImages").upload(
                file=open(os.path.join('img_files', file.filename), 'rb'), path=file.filename, file_options={"upsert": "true", "content-type": file.content_type})

            print(response)
            public_url = supabase.storage.from_(
                "userImages").get_public_url(file.filename)
            tz = datetime.timezone.utc
            ft = "%Y-%m-%dT%H:%M:%S%z"
            t = datetime.datetime.now(tz=tz).strftime(ft)
            try:
                data_to_push = imageSchema.load(
                    {
                        "userid": userId,
                        "img_url": public_url,
                        "date": t,
                        "isProcessed": False,
                        "isEligible": False,
                        "userAddress": userAddress,
                        "userName": userName,
                        "weightOfWaste": weightOfWaste
                    }
                )
            except marshmallow.exceptions.ValidationError:
                return {"message": "data format not correct"}, 500
            up = images_data.find_one_and_update(
                {"_id": ObjectId(imgid)}, {"$set": imageSchema.load(data_to_push)})
            id = imgid
            return {"message": "data got updated", "url": public_url, "updated_document_id": str(id)}
        else:
            return {"message": "no file was sent in request"}, 401

    def put(self):
        if 'userid' not in request.form:
            return {"message": "missing data !!!"}

        userId: str = request.form['userid']
        userAddress: str = request.form['userAddress']
        userName: str = request.form['userName']
        weightOfWaste = request.form['weightOfWaste']
        if 'file' in request.files:
            file = request.files['file']

            if file.filename == '':
                return {"message": "no file was selected"}, 401

            file.save(os.path.join('img_files', file.filename))
            response = supabase.storage.from_("userImages").upload(
                file=open(os.path.join('img_files', file.filename), 'rb'), path=file.filename, file_options={"upsert": "true", "content-type": file.content_type})

            print(response)
            public_url = supabase.storage.from_(
                "userImages").get_public_url(file.filename)
            tz = datetime.timezone.utc
            ft = "%Y-%m-%dT%H:%M:%S%z"
            t = datetime.datetime.now(tz=tz).strftime(ft)
            try:
                data_to_push = imageSchema.load(
                    {
                        "userid": userId,
                        "img_url": public_url,
                        "date": t,
                        "isProcessed": False,
                        "isEligible": False,
                        "userAddress": userAddress,
                        "userName": userName,
                        "weightOfWaste": weightOfWaste
                    }
                )
            except marshmallow.exceptions.ValidationError:
                return {"message": "data format not correct"}, 500
            id = images_data.insert_one(data_to_push).inserted_id
            return {"message": "file was saved in server folder", "url": public_url, "inserted_id": str(id)}
        else:
            return {"message": "no file was sent in request"}, 401


api.add_resource(HelloWorld, '/')
api.add_resource(Image, '/image')
if __name__ == '__main__':
    app.run(debug=True)
