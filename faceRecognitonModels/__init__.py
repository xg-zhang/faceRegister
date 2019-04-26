__author__ = '孟汉君'
__email__ = 'menghanjun001@gmail.com'

from pkg_resources import resource_filename


def pose_predictor_model_location():
    return resource_filename(__name__, 'models/shape_predictor_68_face_landmarks.dat')


def pose_predictor_five_point_model_location():
    return resource_filename(__name__, "models/shape_predictor_5_face_landmarks.dat")


def face_recognition_model_location():
    return resource_filename(__name__, "models/dlib_face_recognition_resnet_model_v1.dat")


def cnn_face_detector_model_location():
    return resource_filename(__name__, "models/mmod_human_face_detector.dat")
