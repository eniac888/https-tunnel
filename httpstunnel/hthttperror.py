
def get_http_error(error_code):
    '''Generates custom HTTP error page, can be overrided.'''
    error_code = int(error_code)
    http_error_table = {
        400: 'Bad Request',
        404: 'Not Found',
        405: 'Method Not Allowed',
        500: 'Internal Server Error',
        503: 'Service Unavailable'
    }
    return ('HTTP/1.1 %d %s\r\nContent-Length: 0\r\nConnection: close\r\n\r\n' % (error_code, http_error_table[error_code])).encode('iso-8859-1', 'replace')
