###############################################################################
#
#  Project:  Embedded Learning Library (ELL)
#  File:     tutorial_helpers.py
#  Authors:  Chris Lovett
#            Byron Changuion
#            Kern Handa
#
#  Requires: Python 3.x
#
###############################################################################

import os
import sys
import math
import platform
import cv2
import numpy as np

# Find any child directory that matches the four deployment targets (pi3,
# pi3_64, aarch64, host) or begins with "model". For all these directories,
# add it and its platform-specific build directory to Python's import lookup
# path
SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
SEARCH_DIRS = [d for d in os.listdir(SCRIPT_PATH) if
               os.path.isdir(d) and (
               d in ["pi3", "pi3_64", "aarch64", "host"] or
               d.startswith("model"))]
sys.path += SEARCH_DIRS
sys.path += [os.path.join(d, "build") for d in SEARCH_DIRS]
if platform.system() == "Windows":
    sys.path += [os.path.join(d, "build", "Release") for d in SEARCH_DIRS]
else:
    sys.path += [os.path.join(d, "build") for d in SEARCH_DIRS]

def prepare_image_for_model(image, width, height, reorder_to_rgb=False):
    """Prepare an image for use with a model. Typically, this involves:
        - Resize and center crop to the required width and height while
          preserving the image's aspect ratio.
          Simple resize may result in a stretched or squashed image which will
          affect the model's ability to classify images.
        - OpenCV gives the image in BGR order, so we may need to re-order the
          channels to RGB.
        - Convert the OpenCV result to a std::vector<float> for use with the
          ELL model.
    """
    if image.shape[0] > image.shape[1]:  # Tall (more rows than columns)
        row_start = int((image.shape[0] - image.shape[1]) / 2)
        row_end = row_start + image.shape[1]
        col_start = 0
        col_end = image.shape[1]
    else:  # Wide (more columns than rows)
        row_start = 0
        row_end = image.shape[0]
        col_start = int((image.shape[1] - image.shape[0]) / 2)
        col_end = col_start + image.shape[0]

    # Center crop the image maintaining aspect ratio
    cropped = image[row_start:row_end, col_start:col_end]

    # Resize to model's requirements
    resized = cv2.resize(cropped, (height, width))

    # Re-order color channels if needed
    if reorder_to_rgb:
        resized = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    # Return as a vector of floats
    result = resized.astype(np.float).ravel()
    return result


def get_top_n(predictions, n=5, threshold=0.20):
    """Return at most the top N predictions as a list of tuples that meet the
    threshold.
    The first of element of each tuple represents the index or class of the
    prediction and the second element represents that probability or confidence
    value.
    """
    filtered_predictions = [(i, predictions[i]) for i in
                            range(len(predictions)) if predictions[i] >=
                            threshold]
    filtered_predictions.sort(key=lambda tup: tup[1], reverse=True)
    result = filtered_predictions[:n]
    return result


def get_mean_duration(accumulated, duration, max_accumulation_entries=30):
    """Add a duration to an array and calculate the mean duration."""
    accumulated.append(duration)
    if (len(accumulated) > max_accumulation_entries):
        accumulated.pop(0)
    durations = np.array(accumulated)
    mean = np.mean(durations)
    return mean


def draw_header(image, text):
    """Helper to draw header text block onto an image"""
    draw_text_block(image, text, (0, 0), (50, 200, 50))
    return


def draw_footer(image, text):
    """Helper to draw footer text block onto an image"""
    draw_text_block(image, text, (0, image.shape[0] - 40), (200, 100, 100))
    return


def draw_text_block(image, text, block_top_left=(0, 0),
                    block_color=(50, 200, 50), block_height=40):
    """Helper to draw a filled rectangle with text onto an image"""
    FONT_SCALE = 0.7
    cv2.rectangle(
        image, block_top_left, (image.shape[1], block_top_left[1] +
                                block_height),
        block_color, cv2.FILLED)

    cv2.putText(
        image, text, (
            block_top_left[0] + int(block_height / 4), block_top_left[1] +
            int(block_height * 0.667)),
        cv2.FONT_HERSHEY_COMPLEX_SMALL, FONT_SCALE, (0, 0, 0), 1, cv2.LINE_AA)


class TiledImage:
    """ Helper class to create a tiled image out of many smaller images.
        The class calculates how many horizontal and vertical blocks are needed
        to fit the requested number of images and fills in unused blocks as
        blank. For example, to fit 4 images, the number of tiles is 2x2, to fit
        5 images, the number of tiles is 3x2, with the last tile being blank.

        `numImages` - the maximum number of images that need to be composed
        into the tiled image. Note that the actual number of tiles is equal
        to or larger than this number.

        `outputHeightAndWidth` - a list of two values giving the rows and
        columns of the output image. The output tiled image is a
        composition of sub images.
    """
    def __init__(self, numImages=2, outputHeightAndWidth=(600, 800)):
        self.composed_image_shape = self.get_composed_image_shape(numImages)
        self.number_of_tiles = (self.composed_image_shape[0] *
                                self.composed_image_shape[1])
        self.output_height_and_width = outputHeightAndWidth
        self.images = None
        self.window_name = "ELL side by side"

        # Ensure the window is resizable
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)

        # The aspect ratio of the composed image is now
        # self.composed_image_shape[0] : self.composed_image_shape[1]
        # Adjust the height of the window to account for this, else images
        # will look distorted
        cv2.resizeWindow(
            self.window_name, outputHeightAndWidth[1],
            int(outputHeightAndWidth[0] * (
                self.composed_image_shape[0] / self.composed_image_shape[1])))

    def get_composed_image_shape(self, num_images):
        """Returns a tuple indicating the (rows,cols) of the required number of
        tiles to hold `num_images`.
        """
        # Split the image horizontally
        num_horizontal = math.ceil(math.sqrt(num_images))
        # Split the image vertically
        num_vertical = math.ceil(num_images / num_horizontal)

        return (num_vertical, num_horizontal)

    def resize_to_same_height(self, images):
        """Resizes a list of images to the minimum height among the images"""
        min_height = min([i.shape[0] for i in images])
        for i, image in enumerate(images):
            shape = image.shape
            height = shape[0]
            if height > min_height:
                scale = min_height / height
                new_size = (int(shape[1] * scale), int(shape[0] * scale))
                images[i] = cv2.resize(image, new_size)
        return images

    def compose(self):
        """Composes an image made by tiling all the sub-images set with
        `set_image_at`.
        """
        y_elements = []
        for vertical_index in range(self.composed_image_shape[0]):
            x_elements = []
            for horizontal_index in range(self.composed_image_shape[1]):
                current_index = (
                    vertical_index * self.composed_image_shape[1] +
                    horizontal_index)
                x_elements.append(self.images[current_index])

            # np.hstack only works if the images are the same height
            x_elements = self.resize_to_same_height(x_elements)
            horizontal_image = np.hstack(tuple(x_elements))
            y_elements.append(horizontal_image)

        composed_img = np.vstack(tuple(y_elements))

        # Draw separation lines
        y_step = int(composed_img.shape[0] / self.composed_image_shape[0])
        x_step = int(composed_img.shape[1] / self.composed_image_shape[1])
        y = y_step
        x = x_step

        for horizontal_index in range(1, self.composed_image_shape[1]):
            cv2.line(composed_img, (x, 0), (x, composed_img.shape[0]),
                     (0, 0, 0), 3)
            x += x_step

        for vertical_index in range(1, self.composed_image_shape[0]):
            cv2.line(composed_img, (0, y), (composed_img.shape[1], y),
                     (0, 0, 0), 3)
            y += y_step

        return composed_img

    def set_image_at(self, image_index, frame):
        """Sets the image at the specified index. Once all images have been
        set, the tiled image result can be retrieved with `compose`.
        """
        # Ensure self.images is initialized.
        if self.images is None:
            self.images = [None] * self.number_of_tiles
            for i in range(self.number_of_tiles):
                self.images[i] = np.zeros((frame.shape), np.uint8)

        # Update the image at the specified index
        if image_index < self.number_of_tiles:
            self.images[image_index] = frame
            return True
        return False

    def show(self):
        """Shows the final result of the tiled image. Returns True if the user
        indicates they are done viewing by pressing `Esc`.
        """
        # Compose the tiled image
        image_to_show = self.compose()
        # Show the tiled image
        cv2.imshow(self.window_name, image_to_show)


def play_sound(sound_file):
    """Plays the audio file that is at the fully qualified path `sound_file`"""
    system = platform.system()
    if system == "Windows":
        import winsound
        winsound.PlaySound(sound_file,
                           winsound.SND_FILENAME | winsound.SND_ASYNC)
    elif system == "Darwin":  # macOS
        from AppKit import NSSound
        from Foundation import NSURL
        cwd = os.getcwd()
        url = NSURL.URLWithString_("file://" + sound_file)
        NSSound.alloc().initWithContentsOfURL_byReference_(url, True).play()
    else:  # Linux
        import subprocess
        command = ["aplay", sound_file]
        subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            bufsize=0, universal_newlines=True)
