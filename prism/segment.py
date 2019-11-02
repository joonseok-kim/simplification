"""
Segment to support the ring structure
"""
import numpy as np
import math

__all__ = ['Segment']


class Segment:
    """
    This class represents a segment that implements bidirectional links to previous and next segments of a ring.
    """
    def __init__(self, sp, ep):
        """
        Initialize with a pair of start and end points.
        :param sp: start point consisting of a pair of coordinates
        :param ep: end point consisting of a pair of coordinates
        """
        self._coordinates = [sp, ep]

    def _set_sp(self, sp):
        """
        Set the start point.
        :param sp: the start point
        :return: None
        """
        self._coordinates[0] = sp

    def _get_sp(self):
        """
        Get the start point.
        :return: the start point
        """
        return self._coordinates[0]

    # start point
    sp = property(_get_sp, _set_sp)

    def _set_ep(self, ep):
        """
        Set the end point.
        :param ep: the end point
        :return: None
        """
        self._coordinates[1] = ep

    def _get_ep(self):
        """
        Get the end point.
        :return: the end point
        """
        return self._coordinates[1]

    ep = property(_get_ep, _set_ep)

    def _set_next_seg(self, seg):
        """
        Set the next segment of the segment.
        :param seg: segment to link to as the next segment
        :return: None
        """
        self._next = seg

    def _get_next_seg(self):
        """
        Get the next segment of the segment.
        :return: the next segment
        """
        return self._next

    # property for the next segment
    next_seg = property(_get_next_seg, _set_next_seg)

    def _set_prev_seg(self, seg):
        """
        Set the previous segment of the segment.
        :param seg: segment to link to as the previous segment
        :return: None
        """
        self._prev = seg

    def _get_prev_seg(self):
        """
        Get the previous segment of the segment.
        :return: the previous segment
        """
        return self._prev

    # property for the previous segment
    prev_seg = property(_get_prev_seg, _set_prev_seg)

    # comparison operators used for a priority queue
    def __lt__(self, other):
        return self.length() < other.length()

    def __gt__(self, other):
        return self.length() > other.length()

    def __le__(self, other):
        return self.length() <= other.length()

    def __ge__(self, other):
        return self.length() >= other.length()

    def __repr__(self):
        return "[{}->{}]".format(self.sp, self.ep)

    def length(self):
        """
        Returns the length of the segment.
        :return: the length of the segment
        """
        return np.linalg.norm(np.array(self.sp) - np.array(self.ep))

    def angle(self):
        """
        Returns the angle between the segment and the next segment (in radian).
        :return: the angle between the segment and the next segment (in radian)
        """
        a = np.array(self.sp)
        b = np.array(self.ep)
        c = np.array(self.next_seg.ep)
        ba = a - b
        bc = c - b
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        cosine_angle = np.maximum(-1, np.minimum(1, cosine_angle))
        return np.arccos(cosine_angle)

    def slope_as_angle(self):
        """
        Returns the angle of the segment (in radian).
        :return: the angle of the segment (in radian)
        """
        b = np.array(self.sp)
        c = np.array(self.ep)

        delta = np.arctan2(c[1] - b[1], c[0] - b[0])
        if delta < 0:
            return math.pi * 2 + delta
        return delta
