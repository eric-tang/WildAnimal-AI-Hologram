#!/usr/bin/env python3

import sys, getopt
import subprocess
import time
import cv2

# Import helper functions
import tutorial_helpers as helpers

# Import the Python wrapper for the ELL model
import model

def send_to_hologram(messages):
    # Hologram SDK only works in Python 2.7 enviroment. So we have to call its function in this way
    call_hologram_command = "sudo python2.7 send_to_hologram.py " + messages

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
        filepath = output_frame_path + "recognized_{}.png".format(frame_count)
        cv2.imwrite(filepath, frame)
        print "Processed frame {}: header text: {}, footer text: {}".format(frame_count, header_text, footer_text)
        return header_text
    else:
        print "Processed frame {}: No recognized frame!"
        return None

def analyze_video(input_video_path, output_frame_path):
    # Open the video camera. To use a different camera, change the camera
    # index.
    camera = cv2.VideoCapture(video_path)
    output = []

    # Read the category names
    with open("categories.txt", "r") as categories_file:
        categories = categories_file.read().splitlines()

    while (camera.isOpened()):
        # Get an image from the camera.
        start = time.time()
        image = get_image_from_camera(camera)
        end = time.time()
        time_delta = end - start
        print("Getting frame {}, time: {:.0f}ms".format(i, time_delta*1000))
        if not (image is None):
            result = process_frame(frame, categories, i)
            if result is not None:
                output.append(result)
        else:
            print("WARNING: frame is not supported! Skip!")
        i += 1

    return output

def main(argv):
    input_video_path = ''
    output_frame_path = ''
    try:
        opts, args = getopt.getopt(argv,"hi:o:",["input-video-path=","output-frame-path="])
    except getopt.GetoptError:
        print 'process_video.py -i <input_video_path> -o <output_frame_path>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'process_video.py -i <input_video_path> -o <output_frame_path>'
            sys.exit()
        elif opt in ("-i", "--input-video-path"):
            input_video_path= arg
        elif opt in ("-o", "--output-frame-path"):
            output_frame_path= arg
    print("Input video path {}, output recognized frame path: {}", input_video_path, output_frame_path)
    output = analyze_video(input_video_path, output_frame_path)
    print "Video has been fully analyzed. Sending the recognized result to Hologram clound..."
    send_to_hologram(", ".join(output))
    print "Done!"

if __name__ == "__main__":
   main(sys.argv[1:])


