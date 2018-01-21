#!/usr/bin/env python3

import argparse
import subprocess
import time
import os
import cv2

# Import helper functions
import tutorial_helpers as helpers

# Import the Python wrapper for the ELL model
import model

def send_data(recognized_result_list):
    print("Calling send_to_hologram...")
    for (recognized_text, recognized_frame_path) in recognized_result_list:
        # encode the image in base 64
        with open(recognized_frame_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())
            # put all the data in json format
            send_to_hologram(encoded_string)

def send_to_hologram(messages, is_custom_cloud=False):
    # Hologram SDK only works in Python 2.7 enviroment. So we have to call its function in this way
    call_hologram_command = "sudo python2.7 send_to_hologram.py " + messages
    if is_custom_cloud:
        call_hologram_command = call_hologram_command + " --custom-cloud"

    with subprocess.Popen(call_hologram_command, shell=True, stdout=subprocess.PIPE,stderr=subprocess.PIPE, universal_newlines=True) as proc:
        for line in proc.stdout:
            print(line.strip("\n"), flush=True)
        for line in proc.stderr:
            print(line.strip("\n"), flush=True)

def get_image_from_camera(camera):
    """Read an image from the camera"""
    if camera:
        ret, frame = camera.read()
        if not ret:
            print("WARNING: your capture device is not returning images")
            return None
        return frame
    return None

# This function is from Microsoft ELL tutorials
def process_frame(frame, categories, frame_count, output_frame_path):
    if frame is None:
        print("Not valid input frame! Skip...")
        return

    # Get the model's input shape. We will use this information later to resize
    # images appropriately.
    input_shape = model.get_default_input_shape()

    # Get the model's output shape and create an array to hold the model's
    # output predictions
    output_shape = model.get_default_output_shape()
    predictions = model.FloatVector(output_shape.Size())

    # Prepare an image for processing
    # - Resize and center-crop to the required width and height while
    #   preserving aspect ratio.
    # - OpenCV gives the image in BGR order. If needed, re-order the
    #   channels to RGB.
    # - Convert the OpenCV result to a std::vector<float>
    input_data = helpers.prepare_image_for_model(
        frame, input_shape.columns, input_shape.rows)

    # Send the image to the compiled model and fill the predictions vector
    # with scores, measure how long it takes
    start = time.time()
    model.predict(input_data, predictions)
    end = time.time()

    # Get the value of the top 5 predictions
    top_5 = helpers.get_top_n(predictions, 5)

    if (len(top_5) > 0):
        # Generate header text that represents the top5 predictions
        header_text = ", ".join(["({:.0%}) {}".format(
            element[1], categories[element[0]]) for element in top_5])
        helpers.draw_header(frame, header_text)

        # Generate footer text that represents the mean evaluation time
        time_delta = end - start
        footer_text = "{:.0f}ms/frame".format(time_delta * 1000)
        helpers.draw_footer(frame, footer_text)

        # save the processed frame
        output_file_path = os.path.join(output_frame_path, "recognized_{}.png".format(frame_count))
        cv2.imwrite(output_file_path, frame)
        print("Processed frame {}: header text: {}, footer text: {}".format(frame_count, header_text, footer_text))
        return (header_text, output_file_path)
    else:
        print("Processed frame {}: No recognized frame!")
        return None

def analyze_video(input_video_path, output_frame_path):
    # Open the video camera. To use a different camera, change the camera
    # index.
    camera = cv2.VideoCapture(input_video_path)
    output = []

    # Read the category names
    with open("categories.txt", "r") as categories_file:
        categories = categories_file.read().splitlines()

    i = 0
    while (camera.isOpened()):
        # Get an image from the camera.
        start = time.time()
        image = get_image_from_camera(camera)
        end = time.time()
        time_delta = end - start
        print("Getting frame {}, time: {:.0f}ms".format(i, time_delta*1000))
        if not (image is None):
            result = process_frame(image, categories, i, output_frame_path)
            if result is not None:
                output.append(result)
        else:
            print("WARNING: frame is not supported! Skip!")
        i += 1

    return output

def analyze_images(input_image_dir_path, output_frame_path):
    if not os.path.exists(input_image_dir_path):
        print("Input image dir path {} does not exist. Return...".format(input_image_dir_path))
        return

    if not os.path.exists(output_frame_path):
        print("Output frame path {} does not exist. Create the folder...".format(output_frame_path))
        os.makedirs(output_frame_path)

    # Read the category names
    with open("categories.txt", "r") as categories_file:
        categories = categories_file.read().splitlines()

    output = []
    i = 0
    for image_name in os.listdir(input_image_dir_path):
        image_path = os.path.join(input_image_dir_path, image_name)
        if os.path.isfile(image_path):
            print("Predicting image:{}".format(image_path))
            image = cv2.imread(image_path)
            result = process_frame(image, categories, i, output_frame_path)
            if result is not None:
                output.append(result)
            i += 1
    return output

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Analyze an video through ELL and send the recognized result using Hologram')
    parser.add_argument('-i', '--input-path', required=True, help='The path for the video or the folder containing images to be analyzed.')
    parser.add_argument('-o', '--output-frame-path', required=True, help='The output path for recognized frame from ELL.')
    parser.add_argument('--is-video', action='store_true', help='if the input source is video')

    args = parser.parse_args()
    print("Input path {}, output recognized frame path: {}".format(args.input_path, args.output_frame_path))
    if args.is_video:
        # The output of analyze_video will be a list of tuples which includes the recognized result and
        # processed snapshot (frame)
        output = analyze_video(args.input_path, args.output_frame_path)
        print("Video has been fully analyzed. Sending the recognized result to Hologram cloud...")
    else:
        output = analyze_images(args.input_path, args.output_frame_path)
        print("All images have been fully analyzed. Sending the recognized result to Hologram cloud...")
    send_data(output)
    print("Done!")