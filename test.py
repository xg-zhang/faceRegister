import api
import cv2
import sqlite3

conn = sqlite3.connect('data.sqlite')
c = conn.cursor()
print('数据库开启成功')
cursor = c.execute('SELECT username,face_encoding from users')

# Get a reference to webcam #0 (the default one)
video_capture = cv2.VideoCapture(0)

# # Load a sample picture and learn how to recognize it.
# menghanjun_image = api.load_image_file("faces/menghanjun.jpeg")
# menghanjun_face_encoding = api.face_encodings(menghanjun_image)[0]
# # print(menghanjun_face_encoding)
#
# # Load a second sample picture and learn how to recognize it.
# wangkang_image = api.load_image_file("faces/wangkang.jpeg")
# wangkang_face_encoding = api.face_encodings(wangkang_image)[0]

# Create arrays of known face encodings and their names
known_face_names = []
known_face_encodings = []
for i, j in cursor:
    print(i,j)
    if j != None:
        known_face_names.append(i)
        known_face_encodings.append(eval(j))
print(known_face_names)
print(known_face_encodings)

# Initialize some variables
face_locations = []
face_encodings = []
face_names = []
process_this_frame = True

while True:
    # Grab a single frame of video
    ret, frame = video_capture.read()

    # Resize frame of video to 1/4 size for faster face recognition processing
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

    # Convert the image from BGR color (which OpenCV uses) to RGB color (which api uses)
    rgb_small_frame = small_frame[:, :, ::-1]

    # Only process every other frame of video to save time
    if process_this_frame:
        # Find all the faces and face encodings in the current frame of video
        face_locations = api.face_locations(rgb_small_frame)
        face_encodings = api.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        for face_encoding in face_encodings:
            # See if the face is a match for the known face(s)
            matches = api.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"

            # If a match was found in known_face_encodings, just use the first one.
            if True in matches:
                first_match_index = matches.index(True)
                name = known_face_names[first_match_index]

            face_names.append(name)

    process_this_frame = not process_this_frame

    # Display the results
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        # Scale back up face locations since the frame we detected in was scaled to 1/4 size
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        # Draw a box around the face
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

        # Draw a label with a name below the face
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

    # Display the resulting image
    cv2.imshow('Video', frame)

    # Hit 'q' on the keyboard to quit!
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release handle to the webcam
video_capture.release()
cv2.destroyAllWindows()
