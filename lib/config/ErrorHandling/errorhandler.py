#   Importing responsories
from werkzeug.exceptions import HTTPException, InternalServerError
#   Custom responsories

#   cs50 responsories
from lib.helpers import apology

class ErrorHandler()

    def __init__():
        return

    def httpexception(self, e):
        "   Handles HTTP Exceptions "
        if not isinstance(e, HTTPException): return apology(InternalServerError().name, InternalServerError().code)
