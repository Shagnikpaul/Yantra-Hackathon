from flask import Flask, request
from flask_restful import Resource, Api
import os
import marshmallow
from supabase import create_client, Client
from pymongo import MongoClient, ReturnDocument
from dotenv import load_dotenv
import datetime
from bson import ObjectId


from schemas import imageSchema, imagesSchema, userSchema

load_dotenv()

app = Flask(__name__)
api = Api(app)


url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)


client = MongoClient(os.environ.get("MONGO"))
db = None
images_data = None
users_data = None

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB! now retrieving database...")
    db = client["wastesegregator"]
    images_data = db["images"]
    users_data = db['users']
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


class User(Resource):
    def get(self, userid):
        user_data = users_data.find_one({"userid": userid})

        if user_data is None:
            return {"message": "userid does not exist"}, 401

        try:
            data = userSchema.dump(user_data)

        except:
            return {"message": "Schema error"}
        return {"message": f"get request for data of {userid}", "data": data}

    def patch(self, userid):
        json_data = request.get_json()
        already_exists = users_data.find_one({"userid": userid})
        if not already_exists:
            return {"message": "given user does not exist"}, 401
        try:
            username = json_data['username']
            address = json_data['address']
        except:
            return {"message": "missing required parameters username or address"}

        data = {
            "userid": userid,
            "username": username,
            "address": address,
            "contributions": [],
            "biocontributions": [],
            "nonbiocontributions": [],
            "eligibleContri": [],
            "ineligibleContri": [],
            "inprocessContri": []
        }
        try:
            userSchema.validate(data)
        except:
            return {"message": "wrong data format"}, 401

        doc = users_data.find_one_and_update(
            {"userid": userid}, {"$set": userSchema.load(data)},
            return_document=ReturnDocument.AFTER)

        return {"message": "data updated", "new_data": userSchema.dump(doc)}

    def put(self, userid):
        json_data = request.get_json()
        already_exists = users_data.find_one({"userid": userid})
        if already_exists:
            return {"message": "user data already exists if you want to modify call patch method"}, 401
        try:
            username = json_data['username']
            address = json_data['address']
        except:
            return {"message": "missing required paramets username or address"}

        data = {
            "userid": userid,
            "username": username,
            "address": address,
            "contributions": [],
            "biocontributions": [],
            "nonbiocontributions": [],
            "eligibleContri": [],
            "ineligibleContri": [],
            "inprocessContri": []
        }
        try:
            userSchema.validate(data)
        except:
            return {"message": "wrong data format"}, 401
        id = str(users_data.insert_one(data).inserted_id)
        return {"message": "Inserted new user entry", "id": id}


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

        # segregation list has to be a comma seperated list of strings with no quotes
        if 'userid' not in request.form:
            return {"message": "missing data !!!"}
        imgid: str = request.form['imgid']
        userId: str = request.form['userid']
        userAddress: str = request.form['userAddress']
        userName: str = request.form['userName']
        weightOfWaste = request.form['weightOfWaste']
        segregationList = request.form['segregationList'].split(",")
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
                        "weightOfWaste": weightOfWaste,
                        "segregationData": segregationList
                    }
                )
            except marshmallow.exceptions.ValidationError:
                return {"message": "data format not correct", "list received": segregationList}, 500
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
                        "weightOfWaste": weightOfWaste,
                        "segregationData": []
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

api.add_resource(User, '/user/<string:userid>')
if __name__ == '__main__':
    app.run(debug=True)
