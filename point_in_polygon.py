def point_in_polygon(x, y, polygon):
    """
    Determine if point (x, y) is inside a polygon.
    
    Args:
        x (float): x-coordinate of the point.
        y (float): y-coordinate of the point.
        polygon (list of tuples): list of (x, y) vertices of the polygon in order.

    Returns:
        bool: True if point is inside polygon, False otherwise.
    """
    inside = False
    n = len(polygon)

    for i in range(n):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % n]  # wrap to first vertex
        
        # Check if ray intersects edge
        if ((y1 > y) != (y2 > y)):
            # Intersection point's x-coordinate
            x_intersect = (x2 - x1) * (y - y1) / (y2 - y1) + x1
            if x < x_intersect:
                inside = not inside

    return inside
