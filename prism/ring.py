from prism.segment import Segment

__all__ = ['Ring']


class Ring:
    def __init__(self, coordinates):
        self._segments = []
        for i in range(len(coordinates)-1):
            self._segments.append(Segment(coordinates[i], coordinates[i + 1]))

        for i in range(len(self._segments)-1):
            self._segments[i].prev_seg = self._segments[i - 1]
            self._segments[i].next_seg = self._segments[i + 1]

        self._segments[-1].prev_seg = self._segments[-2]
        self._segments[-1].next_seg = self._segments[0]

    @property
    def segments(self):
        return self._segments

    def merge(self, seg):
        """
        Merge the segment with next segment.
        :param seg: segment to merge
        :return: None
        """
        if seg in self.segments:
            seg.prev_seg.next_seg = seg.next_seg
            seg.next_seg.prev_seg = seg.prev_seg
            seg.next_seg.sp = seg.prev_seg.ep
            self.segments.remove(seg)

    def update(self, seg, sp, ep):
        """
        Update the segment with new start and end points.
        :param seg: segment to update
        :param sp: start point
        :param ep: end point
        :return: new segment
        """
        if seg in self.segments:
            seg.sp = sp
            seg.ep = ep
            seg.prev_seg.ep = seg.sp
            seg.next_seg.sp = seg.ep
            return seg

    def remove(self, seg, q):
        """
        Remove the segment and join two neighboring segments on q.
        :param seg: segment to remove
        :param q: new point
        :return: None
        """
        if seg in self.segments:
            seg.prev_seg.next_seg = seg.next_seg
            seg.next_seg.prev_seg = seg.prev_seg
            seg.prev_seg.ep = q
            seg.next_seg.sp = q
            self.segments.remove(seg)

    def __getitem__(self, index):
        return self.segments[index]

    def __len__(self):
        return len(self.segments)

    def __repr__(self):
        _mgs = ''
        for i in range(len(self.segments)):
            _mgs += str(self.segments[i]) + ',' if i < len(self.segments) else str(self.segments[i])
        return _mgs

    @property
    def coordinates(self):
        _coordinates = []
        for seg in self.segments:
            _coordinates.append(seg.sp)

        _coordinates.append(self.segments[-1].ep)
        return _coordinates
