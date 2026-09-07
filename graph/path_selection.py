def get_selected_path(critical_paths, path_id):
    """
    Return the complete information for one ranked path.
    """

    for path_data in critical_paths:

        if path_data.get("path_id") == path_id:
            return path_data

    return None