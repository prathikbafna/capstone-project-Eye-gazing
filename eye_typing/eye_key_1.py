from __future__ import print_function
import numpy
import threading
import time
import cv2
import numpy as np
import random
import dlib
import sys
import pyttsx3
from main import *
from eye_key_funcs import *
from projected_keyboard import get_keyboard
#voiceEngine = pyttsx3.init()

# newVoiceRate = 160



# # ------------------------------------ Inputs
camera_ID = 0  # select webcam

width_keyboard, height_keyboard = 1000, 500 # [pixels]
offset_keyboard = (100, 80) # pixel offset (x, y) of keyboard coordinates

resize_eye_frame = 4.5 # scaling factor for window's size
resize_frame = 0.3 # scaling factor for window's size
# # ------------------------------------

# ------------------------------------------------------------------- INITIALIZATION
# Initialize the camera
camera = init_camera(camera_ID = camera_ID)
#cap = cv2.VideoCapture(0)

# take size screen
#size_screen = (camera.set(cv2.CAP_PROP_FRAME_HEIGHT,800), camera.set(cv2.CAP_PROP_FRAME_WIDTH,1000))
size_screen=(1000,1300)#screen size for making keyboard


# make a page (2D frame) to write & project
keyboard_page = make_black_page(size = size_screen)

calibration_page = make_black_page(size = size_screen)

# Initialize keyboard
key_points = get_keyboard(width_keyboard  = width_keyboard ,
                       height_keyboard = height_keyboard ,
                       offset_keyboard = offset_keyboard)
preds = ['hi', 'water', 'Im','help']
dynamic_key_points = []

# upload face/eyes predictors
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
# -------------------------------------------------------------------

# ------------------------------------------------------------------- CALIBRATION
corners = [(offset_keyboard),
           (width_keyboard+offset_keyboard[0], height_keyboard + offset_keyboard[1]),
           (width_keyboard+offset_keyboard[0], offset_keyboard[1]),
           (offset_keyboard[0], height_keyboard + offset_keyboard[1])]


calibration_cut = []
corner = 0


# while(corner<4): # calibration of 4 corners
#
#     ret, frame = camera.read()   # Capture frame
#     frame = adjust_frame(frame)  # rotate / flip
#
#     gray_scale_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) # gray-scale to work with
#     #cv2.putText(image, text, org, font, fontScale, color[, thickness[, lineType[, bottomLeftOrigin]]])
#     #org is the coordinates of the bottom-left corner of the text string in the image. The coordinates are represented as tuples of two values i.e. (X coordinate value, Y coordinate value).
#     # messages for calibration
#     cv2.putText(calibration_page, 'calibration: look at the circle and blink', tuple((np.array(size_screen)/7).astype('int')), cv2.FONT_HERSHEY_SIMPLEX, 1.5,(0, 0, 255), 3)
#     cv2.circle(calibration_page, corners[corner], 40, (0, 255, 0), -1)
#     #cv2.circle(image, center_coordinates, radius, color, thickness)
#
#     # detect faces in frame
#     faces = detector(gray_scale_frame)
#     if len(faces)> 1:
#
#         print('please avoid multiple faces.')
#         sys.exit()
#
#     for face in faces:
#         display_box_around_face(frame, [face.left(), face.top(), face.right(), face.bottom()], 'green', (20, 40))
#
#         landmarks = predictor(gray_scale_frame, face) # find points in face
#         #display_face_points(frame, landmarks, [0, 68], color='red') # draw face points
#         #print('landmarks',landmarks)
#         # get position of right eye and display lines
#         right_eye_coordinates = get_eye_coordinates(landmarks, [42, 43, 44, 45, 46, 47])
#         #left_eye_coordinates = get_eye_coordinates(landmarks, [36, 37, 38, 39, 40, 41])
#         display_eye_lines(frame, right_eye_coordinates, 'green')
#         #print("right_eye_coordinates",right_eye_coordinates)
#
#
#         # define the coordinates of the pupil from the centroid of the right eye
#         pupil_coordinates = np.mean([right_eye_coordinates[2], right_eye_coordinates[3]], axis = 0).astype('int')
#
#
#
#         if is_blinking(right_eye_coordinates):
#             print('pupil coordinates',pupil_coordinates)
#             calibration_cut.append(pupil_coordinates)
#
#
#             # visualize message
#             cv2.putText(calibration_page, 'ok',tuple(np.array(corners[corner])-5), cv2.FONT_HERSHEY_SIMPLEX, 2,(255, 255, 255), 5)
#             # to avoid is_blinking=True in the next frame
#             time.sleep(0.9)#Python time method sleep() suspends execution for the given number of seconds.
#             # The argument may be a floating point number to indicate a more precise sleep time.
#             corner = corner + 1
#
#     print('calibration cut',calibration_cut, '    len: ', len(calibration_cut))
#     show_window('projection', calibration_page)
#     show_window('frame', cv2.resize(frame,  (630, 460)))
#     #waitKey(0) will display the window infinitely until any keypress (it is suitable for image display).
#
#     # waitKey(1) will display a frame for 1 ms, after which display will be automatically closed
#     #cv2 waitkey() allows you to wait for a specific time in milliseconds until you press any button on the keyword.
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break
#
#
#
# cv2.destroyAllWindows()
# -------------------------------------------------------------------

# ------------------------------------------------------------------- PROCESS CALIBRATIONcalibration cut [array([170, 289]), array([277, 335]), array([409, 292]), array([183, 399])]
calibration_cut= [[229, 306], [360, 379], [373, 305]]
#calibration_cut = [[170,289],[277,335],[409,292],[183,399]]
# find limits & offsets for the calibrated frame-cut
x_cut_min, x_cut_max, y_cut_min, y_cut_max = find_cut_limits(calibration_cut)
offset_calibrated_cut = [ x_cut_min, y_cut_min ]

# ----------------- message for user
# MIC: aggiungi il fattore tempo, i.e., l'immagine si chiude dopo 5 sec, senza input from keyboard
print('message for user')
cv2.putText(calibration_page, 'calibration done. please wait for the keyboard...',
            tuple((np.array(size_screen)/5).astype('int')), cv2.FONT_HERSHEY_SIMPLEX, 1.4,(255, 255, 255), 3)
print("calibration done")
show_window('projection', calibration_page)



print('keyboard appearing')
# -------------------------------------------------------------------

# ------------------------------------------------------------------- WRITING
pressed_key = True
# key_on_screen = " "
length = 0
string_to_write = "text:"

while(True):

    ret, frame = camera.read()   # Capture frame
    frame = adjust_frame(frame)  # rotate / flip"
    #print("rotating frame",frame)
    #print("frame",frame)
    #print(frame[y_cut_min:y_cut_max, x_cut_min:x_cut_max, :])

    cut_frame = np.copy(frame[y_cut_min:y_cut_max, x_cut_min:x_cut_max, :])
    #print("cut_frame",cut_frame)
    #print("cut frame is",cut_frame)
    #cut_frame = np.copy(frame[270:338, 197:430, :])

    # make & display on frame the keyboard
    keyboard_page = make_black_page(size = size_screen)
    image_page = make_black_page(size = size_screen)

    dysplay_keyboard(img = keyboard_page, keys = key_points)
    #dysplay_keyboard(img=keyboard_page, keys=key_points+dynamic_key_points)
    dynamic_key_points = []
    #dysplay_keyboard(img = image_page, keys = key_points)
    #show_windows()
    text_page = make_white_page(size = (700, 800))


    gray_scale_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) # gray-scale to work with

    faces = detector(gray_scale_frame)  # detect faces in frame
    if len(faces) > 1:
        print('please avoid multiple faces..')
        sys.exit()
    #text_coordinates = [20, 70]




    for face in faces:
        display_box_around_face(frame, [face.left(), face.top(), face.right(), face.bottom()], 'green', (20, 40))

        landmarks = predictor(gray_scale_frame, face) # find points in face
        #display_face_points(frame, landmarks, [0, 68], color='red') # draw face points

        # get position of right eye and display lines
        right_eye_coordinates = get_eye_coordinates(landmarks, [42, 43, 44, 45, 46, 47])
        display_eye_lines(frame, right_eye_coordinates, 'green')

         # define the coordinates of the pupil from the centroid of the right eye

        pupil_cordinates = np.mean([right_eye_coordinates[2], right_eye_coordinates[3]], axis = 0).astype('int')
        #print("pupil on frame",pupil_on_frame)

        pupil_on_cut = np.array([pupil_cordinates[0] - offset_calibrated_cut[0], pupil_cordinates[1] - offset_calibrated_cut[1]])
        #print("pupil_on_cut",pupil_on_cut)

        #drawing blue circle on cutfram on pupil
        cv2.circle(cut_frame, (pupil_on_cut[0], pupil_on_cut[1]), int(take_radius_eye(right_eye_coordinates)/1.5), (255, 0, 0), 1)

        if pupil_on_cut_valid(pupil_on_cut, cut_frame):

            pupil_on_keyboard = project_on_page(img_from = cut_frame[:,:, 0], # needs a 2D image for the 2D shape
                                                img_to = keyboard_page[:,:, 0], # needs a 2D image for the 2D shape
                                                point = pupil_on_cut)

            # pupil_on_image = project_on_page(img_from=cut_frame[:, :, 0],  # needs a 2D image for the 2D shape
            #                                     img_to=image_page[:, :, 0],  # needs a 2D image for the 2D shape
            #                                     point=pupil_on_cut)
            # pupil_on_tkinter = project_on_page(img_from=cut_frame[:, :, 0],  # needs a 2D image for the 2D shape
            #                                     img_to=show_windows(),  # needs a 2D image for the 2D shape
            #                                     point=pupil_on_cut)

            # draw circle at pupil_on_keyboard on the keyboard
            cv2.circle(keyboard_page, (pupil_on_keyboard[0], pupil_on_keyboard[1]), 20, (0, 255, 0), 2)
            #cv2.circle(show_windows(), (pupil_on_tkinter[0], pupil_on_tkinter[1]), 10, (0, 255, 0), 4)
            #cv2.circle(image_page, (pupil_on_image[0], pupil_on_image[1]), 10, (0, 255, 0), 4)
            # cv2.circle(image, center_coordinates, radius, color, thickness)

            if is_blinking(right_eye_coordinates):

                pressed_key = identify_key(key_points = key_points, coordinate_X = pupil_on_keyboard[1], coordinate_Y = pupil_on_keyboard[0])
                print('presses key',pressed_key)
                #print('pupil on keyboard[0] and 1',pupil_on_keyboard[0],pupil_on_keyboard[1])


                if pressed_key:

                    if pressed_key==' ':
                        '''t1 = threading.Thread(target=read_word, args=(string_to_write[5:]))
                        t1.start()'''

                        #read_word(string_to_write[5:])
                        string_to_write = string_to_write + pressed_key


                    elif pressed_key == 'del':
                        string_to_write = string_to_write[: -1]

                    elif pressed_key == '##':
                        string_to_write = string_to_write + "##"
                        new = string_to_write.split('##')[length]

                        if length == 0:
                            '''t2 = threading.Thread(target=talk, args=(new[5:]))
                            t2.start()
                            #talk(new[5:])'''
                        else:
                            '''t3 = threading.Thread(target=talk, args=(new))
                            t3.start()
                            #talk(new)'''
                        length+=1
                        print('new', new)
                        print('string_to_write', string_to_write)

                    else:
                        string_to_write = string_to_write + pressed_key
                        if len(string_to_write) > 2:
                            predictions = help_me(str(string_to_write[5:]))
                            dynamic_key_points.append([predictions[0], (100 - 10, 620), (100 - 40, 550), (100 + 200, 700)])
                            dynamic_key_points.append([predictions[1], (200 + 130, 620), (200 + 100, 550), (200 + 340, 700)])
                            dynamic_key_points.append([predictions[2], (300 + 270, 620), (300 + 240, 550.0), (300 + 480, 700)])
                            dynamic_key_points.append([predictions[3], (400 + 410, 620), (400 + 380, 550.0), (400 + 620, 700)])
                            key_points = key_points[:-4] + dynamic_key_points
                            #dysplay_keyboard(img = keyboard_page, keys = dynamic_key_points)
                            #show_window('projection', keyboard_page)
                            #time.sleep(10)
                            #dynamic_key_points = []

                            print('#############')
                            print(string_to_write[5:], type(string_to_write))
                            print(predictions)
                            print('##############')

                    '''t4 = threading.Thread(target=talk, args=(pressed_key))
                    if t4.is_alive():
                        continue
                    else:

                        t4.start()
                    #talk(pressed_key)'''

                time.sleep(0.1) # to avoid is_blinking=True in the next frame



        # print on screen the string
            y0, dy = 50,60
            for i, line in enumerate(string_to_write.split('##')):
                y = y0 + i * dy
                cv2.putText(text_page, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,0),5)

            #cv2.putText(text_page, string_to_write,(50,70), cv2.FONT_HERSHEY_SIMPLEX, 2,(0, 0, 0), 5)

        ##cv2.putText(image, text, org, font, fontScale, color[, thickness[, lineType[, bottomLeftOrigin]]])

            # visualize windows

    show_window('projection', keyboard_page)
    show_window('cut_frame', cv2.resize(cut_frame, (int(cut_frame.shape[1] *resize_eye_frame), int(cut_frame.shape[0] *resize_eye_frame))))
    show_window('text_page',text_page)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
# -------------------------------------------------------------------

shut_off(camera) # Shut camera / windows off
