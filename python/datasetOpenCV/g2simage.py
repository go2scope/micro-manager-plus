"""
Go2Scope image

Image representation for go2scope
"""


class G2SImage:
    """ go2scope image """

    def __init__(self, cv2image, z_pos):
        self.z = z_pos
        self.pixels = cv2image
