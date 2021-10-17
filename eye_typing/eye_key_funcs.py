import cv2
import numpy as np
import random
import time
import dlib
import sys
import nltk
import time
from collections import defaultdict
import pygtrie
import re
import os
import argparse
import pyttsx3

voiceEngine = pyttsx3.init()
newVoiceRate = 250
newVolume = 1
voiceEngine.setProperty('rate', newVoiceRate)
voiceEngine.setProperty('volume', newVolume)
# # ------------------------------------ Inputs
ratio_blinking = 0.2  # calibrate with my eyes
dict_color = {'green': (0, 255, 0),
              'blue': (255, 0, 0),
              'red': (0, 0, 255),
              'yellow': (0, 255, 255),
              'white': (255, 255, 255),
              'black': (0, 0, 0)}


# # ------------------------------------
# -----   Initialize camera
# Use cv2.VideoCapture() to get a video capture object for the camera.
# Set up an infinite while loop and use the read() method to read the frames using the above created object.
# Use cv2.imshow() method to show the frames in the video.
# Breaks the loop when the user clicks a specific key.
def init_camera(camera_ID):
    camera = cv2.VideoCapture(0)
    return camera


# --------------------------------------------------

# -----  black page [3 channels]
def make_black_page(size):
    page = (np.zeros((int(size[0]), int(size[1]), 3))).astype('uint8')
    return page


# --------------------------------------------------

# ----- Make white page [3 channels]
def make_white_page(size):
    page = (np.zeros((int(size[0]), int(size[1]), 3)) + 255).astype('uint8')
    return page


# --------------------------------------------------

# -----   Rotate / flip / everything else (NB: depends on camera conf)
def adjust_frame(frame):
    # frame = cv2.rotate(frame, cv2.ROTATE_180)
    frame = cv2.flip(frame, 1)
    return frame


# --------------------------------------------------

# ----- Shut camera / windows off
def shut_off(camera):
    camera.release()  # When everything done, release the capture
    cv2.destroyAllWindows()


# --------------------------------------------------

# ----- Show a window
def show_window(title_window, window):
    cv2.namedWindow(title_window)
    cv2.imshow(title_window, window)


# --------------------------------------------------

# ----- show on frame a box containing the face
def display_box_around_face(img, box, color, size):
    x_left, y_top, x_right, y_bottom = box[0], box[1], box[2], box[3]
    cv2.rectangle(img, (x_left - size[0], y_top - size[1]), (x_right + size[0], y_bottom + size[1]),
                  dict_color[color], 5)
    # cv2.rectangle(image, start_point, end_point, color, thickness)


# --------------------------------------------------

# ----- get mid point
def half_point(p1, p2):
    return int((p1.x + p2.x) / 2), int((p1.y + p2.y) / 2)


# --------------------------------------------------

# ----- get coordinates eye
def get_eye_coordinates(landmarks, points):
    x_left = (landmarks.part(points[0]).x, landmarks.part(points[0]).y)
    x_right = (landmarks.part(points[3]).x, landmarks.part(points[3]).y)

    y_top = half_point(landmarks.part(points[1]), landmarks.part(points[2]))
    y_bottom = half_point(landmarks.part(points[5]), landmarks.part(points[4]))

    return x_left, x_right, y_top, y_bottom


# --------------------------------------------------

# ----- draw line on eyes
def display_eye_lines(img, coordinates, color):
    cv2.line(img, coordinates[0], coordinates[1], dict_color[color], 2)
    cv2.line(img, coordinates[2], coordinates[3], dict_color[color], 2)


# --------------------------------------------------

# ----- draw circle at face landmark points
def display_face_points(img, landmarks, points_to_draw, color):
    for point in range(points_to_draw[0], points_to_draw[1]):
        x = landmarks.part(point).x
        y = landmarks.part(point).y
        cv2.circle(img, (x, y), 4, dict_color[color], 2)


# --------------------------------------------------

# ----- function to check blinking
def is_blinking(eye_coordinates):
    blinking = False

    major_axis = np.sqrt(
        (eye_coordinates[1][0] - eye_coordinates[0][0]) ** 2 + (eye_coordinates[1][1] - eye_coordinates[0][1]) ** 2)
    minor_axis = np.sqrt(
        (eye_coordinates[3][0] - eye_coordinates[2][0]) ** 2 + (eye_coordinates[3][1] - eye_coordinates[2][1]) ** 2)

    ratio = minor_axis / major_axis

    if ratio < ratio_blinking: blinking = True

    return blinking


# --------------------------------------------------

# ----- find the limits of frame-cut around the calibrated box
def find_cut_limits(calibration_cut):
    x_cut_max = np.array(calibration_cut)
    x_cut_min = np.array(calibration_cut)
    y_cut_max = np.array(calibration_cut)
    y_cut_min = np.array(calibration_cut)

    x_cut_max1 = np.transpose(x_cut_max)
    x_cut_min1 = np.transpose(x_cut_min)
    y_cut_max1 = np.transpose(y_cut_max)
    y_cut_min1 = np.transpose(y_cut_min)

    x_cut_max2 = x_cut_max1[0].max()
    x_cut_min2 = x_cut_min1[0].min()
    y_cut_max2 = y_cut_max1[1].max()
    y_cut_min2 = y_cut_min1[1].min()
    '''print("x_cut_min",x_cut_min)
    print("x_cut_max",x_cut_max)
    print("y_cut_min",y_cut_min)
    print("y_cut_max",y_cut_max)

    print("x_cut_min1", x_cut_min1)
    print("x_cut_max1", x_cut_max1)
    print("y_cut_min1", y_cut_min1)
    print("y_cut_max1", y_cut_max1)'''

    # print("x_cut_min2", x_cut_min2)
    # print("x_cut_max2", x_cut_max2)
    # print("y_cut_min2", y_cut_min2)
    # print("y_cut_max2", y_cut_max2)

    return x_cut_min2, x_cut_max2, y_cut_min2, y_cut_max2


# --------------------------------------------------

# ----- find if the pupil is in the calibrated frame
def pupil_on_cut_valid(pupil_on_cut, cut_frame):
    in_frame_cut = False
    condition_x = ((pupil_on_cut[0] > 0) & (pupil_on_cut[0] < cut_frame.shape[1]))
    condition_y = ((pupil_on_cut[1] > 0) & (pupil_on_cut[1] < cut_frame.shape[0]))
    if condition_x and condition_y:
        in_frame_cut = True
    # print("cut fram.shape[0]", cut_frame.shape[0])
    # print("cut fram.shape[1]", cut_frame.shape[1])
    # print("result for pupil on cut valid",in_frame_cut)

    return in_frame_cut


# --------------------------------------------------

# ----- find projection on page
def project_on_page(img_from, img_to, point):
    scale = (np.array(img_to.shape) / np.array(img_from.shape))  # .astype('int')

    projected_point = (point * scale).astype('int')
    # print(projected_point)
    # print('####')

    return projected_point


# --------------------------------------------------

# -----   display keys on frame, frame by frame
def dysplay_keyboard(img, keys):
    color_board = (255, 250, 100)
    thickness1 = 4
    # i=50
    # j=100
    for key in keys:
        # print("key[0]",key[0])
        # print("key[1]",key[1])

        cv2.putText(img, key[0], (int(key[1][0]), int(key[1][1])), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 0, 100),
                    thickness=3)
        # cv2.putText(img, (i,j), (i,j), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 0, 100), thickness = 3)

        cv2.rectangle(img, (int(key[2][0]), int(key[2][1])), (int(key[3][0]), int(key[3][1])), color_board, thickness1)
        # cv2.rectangle(img, (i,j), (i,j), color_board, thickness1)


# ----------------------------str----------------------

# -----   check key on keyboard and take input
def identify_key(key_points, coordinate_X, coordinate_Y):
    pressed_key = False
    # print('coordinatex coordinatey',coordinate_X, coordinate_Y)
    for key in range(0, len(key_points)):
        condition_1 = np.mean(np.array([coordinate_Y, coordinate_X]) > np.array(key_points[key][2]))
        condition_2 = np.mean(np.array([coordinate_Y, coordinate_X]) < np.array(key_points[key][3]))

        if int(condition_1 + condition_2) == 2:
            pressed_key = key_points[key][0]
            break

    return pressed_key


# --------------------------------------------------

# -----   compute eye's radius
def take_radius_eye(eye_coordinates):
    radius = np.sqrt(
        (eye_coordinates[3][0] - eye_coordinates[2][0]) ** 2 + (eye_coordinates[3][1] - eye_coordinates[2][1]) ** 2)
    return int(radius)


# --------------------------------------------------
def talk(pressed_key):
    if pressed_key == '.':
        voiceEngine.say('dot')
        voiceEngine.runAndWait()

    elif pressed_key == '?':
        voiceEngine.say('questionmark')
        voiceEngine.runAndWait()
    elif pressed_key == ' ':
        voiceEngine.say('space')
        voiceEngine.runAndWait()
    elif pressed_key == '##':
        voiceEngine.say('newline')
        voiceEngine.runAndWait()
    elif pressed_key == "'":
        voiceEngine.say('Apostrophe')
        voiceEngine.runAndWait()
    elif pressed_key == "!":
        voiceEngine.say('Exclamationmark')
        voiceEngine.runAndWait()
    elif pressed_key == "del":
        voiceEngine.say('delete')
        voiceEngine.runAndWait()
    else:
        voiceEngine.say(pressed_key)
        if voiceEngine._inLoop:
            voiceEngine.endLoop()
        else:

            voiceEngine.runAndWait()
        voiceEngine.runAndWait()




def read_word(string):
    r = ""
    for i in string[::-1]:
        if i != " " and i!="#":
            r = r + i
        else:
            break
    r = r[::-1]
    print('r', r)
    voiceEngine.say(r)
    voiceEngine.runAndWait()
    return





