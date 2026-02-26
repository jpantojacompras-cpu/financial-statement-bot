def health_check():
    """
    Health check endpoint to verify if the service is running.
    Returns a simple JSON response with status.
    """
    return jsonify({'status': 'healthy'}), 200

@bp.route('/delete_all_files', methods=['DELETE'])
def delete_all_files():
    """
    Endpoint to delete all files in the specified directory.
    Requires appropriate permissions.
    """
    # Implement the logic to delete files here
    return jsonify({'message': 'All files deleted successfully.'}), 200
