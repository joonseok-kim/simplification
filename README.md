# Simplification of Indoor Space Footprints #

This project is developed for the simplification algorithm presented in the paper,
titled "Simplification of Indoor Space Footprints" by Joon-Seok Kim and Carola Wenk,
one of the accepted papers of 
[1st ACM SIGSPATIAL International Workshop on Spatial Gems (SpatialGems 2019)](https://www.spatialgems.net/).
Although it is designed to simplify footprints of indoor spaces such as a room and a corridor,
it works with footprints of buildings very well. This library can be utilized for 2/3D building simplification and
generalization.


The original code was developed by Joon-Seok Kim in C# and presented in 
["Simplification of geometric objects in an indoor space"](https://www.sciencedirect.com/science/article/pii/S0924271618303137)
<sup>[1](#isprs)</sup>.
However, the original implementation has the strong dependency on many libraries including [CGAL](https://www.cgal.org) 
(Computational Geometry Algorithms Library) to compute 3D operations.
In order to provide a light weight version, the code is ported in Python based on [Shapely](https://pypi.org/project/Shapely/).
Please make sure that Shapely and Numpy has been installed when you use the simplification.

The following code shows an example of how to use the library.
```python
import prism
from shapely.wkt import loads

polygon = loads('POLYGON ((0 0, 2 0, 2 -1.1, 2.1 -1.1, 2.1 0, 4 0, 1 1.001, 0 2, -1 1, -1 0.99, -2 0, 0 0))')
simplified_polygon = prism.simplify(polygon, tau=1)
print(simplified_polygon.wkt)
```

Copyright by Joon-Seok Kim (jkim258 at gmu.edu)

<a name="isprs">[1]</a>: Joon-Seok Kim, and Ki-Joune Li, "Simplification of geometric objects in an indoor space",
ISPRS Journal of Photogrammetry and Remote Sensing 147 (2019): 146-162

