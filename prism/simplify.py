from heapq import heappush, heappop, heapify
import math
from math import pi, isinf
from prism.ring import Ring
from shapely.geometry import LinearRing
from shapely.geometry import LineString
from shapely.geometry import Point
from shapely.geometry import Polygon
from shapely.wkt import loads

__all__ = ['simplify', 'simplify_ring']

# internal use for debugging
_debug_mode = False


def simplify(polygon, tau=1, epsilon=pi/36, delta=pi/180, gamma=None, merge_first=False):
    # type: (Polygon, float, float, float, float, bool) -> Polygon
    """
    Returns a simplified polygon using a simplification method considering to preserve important spatial properties.
    :param polygon: polygon to simplify
    :param tau: tolerance distance
    :param epsilon: tolerance angle
    :param delta: angle threshold used to determine if consecutive segments are collinear
    :param gamma: distance threshold used to determine whether to join neighboring segments
    :param merge_first: condition whether or not it merges neighbors first when possible
    :return: a simplified polygon
    """
    exterior = simplify_ring(polygon.exterior, tau, epsilon, delta, gamma, merge_first)
    interiors = []
    for ring in polygon.interiors:
        interiors.append(simplify_ring(ring, tau, epsilon, delta, gamma, merge_first))

    if exterior is None:
        return None
    return Polygon(exterior, interiors)


def simplify_ring(linear_ring, tau=1, epsilon=pi/36, delta=pi/180, gamma=None, merge_first=False):
    # type: (LinearRing, float, float, float, float, bool) -> LinearRing
    """
    Returns a simplified ring using a simplification method considering to preserve important spatial properties.
    :param linear_ring: ring to simplify
    :param tau: tolerance distance
    :param epsilon: tolerance angle
    :param delta: angle threshold used to determine if consecutive segments are collinear
    :param gamma: distance threshold used to determine whether to join neighboring segments
    :param merge_first: condition whether or not it merges neighbors first when possible
    :return: a simplified ring
    """
    # Initialize a priority queue
    queue = []
    push = heappush
    pop = heappop

    # deep copy from the linear ring
    _coordinates = []
    for coord in linear_ring.coords:
        _x, _y = coord
        _coordinates.append((_x, _y))
    ring = Ring(_coordinates)

    def remove_from_queue(seg):
        """
        Remove a segment from the queue.
        :param seg: segment to remove from the queue
        :return: None
        """
        try:
            queue.remove(seg)
            heapify(queue)  # it is required to keep the heap structure
        except ValueError:
            # it is possible because some segment can be removed from the queue
            pass

    def enqueue(seg):
        """
        Enqueue a segment. If the segment exists in the queue, the enqueuing is ignored.
        :param seg: segment to enqueue
        :return: None
        """
        if seg in queue:
            # avoid adding the existing segment in the queue
            pass
        else:
            push(queue, seg)

    # Enqueue all segments
    for line_segment in ring:
        enqueue(line_segment)

    def remove_middle_point(seg):
        """
        Remove the middle point between a segment and its next segment
        :param seg: segment
        :return: None
        """
        remove_from_queue(seg.next_seg)
        ring.merge(seg)
        enqueue(seg.next_seg)
        if _debug_mode:
            print('remove_middle_point:', seg.next_seg)

    def project(px, py, x, y, tan):
        """
        Return a point projected from (px,py) on the line that passes through (x, y) with the tangent.
        :param px: x coordinate of a point to project
        :param py: y coordinate of a point to project
        :param x: x coordinate of a line
        :param y: y coordinate of a line
        :param tan: tangent of a line
        :return: the projected point
        """
        if tan == 0:
            new_x = px
            new_y = y
        elif isinf(tan):
            new_x = x
            new_y = py
        else:
            cot = 1.0 / tan
            new_x = (px + tan * tan * x + tan * (py - y)) / (1 + tan * tan)
            new_y = (py + cot * cot * y + cot * (px - x)) / (1 + cot * cot)
        return new_x, new_y

    def intersection2(seg, x, y, tan):
        """
        Returns intersection of one line extending from a segment
        with the line that passes through (x, y) with the tangent.
        :param seg: segment
        :param x: x coordinate of a line
        :param y: y coordinate of a line
        :param tan: tangent of a line
        :return: intersection point. If two lines are parallel, returns None.
        """
        s1 = seg.sp
        e1 = seg.ep
        s2 = (x, y)
        e2 = (x + 1, y + tan)

        a1 = e1[1] - s1[1]
        b1 = s1[0] - e1[0]
        c1 = a1 * s1[0] + b1 * s1[1]
        a2 = e2[1] - s2[1]
        b2 = s2[0] - e2[0]
        c2 = a2 * s2[0] + b2 * s2[1]
        dt = a1 * b2 - a2 * b1
        if dt == 0:
            return None
        new_x = (b2 * c1 - b1 * c2) / dt
        new_y = (a1 * c2 - a2 * c1) / dt
        return new_x, new_y

    def intersection(a, b):
        """
        Returns intersection of two lines extending from two segments.
        :param a: segment a
        :param b: segment b
        :return: intersection point. If two lines are parallel, returns None.
        """
        t = (a.sp[0] - a.ep[0]) * (b.sp[1] - b.ep[1]) - (a.sp[1] - a.ep[1]) * (b.sp[0] - b.ep[0])
        x = (a.sp[0] * a.ep[1] - a.sp[1] * a.ep[0]) * (b.sp[0] - b.ep[0]) - (a.sp[0] - a.ep[0]) * \
            (b.sp[0] * b.ep[1] - b.sp[1] * b.ep[0])
        y = (a.sp[0] * a.ep[1] - a.sp[1] * a.ep[0]) * (b.sp[1] - b.ep[1]) - (a.sp[1] - a.ep[1]) * \
            (b.sp[0] * b.ep[1] - b.sp[1] * b.ep[0])
        if t == 0:
            # if two lines are parallel
            return None
        return x / t, y / t

    def conditional_segment_regression(seg):
        """
        Remove a middle point if the merge_first flag is set and it is appropriate.
        Otherwise, find a segment to consider both length and angle of the previous and next segments.
        :param seg: segment to regress
        :return: None
        """
        if merge_first:
            if seg.prev_seg.length() < tau and seg.next_seg.length() < tau:
                if seg.prev_seg.length() < seg.next_seg.length():
                    if LineString([seg.prev_seg.sp, seg.next_seg.sp]).length < tau:
                        remove_from_queue(seg.prev_seg)
                        remove_middle_point(seg.prev_seg)
                        return
                else:
                    if LineString([seg.prev_seg.ep, seg.next_seg.ep]).length < tau:
                        remove_middle_point(seg)
                        return
        segment_regression(seg)

    def segment_regression(seg):
        """
        Find a segment to consider both length and angle of the previous and next segments.
        :param seg: segment to regress
        :return: None
        """
        remove_from_queue(seg.prev_seg)
        remove_from_queue(seg.next_seg)

        ratio = seg.prev_seg.length()/(seg.prev_seg.length() + seg.next_seg.length())
        line = LineString([seg.sp, seg.ep])
        p = line.interpolate(ratio, normalized=True)

        a1 = seg.prev_seg.slope_as_angle()
        a2 = seg.next_seg.slope_as_angle()
        if abs(a1-a2) > math.pi:
            if a1 > a2:
                a2 += math.pi * 2
            else:
                a1 += math.pi * 2

        angle = a1 * ratio + a2 * (1 - ratio)
        angle = angle if angle <= 2 * math.pi else angle - (2 * math.pi)
        theta = math.tan(angle)
        prev2 = seg.prev_seg.prev_seg
        next2 = seg.next_seg.next_seg
        # Intersection of the previous of the previous segment with the line through p with slope theta.
        q1 = intersection2(prev2, p.xy[0][0], p.xy[1][0], theta)
        if q1 is None or LineString([prev2.sp, prev2.ep]).distance(Point(q1)) > seg.length():
            # Intersection of the previous segment with the line through p with slope theta if q1 is too far.
            q1 = project(seg.prev_seg.sp[0], seg.prev_seg.sp[1], p.xy[0][0], p.xy[1][0], theta)

        # Intersection of the next of the next segment with the line through p with slope theta.
        q2 = intersection2(next2, p.xy[0][0], p.xy[1][0], theta)
        if q2 is None or LineString([next2.sp, next2.ep]).distance(Point(q2)) > seg.length():
            # Intersection of the next segment with the line through p with slope theta if q2 is too far.
            q2 = project(seg.next_seg.ep[0], seg.next_seg.ep[1], p.xy[0][0], p.xy[1][0], theta)

        # update the segment with new two points
        seg = ring.update(seg, q1, q2)

        enqueue(seg.prev_seg)
        enqueue(seg)
        enqueue(seg.next_seg)

        if _debug_mode:
            print('regression:', p.coords.xy, theta, seg, q1, q2)

    def join_segment(seg, p):
        """
        Remove a segment and join the previous and next segments with point p
        :param seg: target segment
        :param p: join point
        :return: None
        """
        remove_from_queue(seg.prev_seg)
        remove_from_queue(seg.next_seg)

        ring.remove(seg, p)
        enqueue(seg.prev_seg)
        enqueue(seg.next_seg)
        if _debug_mode:
            print('join:', p)

    def translate_segment(seg):
        """
        Translate segments depending on the length of the previous and next segments
        :param seg: target segment
        :return: None
        """
        remove_from_queue(seg.prev_seg)
        remove_from_queue(seg.next_seg)
        prev_length = seg.prev_seg.length()
        next_length = seg.next_seg.length()
        p = 'same length'
        if prev_length < next_length:
            p = seg.ep[0] - (seg.prev_seg.ep[0] - seg.prev_seg.sp[0]), seg.ep[1] - \
                (seg.prev_seg.ep[1] - seg.prev_seg.sp[1])
            ring.update(seg, seg.prev_seg.sp, p)
            ring.update(seg.next_seg, p, seg.next_seg.ep)
            ring.remove(seg.prev_seg, seg.sp)
            enqueue(seg)
            enqueue(seg.next_seg)
        elif prev_length > next_length:
            p = seg.sp[0] + (seg.next_seg.ep[0] - seg.next_seg.sp[0]), seg.sp[1] + \
                (seg.next_seg.ep[1] - seg.next_seg.sp[1])
            ring.update(seg.prev_seg, seg.prev_seg.sp, p)
            ring.update(seg, p, seg.next_seg.ep)
            ring.remove(seg.next_seg, seg.ep)
            enqueue(seg)
            enqueue(seg.prev_seg)
        else:
            ring.update(seg, seg.prev_seg.sp, seg.next_seg.ep)
            ring.remove(seg.next_seg, seg.ep)
            ring.remove(seg.prev_seg, seg.sp)
            enqueue(seg)

        if _debug_mode:
            print('translate:', p)

    # main iteration for simplification
    while len(queue) > 0 and len(ring) >= 3:
        s = pop(queue)  # de-queue the next segment
        if _debug_mode:
            print('de-queue:', len(queue), s.length(), s, s.angle())

        dirty = True  # flag used to check if the ring changes
        if pi - delta < s.angle() < pi + delta:
            # if two segments are approximately collinear.
            remove_middle_point(s)
        elif s.length() <= tau:
            _a1 = s.prev_seg.slope_as_angle()
            _a2 = s.next_seg.slope_as_angle()
            if abs(_a1 - _a2) > math.pi:
                if _a1 > _a2:
                    _a2 += math.pi * 2
                else:
                    _a1 += math.pi * 2
            alpha = abs(_a1 - _a2)
            alpha = min(alpha, abs(alpha - pi*2))
            if 0 <= alpha <= epsilon:
                conditional_segment_regression(s)
            elif pi - alpha <= epsilon:
                translate_segment(s)
            else:
                # Intersection of two lines obtained by extending the previous and next segments
                q = intersection(s.prev_seg, s.next_seg)
                _gamma = s.length() if gamma is None else gamma
                _gamma = min(_gamma, tau)
                if q is not None and LineString([s.sp, s.ep]).distance(Point(q)) <= _gamma:
                    join_segment(s, q)
                elif s.prev_seg.length() < s.next_seg.length():
                    remove_from_queue(s.prev_seg)
                    remove_middle_point(s.prev_seg)
                else:
                    remove_middle_point(s)
        else:
            dirty = False

        if _debug_mode:
            # print(queue)
            if dirty:
                print(Polygon(ring.coordinates).wkt)

    if len(ring.coordinates) < 3:
        return None
    return LinearRing(ring.coordinates)


def _test():
    """
    Test simplification with a simple polygon.
    :return:
    """
    polygon = loads('POLYGON ((0 0, 2 0, 2 -1.1, 2.1 -1.1, 2.1 0, 4 0, 1 1.0001, 0 2, -1 1, -1 0.99, -2 0, 0 0))')
    print(polygon.wkt)
    new_polygon = simplify(polygon)
    print(new_polygon.wkt)
    hausdorff = polygon.hausdorff_distance(new_polygon)
    print('Hausdorff Distance', hausdorff)
    union = polygon.union(new_polygon)
    intersection = polygon.intersection(new_polygon)
    area_ratio = intersection.area/union.area
    print('Jaccard Index', area_ratio)


if __name__ == '__main__':
    _debug_mode = False
    _test()
