# You can change this to any folder on your system
from flask import jsonify

import api

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# def detect_faces_in_image(file_stream):
#     # Pre-calculated face encoding of menghanjun generated with api.face_encodings(img)
#     menghanjun_image = api.load_image_file("faces/menghanjun.jpeg")
#     menghanjun_face_encoding = api.face_encodings(menghanjun_image)[0]
#     known_face_encoding = menghanjun_face_encoding
#
#     # Load the uploaded image file
#     img = api.load_image_file(file_stream)
#     # Get face encodings for any faces in the uploaded image
#     unknown_face_encodings = api.face_encodings(img)
#
#     face_found = False
#     is_menghanjun = False
#
#     if len(unknown_face_encodings) > 0:
#         face_found = True
#         # See if the first face in the uploaded image matches the known face of menghanjun
#         match_results = api.compare_faces([known_face_encoding], unknown_face_encodings[0])
#         if match_results[0]:
#             is_menghanjun = True
#
#     # Return the result as json
#     result = {
#         "face_found_in_image": face_found,
#         "is_picture_of_menghanjun": is_menghanjun
#     }
#     return jsonify(result)

def get_face_encoding_in_image(file_stream):
    # Load the uploaded image file
    img = api.load_image_file(file_stream)
    # print(img)
    # Get face encodings for any faces in the uploaded image
    unknown_face_encodings = api.face_encodings(img)
    # print(unknown_face_encodings)
    face_encoding = None
    face_found = False

    if len(unknown_face_encodings) > 0:
        face_found = True
        face_encoding = str(list(unknown_face_encodings[0]))
        print(face_encoding)

    # Return the result as json
    result = {
        "face_found_in_image": face_found,
        "unknown_face_encodings": face_encoding
    }
    # print(result['unknown_face_encodings'])
    return result
