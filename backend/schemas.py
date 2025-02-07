from marshmallow import Schema, fields


class ImageSchema(Schema):
    _id = fields.String()
    userid = fields.String(required=True)
    img_url = fields.String(required=True)
    date = fields.String(required=True)
    isProcessed = fields.Bool()
    isEligible = fields.Bool()
    userAddress = fields.String(required=True)
    userName = fields.String(required=True)
    weightOfWaste = fields.Float()
    segregationData = fields.List(fields.String())


imageSchema = ImageSchema()

imagesSchema = ImageSchema(many=True)
