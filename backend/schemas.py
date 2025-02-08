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

class UserSchema(Schema):
    userid = fields.String(required=True)
    username = fields.String(required=True)
    address = fields.String(required=True)
    contributions = fields.List(fields.Nested(ImageSchema))
    biocontributions = fields.List(fields.Nested(ImageSchema))
    nonbiocontributions = fields.List(fields.Nested(ImageSchema))
    eligibleContri = fields.List(fields.Nested(ImageSchema))
    ineligibleContri = fields.List(fields.Nested(ImageSchema))
    inprocessContri = fields.List(fields.Nested(ImageSchema))




imageSchema = ImageSchema()
imagesSchema = ImageSchema(many=True)
userSchema = UserSchema()


